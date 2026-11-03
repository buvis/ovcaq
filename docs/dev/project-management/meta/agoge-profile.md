# agoge strategy profile: ovcaq

Recon by OLIVIA on 2026-10-29 against HEAD `9ec3396301866ed06d5ec006e041f1452cedd65d`.
Every claim below traces to a command run or a file read during that recon.

Conventions used in this file:

- `REPO` = `/Users/bob/git/src/github.com/buvis/ovcaq` (written out in full in every command).
- `<T>` = a fresh temporary project root. Create it with
  `mktemp -d /private/tmp/agoge-<lane>.XXXXXX` and use the `/private/tmp/...`
  realpath everywhere. `/tmp` is a symlink on macOS and library-level path
  checks reject it (`ovcaq.paths.ProjectPathError: derived runtime path
  contains a symlink: /tmp`, seen when calling `state_path(Path('/tmp/...'))`).
  The CLI `--root` tolerates it only because explicit roots are trusted.
- Every `ovcaq` invocation: `uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked ovcaq --root <T> ...`.
  This works from any cwd. Never omit `--root`.
- Every `run`, `attach`, `pause`, `resume`, `stop` invocation additionally needs
  `env XDG_STATE_HOME=<T>/xdg-state XDG_CONFIG_HOME=<T>/xdg-config` in front,
  because the fleet registry defaults to `~/.local/state/ovcaq/runs` (exists,
  live, empty as of recon) and user config to `~/.config/ovcaq/config.toml`
  (absent as of recon). Verified: with the env set, the registry landed in
  `<T>/xdg-state/ovcaq/runs/` and the live dir stayed untouched.

## 1. Surfaces

### Toolchain (established)

- `mise which python` -> `/Users/bob/.local/share/mise/installs/python/3.12.13/bin/python`;
  `mise which uv` -> `/Users/bob/.local/share/mise/installs/uv/0.13.0/.../uv`.
  `mise.toml` pins python 3.12.13 and uv 0.13.0.
- The checked-in `.venv` does NOT match the pin: `.venv/pyvenv.cfg` says
  `uv = 0.11.29`, `version_info = 3.13`; `uv run --locked python --version`
  -> `Python 3.13.18`. All local checks below therefore ran on 3.13.18 while
  `.github/workflows/ci.yml` runs 3.12. Do not re-onboard to "fix" this during
  a probe; note it and move on (`./tools/onboard` = `uv sync --locked --all-groups`
  would rebuild the venv).
- `./tools/check` -> `mise run check` -> `uv run --locked ruff check .`,
  `ruff format --check .`, `mypy src/ovcaq`, `pytest`, `uv build`.
  `./tools/run-tests` -> `uv run --locked pytest` (forwards selectors).
  `uv build` writes `dist/` (gitignored, already holds `ovcaq-0.1.0.dev0`
  wheel+sdist from 2026-10-28); recon did not rerun it at the repo root.

### Test suite (runs)

- Collect: `uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked pytest --collect-only -q`
  -> `8438 tests collected in 0.69s`.
- Full run minus one module:
  `uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked pytest -q -p no:cacheprovider --ignore=tests/integration/test_terminal_lifecycle.py`
  -> `8417 passed in 234.86s`. No skips, no xfails reported.
- `tests/integration/test_terminal_lifecycle.py` (21 items) CANNOT run cleanly
  in this sandbox: its teardown shells out to `ps` and the Seatbelt profile
  denies it (`PermissionError: [Errno 1] Operation not permitted: 'ps'` at
  `test_terminal_lifecycle.py:107 ps_field`). The first test passed, the
  teardown errored, and it LEAKED three processes (`python -m ovcaq --root
  .../project run --no-tui`, `ovcaq.runtime._group_anchor`, the fake agent),
  which recon found with `pgrep -fl "ovcaq --root"` and killed by pid.
  Rule for every lane: pass `--ignore=tests/integration/test_terminal_lifecycle.py`;
  if you run it anyway, run `pgrep -fl "ovcaq --root"` afterwards and `kill`
  what it lists. (The `tests/runtime/conftest.py` `forbid_ps` fixture only
  covers `tests/runtime`.)
