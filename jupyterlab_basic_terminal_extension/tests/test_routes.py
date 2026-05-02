import json

import pytest


URL_PATH = ("jupyterlab-basic-terminal-extension", "launch-terminal")


async def _post(jp_fetch, body):
    return await jp_fetch(
        *URL_PATH,
        method="POST",
        body=json.dumps(body),
    )


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
