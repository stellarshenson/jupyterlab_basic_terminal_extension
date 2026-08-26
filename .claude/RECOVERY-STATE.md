# Recovery State

Cold-start board for `jupyterlab_basic_terminal_extension`. A fresh session with zero
context resumes from this file alone. Newest brace section last.

---

## BRACE 2026-08-27 - adversarial review interrupted mid-panel

### HORIZON

**UNCONFIRMED at brace time** - the Star Colonel was asked and the session died before
the answer landed. Treat as `SERVER RESTART` (the worse case): assume every process is
gone and relaunch from disk. Nothing in this project depended on a detached job, so the
two horizons differ only in whether the three subagents below are still alive - and they
were in-process session subagents, which die under BOTH horizons.

### What was running (all DEAD after the restart - none were detached)

Three in-process subagents, spawned by the session, holding results that were never
returned to the main context. Each was sent a brace message telling it to dump partials
to disk before idling; check those paths first, and treat a missing file as "that lens
produced nothing recoverable".

| Agent | Purpose | Partial output path (check first) |
| --- | --- | --- |
| architect reviewer | Mode 2 whole-repo architecture audit of the change set | **LANDED** - `reports/adversarial-architect-partial.md` (committed) |
| bug-hunter reviewer | Mode 2 runtime bug hunt - `_INIT_WAITER` bash, pty/WebSocket lifecycle, Makefile-as-shell-program | **LANDED** - `reports/adversarial-bug-hunter-partial.md` (committed) |
| graphify semantic extractor | Semantic layer over the 15 docs/workflows | `tmp/graphify-out/.graphify_chunk_01.json` |

**No detached compute existed.** No `nohup`/`setsid` job, no training run, no sweep. The
PID 116 `conda run ... tensorflow training monitoring` process seen at brace time is a
pre-existing container-level process with PPID 1, unrelated to this project.

### Relaunch commands

Re-run the adversarial panel (toolchain gate first, then both lenses in ONE message so
they run concurrently). Full prompts are reconstructable from the scope block below;
`/devils-advocate:adversarial-review` with args `architect and bug hunter, but only most
important issues, nothing cosmetic` re-enters the same flow.

```bash
# 1. Toolchain gate - MANDATORY before any adversarial-review work
python3 -m pip install --user --upgrade stellars-claude-code-plugins 2>&1 | tail -1
python3 -c "import importlib.metadata as m;print(m.version('stellars-claude-code-plugins'))"
# must equal the plugin version under
# ~/.claude/plugins/cache/stellarshenson-marketplace/devils-advocate/<ver>/.claude-plugin/plugin.json
```

Rebuild the graphify semantic layer (the free AST layer is already on disk and valid):

```bash
cd /home/lab/workspace/private/jupyterlab/jupyterlab_basic_terminal_extension
export GRAPHIFY_OUT=tmp/graphify-out
# AST layer only, no LLM, seconds - safe to re-run any time:
mkdir -p tmp && (cd tmp && GRAPHIFY_OUT=tmp/graphify-out graphify update ..)
```

### Results valid on disk

- **graphify AST layer** - `tmp/graphify-out/.graphify_ast.json`, **219 nodes, 306 edges**,
  deterministic, no LLM cost. Valid. The semantic layer over docs was never merged, so
  `tmp/graphify-out/graph.json` does **not** exist yet - Step 4 of the graphify pipeline
  never ran. `tmp/` is NOT gitignored, so these artefacts show as untracked
- **Working tree change set** - present on disk, uncommitted, and additionally snapshotted
  to `.claude/brace-worktree-2026-08-27.patch` (1005 lines) which IS committed. Restore
  with `git apply .claude/brace-worktree-2026-08-27.patch` if the tree is ever clobbered
- **Verification already passed on this change set** (before the brace): `tsc` compiles
  clean, `pytest` 12/12 pass, `jlpm run lint:check` clean

### What is invalid / unverified

- **The adversarial review reached NO verdict.** Round 1 was still running. Do not record,
  claim, or act on "survived adversarial review" - no lens returned, nothing was triaged,
  nothing was adjudicated