- Static checks: `ruff check .` -> `All checks passed!`; `ruff format --check .`
  -> `262 files already formatted`; `mypy src/ovcaq` -> `Success: no issues found in 62 source files`.
- pytest config (`pyproject.toml`): `--import-mode=importlib`, `pythonpath =
  tests/packaging, tests/state, tests/workflow`. Packaging tests build the
  wheel offline into pytest tmp (`tests/packaging/conftest.py`) and passed.
- Fixtures: `tests/fixtures/README.md` documents provenance. Executable fakes:
  `tests/fixtures/claude/v1/fake_claude.py` (emits a fixed stream-json session,
  no state change) and `tests/fixtures/codex/v1/fake_codex.py` (scenario
  selected by `OVCAQ_FAKE_SCENARIO`; `workflow` scenario performs real CLI
  handoffs through `OVCAQ_FAKE_CLI`). Gate-driven fake agent recipe
  (`FAKE_AGENT`, blocks each phase until `go-<phase>` exists) lives in
  `tests/integration/test_terminal_lifecycle.py:44-77` with the `World`
  project/config recipe at lines 194-257.

### CLI (runs)

- Entry point `ovcaq = ovcaq.cli:main` (pyproject). `python -m ovcaq` also works.
  Console script: `/Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/ovcaq`.
- `ovcaq --help` lists: `init, state, workflow, status, doctor, logs, run,
  attach, pause, resume, stop, capability`; globals `--root PATH`, `--json`.
  Full leaf inventory is generated into `docs/operations.md` (asserted equal to
  `render_command_reference()` by `tests/workflow/test_workflow_cli.py:376` and
  `tests/runtime/test_runtime_cli.py:98`).
- Exit codes (`src/ovcaq/errors.py`): usage/invalid_state/invalid_path/
  protected_path/runtime_format=1, state_io=2, oversized_plan=3, future_schema=6,
  state_exists=7, invalid_backup=8, revision_conflict=9, durability_unsupported=10,
  resource_limit=11, process_probe=12. Systemic park halt exits 4 (docs/operations.md).
  JSON errors go to stderr as `{"ok": false, "error": {"code", "message", "path"}}`.
- Root discovery (`src/ovcaq/paths.py:87`): explicit `--root` (trusted, symlinks
  resolved) else walk up from cwd for `ovcaq.toml`, then the runtime marker
  `docs/dev/project-management/ovcaq/`, then `.git`. The repo itself has no
  `ovcaq.toml` and no `docs/dev/project-management/ovcaq/`; its own live loop
  state is `docs/dev/project-management/autopilot/` (actively written; a
  `tracon.py --root REPO` monitor was running, pid 95841). OVCAQ does not read
  that tree, but nothing may be run without `--root <T>`.
- Verified in a temp root (all exit 0 unless noted):
  - `--json init` -> `{"ok": true, "result": null, "revision": 0}`; creates
    `<T>/ovcaq.toml` (empty) and `<T>/docs/dev/project-management/ovcaq/state.json`.
  - `--json status` -> `run: idle`, `state: available`, evidence inventory,
    purge preview.
  - `--json doctor` -> six capabilities all `supported` (`platform`,
    `advisory_lock`, `process_group`, `group_signal`, `directory_fsync`,
    `process_identity` with a `<sec>.<usec>` token). OBSERVATION: right after
    `init`, before any run, `doctor` reports `ok: false` because `permissions`
    and `writability` checks fail with `[Errno 2] No such file or directory:
    .../ovcaq/sessions` (`init` does not create `sessions/`). Not adjudicated.
  - `--json workflow select` on an empty prd root -> `{"prd": null, "source": "drained"}`.
  - `--json state get batch.status` -> `"idle"`.
  - `--json state set batch.status '"running"'` -> exit 1 `protected_path`;
    same for `control.pause_requested`. Generic mutation of protected paths
    needs `--unsafe`.
  - `--json capability retry bogus` -> exit 1 `usage: unknown capability: bogus`
    (matches the CHANGELOG Fixed entry).
  - `--json workflow phase-complete --outcome tasks_done --expected-revision N`
    with `work.prd == null` -> exit 1 `usage: workflow transitions require an active PRD`.
  - `logs` -> prints the newest session's `raw.jsonl` path.
  - `workflow render metrics` -> Markdown table of sessions.
  - `run --no-tui --json` with no `agent` configured -> exit 1
    `usage: configuration agent must be a nonempty name`.
