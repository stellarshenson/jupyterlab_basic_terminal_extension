<!-- @import /home/lab/workspace/.claude/CLAUDE.md -->

# Project-Specific Configuration

This file imports workspace-level configuration from `/home/lab/workspace/.claude/CLAUDE.md`.
All workspace rules apply. Project-specific rules below strengthen or extend them.

The workspace `/home/lab/workspace/.claude/` directory contains additional instruction files
(MERMAID.md, NOTEBOOK.md, DATASCIENCE.md, GIT.md, and others) referenced by CLAUDE.md.
Consult workspace CLAUDE.md and the .claude directory to discover all applicable standards.

## Mandatory Bans (Reinforced)

The following workspace rules are STRICTLY ENFORCED for this project:

- **No automatic git tags** - only create tags when user explicitly requests
- **No automatic version changes** - only modify version in package.json/pyproject.toml/etc. when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload`, or similar without explicit user request
- **No manual package installs if Makefile exists** - use `make install` or equivalent Makefile targets, not direct `pip install`/`uv install`/`npm install`/`jlpm install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

`jupyterlab_basic_terminal_extension` is a JupyterLab 4 extension that exposes a command for launching a utility terminal that runs without a shell. The terminal is intended for short-lived console utilities - when the utility process exits, the terminal window/tab closes automatically.

**Technology Stack**:

- JupyterLab 4 (`@jupyterlab/application`, `@jupyterlab/coreutils`, `@jupyterlab/services`)
- TypeScript 5 frontend (`src/`) compiled to `lib/` and bundled into `jupyterlab_basic_terminal_extension/labextension/`
- Python 3.10+ server extension (`jupyterlab_basic_terminal_extension/`) using `jupyter_server`
- Hatch + `hatch-jupyter-builder` build backend defined in `pyproject.toml`
- Jest for frontend unit tests, Pytest for server tests, Playwright + Galata for UI integration tests in `ui-tests/`
- jupyter-releaser for tagged releases via GitHub Actions

**Project Naming**:

- npm package: `jupyterlab_basic_terminal_extension`
- PyPI package: `jupyterlab-basic-terminal-extension` (hyphens, normalized by PyPI)

## Required Workspace Skills

The following workspace skills MUST be referenced when their domain is in scope. They live at
`/home/lab/workspace/.claude/skills/` (with a fallback to `/home/lab/.claude/skills/` for the
home-global copies). Discover via the SKILL.md frontmatter in each skill directory.

- **jupyterlab-extension** - JupyterLab extension development guidelines, testing strategy, jupyter-releaser CI/CD workflows, common caveats, TypeScript compatibility, syntax highlighting, local development patterns. MUST be consulted for any work on this extension's source, build, tests, or release pipeline.
- **playwright** - Browser automation for screenshots and UI verification. MUST be used when capturing screenshots for `README.md`, the `.resources/` folder, or when programmatically verifying the extension's behaviour inside a running JupyterLab instance.

## Makefile Synchronization

**MANDATORY**: At the start of every session that touches build, install, publish, or test
targets, compare the local `Makefile` version header against the canonical Makefile at
`/home/lab/workspace/private/jupyterlab/@utils/jupyterlab-extensions/Makefile`. The version
is declared on the first line as `# Makefile for Jupyterlab extensions version X.YY`.

- If the canonical Makefile has a higher version, update the local `Makefile` to match before doing any other build-related work
- Preserve any project-local additions when porting forward, but treat the canonical file as the source of truth for shared targets
- After updating, mention the version bump explicitly to the user (do not commit silently)

## Build and Install

**MANDATORY**: Always install via `make install`. Never run `pip install`, `jlpm install`,
`npm install`, or `python -m build` directly - the Makefile orchestrates the correct ordering
(clean -> increment_version -> dependency check -> npm/jlpm install -> prettier -> python build
-> pip install of the wheel). Direct invocations skip steps and produce inconsistent state.

The `build` target also runs `prettier --write` against `package.json` and `package-lock.json`,
so both files MUST be kept under version control and committed together whenever either changes.
Do not gitignore `package-lock.json` - reproducible installs depend on it.

## Journal Rules (Project-Specific)

- **APPEND ONLY**: New journal entries MUST be appended at the end of the file, never inserted between existing entries
- Entries maintain strict chronological order by position - the last entry in the file is always the most recent work
- Never reorder, move, or insert entries out of sequence
- The Stellars **journal plugin** is the canonical tool for this file: create via `/journal:create`, append via `/journal:update`, archive via `/journal:archive`. The `journal:journal` skill auto-triggers on any mention of "journal" and runs `journal-tools check` after every write
- Direct edits to `JOURNAL.md` are a last resort - prefer the plugin so modus secundis format, continuous numbering and append-only order are enforced automatically

## Strengthened Rules

- **GitHub project**: This repository is hosted on GitHub. Follow the `my-repository` skill for badge templates, naming conventions, and link-checker configuration. README badges already include GitHub Actions, npm, PyPI, pepy downloads, JupyterLab 4, KOLOMOLO, and PayPal donate
- **JupyterLab extension specifics**: Always follow the `jupyterlab-extension` skill for release flow (jupyter-releaser), TypeScript pinning compatible with `@jupyterlab/builder`, syntax-highlighting peer dependencies, and local development install patterns
- **Playwright for UI verification**: When asked to verify a feature, capture a screenshot, or reproduce a UI bug, use the `playwright` skill rather than guessing from source code
