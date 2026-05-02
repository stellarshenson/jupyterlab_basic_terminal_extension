# Logs

Background-job log directory required by the workspace `CLAUDE.md` rule
"all background jobs MUST log progress to a file in the `logs/` directory".

Log files in this directory:

- `make-publish.log` - captures the full output of `make publish`. Useful when the
  npm/PyPI/twine flow fails partway through and you need to see which step exited.

The `*.log` files themselves are excluded by `.gitignore` (`*.log` rule); only this
README is tracked.