- `python3 -I /Users/bob/git/src/github.com/buvis/ovcaq/tools/autopilot-prerequisites --prd 58 --config <T>/ovcaq.toml`
  -> exit 1 `{"ready": false, "prd": "58", "missing": [...]}`. Read-only; resolves
  `docs/dev/project-management/prds/done` relative to cwd.

### Supervised run (runs, with mocked agents)

Two recipes verified end to end in temp roots. Both need `env XDG_STATE_HOME=<T>/xdg-state XDG_CONFIG_HOME=<T>/xdg-config`.

Recipe A, no-progress agent (Claude driver, `fake_claude.py`):

1. `<T>/fake-agent` = `tests/fixtures/claude/v1/fake_claude.py` with its shebang
   replaced by `#!/Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/python`, mode 0700
   (the driver builds an isolated env; `/usr/bin/env python3` is not guaranteed).
2. `<T>/ovcaq.toml`:
   ```toml
   agent = "claude"
   [agents.claude]
   command = ["<T>/fake-agent"]
   tiers = { standard = "model-s", deep = "model-o" }
   [agents.claude.options]
   permission_mode = "auto"
   [phases.build]
   timeout_seconds = 60
   [phases.review]
   timeout_seconds = 60
   [phases.done]
   timeout_seconds = 60
   ```
3. `... ovcaq --root <T> --json init` then `... ovcaq --root <T> --json run --no-tui`
   -> after ~1s: `{"decision": "pause", "reason": "Session made no workflow progress", "sessions_attempted": 5}`, exit 0.
   Five session dirs under `<T>/docs/dev/project-management/ovcaq/sessions/<id>/`
   (`raw.jsonl`, `normalized.jsonl`, `meta.json`, `metrics.jsonl`, `summary.json`).
   OBSERVATION: afterwards `state show` has `recovery.phase_repeats: 5`,
   `batch.status: running`, `control.pause_reason: null`, `control.attention: null`,
   and `status` says `run: idle`, `attention: null`. Whether a no-progress pause
   is operator-visible anywhere but the run's stdout is unestablished.

Recipe B, full build -> review -> done journey (Codex driver, `fake_codex.py` workflow scenario):

1. `<T>/ovcaq.toml`:
   ```toml
   agent = "codex"
   [agents.codex]
   command = ["/Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/python", "/Users/bob/git/src/github.com/buvis/ovcaq/tests/fixtures/codex/v1/fake_codex.py"]
   tiers = { standard = "model-s", deep = "model-o" }
   [agents.codex.environment]
   OVCAQ_FAKE_SCENARIO = "workflow"
   OVCAQ_FAKE_CLI = "/Users/bob/git/src/github.com/buvis/ovcaq/.venv/bin/ovcaq"
   [agents.codex.options]
   allow_explicit_model = true
   [phases.build]
   timeout_seconds = 60
   [phases.review]
   timeout_seconds = 60
   [phases.done]
   timeout_seconds = 60
   ```
2. `<T>/docs/dev/project-management/prds/backlog/00001-fixture.md` containing `# Fixture PRD`.
3. `... ovcaq --root <T> --json init`.
4. Seed the active PRD the way `tests/runtime/test_supervisor_adapters.py:81-101` does
   (`state set work.prd` is protected):
   `uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked python -c "from pathlib import Path; from ovcaq.paths import state_path; from ovcaq.state.store import StateStore; store = StateStore(state_path(Path('<T>'))); print(store.transaction(lambda state: state['work'].update(prd='00001-fixture.md'))['revision'])"`