- Any partial findings recovered from the two `reports/*-partial.md` files are **untriaged
  round-1 output**. Context-free reviewers raise false positives. Confirm each against the
  code before acting, per the rounds protocol

### The change set that was under review (now in stash@{0} + the patch, NOT the worktree)

| File | Change |
| --- | --- |
| `jupyterlab_basic_terminal_extension/routes.py` | A non-absolute `cwd` is resolved against `self.settings["server_root_dir"]` (via `os.path.expanduser`) before the `isdir` check; absolute values pass through unchanged |
| `src/index.ts` | `IDefaultFileBrowser` added as an OPTIONAL plugin dependency; a caller passing no `cwd` now defaults to `fileBrowser?.model.path` via `??` (so an explicit `''` meaning root survives) |
| `package.json` | `@jupyterlab/filebrowser: ^4.0.0` added to `dependencies` |
| `jupyterlab_basic_terminal_extension/tests/test_routes.py` | Three new tests - relative cwd resolves, `''` means root, bad relative returns 400 |
| `Makefile` | Synced from the canonical shared Makefile, v1.31 → v1.37 |
| `.gitignore` | `.nodeenv/` entry added |

Motivation for the cwd work: `jupyter_app_launcher`'s `jupyterlab-commands` factory
discards the args object carrying JupyterLab Launcher's `cwd`, so launcher tiles always
landed in the server process's working directory. Both halves (frontend default +
server-side resolution) had to land together.

**Known open question, never put to the Star Colonel:** a relative `cwd` such as
`"../../etc"` escapes `root_dir`. No containment check was added, on the reasoning that
the endpoint already accepts arbitrary absolute paths by design, so relative traversal
grants no new capability. This decision is unreviewed - it is exactly the kind of thing
the architect lens was spawned to challenge.

### Review scope as given to the panel

- **In scope** - `src/`, `jupyterlab_basic_terminal_extension/` (incl. `tests/`),
  `ui-tests/`, `package.json`, `pyproject.toml`, `tsconfig.json`, `Makefile`,
  `.github/workflows/`, `install.json`, `jupyter-config/`, `README.md`
- **Out of scope** - `node_modules/`, `lib/`, `jupyterlab_basic_terminal_extension/labextension/`,
  `yarn.lock`, `package-lock.json`, `tmp/`, `.claude/JOURNAL.md`, `CHANGELOG.md`
- **Severity floor** - CRITICAL and MAJOR only. The Star Colonel explicitly ruled cosmetic
  and taste findings out of scope for this run
- **Locked decisions passed to both lenses** (not to be re-litigated) - arbitrary
  caller-supplied `argv` is the design and sits behind `jupyter_server` auth; `argv`-only
  contract with no shell-string parsing and no `env` passthrough; no UI surface, command
  registration only; `make install` is the mandatory build path; versions and releases
  change only on explicit request

### Architect lens DID return - partial, DO-NOT-SHIP, and NOT yet triaged

`reports/adversarial-architect-partial.md` (132 lines, committed). `VERDICT: DO-NOT-SHIP
(5 findings)`, all MAJOR, none CRITICAL. Its own summary of the diff: correct, and its
Python side passes - but the frontend half is verified by nothing and the package's only
public contract is written down nowhere. Untriaged.

1. **MAJOR** - `/bin/bash` is a bare literal at `routes.py:39` and the hard dependency is
   declared nowhere (not README, not `pyproject.toml`). The waiter is genuinely
   bash-specific, so `/bin/sh` is not a substitute. On a bash-less image the tab opens and
   closes instantly, indistinguishable from "the utility exited"
2. **MAJOR** - the `or "~"` fallback in the cwd resolution guards a state that cannot occur
   (`server_root_dir` is set unconditionally by `jupyter_server`) and, if it ever fired,
   would resolve against `$HOME` and return 200 - a wrong directory reported as success
