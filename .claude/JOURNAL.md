# Claude Code Journal

This journal tracks substantive work on documents, diagrams, and documentation content.

---

1. **Task - Project initialization** (v0.1.0): Bootstrapped `jupyterlab_basic_terminal_extension` as a new JupyterLab 4 extension with Claude configuration, README, and initial git import<br>
   **Result**: Project was scaffolded from the JupyterLab copier template (TypeScript frontend in `src/`, Python server extension in `jupyterlab_basic_terminal_extension/`, hatch/`hatch-jupyter-builder` build backend, Jest + Pytest + Playwright/Galata stack, jupyter-releaser CI). Replaced the inlined `.claude/CLAUDE.md` with a thin import of the workspace file plus sections for Mandatory Bans, Required Workspace Skills (`jupyterlab-extension`, `playwright`), mandatory Makefile sync against `@utils/jupyterlab-extensions/Makefile` v1.31, mandatory `make install`, and keeping both `package.json` and `package-lock.json` versioned. Rewrote `README.md` after the `jupyterlab_terminal_show_in_file_browser_extension` pattern - kept up to `## Uninstall`, added the full workspace badge set (GitHub Actions, npm, PyPI, pepy, JupyterLab 4, KOLOMOLO, PayPal) and a Features section. Ran `git init -b main` and made the initial import commit.
