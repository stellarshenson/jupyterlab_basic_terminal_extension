# Recovery State

Cold-start board for `jupyterlab_basic_terminal_extension`. A fresh session with zero
context resumes from this file alone. Newest brace section last.

---

## BRACE 2026-08-27 - adversarial review interrupted mid-panel

> [!NOTE]
> **RESOLVED 2026-08-27.** The session came back, both lenses' findings were
> triaged against the live tree, and the confirmed ones are fixed (see the
> resolution log at the end of this file). This section is kept as the record of
> what the brace preserved; it is no longer a live recovery instruction.

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


---

## RESOLUTION 2026-08-27 - review triaged, scoped fixes applied

### Divergence: settled in origin's favour

`origin/main`'s `1bf0578` was kept; the local implementation in `stash@{0}` was
**superseded, not merged**. Origin's version was strictly better on the two points the
review raised: it already indexes `self.settings["server_root_dir"]` directly (no `or "~"`
fallback), and it already carried real tests - a Jest spec asserting the POSTed `cwd` and
Python tests inspecting the spawned pty's actual working directory.

The stash's only unique content was the Makefile v1.31 → v1.37 sync and the `.nodeenv/`
ignore entry. Both are now applied, taken from the canonical Makefile at
`/home/lab/workspace/private/jupyterlab/@utils/jupyterlab-extensions/Makefile` rather than
from the stash, so the local copy matches the shared source of truth byte for byte.

`stash@{0}` is now fully superseded and safe to drop; it is left in place because dropping
it is the owner's call. `.claude/brace-worktree-2026-08-27.patch` remains committed either way.

### Findings triaged

| # | Lens | Finding | Outcome |
| --- | --- | --- | --- |
| BH-1 | bug-hunter | CRITICAL - pty death before WebSocket attach spawns the user's `$SHELL` | **CONFIRMED against the live JupyterLab bundle, fixed** |
| BH-2 | bug-hunter | MAJOR - `terminal:open` returns undefined on the tracker-hit path, skipping disposal wiring | **CONFIRMED, deliberately deferred** - see below |
| BH-3 | bug-hunter | MAJOR - file browser path sent without `contents.localPath()` | **CONFIRMED, fixed** |
| A-1 | architect | MAJOR - `/bin/bash` bare literal, dependency undeclared | **CONFIRMED, fixed** |
| A-2 | architect | MAJOR - `or "~"` fallback guards an impossible state | **Already fixed by origin's `1bf0578`** - false positive against the checked-out tree |
| A-3 | architect | MAJOR - the only public interface is undocumented | **CONFIRMED, fixed** |
| A-4 | architect | MAJOR - the change is asserted by no test | **Largely already fixed by origin's `1bf0578`**; extended further |
| A-5 | architect | MAJOR - two package managers own one dependency set | **Deferred - owner's call** - see below |

### What was verified, not assumed

BH-1 was confirmed by reading the installed bundle
(`/opt/conda/share/jupyter/lab/static/jlab_core.a3196067513a13d4.js`), not inferred:

- `terminal:open` is `execute: i => { let r = i.name, s = t.find(e => e.content.session.name === r); if (!s) return c.execute(n.createNew, {name: r}); e.shell.activateById(s.id) }` - so a tracker miss delegates to `create-new`, and the hit path returns `undefined`
- terminal `create-new` is `... n = r ? (await TerminalAPI.listRunning(...)).map(e => e.name).includes(r) ? terminals.connectTo({model:{name:r}}) : await terminals.startNew({name:r, cwd:d}) : ...` - so a name absent from `listRunning` takes `startNew`, which spawns the server's default shell with no argv and no cwd

Trigger: terminado frees the name on EOF, so any pty exiting before the frontend's
`terminal:open` arrives arms this. The old 5s waiter cap was shorter than a cold-start
round-trip, which is what made it reachable in practice.

### Fixes applied