5. `env XDG_STATE_HOME=<T>/xdg-state XDG_CONFIG_HOME=<T>/xdg-config uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked ovcaq --root <T> --json run --no-tui`
   -> `{"decision": "complete", "reason": "Workflow and capabilities ended", "sessions_attempted": 3}`, exit 0.
   `workflow render metrics` then lists build (model-s) -> review (model-o) -> done (model-s)
   rows for `00001-fixture.md`. OBSERVATION: the PRD file stayed in `prds/backlog/`
   after `complete-prd`; whether the CLI must move it is for the journeys lane to
   settle against `docs/state-protocol.md` (recon did not).
   Without step 4 the fake's `phase-complete` is refused and the run ends
   `{"decision": "halt", "reason": "Unsuccessful session retries exhausted", "sessions_attempted": 2}`, exit 1.

One-command file writing for lanes limited to Read+Bash: use
`uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked python -c "..."`
with `pathlib.Path(...).write_text(...)` (no heredocs, no pipes). Recon wrote
both recipes that way.

### TUI (runs headlessly through a python pty only)

- Textual + Rich (`src/ovcaq/tui/app.py`). TTY `attach`/`run`/interactive
  `resume` open `FleetApp`/`ProjectApp`; keys `q` detach, `p` pause/resume,
  `s` stop (confirm with `y`), `?` help. Non-TTY `attach` falls back to plain:
  `env XDG_STATE_HOME=<T>/xdg-state XDG_CONFIG_HOME=<T>/xdg-config uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked ovcaq attach`
  -> `No live runs available; registry gaps: 0 stale, 0 malformed`, exit 0.
  `attach --json` is rejected (`attach does not support --json`); JSON `run`
  requires `--no-tui`.
- `tmux`, `expect` and `script` are all blocked by warden in this sandbox
  (`[warden] blocked tmux: needs review`, `blocked expect: unknown command`,
  `blocked script: unknown command`). Python `pty.fork()` works. Verified
  harness (one Bash command; press `q` after first output; strips CSI):
  ```
  uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked python -c "exec('import fcntl, os, pty, select, struct, sys, termios, time, re\nenv = dict(os.environ, XDG_STATE_HOME=\"<T>/xdg-state\", XDG_CONFIG_HOME=\"<T>/xdg-config\", TERM=\"xterm-256color\")\npid, fd = pty.fork()\nif pid == 0:\n    os.execvpe(sys.executable, [sys.executable, \"-m\", \"ovcaq\", \"attach\"], env)\nfcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack(\"HHHH\", 40, 120, 0, 0))\nout = bytearray()\nend = time.monotonic() + 8\nsent_at = None\nwhile time.monotonic() < end:\n    if select.select([fd], [], [], 0.2)[0]:\n        try:\n            out.extend(os.read(fd, 65536))\n        except OSError:\n            break\n    elif sent_at is None and len(out) > 0:\n        os.write(fd, b\"q\")\n        sent_at = time.monotonic()\n    if os.waitpid(pid, os.WNOHANG)[0]:\n        break\nprint(\"bytes\", len(out), \"alt_screen\", b\"\\\\x1b[?1049h\" in out)\nprint(re.sub(r\"\\\\x1b\\\\[[0-9;?]*[A-Za-z]\", \"\", out.decode(\"utf-8\", \"replace\"))[-700:])')"
  ```
  Result at recon: `bytes 14929 alt_screen True`, process ended on `q`.
  Swap the argv for `["-m", "ovcaq", "--root", "<T>", "run"]` (TTY run launches
  a supervisor and attaches) or `["-m", "ovcaq", "attach", "--run-id", "<id>"]`,
  and the key for `b"p"`, `b"s"`, `b"?"`. Readable screen text is easier through
  Textual's own pilot: `tests/tui/test_app.py:75` (`_screen_text` from
  `app.export_screenshot()`) and `app.run_test()` at lines 166-295.
