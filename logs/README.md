# Logs

Background-job log directory required by the workspace `CLAUDE.md` rule
"all background jobs MUST log progress to a file in the `logs/` directory".

Log files in this directory:

- `make-publish.log` - captures the full output of `make publish`. Useful when the
  npm/PyPI/twine flow fails partway through and you need to see which step exited.
- `deps-install.log` - `npm install` + `jlpm install` (and the prettier pass over the
  lockfiles) when dependencies change.
- `jest-test.log` - `jlpm test` run over the frontend suite.
- `jest-mutation-check.log` - jest run against a temporarily reverted `src/index.ts`,
  proving the cwd-fallback tests can fail.
- `pytest-routes.log` - pytest run over `jupyterlab_basic_terminal_extension/tests/`.
- `pytest-mutation-check.log` - pytest run against the pre-fix `routes.py`, proving
  the cwd-resolution tests can fail.
- `lint-check.log` - `jlpm lint:check` / `jlpm eslint:check` output.
- `wheel-build.log` - `python -m build` output producing the sdist and wheel in `dist/`.

The `*.log` files themselves are excluded by `.gitignore` (`*.log` rule); only this
README is tracked.