- `routes.py` - `_INIT_SHELL = "/bin/bash"` names the hard bash dependency at one place; `_INIT_WAIT_POLLS` replaces the inline `50` (final value 100 after round 2 - see below)
- `src/index.ts` - before `terminal:open`, the frontend now refreshes the running list and throws if the launched name is gone, so a dead pty fails loudly instead of silently becoming a shell; the file browser path is routed through `contents.localPath()` so a drive-prefixed path no longer 400s
- `README.md` - a Usage section documenting the command id, the `argv`/`cwd` contract and the cwd resolution rule, plus the bash requirement in Installation
- tests - four new Jest cases (drive-prefix stripping, root-as-empty-path, and two on the vanished-pty guard) and two new Python cases pinning the shell constant and the wait window
- `Makefile` synced to canonical v1.37; `.gitignore` gained `.nodeenv/`, `junit.xml`, `tmp/`; `.prettierignore` gained `reports`, `tmp`, `.claude` so review artefacts are not reformatted

### Deliberately not done, and why

- **BH-2** - reaching the stale widget needs `ITerminalTracker`, i.e. a new `@jupyterlab/terminal` dependency, and its trigger requires the disposal wiring to have already failed once. The remedy is larger than the defect, so it is recorded rather than applied
- **A-5** - dropping `$(NPM) install` and untracking `package-lock.json` contradicts the standing rule in this project's `.claude/CLAUDE.md`, and the real fix belongs in the canonical Makefile, where a local edit would be reverted by the next sync. Owner's decision

### Verification

`pytest` 15 passed · `jlpm test` 7 passed · `tsc` clean · `jlpm run lint:check` clean ·
graph refreshed to 416 nodes / 480 edges.

### Still open (unchanged by this session)

`stellars_jupyterlab_ds` has still not received the launcher YAML and `launch-lab-utils.sh`
changes described in the pending-work section above.

---

## ROUND 2 - re-confirm, pinned to the fixes

Both lenses returned `DO-NOT-SHIP` **against my own round-1 fixes**. Four findings, all
confirmed by reproduction, all fixed. Three were regressions I introduced; the fourth
replaced my remedy with a better one.

### R2-1 (bug-hunter, MAJOR) - the launch guard read a cache, not the server

`terminals.refreshRunning()` is a `@lumino/polling` refresh, which dedups concurrent
refreshes, resolves without refetching while on standby, and swallows request errors. Two
launches fired close together therefore shared one pre-launch snapshot: the second was
rejected as "exited" while its pty ran on unattached and leaked. Worse, the command rejects
into a floating promise with no `commandFailed` subscriber anywhere in JupyterLab, so the
user saw nothing at all. **A regression** - before my guard, `terminal:create-new` did its own
uncached `TerminalAPI.listRunning` *after* the create and connected correctly.
Fixed by calling `TerminalAPI.listRunning(serverSettings)` directly - same single round-trip,
never deduped, and it rejects on a server error instead of masquerading as "exited".

### R2-2 (both lenses, MAJOR) - widening the wait was the wrong remedy

Round 1 set `_INIT_WAIT_POLLS = 300` to outlast the frontend round-trip. Both lenses showed
that cost far more than it bought: the budget is also the blank-screen stall whenever no
resize arrives, and terminado skips `setwinsize` when the client's size already equals the
pty's, so a panel fitting to exactly the 24x80 spawn default stalls for the *whole* budget.
Measured at 300 polls: 33.5s. Every bad `argv[0]` also took 33.5s to surface, since the exec
only fails after the wait.

Replaced with a better mechanism rather than a tuned number: the waiter now runs
`stty rows 1 cols 1` **before** arming the trap, so the pty no longer sits at the default and
any real client size differs - the resize always fires and the wait always ends on attach.
The 1x1 sentinel is restored to 24x80 if the timeout wins, so a client-less run does not
execute in a 1x1 terminal. The backstop returns to 50 polls, and now only governs the
genuinely client-less case.

Measured with the shipped waiter under terminado-accurate resize semantics:

| case | before (300 polls) | after |
| --- | --- | --- |
| client fits exactly 24x80 | 33.5s stall | **0.32s** |
| client fits 30x100 | 0.31s | 0.31s |
| bad `argv[0]`, client attached | 33.5s | **0.31s** |
| no client ever attaches | 33.5s | 7.9s |