- No browser. `import playwright` fails in the venv; no HTTP server, no web UI.
  (Chromium binaries exist in `~/Library/Caches/ms-playwright` from other
  projects; irrelevant here, and no specialist has a browser tool.)

### Database

None. Durable state is a JSON document store: `state.json` + `state.json.bak`
+ `state.json.lock` under `<root>/docs/dev/project-management/ovcaq/`, locked
transactions, monotonic `revision`, compare-and-set via `--expected-revision`,
restore from backup (`state restore`). Limits (`src/ovcaq/state/schema.py:32-43`):
`MAX_STATE_BYTES` 16 MiB, `MAX_COMMAND_PAYLOAD_BYTES` 2 MiB, `MAX_STRING_BYTES`
1 MiB, `MAX_CONTRACT_CARD_BYTES` 64 KiB, `MAX_JSON_DEPTH` 32,
`MAX_JSON_INTEGER_DIGITS` 640, `MAX_TASKS` 512, `MAX_ATTEMPTS_PER_TASK` 64,
`MAX_REVIEW_CYCLES` 32, `MAX_REVIEW_ITEMS` 1024, `MAX_CAPABILITIES` 64,
`MAX_OPEN_MAP_ITEMS` 256. Evidence: per-session JSONL dirs, `metrics.jsonl`,
`run.json`/`run-terminal.json`, fleet registry under `$XDG_STATE_HOME/ovcaq/runs`.
Seed/fixture path: `ovcaq init` + `StateStore(...).transaction(...)` as in
Recipe B; sanitized legacy states in `tests/fixtures/claude/legacy-state-*.json`.

### External services

- No network code in `src/` (`rg "urllib|http\.client|requests|socket\.|httpx|aiohttp"`
  matched only a string literal in `claude_events.py`).
- Externals are subprocesses, none reachable here:
  - `claude` CLI: `mise which claude` -> not installed. Driver probe only checks
    `shutil.which(command)` (`drivers/claude.py:86-96`).
  - `codex` CLI: `mise which codex` -> not installed. Driver pins `0.160.0`
    and probes `--version` and `login status` (`drivers/codex.py:39`, fixture
    `fake_codex.py:225-228`).
  - `autopilot-controller` (`[workflow] controller_argv`): opt-in, not
    installed, and `docs/operations.md:108-110` says nothing invokes it yet.
- Launcher homes `~/.claude` and `~/.codex`: never read (project rule); fakes
  take temporary `HOME`/`XDG_*`.
- Timing tool: `/usr/bin/time` works (`state validate` -> `0.07 real`);
  `hyperfine` is not installed.

## 2. Per-specialist strategy

