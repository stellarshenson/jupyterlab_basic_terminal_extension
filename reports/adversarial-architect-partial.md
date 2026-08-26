# Adversarial review - lens: architect - PARTIAL (session braced)

NOTE ON LOCATION: the coordinator asked for `<repo>/reports/adversarial-architect-partial.md`.
Standing constraint for this reviewer is "never modify a file in the repo under review; scratch
files under /tmp". Persisted here instead. Copy it in if the owner wants it tracked.

VERDICT: DO-NOT-SHIP (4 findings) - the diff itself is correct and passes; what fails is that its
frontend half is verified by nothing, and the package's only public contract is written down nowhere.

## Scope given
src/, jupyterlab_basic_terminal_extension/ (incl. tests/), ui-tests/, package.json, pyproject.toml,
tsconfig.json, Makefile, .github/workflows/, install.json, jupyter-config/, README.md.
Out: node_modules/, lib/, labextension/, lockfile contents, tmp/, JOURNAL.md, CHANGELOG.md.
Locked, not relitigated: arbitrary argv by design, argv-only contract, no UI surface, make install
mandatory, version/release only on request.

## READ (evidence base)
routes.py (all 132 lines), src/index.ts, src/request.ts, src/__tests__/*.spec.ts,
tests/test_routes.py, conftest.py, __init__.py, package.json, pyproject.toml, tsconfig.json,
tsconfig.test.json, jest.config.js, babel.config.js, .prettierignore, .yarnrc.yml, install.json,
jupyter-config/server-config/*.json, setup.py, Makefile (all 211 lines), .github/workflows/build.yml,
README.md, ui-tests/package.json, ui-tests/jupyter_server_test_config.py, ui-tests/tests/*.spec.ts.
External evidence: /opt/conda/.../jupyter_server/serverapp.py:472,
/opt/conda/.../jupyter_server_terminals/api_handlers.py, node_modules/@jupyterlab/builder/lib/extensionConfig.js,
jupyterlab/staging/package.json singletonPackages.

## RAN
- `python -m pytest jupyterlab_basic_terminal_extension/tests -q` -> 12 passed, 0.48s
- confirmed `@jupyterlab/filebrowser` present in node_modules
- confirmed `pip uninstall -y dist/*.whl` derives the project name from the wheel filename
  (a suspected Makefile no-op; DISPROVEN, dropped from findings)
- confirmed `@jupyterlab/filebrowser` IS in JupyterLab core singletonPackages, so the new
  `optional: [IDefaultFileBrowser]` token cannot be duplicated by the federated bundle
  (suspected CRITICAL; DISPROVEN, dropped)

## NOT REACHED - treat as UNREVIEWED, not clean
- .github/workflows/check-release.yml, prep-release.yml, publish-release.yml, enforce-label.yml,
  update-integration-tests.yml
- RELEASE.md, .copier-answers.yml, ui-tests/playwright.config.js, ui-tests/README.md, logs/README.md
- style/base.css, style/index.css, style/index.js
- No TypeScript compile/build was run; `tsc` and `jlpm build` were never executed this session
- No live JupyterLab verification of the new file-browser cwd default (Playwright not run)

## FINDINGS (full text as it would have been reported)

### MAJOR 1 - hard `/bin/bash` requirement lives as a bare literal at a call site
FACT. `jupyterlab_basic_terminal_extension/routes.py:39` - `return ["/bin/bash", "-c", _INIT_WAITER,
"basic-terminal-init", *argv]`. Every launch on every path goes through it. The waiter is
bash-specific (`read R0 C0 < <(stty size ...)` process substitution at routes.py:25, `trap ... WINCH`
at :23), so `/bin/sh` is not a substitute. Nothing declares this: not README.md, not
pyproject.toml:25-27 (`jupyter_server` only), not a named constant. On a bash-less image the pty
spawns, dies instantly and the tab closes - indistinguishable from "the utility exited".
REMEDY: add `_INIT_SHELL = "/bin/bash"` beside `_INIT_WAITER` (routes.py:22) and reference it at :39;
one line in README stating bash is required on the server. Leaves the waiter script untouched.
Breaks nothing. Do NOT add an sh fallback - the script cannot run under sh.

### MAJOR 2 - `or "~"` guards a state that cannot occur, and would silently pick the wrong directory
FACT. `routes.py:89-91` - `os.path.expanduser(self.settings.get("server_root_dir") or "~")`.
`server_root_dir` is set unconditionally by jupyter_server at
/opt/conda/lib/python3.13/site-packages/jupyter_server/serverapp.py:472. Upstream's own terminals
handler indexes it directly. If the impossible branch ever fired, a relative `cwd` would resolve
against `$HOME` and still return 200 - a wrong directory reported as success.
REMEDY: `root_dir = os.path.expanduser(self.settings["server_root_dir"])`. Deletes one branch and one
literal; keeps expanduser, which matches upstream. Could break: a hand-rolled Tornado app mounting
this handler without jupyter_server settings now raises -> 500, which is the correct signal.

### MAJOR 3 - the package's only public interface is documented nowhere, and its cwd rule now
diverges from the sibling terminals API
FACT. README.md:11-18 never names `basic-terminal:launch`, `argv`, `cwd`, or
`POST <base_url>/jupyterlab-basic-terminal-extension/launch-terminal`; README.md:15 says only "Adds a
JupyterLab command". With no menu, palette or launcher entry (src/index.ts:31-80 registers a command
and nothing else), the command id IS the product, and the npm/PyPI page tells a caller nothing.
FACT. routes.py:79-96 resolves a relative `cwd` against root_dir unconditionally and 400s if the
result is not a directory. jupyter_server_terminals/api_handlers.py `TerminalRootHandler.post` on the
same server tries the path as given first, falls back to root_dir, and silently DROPS cwd if neither
exists. Same concept, same server, two rules - and for callers of the already-published v1.0.6 this
is a silent semantic change (a relative cwd used to mean "relative to the server process cwd").
REMEDY: one "Usage" section in README - command id, `{argv: string[], cwd?: string}`, the exact cwd
rule (absolute used as-is; relative resolved against `ServerApp.root_dir`; unknown -> 400), and the
note that there is deliberately no UI entry. ~15 lines of README, zero code. Explicitly do NOT copy
upstream's silent-drop behaviour - the 400 is the better failure and should be documented, not
changed.

### MAJOR 4 - the change's behaviour is asserted by no test at any level
FACT, three occurrences:
- `src/__tests__/jupyterlab_basic_terminal_extension.spec.ts:6-8` is the cookiecutter placeholder
  (`expect(1 + 1).toEqual(2)`), and jest.config.js:26 `testRegex: 'src/.*/.*.spec.ts'` finds only it.
  So `jlpm test --coverage` (package.json:53), run in CI at .github/workflows/build.yml:36, emits a
  coverage report over src/ that no test touches - a green signal standing for zero verification.