The architect additionally argued the constant "can never be too short" because the resize is
downstream of the `listRunning` decision. That conflates *exiting early* with *timing out* -
at 50 the pty dies whether or not the widget attached - so the backstop still has to outlast
the round-trip. It does.

### R2-3 (bug-hunter, MAJOR) - `localPath` turned a loud 400 into a silent wrong directory

Round 1 routed the file browser path through `contents.localPath()`. On a registered
non-default drive that strips the prefix without telling the caller: `S3:data/raw` became
`data/raw`, which the server resolved against its **own** root. If a local `data/raw` also
existed, the utility launched there and operated on the wrong files with no error.
**A regression** - it reliably 400d before. Fixed by checking `contents.driveName(path) === ''`
and skipping the fallback entirely off the server drive, since no local directory corresponds
to a remote drive path.

### Verification

17 pytest, 8 jest, tsc clean, prettier clean. Three mutants of the new waiter logic (sentinel
set to 24x80, trap armed before the sentinel, restore removed) were each killed by exactly
one test.

### Still open

- The `terminal:open`-returns-undefined disposal gap (needs `@jupyterlab/terminal`) and the
  dual package-manager finding remain deliberately declined, unchanged from round 1
- Not verified by anyone yet: closing the tab mid-wait. Traced only - terminado's
  `NamedTermManager` inherits a no-op `client_disconnected`, so the pty likely survives the
  WebSocket close and execs the argv headless when the backstop expires
- A third round has not been run. Round 2 found real defects, so by the rounds protocol this
  is **not** yet a clean confirming round

---

## ROUND 3 (architect returned, bug-hunter in flight)

### R3-1 (architect, MAJOR) - the drive gate is not the test its own rationale claimed

Fixes A and B were confirmed clean and re-verified empirically by the reviewer on a real pty
(exact-fit client exec at 24x80 in 0.73s; no client 5.45s then restored). The finding lands on
Fix C's *justification*, not its behaviour.

`ContentsManager.driveName` returns non-empty only when the path prefix is in
`_additionalDrives` - it tests **registered**, not **remote**. `Drive` defaults `apiEndpoint`
to `api/contents` and `_getUrl` builds `baseUrl + apiEndpoint + localPath` with the drive name
never sent. So a drive registered under a name but without an endpoint override reads and
writes the **same** `root_dir`, and its `localPath()` is exactly the server-relative path the
handler expects. Both facts independently re-verified against
`node_modules/@jupyterlab/services/lib/contents/index.js`.

The gate therefore also skips drives that ARE server-backed. The claims "only the default drive
is backed by the server filesystem" (code comment) and "a remote drive path has no local
directory to spawn in" (README) were false as general rules.

**Fixed by deletion, no behaviour change**: the comment, the `cwd` JSDoc and the README bullet
now state what the code actually tests - a registered drive is not *assumed* to map onto the
server filesystem, and there is no Contents API to ask which do.