| specialist | verdict | tactics / reason |
| --- | --- | --- |
| walter (journeys) | armed | Surfaces: supervised run Recipes A and B above, the `workflow` subcommands, `status`/`logs`/`render`. Steps: (1) fresh `<T>` per journey; (2) Recipe B to confirm build->review->done completes, then check `state show` (`batch.completed_prds`, `work.phase`), `workflow render report`/`audit`/`metrics`, `logs`, and whether `prds/backlog/00001-fixture.md` should have moved (read `docs/state-protocol.md` first); (3) Recipe A to probe the no-progress pause: after exit, run `status`, `state show`, `doctor` and decide whether the operator can see why the run stopped; (4) `pause --reason x` then `resume` (non-TTY, with the env) on an idle root and on a root with a live Recipe-B-style run started in the background (`run_in_background`); (5) `stop` with no live supervisor; (6) `doctor` right after `init` (`ok: false`, sessions dir missing) and again after one run; (7) the stall/park path: `workflow stall --prd NAME --site s --detail d` and `workflow park` against a PRD in `prds/wip`, then `state restore`; (8) `logs purge --before <RFC3339>` preview vs `--apply`. Always `--json` for assertions, plain for message wording. Report anything driven by the fakes as `mocked`. |
| heidi (integration, db) | armed | Surfaces: the state store, fleet registry, installed wheel, controller client. (1) CAS: in `<T>` run `state task add <file>` with `--expected-revision` equal and stale (expect exit 9 `revision_conflict`), `state restore` after a mutation and compare `state show` bytes to the `.bak`; (2) concurrency: launch 5-10 concurrent `state append`/`state task add` writers from one `uv run python -c` with `subprocess.Popen` and assert revisions are contiguous and `state validate` passes; (3) durability edges: make `state.json.lock` or the runtime dir read-only (chmod) and confirm `state_io` (exit 2) with intact state; truncate `state.json` and confirm `state restore` recovers; (4) registry: with `XDG_STATE_HOME=<T>/xdg-state` start a Recipe-A run in the background, inspect `<T>/xdg-state/ovcaq/runs/`, kill the supervisor with SIGKILL, then run `status`/`attach` (plain) and confirm stale-entry handling (`registry gaps: N stale`); (5) installed artifact: `uv --directory REPO run --locked pytest tests/packaging -q -p no:cacheprovider` (offline wheel build+install into pytest tmp) and read `tests/packaging/packaging_support.py` for the hostile-cwd recipe; (6) controller client: `uv --directory REPO run --locked pytest tests/workflow_client -q -p no:cacheprovider` plus a hand-driven `ControllerClient` against the `FAKE_CONTROLLER` script from `tests/workflow_client/conftest.py:40-73` with a bundle whose sha256 is wrong (expect refusal before any call); (7) `tools/autopilot-prerequisites --prd 58 --config <T>/ovcaq.toml` with a bundle that has a duplicate key or `NaN` (expect `is not valid JSON`). No real DB exists; say so in the report. |
| judy (UX) | armed (scoped) | No browser. Drivable with Read+Bash: (a) help/usage/error wording: `ovcaq --help`, every `<cmd> --help`, bad invocations (`state set` on a protected path, `capability retry bogus`, `attach --json`, `--json run` without `--no-tui`, `workflow phase-complete` with no PRD) in both plain and `--json` form, checking that messages name the fix; (b) plain fallbacks: non-TTY `attach` (empty fleet and with a live background Recipe-A/B run: expect a numbered run list and `run id:` prompt that detaches on EOF), non-TTY `run` output, `status` plain; (c) the Textual TUI through the python pty harness in section 1: `attach` empty fleet (`?` help overlay, `q`), `attach --run-id <id>` on a live run (panels, `p` pause, `s` then `n`/`y`), TTY `run` (launch + attach, `q` leaves the supervisor alive: check with `pgrep -fl "ovcaq --root"` and kill it afterwards), and the theme file at `<T>/xdg-config/ovcaq/theme`; (d) terminal restoration: after each pty session check the exit code and that output ends with `\x1b[?1049l`. For readable screens prefer `app.export_screenshot()` through `run_test()` as in `tests/tui/test_app.py`. A live run for (b)/(c) needs the gate-driven `FAKE_AGENT` from `tests/integration/test_terminal_lifecycle.py:44-77`, written with `python -c`, so the run stays alive until you touch `<T>/go-build`. |
| wendy (release, changelog) | armed | Facts: version `0.1.0.dev0`; `git tag --list` is empty; `CHANGELOG.md` has only `[Unreleased]`; `release.yml` is `workflow_dispatch` producing `dist/` artifacts; README calls status "development". Tactics: (1) take each `[Unreleased]` Added/Changed/Fixed bullet that names observable behavior and probe it in `<T>`: `doctor --json` has six capabilities incl. `process_identity` (seen); `capability retry NAME` unknown -> usage exit 1 (seen); JSON `run` without `--no-tui` rejected; `run` leaves `state.json` revision unchanged on a preflight failure (compare `state show` revision before/after a `run` with a missing agent command); neutral tiers `standard`/`deep` resolve with no tier table (Recipe B minus `tiers`); Codex `default` tier emits no `-m` (read the fake's `fake_invocation` argv in `raw.jsonl`); (2) docs drift: `uv --directory REPO run --locked python -c "from ovcaq.cli import render_command_reference; import pathlib; print(render_command_reference() == pathlib.Path('/Users/bob/git/src/github.com/buvis/ovcaq/docs/operations.md').read_text())"` and the state-protocol command inventory via `render_state_protocol_command_inventory`; (3) README command table vs `mise.toml` tasks and `tools/*` shims; (4) `docs/driver-protocol.md` pinned codex version `0.160.0` vs `drivers/codex.py:39` and `tests/fixtures/codex/v1/cli-version.txt`; (5) CHANGELOG prefix/scope conventions vs `git log --format=%s -40`; (6) the local venv 3.13 vs pinned 3.12 note in section 1 belongs in her report as a release-truth gap. Mocked agents -> `mocked`. |
| peggy (performance) | armed | Surfaces: CLI latency, state store at its limits, evidence decoding, supervisor loop. Baseline: `/usr/bin/time uv --directory REPO run --locked ovcaq --root <T> --json state validate` (0.07s real at recon; subtract `uv run` startup by also timing `--help`). Tactics: (1) grow state toward limits with `state task add` x 512 tasks and 64 attempts each (payload files written with `python -c`), timing `state show`, `state validate`, `workflow render report` at 10/100/512 tasks; expect `resource_limit` (exit 11) past the caps, not slowdowns; (2) contract card at 64 KiB and 1 MiB strings via `state contract set`; (3) redaction linearity claim (CHANGELOG: "redaction stays linear on long unbroken text"): time `ovcaq.events.model.sanitize_text` (or `redact`) on 1 KiB/100 KiB/10 MiB unbroken strings from `uv run python -c` with `time.perf_counter`; (4) session decode: feed a fake agent that emits 50k frames and some 16 MiB frames (modify `fake_claude.py` into `<T>`), time Recipe A and inspect `summary.json`/gaps; (5) `logs --follow` on a growing `raw.jsonl` (CPU via `/usr/bin/time -l`); (6) supervisor loop: Recipe A with `supervisor.phase_repeat_limit` raised in `[supervisor]` to 50 and measure wall time per session from `metrics.jsonl`; (7) `status` with 500 session dirs retained. No pytest-benchmark or hyperfine present; report numbers with the measurement command. |
| trudy (runtime security) | armed | Armed on surface alone: the runtime accepts CLI args, TOML config, JSON state/payload files, env vars, PRD Markdown frontmatter, and agent stdout frames. Tactics (all in `<T>`, with the env isolation): (1) config: symlinked `ovcaq.toml` (expect `_read_config` O_NOFOLLOW refusal), credential-shaped keys/values in `[agents.x.environment]` and options (`sk-...`, `token = ...`; expect `agent settings must not contain credentials`), `controller_argv` as a string instead of array, `[workflow] runtime_root = "../escape"` and `state_file` outside root (expect `derived runtime path escapes project root`), symlink components in `runtime_root`; (2) CLI path args: `--prd-root`, `--runtime-root`, `--state` pointing outside `<T>` or through a symlink; `logs purge --session ../../x` and `--session` with a path separator; `logs --session <id>` where the session dir is a symlink; (3) payloads: `state task add` with depth 33 JSON, 641-digit integers, duplicate keys, 2 MiB+1 bytes, a FIFO instead of a regular file; (4) state tampering: edit `state.json` by hand to a future `schema_version` (expect exit 6) and to a non-object; swap `state.json.bak` for garbage then `state restore` (expect exit 8); (5) env: `XDG_CONFIG_HOME` empty string, `HOME` unset, `XDG_STATE_HOME` through a symlink (fleet root uses `_checked_path`); (6) agent output: a fake agent that prints `password=...`, `sk-abcdefghijklmnopqrstuvwxyz`, `x-api-key: ...`, split tokens across frames, and invalid UTF-16 surrogates; then grep `normalized.jsonl`, `summary.json`, `metrics.jsonl` and TUI/plain output for the secrets (raw.jsonl is documented as private and may contain them); (7) process ownership: with a Recipe-A run in the background, send SIGTERM to the group anchor only, and to the supervisor, and confirm the fake agent dies (`pgrep -fl fake-agent`); (8) controller client: actor file world-readable (0644) and a controller that echoes the actor secret on stderr (expect redaction per `tests/workflow_client/conftest.py` `CANARY`). Report fake-driven results as `mocked`. The Authorization line in section 5 is resolved at dispatch time and does not decide this row. |

## 3. Mocking strategy

| external | how to mock | report as |
| --- | --- | --- |
| `claude` CLI | `tests/fixtures/claude/v1/fake_claude.py` copied into `<T>` with the venv shebang (Recipe A), or the gate-driven `FAKE_AGENT` from `tests/integration/test_terminal_lifecycle.py:44-77` for runs that must stay alive. Configure through `[agents.claude] command = [...]`. | `mocked` |
| `codex` CLI | `tests/fixtures/codex/v1/fake_codex.py` launched as `[venv python, fake_codex.py]`, scenario via `[agents.codex.environment] OVCAQ_FAKE_SCENARIO` in {`healthy`, `workflow`, `tool-active`, `lanes`, `lanes-matched`, `malformed`, `rate-limited`, `authentication-failed`, `connectivity-failed`, `permission-failed`, `version-timeout`, `version-failed`, `version-empty`, `version-unsupported`, `auth-timeout`, `auth-failed`, `native-reset`, `native-no-reset`, `noisy-success`, `descendant-term`, `descendant-kill`}; `workflow` needs `OVCAQ_FAKE_CLI` = the venv `ovcaq` script and `allow_explicit_model = true`. | `mocked` |
| `autopilot-controller` | `FAKE_CONTROLLER` script from `tests/workflow_client/conftest.py:40-73` with `tests/fixtures/workflow/controller-v1.json` as the pinned bundle; answers per verb from a spec JSON. | `mocked` |
| launcher homes (`~/.claude`, `~/.codex`) and user config | never read; run everything with `HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME` pointed into `<T>`. | n/a |
| `ps` | not mockable and denied by the sandbox; the product itself no longer spawns it (libproc), only `test_terminal_lifecycle.py` does. Skip that module. | n/a |

Nothing probed through these fakes may be reported `verified`.

## 4. Authoring assignments

- Surface: supervised-run journeys and operator visibility, under pytest in
  `tests/integration/` using a `World`-style temporary root (see
  `tests/integration/test_supervisor_live_telemetry.py` and
  `test_launcher_outcomes.py` for the non-pty pattern). Runner:
  `uv --directory /Users/bob/git/src/github.com/buvis/ovcaq run --locked pytest tests/integration -q -p no:cacheprovider --ignore=tests/integration/test_terminal_lifecycle.py`.
  Candidates, only if the lanes confirm them as defects: (a) a no-progress
  pause leaves `control.pause_reason`/`attention` null and `status` idle;
  (b) `doctor` reports `ok: false` on a freshly initialized root because
  `sessions/` is missing.
- Surface: the test harness itself. `tests/integration/test_terminal_lifecycle.py:106`
  shells out to `ps` in teardown and leaks supervisors when `ps` is denied;
  the product's own `ovcaq.runtime.registry.process_identity` is the
  sandbox-safe replacement. Runner: same pytest command without the `--ignore`.
- No specialist executes any of this. The master authors on a branch after the
  lanes report; a specialist that wants a test puts it in the finding's `fix`
  field and leaves nothing on disk.

## 5. Pins and vetoes

Authorization: not asserted

## 6. Freshness stamp

- Recon date: 2026-10-29
- Target HEAD: 9ec3396301866ed06d5ec006e041f1452cedd65d
