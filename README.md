# jupyterlab_basic_terminal_extension

[![GitHub Actions](https://github.com/stellarshenson/jupyterlab_basic_terminal_extension/actions/workflows/build.yml/badge.svg)](https://github.com/stellarshenson/jupyterlab_basic_terminal_extension/actions/workflows/build.yml)
[![npm version](https://img.shields.io/npm/v/jupyterlab_basic_terminal_extension.svg)](https://www.npmjs.com/package/jupyterlab_basic_terminal_extension)
[![PyPI version](https://img.shields.io/pypi/v/jupyterlab-basic-terminal-extension.svg)](https://pypi.org/project/jupyterlab-basic-terminal-extension/)
[![Total PyPI downloads](https://static.pepy.tech/badge/jupyterlab-basic-terminal-extension)](https://pepy.tech/project/jupyterlab-basic-terminal-extension)
[![JupyterLab 4](https://img.shields.io/badge/JupyterLab-4-orange.svg)](https://jupyterlab.readthedocs.io/en/stable/)
[![Brought To You By KOLOMOLO](https://img.shields.io/badge/Brought%20To%20You%20By-KOLOMOLO-00ffff?style=flat)](https://kolomolo.com)
[![Donate PayPal](https://img.shields.io/badge/Donate-PayPal-blue?style=flat)](https://www.paypal.com/donate/?hosted_button_id=B4KPBJDLLXTSA)

Launch a utility terminal in JupyterLab that runs without a shell. Perfect for spawning short-lived console utilities that close their tab automatically when the underlying process exits, instead of leaving behind an idle shell prompt.

## Features

- **Shell-less terminal command** - Adds a JupyterLab command that opens a terminal bound directly to a utility process, with no surrounding shell
- **Auto-close on exit** - Terminal tab closes as soon as the utility process finishes, keeping the workspace tidy
- **Server extension companion** - Python `jupyter_server` extension exposes the route used by the frontend to spawn the process
- **JupyterLab 4 native** - Built against `@jupyterlab/application` 4.x and ships as a prebuilt federated extension

## Installation

Requires JupyterLab 4.0.0 or higher, and `bash` on the server - the terminal
initialisation step uses bash-specific syntax, so a `sh`-only image will not work.

```bash
pip install jupyterlab_basic_terminal_extension
```

## Usage

The extension deliberately adds no menu item, palette entry or launcher tile. Its
entire surface is one command, invoked programmatically by other extensions,
notebook code, or a `jupyter_app_launcher` tile:

```ts
await app.commands.execute('basic-terminal:launch', {
  argv: ['/opt/utils/my-utility.sh'],
  cwd: 'projects/demo'
});
```

- **`argv`** (required) - non-empty array of strings. `argv[0]` is executed directly; there is no shell, so no globbing, pipes or redirection
- **`cwd`** (optional) - absolute path used as-is, or a server-relative path resolved against `ServerApp.root_dir` (`''` is the root). Omit it and the current file browser folder is used, unless the browser is on a registered non-default drive - such a drive is not assumed to map onto the server filesystem, so the server's own working directory is used instead. A path that does not resolve to a directory is rejected with HTTP 400

The command resolves to the terminal widget, and rejects if the process exits
before the widget can be displayed.

## Uninstall

To remove the extension, execute:

```bash
pip uninstall jupyterlab_basic_terminal_extension
```