3. **MAJOR** - `README.md` never names `basic-terminal:launch`, `argv`, `cwd`, or the
   endpoint. With no menu, palette or launcher entry, the command id *is* the product.
   Separately: the new relative-`cwd` rule diverges from the sibling
   `jupyter_server_terminals` API on the same server, and is a **silent semantic change for
   callers of the already-published v1.0.6**, where a relative `cwd` meant "relative to the
   server process cwd"
4. **MAJOR** - the change is asserted by no test at any level. The Jest spec is still the
   cookiecutter `expect(1 + 1).toEqual(2)`, so the CI coverage step stands for zero
   verification; the Python tests assert HTTP status only. Its stated position: either add
   the two small tests, or delete the frontend test surface - keeping a CI step that
   advertises coverage it does not have is the one option that is not defensible
5. **MAJOR** - two package managers own one dependency set (`$(NPM) install` then
   `jlpm install`), and nothing consumes `package-lock.json`. **Flagged as the owner's call,
   not a silent edit**: the project `.claude/CLAUDE.md` currently mandates keeping
   `package-lock.json` committed, and the fix belongs in the *canonical* Makefile at
   `/home/lab/workspace/private/jupyterlab/@utils/jupyterlab-extensions/Makefile`, since a
   local-only edit is reverted by the next sync

It also **dismissed with evidence** - do not re-raise these: the `IDefaultFileBrowser`
singleton-token worry (filebrowser is in core `singletonPackages`); `..` traversal in a
relative cwd (grants nothing over the locked arbitrary-argv decision); and
`pip uninstall -y dist/*.whl`, which it actually ran and found works.

Same tree-swap caveat as the bug-hunter: re-anchor line numbers before acting.

Unreviewed, not clean: the five release-related workflows, `RELEASE.md`,
`.copier-answers.yml`, `ui-tests/playwright.config.js`, `ui-tests/README.md`, `style/*`. No
TypeScript compile was run, and the file-browser default was never verified against a live
JupyterLab.

### Both lenses agree on one thing

`routes.py`'s `or "~"` fallback is dead code that would fail silently if reached, and the
`/bin/bash` hardcoding is undeclared. Two independent lenses reaching the same two spots is
the strongest signal in this round - but the panel was never adjudicated, so treat even
that as input to a decision, not a work order.

### Bug-hunter lens DID return - partial, DO-NOT-SHIP, and NOT yet triaged

`reports/adversarial-bug-hunter-partial.md` (172 lines, committed) holds a partial round-1
review: `VERDICT: DO-NOT-SHIP (3 findings)`, cut short by the brace. Untriaged. Confirm each
against the code before acting - a context-free reviewer raises false positives.

Headline findings, verbatim severities:

1. **CRITICAL** - if the pty dies before the browser's WebSocket attaches, terminado has
   already freed the name, so JupyterLab's `terminal:open` falls through to
   `terminal:create-new`, which spawns the user's default interactive `$SHELL` under that
   name - with no cwd and no `_INIT_WAITER`. The exact failure this extension exists to
   prevent, surfaced as no error at all. Reachable via the 5s waiter timeout, or via any
   missing/non-executable `argv[0]` (only `/bin/bash` is validated at spawn)
2. **MAJOR** - `terminal:open` returns undefined on the already-tracked-widget path, so
   `src/index.ts` silently skips both the focus call and the disposal wiring; the tab then
   never auto-closes. Reachable because terminado reuses freed integer names
3. **MAJOR** - the file-browser path is sent without `contents.localPath()`, so a
   drive-prefixed path (`Drive:some/dir`, e.g. jupyter-fs / S3 / RTC) 400s every no-cwd
   launch. JupyterLab's own terminal command calls `localPath()` for exactly this reason

It also **cleared** one thing: `pytest` 12/12 pass and the cwd resolution is genuinely
exercised. And it flagged the `or "~"` fallback in `routes.py` as dead in practice, since
`server_root_dir` is always set by `jupyter_server`.

