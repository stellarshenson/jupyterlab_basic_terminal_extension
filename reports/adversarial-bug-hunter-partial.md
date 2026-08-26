# Adversarial review - PARTIAL (session terminated mid-hunt)

Lens: bug-hunter (runtime bugs; quoting/expansion, conditionals, set -e, fresh-vs-restart
asymmetry, interrupt safety, installer/uninstaller contract, lifecycle races).
Target: /home/lab/workspace/private/jupyterlab/jupyterlab_basic_terminal_extension @ main,
uncommitted working tree.

NOTE: written to /tmp scratchpad, NOT into the repo - the review contract for this agent is
critique-only, no writes into the tree under review.

VERDICT (provisional): DO-NOT-SHIP (3 findings) - worst is the pty-death-before-WebSocket
race, which makes JupyterLab silently spawn the user's default interactive $SHELL under the
launched terminal's name.

## Coverage - what was actually read

READ AND TRACED
- jupyterlab_basic_terminal_extension/routes.py (whole file)
- src/index.ts (whole file)
- jupyterlab_basic_terminal_extension/__init__.py, conftest.py
- jupyterlab_basic_terminal_extension/tests/test_routes.py (whole file)
- git diff for .gitignore, Makefile, routes.py, test_routes.py, package.json, src/index.ts
- Dependency behaviour traced in installed sources:
  /opt/conda/lib/python3.13/site-packages/terminado/management.py,
  terminado/websocket.py, jupyter_server_terminals/terminalmanager.py,
  jupyter_server_terminals/api_handlers.py,
  and the minified JupyterLab 4.6.3 bundle
  /opt/conda/share/jupyter/lab/static/jlab_core.a3196067513a13d4.js
  (terminal:open / terminal:create-new implementations)

TESTED
- `python -m pytest -vv -r ap` -> 12 passed, 0 failed (includes the 3 new cwd tests)

NOT REACHED - treat as UNREVIEWED, not clean
- _INIT_WAITER executed in a real pty. NO runtime test was run. All statements about its
  timing, SIGWINCH delivery, `read ... < <(...)` interruption, `clear` under a missing/dumb
  TERM, and the exit-status path of a failed `exec` are UNVERIFIED reasoning only.
- Makefile: only the DIFF was read, never the full file. `install`, `uninstall`, `publish`
  bodies below the diff hunks, the `help` target, and the tail of `check_dependencies`
  (the branch that invokes install_dependencies) were never seen.
