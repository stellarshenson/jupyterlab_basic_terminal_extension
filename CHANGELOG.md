# Changelog

<!-- <START NEW CHANGELOG ENTRY> -->

<!-- <END NEW CHANGELOG ENTRY> -->

## [1.0.9] - 2026-10-16

### Added

- `basic-terminal:launch` takes the optional argument `shutdownOnClose`, default `false`. When it is `true` and the user closes the tab while the program still runs, the terminal session is shut down and the program ends. A tab that closes because the program ended sends no shutdown

### Changed

- Requires JupyterLab 4.6 or later and `jupyter_server` 2.21 or later: the package floors follow the extension template v4.6.5, which also moves linting to ESLint 9 and the build to `jupyter-builder`
- `Makefile` synced to canonical version 1.46

## [1.0.8] - 2026-10-13

### Fixed

- A launch that the server refuses now rejects with the server's code as the message of the error, for example `invalid_cwd` for a working directory that does not exist. The message was the whole answer object, which a caller that displays it showed as `[object Object]`

## [1.0.7] - 2026-08-27

### Fixed

- Launch no longer falls through to the user's `$SHELL`. `terminal:open` delegates a name it cannot find to `terminal:create-new`, which spawns a plain login shell with no argv, no cwd and no auto-close - so a pty that exited before the widget mounted silently became the very thing this extension exists to avoid. The command now checks the live terminal list and fails loudly instead
- Utilities no longer paint their first frame at terminado's 24x80 default inside a wider tab. The init waiter shrinks the pty to 1x1 before arming the `SIGWINCH` trap, so the client's size always differs and the resize always fires; a panel fitting exactly 24x80 previously stalled 7.85s on a blank screen and now starts in 0.42s
- A bad `argv[0]` no longer holds a blank terminal open for the whole wait budget
- Omitting `cwd` while the file browser sits on a registered non-default drive no longer strips the drive prefix and resolves the remainder against the server's own root, which could launch the utility in an unrelated local directory of the same name

### Changed

- The `cwd` fallback uses the file browser's folder only while the browser is on the default drive; a registered drive is not assumed to map onto the server filesystem
- The init waiter restores a usable 24x80 when no client ever attaches, so a headless run is not left executing in a 1x1 terminal
- `Makefile` synced to canonical version 1.37

### Added

- `README.md` Usage section documenting the `basic-terminal:launch` command, its `{argv, cwd}` contract, and the `/bin/bash` runtime requirement
- Server tests covering the waiter's sentinel ordering, size restoration and backstop budget; frontend tests covering the drive gate, the root-as-empty-path case and the live-list launch guard
