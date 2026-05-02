"""Tornado API handlers for the basic terminal extension."""
from __future__ import annotations

import json
import os

import tornado
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join


URL_PREFIX = "jupyterlab-basic-terminal-extension"


class LaunchTerminalHandler(APIHandler):
    """Spawn a JL terminal whose pty's only process is the supplied argv.

    Bypasses ``terminal:create-new`` (which spawns the user's $SHELL) by
    calling ``jupyter_server_terminals``' ``TerminalManager.create`` with
    terminado's per-call ``shell_command`` kwarg. The pty's only process is
    the caller-supplied utility - when it exits, the JL tab closes.
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
            if not isinstance(cwd, str) or not os.path.isdir(cwd):
                self.set_status(400)
                self.finish(json.dumps({"error": "invalid_cwd"}))
                return

        terminal_manager = self.settings.get("terminal_manager")
        if terminal_manager is None:
            self.set_status(503)
            self.finish(json.dumps({"error": "terminal_service_unavailable"}))
            return

        kwargs: dict = {"shell_command": argv}
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