> [!WARNING]
> **The tree changed underneath this reviewer mid-review.** The brace stashed the local
> implementation and rebased onto origin's `1bf0578` while the lens was still reading. Its
> `file:line` citations therefore may point at either version. Confirmed shift: the review
> cites `src/index.ts:47` with `cwd ?? fileBrowser?.model.path`; the checked-out origin
> version has that logic at `src/index.ts:53-54` as `cwd !== undefined ? cwd : defaultBrowser?.model.path`.
> Re-anchor every line number before acting on any finding. Finding 3 (`localPath`) does
> still apply to the checked-out tree - `grep` confirms no `localPath` call in `src/index.ts`.

Unreached scope the lens explicitly declared UNREVIEWED, not clean: `_INIT_WAITER` was never
executed in a real pty; the Makefile was seen only as a diff, never in full; and
`.github/workflows/`, `pyproject.toml`, `install.json`, `jupyter-config/`, `ui-tests/`,
`src/request.ts` and `src/__tests__/` were never opened.

### CRITICAL - the local change set DIVERGES from what is already on origin

Discovered while pushing this brace commit. `origin/main` already contained
`1bf0578 feat: launch the terminal in the browsed folder` - a **different and fuller
implementation of the same cwd feature**, pushed from outside this session. It carries
things the local worktree did not: ~52 lines of server tests (local had ~19), ~65 lines
of frontend Jest tests in `src/__tests__/`, and a `logs/README.md`.

Nothing was merged and nothing was discarded. Both sides are preserved:

- **origin's version** is now the checked-out tree (`1bf0578`, HEAD~1)
- **the local version** is preserved twice - as `stash@{0}`
  (`brace-2026-08-27: local cwd impl + Makefile v1.37, diverges from origin 1bf0578`)
  and as the committed patch `.claude/brace-worktree-2026-08-27.patch`

The local side additionally holds the **Makefile v1.31 → v1.37 sync**, which is NOT in
`1bf0578` and is NOT on origin. That work exists only in the stash and the patch.

**Do not `git stash pop` blindly** - it will conflict with `1bf0578` on `routes.py`,
`src/index.ts`, `test_routes.py` and `package.json`. Diff the two implementations first
and put the choice to the Star Colonel:

```bash
git stash show -p stash@{0}                      # what the local side holds
git show 1bf0578                                 # what origin already took
git diff stash@{0} HEAD -- jupyterlab_basic_terminal_extension/routes.py src/index.ts
```

The Makefile and `.gitignore` hunks are the only parts of the stash that are certain to
be wanted and certain not to conflict - they can be extracted on their own:

```bash
git checkout stash@{0} -- Makefile .gitignore
```

### Pending work carried over (predates this brace)

1. **`stellars_jupyterlab_ds` never received the launcher changes.** Explicitly requested;
   only the `git pull` was done. Two files still need the edits already applied to the
   live host copies under `/opt`:
   - `services/jupyterlab/conf/share/jupyter/jupyter_app_launcher/jp_app_launcher_other.yml`
     - still `type: terminal` with `source: 'exec /opt/utils/launch-lab-utils.sh'`; needs
     converting to the `jupyterlab-commands` form invoking `basic-terminal:launch` with
     `argv: [/opt/utils/launch-lab-utils.sh]`
   - `services/jupyterlab/conf/utils/launch-lab-utils.sh` - still carries the trailing
     pause / "Press Enter to close" block that was stripped from the host copy
2. **Uncommitted change set** - the cwd work and the Makefile v1.37 sync are both still
   uncommitted. No commit was authorised for them
3. **Workspace submodule commit `563cfa8` is local-only** - never pushed
4. **Journal entry for the cwd work was never written.** Use `/journal:update`, never a
   direct edit of `.claude/JOURNAL.md`

### FIRST ACTION for the next session

Both partials ARE on disk under `reports/` and committed. Tell the Star Colonel in one short summary that both lenses returned partial
DO-NOT-SHIP reviews, that neither was triaged or adjudicated, and that the reviewed tree
was swapped mid-run. Ask whether to re-run the panel from round 1 or to
triage whatever partials survived. **Do not commit the change set and do not resume the
review without the Star Colonel's word.**