- .github/workflows/* - not opened at all
- pyproject.toml, install.json, jupyter-config/ - not opened at all
- ui-tests/ (playwright specs, jupyter_server_test_config.py) - not opened at all
- src/request.ts, src/__tests__/ - not opened at all
- The live-server race test (spin up jupyter_server, POST a fast-exiting argv, then attach
  the WebSocket late and observe what process the pty runs) was designed but NOT run.

## Findings

### 1. [CRITICAL] Pty death before the WebSocket attaches makes JupyterLab spawn the user's default $SHELL under that terminal name

Evidence chain, all traced in installed source:
- routes.py:107 `model = terminal_manager.create(**kwargs)` registers the name and starts
  the pty immediately, BEFORE any client exists.
- terminado/management.py:421-427 `NamedTermManager.on_eof` -> `self.terminals.pop(name, None)`:
  when the pty EOFs, the name is REMOVED from the manager's dict.
- JupyterLab 4.6.3 `terminal:open` (jlab_core bundle):
  `execute: i => { let r=i.name, s=tracker.find(e=>e.content.session.name===r);
   if(!s) return commands.execute('terminal:create-new',{name:r}); shell.activateById(s.id) }`
- `terminal:create-new` with a name:
  `n = r ? ((await TerminalAPI.listRunning(...)).map(e=>e.name).includes(r)
        ? terminals.connectTo({model:{name:r}})
        : await terminals.startNew({name:r, cwd:d})) : ...`
  The name is gone from listRunning, so it takes the `startNew({name})` branch.
- That POSTs /api/terminals -> jupyter_server_terminals TerminalManager.create(name=...)
  -> terminado new_terminal, management.py:228 `options["shell_command"] = self.shell_command`
  i.e. the DEFAULT interactive shell, with no cwd and no _INIT_WAITER.

Wrong behaviour: the user gets a plain interactive $SHELL tab that never auto-closes, which is
precisely the thing this extension exists to prevent. No error is surfaced anywhere.

Trigger (sequence): the argv's pty reaches EOF between the POST returning and the browser's
WebSocket attaching. Concretely reachable via
(a) the 5s `_INIT_WAITER` timeout path - no client connected within 5s (cold JupyterLab
    start, slow `TerminalAPI.listRunning` round-trip, a heavy tab) - after which argv runs
    unattached and, being a short-lived utility, exits in milliseconds; or
(b) any argv[0] that is missing / non-executable: ptyprocess only validates `/bin/bash`
    (routes.py:39 hardcodes it), so creation succeeds and bash exits 127 the instant it
    reaches `exec "$@"`.

REMEDY (diff scale, server side, ~6 lines in routes.py): do not hand the frontend a bare
name it must re-resolve. Either
- have the frontend pass the name to `terminal:create-new` only after confirming the terminal
  is still in `/api/terminals`, and surface an explicit error when it is not; or better
- keep the pty alive until a client attaches: make `_INIT_WAITER` not time out into `exec`
  but exit non-zero, and have the frontend treat a vanished name as a failed launch.
Leaves alone: the argv contract, the cwd logic, the auth surface. Risk: option 2 changes the
"no client ever connects" fallback from "run anyway" to "do not run", which is a behaviour
change the owner must sign off on.

### 2. [MAJOR] `terminal:open` returns undefined for an already-tracked widget, so focus and the auto-close wiring are both silently skipped

- src/index.ts:56-77 assumes `terminal:open` resolves to the widget. It does not: the bundle's
  `terminal:open` returns `commands.execute('terminal:create-new',...)` only on the miss path;
  on the hit path it runs `shell.activateById(s.id)` and returns undefined.
- src/index.ts:59 `if (widget?.id)` and src/index.ts:62 `widget?.content?.session` then both
  short-circuit: no `activateById`, and crucially NO disposal handlers are connected. The tab
  therefore does not auto-close when the process exits - the extension's headline behaviour.
- The hit path is reachable because terminado reuses freed names:
  terminado/management.py:394-399 `_next_available_name` returns the first integer name not
  currently in `self.terminals`, and management.py:427 frees the name on EOF. So launch #2
  can legitimately be handed name "1" again while an undisposed widget for "1" is still in the
  tracker. `terminal:open` then activates the OLD dead widget, returns undefined, and the NEW
  pty is left with no client at all - it waits out the 5s, runs argv unattached, and orphans.
- src/index.ts:78 `return widget;` also returns undefined to the caller in this case.

Trigger: launch a utility, let it exit, leave the (now-dead) tab open - i.e. any path where
the disposal wiring did not fire, including the very case in this finding - then launch again.

REMEDY (frontend, ~4 lines in src/index.ts): stop relying on `terminal:open`'s return value.
Call `terminal:create-new` with `{name: launched.terminal_name}` directly, which always
resolves to the MainAreaWidget; or, if `terminal:open` must be kept, look the widget up from
`ITerminalTracker` after the call instead of from the return value. Leaves alone: the server,
the argv/cwd contract. Risk: `terminal:create-new` will `connectTo` an already-connected name,
so a duplicate widget for the same pty becomes possible - needs a tracker guard.

### 3. [MAJOR] The file-browser path is sent raw, without `contents.localPath()`, so any non-default drive 400s every no-cwd launch

- src/index.ts:47 `const effectiveCwd = cwd ?? fileBrowser?.model.path;`
- JupyterLab's own terminal command in the same bundle does NOT do this - it does
  `let l=i.cwd, d = l ? h.contents.localPath(l) : void 0;` before sending. The
  `localPath()` call exists specifically to strip a `Drive:` prefix from a Contents path.
- With any drive-mounted file browser (jupyter-fs, an S3/GCS drive, RTC), `model.path` is
  `"Drive:some/dir"`. routes.py:88 `os.path.isabs("Drive:some/dir")` is False, so routes.py:92
  joins it onto root_dir producing `<root>/Drive:some/dir`, routes.py:93 `isdir` fails, and the
  handler returns HTTP 400 `invalid_cwd`. src/index.ts's `requestAPI` throws, the command
  rejects, and the launcher tile does nothing visible.

FACT for the code path and the 400; SUSPICION only for how commonly a deployment puts the
DEFAULT browser on a prefixed drive. Settling test: run JupyterLab with jupyter-fs (or any
IDrive-registering extension), point the default file browser at that drive, invoke
`basic-terminal:launch` with no cwd, and check the network tab for the 400.

REMEDY (1 line, src/index.ts:47): mirror JupyterLab -
`const p = cwd ?? fileBrowser?.model.path;`
`const effectiveCwd = p === undefined ? undefined : app.serviceManager.contents.localPath(p);`
Leaves alone: everything server-side; `localPath('')` is `''` so the root case is unchanged,
and absolute programmatic cwds are unaffected (localPath only strips a drive prefix).

## Suspicions raised but NOT verified - next session should test these first

- `_INIT_WAITER` (routes.py:22-33) never executed. Specific untested concerns:
  * `resize_to_smallest` (terminado/management.py:78-82) only calls `setwinsize` when the size
    actually differs, so a client that fits to exactly 24x80 produces NO SIGWINCH and NO size
    diff -> the loop burns the full 5s before launching. Degraded, not broken; likely MINOR.
  * `for i in $(seq 1 50)` - if `seq` is absent the word list is empty, the loop body never
    runs, and the waiter degrades to zero wait plus a "command not found" on the pty.
  * `clear` with an unset/dumb TERM. terminado forces TERM=xterm-256color
    (terminado/management.py:41, 194), so this is probably a false alarm - confirm.
  * SIGWINCH arriving while bash is blocked in `read r c < <(...)`: does the trap fire, does
    `read` return partial/empty, and does the empty-vs-$R0 comparison then break correctly.
  * `/bin/bash` hardcoded at routes.py:39 - on an image without bash, ptyprocess raises
    FileNotFoundError out of `terminal_manager.create()` at routes.py:107 with no try/except,
    giving an unhandled 500. Untested.
- Makefile, DIFF ONLY. Unverified suspicion worth testing first:
  `uninstall: pip uninstall -y dist/*.whl 2>/dev/null || true` - `pip uninstall` takes
  distribution NAMES, not wheel paths; if it rejects the path then `make uninstall` has always
  been a silent no-op and `make install` never removes the prior install. One-line test:
  `pip uninstall -y ./some.whl; echo $?`. The rest of the Makefile (install/publish/help
  bodies, the install_dependencies invocation inside check_dependencies) was never read.
- Concurrency: two `basic-terminal:launch` calls in flight at once were never exercised.
  `_next_available_name` is not reserved until `new_named_terminal` completes, but the whole
  handler runs on the tornado IO loop without an await between naming and registration, so
  this is probably safe - confirm by reading routes.py:98-117 against an async boundary audit.

## Journeys re-walked
- Fresh install (no .nodeenv, no node_modules): NOT walked - Makefile only partly read.
- Restart (existing state): partially - the terminado name-reuse path in finding 2 is exactly
  this axis and is traced.
- Interrupt: NOT walked. Ctrl+C into the waiter, and closing the browser tab mid-wait
  (`client_disconnected` is a no-op on NamedTermManager, terminado/management.py:283-284)
  were both left unexamined.
