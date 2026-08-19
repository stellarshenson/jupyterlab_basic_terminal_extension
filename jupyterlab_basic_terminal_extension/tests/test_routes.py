import json
import os

import pytest


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