**Correction to the R2-3 note above**: its closing clause ("no local directory corresponds to a
remote drive path") is the same overclaim and is superseded by this section.

### Deliberately NOT done - the RTC allowlist

The architect's secondary remedy was `SERVER_BACKED_DRIVES = ['', 'RTC']`, on the judgement
that jupyter-collaboration's browser reports `RTC:dir` while pointing at the same `root_dir` -
which would mean this fix silently disables the browsed-folder feature on every collaborative
deployment. The reviewer flagged this as unverified, and `jupyter_collaboration` is confirmed
absent from this box (`ModuleNotFoundError`), so it could not be checked here either.
**Open decision for the user**; needs a live collaborative install (Playwright) before shipping.

### Verification after the round-3 fix

17 pytest, 8 jest, tsc clean, prettier clean.

### Containment check (graphify, post-round-3)

Graph refreshed AST-only after the fix: 437 -> 441 nodes, 502 -> 506 edges, 37 communities.

Blast radius of every touched symbol, at depth 4:

| symbol | dependents |
|---|---|
| `plugin` (src/index.ts) | none - terminal node, consumed by JupyterLab at runtime |
| `_wrap_with_init()` | `post()` only, same file |
| `post()` | `_wrap_with_init()` only, same file |
| `requestAPI()` | `index.ts` - untouched, so nothing propagates |
| `routes.py` | `__init__.py` re-exports `setup_route_handlers` only - untouched |

**Contained.** The affected set is exactly `routes.py` + `src/index.ts` and their two test files,
which is exactly what the code diff touches. Nothing edited falls outside the set; nothing inside
it was left unedited.

**What the graph cannot contain**: it finds NO path between `index.ts` and `routes.py`. Their
coupling is the HTTP JSON body `{argv, cwd}` plus the URL prefix - not an import edge, so AST
cannot see it. That contract is precisely what rounds 2 and 3 kept finding defects in. Only the
two test suites and the README pin it; the graph offers no protection there.

**Separable from the fix set**: `Makefile` (canonical v1.31 -> v1.37 sync, 136 lines), `.gitignore`,
`.prettierignore`. Not code nodes, not part of the review remedy.

**Semantic layer is stale**: duplicate `rationale_*` nodes survive from earlier extractions and the
rewritten comments are not reflected. Refreshing needs `/graphify --update`, which is LLM-billed -
not run, pending the user's word.

### R3-2 (bug-hunter) - SHIP, 0 findings

All three round-2 fixes reproduce and hold under runtime evidence, not reading. The reviewer
spawned the real `_wrap_with_init()` argv through `ptyprocess.PtyProcessUnicode` with a client
mimicking terminado's `resize_to_smallest`, and drove real JupyterLab 4.6.3 + chromium against a
throwaway server. Repo unmodified by the review (`git diff --stat` byte-identical).

Highlights worth keeping:

- **The motivating bug is confirmed fixed.** Client fitting to exactly 24x80: HEAD waiter stalls
  7.85s issuing no ioctl at all; fixed waiter breaks in 0.42s. Browser end-to-end 0.65 / 0.44 /
  0.44s from `commands.execute` to first instruction, correct size every time
- **The self-inflicted `stty rows 1 cols 1` does not trip its own trap** - SIGWINCH at default
  disposition is discarded, never queued. Measured: no-client run breaks at 5.11s, not ~0ms
- **The sentinel is always distinguishable.** `@xterm/addon-fit` clamps `cols` to >= 2, so a
  client can never report 1x1. A collapsed 1x2 panel breaks in 0.52s
- **`stty` absent degrades gracefully** - 5.11s, pty untouched, no stderr leaked into the pty
- **One hypothesis reproduced at pty level then disproven on the wire.**
  `@jupyterlab/terminal/lib/widget.js:311` sets session size from `_initialConnection` before
  `fit()` necessarily runs, so the first `set_size` could in principle carry xterm's unfitted
  24x80 - which the sentinel would now honour. At pty level that failure is real. On the wire it
  is not: JupyterLab 4.6.3 sends `set_size` twice 0-1ms apart, **both already fitted**, on first
  and second terminal, at normal speed and under 6x CPU throttling

**Mutation testing**: 9 mutants killed, including sentinel-after-trap, restore removed, budget cut
to 20, `/bin/sh` for `/bin/bash`, drive gate ignoring `driveName`, guard `throw` removed, and
`browserPath !== undefined` weakened to truthiness (which catches the `''`-is-root case).

**One surviving mutant, recorded not filed**: inverting the restore guard to
`if [ -n "$CHANGED" ] || ...` passes all 17 python tests, because
`test_waiter_restores_a_usable_size_when_no_client_arrives` asserts only that the substring
`stty rows 24 cols 80` is present, not that it is guarded. The shipped guard is correct - the pty
ends at the client's size in every attach scenario - so this is a coverage gap, not a defect.
Strengthening it is one assertion; not done, pending the user's word.

### Round 3 standing

Bug-hunter clean. Architect raised one MAJOR, fixed by deleting a false claim with no behaviour
change; that correction has NOT been re-reviewed. By the strict rounds protocol this is therefore
**not yet a clean confirming round**. Against that, CLAUDE.md's own stopping rule warns that
re-running a loop to re-review prose is how rounds start manufacturing defects. The three
corrected sentences were verified directly against
`node_modules/@jupyterlab/services/lib/contents/index.js`. **Whether to spend a round 4 on them is
the user's call.**
