import json
import os

import pytest

from jupyterlab_basic_terminal_extension import routes


URL_PATH = ("jupyterlab-basic-terminal-extension", "launch-terminal")


async def _post(jp_fetch, body):
    return await jp_fetch(
        *URL_PATH,
        method="POST",
        body=json.dumps(body),
    )


def _spawned_cwd(jp_serverapp, terminal_name):
    """Read the live cwd of the spawned pty process straight from /proc."""
    term = jp_serverapp.web_app.settings["terminal_manager"].terminals[terminal_name]
    return os.readlink(f"/proc/{term.ptyproc.pid}/cwd")


async def test_invalid_json(jp_fetch):
    with pytest.raises(Exception) as exc:
        await jp_fetch(
            *URL_PATH,
            method="POST",
            body="not json",
        )
    assert "400" in str(exc.value)


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"argv": []},
        {"argv": "echo hello"},
        {"argv": [""]},
        {"argv": [123]},
    ],
)
async def test_invalid_argv(jp_fetch, body):
    with pytest.raises(Exception) as exc:
        await _post(jp_fetch, body)
    assert "400" in str(exc.value)


async def test_invalid_cwd(jp_fetch):
    with pytest.raises(Exception) as exc:
        await _post(
            jp_fetch,
            {"argv": ["echo", "hi"], "cwd": "/this/path/does/not/exist/xyz"},
        )
    assert "400" in str(exc.value)


async def test_launch_returns_terminal_name(jp_fetch, tmp_path):
    response = await _post(
        jp_fetch,
        {"argv": ["echo", "hello"], "cwd": str(tmp_path)},
    )
    assert response.code == 200
    payload = json.loads(response.body)
    assert isinstance(payload.get("terminal_name"), str)
    assert payload["terminal_name"]


async def test_launch_without_cwd(jp_fetch):
    response = await _post(jp_fetch, {"argv": ["echo", "hello"]})
    assert response.code == 200
    payload = json.loads(response.body)
    assert isinstance(payload.get("terminal_name"), str)


async def test_relative_cwd_resolves_under_root(jp_fetch, jp_serverapp):
    subdir = os.path.join(jp_serverapp.root_dir, "browser-subdir")
    os.makedirs(subdir, exist_ok=True)
    response = await _post(
        jp_fetch,
        {"argv": ["sleep", "60"], "cwd": "browser-subdir"},
    )
    assert response.code == 200
    payload = json.loads(response.body)
    assert _spawned_cwd(jp_serverapp, payload["terminal_name"]) == os.path.realpath(
        subdir
    )


async def test_empty_cwd_resolves_to_root(jp_fetch, jp_serverapp):
    response = await _post(jp_fetch, {"argv": ["sleep", "60"], "cwd": ""})
    assert response.code == 200
    payload = json.loads(response.body)
    assert _spawned_cwd(jp_serverapp, payload["terminal_name"]) == os.path.realpath(
        jp_serverapp.root_dir
    )


async def test_absolute_cwd_spawns_in_that_dir(jp_fetch, jp_serverapp, tmp_path):
    response = await _post(
        jp_fetch,
        {"argv": ["sleep", "60"], "cwd": str(tmp_path)},
    )
    assert response.code == 200
    payload = json.loads(response.body)
    assert _spawned_cwd(jp_serverapp, payload["terminal_name"]) == os.path.realpath(
        str(tmp_path)
    )


async def test_nonexistent_relative_cwd(jp_fetch):
    with pytest.raises(Exception) as exc:
        await _post(
            jp_fetch,
            {"argv": ["echo", "hi"], "cwd": "does/not/exist/xyz"},
        )
    assert "400" in str(exc.value)
    assert json.loads(exc.value.response.body)["error"] == "invalid_cwd"


def test_waiter_shrinks_the_pty_before_arming_the_resize_trap():
    """Terminado only resizes when the client size differs from the pty's,
    so without a sentinel a client fitting to the 24x80 spawn default sends
    nothing and the waiter stalls for its whole budget. Shrinking first
    guarantees a difference; the trap must be armed after, or the
    self-inflicted SIGWINCH ends the wait immediately."""
    sentinel = f"stty rows {routes._INIT_SENTINEL_ROWS} cols {routes._INIT_SENTINEL_COLS}"
    assert routes._INIT_WAITER.index(sentinel) < routes._INIT_WAITER.index("trap")
    assert (routes._INIT_SENTINEL_ROWS, routes._INIT_SENTINEL_COLS) != (24, 80)


def test_waiter_restores_a_usable_size_when_no_client_arrives():
    """The sentinel must not survive into the launched process: a headless
    run would otherwise execute in a 1x1 terminal."""
    assert "stty rows 24 cols 80" in routes._INIT_WAITER


def test_init_wait_backstop_outlasts_the_frontend_roundtrip():
    """Only reached when no client ever attaches, but it still has to
    outlast POST -> terminal:open, or the freed name lets JupyterLab spawn
    the user's shell in place of the utility."""
    assert routes._INIT_WAIT_POLLS >= 50  # 0.1s per poll -> >= 5s
    assert f"seq 1 {routes._INIT_WAIT_POLLS}" in routes._INIT_WAITER


def test_argv_is_wrapped_in_bash_without_a_login_shell():
    wrapped = routes._wrap_with_init(["echo", "hi"])
    assert wrapped[0] == routes._INIT_SHELL == "/bin/bash"
    assert wrapped[1] == "-c"
    assert wrapped[-2:] == ["echo", "hi"]
