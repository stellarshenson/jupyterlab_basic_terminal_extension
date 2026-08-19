"""Tornado API handlers for the basic terminal extension."""
from __future__ import annotations

import json
import os

import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join


URL_PREFIX = "jupyterlab-basic-terminal-extension"

# bash one-liner that waits for the JL WebSocket client to resize the pty
# from terminado's default 24x80 before `exec`ing the real argv. A fixed
# size-threshold check is a no-op (24x80 already passes any "is at least
# 80 cols" test), so we capture the initial size, install a WINCH trap,
# and break on either signal or a polled size diff. The exec replaces
# bash so the pty's only process is the target - auto-close on exit
# still works. 5s timeout means if no client ever connects we still
# launch rather than hanging the pty forever.
_INIT_WAITER = (
    "trap 'CHANGED=1' WINCH; "
    "read R0 C0 < <(stty size 2>/dev/null || echo '0 0'); "
    "for i in $(seq 1 50); do "
    'if [ -n "$CHANGED" ]; then break; fi; '
    "read r c < <(stty size 2>/dev/null || echo '0 0'); "
    'if [ "$r" != "$R0" ] || [ "$c" != "$C0" ]; then break; fi; '
    "sleep 0.1; "
    "done; "
    "clear; "
    'exec "$@"'
)


def _wrap_with_init(argv: list[str]) -> list[str]:
    """Prepend the terminal-init waiter so the spawned argv only starts once
    the JL terminal widget has connected and sized the pty."""
    return ["/bin/bash", "-c", _INIT_WAITER, "basic-terminal-init", *argv]


class LaunchTerminalHandler(APIHandler):
    """Spawn a JL terminal whose pty's only process is the supplied argv.

    Bypasses ``terminal:create-new`` (which spawns the user's $SHELL) by
    calling ``jupyter_server_terminals``' ``TerminalManager.create`` with
    terminado's per-call ``shell_command`` kwarg. A short bash waiter
    (``_INIT_WAITER``) ``exec``s into the caller-supplied argv only after
    the WebSocket client has resized the pty to a usable window, so dialog /
    TUI utilities see a real terminal size at launch instead of the pty's
    default. After exec the pty's only process is the target - when it
    exits, the JL tab closes.
    """

    @tornado.web.authenticated
    async def post(self) -> None:
        try:
            body = json.loads(self.request.body or b"{}")
        except json.JSONDecodeError:
            self.set_status(400)
            self.finish(json.dumps({"error": "invalid_json"}))
            return

        argv = body.get("argv")
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(a, str) and a for a in argv)
        ):
            self.set_status(400)
            self.finish(json.dumps({"error": "invalid_argv"}))
            return

        cwd = body.get("cwd")
        if cwd is not None:
            if not isinstance(cwd, str):
                self.set_status(400)
                self.finish(json.dumps({"error": "invalid_cwd"}))
                return
            # Non-absolute cwd is a server-relative API path (what the file
            # browser reports; '' is the server root itself) - resolve it
            # against the server root before validating.
            if not os.path.isabs(cwd):
                root = os.path.expanduser(self.settings["server_root_dir"])
                cwd = os.path.join(root, cwd)
            if not os.path.isdir(cwd):
                self.set_status(400)
                self.finish(json.dumps({"error": "invalid_cwd"}))
                return

        terminal_manager = self.settings.get("terminal_manager")
        if terminal_manager is None:
            self.set_status(503)
            self.finish(json.dumps({"error": "terminal_service_unavailable"}))
            return

        kwargs: dict = {"shell_command": _wrap_with_init(argv)}
        if cwd is not None:
            kwargs["cwd"] = cwd
        model = terminal_manager.create(**kwargs)

        name = (
            model.get("name") if isinstance(model, dict) else getattr(model, "name", None)
        )
        if not isinstance(name, str):
            self.set_status(500)
            self.finish(json.dumps({"error": "terminal_create_failed"}))
            return

        self.finish(json.dumps({"terminal_name": name}))


def setup_route_handlers(web_app) -> None:
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]

    handlers = [
        (
            url_path_join(base_url, URL_PREFIX, "launch-terminal"),
            LaunchTerminalHandler,
        ),
    ]

    web_app.add_handlers(host_pattern, handlers)