- `ui-tests/tests/jupyterlab_basic_terminal_extension.spec.ts:9-25` asserts one activation console
  message and nothing else.
- The three new Python tests (tests/test_routes.py:52-68) assert HTTP status only. `terminal_manager`
  is never inspected, so the directory the pty actually receives is observed by nothing;
  `test_empty_cwd_means_root_dir` (:59) in particular would pass unchanged if the handler resolved
  to `$HOME`.
The frontend half of the diff - `const effectiveCwd = cwd ?? fileBrowser?.model.path`
(src/index.ts:47) and the disposal wiring at src/index.ts:62-77 - is exactly the part that can
silently no-op (optional token resolving null) and exactly the part nothing exercises.
REMEDY, smallest that closes it: (a) replace the placeholder spec body with one test that calls
`plugin.activate` against a stub app carrying a real `CommandRegistry` and a stub
`{model: {path: 'projects/demo'}}`, and asserts the POSTed body's `cwd` - ~25 lines in the file that
already exists, no new dependency (`@jupyterlab/testutils` is already at package.json:66); and
(b) in tests/test_routes.py:52, capture `terminal_manager.create` kwargs via monkeypatch and assert
`kwargs["cwd"] == str(jp_root_dir / "subdir")` - ~5 lines.
If the owner declines (a): then delete `src/__tests__/` and the `test` script rather than keep a CI
step that advertises coverage it does not have. Either is defensible; keeping it as-is is not.

### MAJOR 5 - two package managers and two lockfiles own one dependency set
FACT. Makefile:84-85 runs `$(NPM) install` and then `jlpm install` into the same tree, and
.yarnrc.yml:1 (`nodeLinker: node-modules`) means both write `node_modules`. Nothing consumes
`package-lock.json`: CI uses jlpm only (.github/workflows/build.yml:30,36), the wheel build hook is
`npm = ["jlpm"]` (pyproject.toml:71,75), and package.json:19-23 `files` does not ship it. So it is a
second resolution source that can drift from yarn.lock with no consumer to catch the drift, plus a
full extra install on every `make build`.
REMEDY: drop `$(NPM) install` from the `build` recipe in the CANONICAL Makefile at
/home/lab/workspace/private/jupyterlab/@utils/jupyterlab-extensions/Makefile and re-sync - a local-only
edit is reverted by the next sync. Stop tracking package-lock.json. NOTE THE CONFLICT: .claude/CLAUDE.md
currently mandates keeping package-lock.json committed and prettier-formatted, so this is the owner's
call, not a silent edit. Breaks: nothing in CI or the wheel build; only an undocumented local `npm ci`.

## Considered and DISMISSED (do not re-raise without new evidence)
- `@jupyterlab/filebrowser` bundling / token identity - it is in core singletonPackages, so the
  builder marks it `singleton: true, import: false`; the optional token resolves correctly.
- `..` traversal in a relative cwd - argv is arbitrary by owner's locked decision, so cwd traversal
  grants nothing new.
- `pip uninstall -y dist/*.whl` (Makefile:110) - pip derives the project name from the wheel
  filename; verified working, not a no-op.
- `_INIT_WAITER`'s `seq 1 50` / `sleep 0.1` timeout literals (routes.py:26-29) - load-bearing but
  documented in the comment directly above, and naming them would require f-string interpolation
  into a bash script. MINOR at most, below the floor for this run.
- ContentsManager.root_dir vs ServerApp.root_dir divergence - possible only under explicit
  non-default trait config; hypothetical, not flagged.
