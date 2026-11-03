# Product readiness review — OVCAQ — 2026-10-18

Target: `master` at `cf0a506` (lanes ran at `c9980a5`; the one commit between
them touches only docs, `mise.toml`, `tools/`, `.gitignore`). Question asked:
is the product ready for a public beta, and is it properly tested.

Method: four independent lanes, each with a fresh context and a read-and-run
brief, then the master re-ran the most severe claims before accepting them.

| Lane | Scope | Status |
| --- | --- | --- |
| journeys (agoge walter) | install, init, workflow, run, controls, error UX, docs walk | verified, except `run` (sandbox) |
| release truth (agoge wendy) | metadata, artifacts, README, CHANGELOG, generated docs, CI, upgrade, hygiene | verified; ubuntu CI outcome unverified |
| test-suite quality | inventory, per-dir execution, mocks, intent sample, flakiness, coverage | verified; runtime/tui numbers sandbox-depressed |
| critical-path trace | `run --no-tui` chain, hold-PRD status at HEAD, invariant sweeps | verified where no process spawn was needed |
| security (agoge trudy) | not dispatched | skipped: no `--authorized` assertion |

Sandbox limit: the macOS Seatbelt profile denies `/bin/ps`.
`runtime/registry.py:130` runs `ps` for process identity, so every supervised
run, `attach`, `stop`, and every test that spawns a supervisor dies there.
Anything past `Supervisor._publish_ownership` is read-derived in this review.

## Verdict

Not half-baked in the way feared, and not shippable as a public beta either.

- **What is solid.** State kernel, workflow transitions, both decoders, event
  normalization, TUI panels. In-sandbox: 6499 tests pass, 0 fail for product
  reasons, 0 skipped, 0 xfail, 0 flakes across three runs of the process-heavy
  suites, 0 tautologies; 20 of 24 randomly sampled tests bind to a real rule.
  Mocks sit at the OS boundary, not around the unit under test. The 2026-09-06
  hold backlog is mostly stale: of 11 items checked at HEAD, 8 are fixed
  (both CRITICALs included), 2 partial, 1 live.
- **What blocks a beta.** (1) No production verb activates a PRD or moves it
  between buckets, so an operator cannot drive a lifecycle without writing a
  protected state path with `--unsafe`; a mistimed `stall` wedges the project
  with no supported way out. (2) The supervised run from a fresh `init` to a
  completed batch is proven by no test and could not be run here; it has a hard
  `ps` dependency that surfaces as a `state_io` error. (3) The repo and release
  surface: ~2800 tracked evidence files with the owner's home path, no install
  or quickstart, CI that has never run, a changelog that contradicts the binary.

## Test gate in this sandbox

`./tools/check` at `cf0a506`: ruff check pass, ruff format pass, mypy pass
(61 files), `uv build` pass.

| pytest | count |
| --- | --- |
| collected | 7257 |
| passed | 6499 |
| failed | 561 |
| errored | 198 |
| failures/errors whose first `E` line is the `ps` denial | 648 |
| remaining, all traced to the same denial inside a spawned child | 111 |
| confirmed product failures | 0 |

Per directory: characterization, events, state, workflow pass completely;
drivers 1643/1651; packaging 114/142; tui 245/389; runtime 1191/1631;
integration 26/164. Every miss is the denial. Last full pass outside the
sandbox on record: 7251 passed at `ab3101b` (project capsule, 2026-10-15).
The local `.venv` runs Python 3.13.16, not the pinned 3.12.13.

## Findings

Severity is the strictest any lane gave after the master's audit. Status is
the finding-contract word: only `verified` was watched happening.

### 1. CRITICAL — a refused `workflow stall` bricks the project

`verified` (journeys; master re-ran on the walker's project).
With `work.prd` set and the PRD file still in `backlog/`,
`workflow stall --prd ... --site ... --detail ...` exits 2
"PRD is not present in wip or hold" but has already committed
`recovery.operation` with `artifact: null`, `step: intent`. Afterwards
`phase-complete`, `complete-prd`, `defer`, `state restore`,
`state set --unsafe recovery.operation null` and
`state delete --unsafe recovery.operation` all exit 1
"recovery operation '...' is active; reconcile it first". Replaying `stall`
repeats the refusal; moving the file into `wip/` by hand makes `stall` and
`park` fail "PRD artifact identity changed". The only exit is editing
`state.json` by hand, which invariant 1 forbids.
Paths: `workflow/records.py` (~506-521 commits the intent before source
validation), `workflow/_files.py:543` (`_require_artifact_identity` rejects a
null identity forever), `state/commands.py`.
Fix: validate the source before committing the intent, or let a replay with a
null artifact re-bind identity; give `state restore` an explicit override for
a stuck recovery operation.

### 2. HIGH — nothing in the product activates a PRD or moves it through the buckets

`verified` (journeys, trace; tests lane confirms no end-to-end test).
`workflow select` returns `{"prd", "source"}` and commits nothing
(`workflow_cli.py:290-294`). `work.prd` is written by no production code
(`new_state` sets `None`, `schema.py:301`; `frontmatter.apply_to_store`
requires it, `frontmatter.py:173-177`; `complete_prd` raises without it,
`records.py:158-160`). It is a protected path, so the only route is
`ovcaq state set --unsafe work.prd '"..."'`, which is undocumented. Only
wip -> hold file moves exist (`records.py:261-308`); after `complete-prd` and
`phase-complete --outcome drained` succeed, the file stays in `wip/`,
`batch.status` stays `running`, and `select` re-offers the completed PRD.
Every drain test seeds `batch.*` and `work.prd` straight through the store
(`tests/runtime/test_supervisor.py:215`, `tests/packaging/test_installed_supervisor_cli.py:68`,
`tests/runtime/test_supervisor_adapters.py:96`; 61 seeding lines in 34 files).
Fix: a committing `workflow select` (or `workflow activate`) that sets
`work.prd` and moves backlog -> wip; `complete-prd` moves wip -> done or
`select` skips `completed_prds`; one installed-wheel test from `ovcaq init` to
`batch.status == "completed"` with the fake agent mutating state only through
the `ovcaq` console script, for both launchers.

### 3. HIGH — `phase-complete --outcome tasks_done` is accepted on an idle batch with no PRD

`verified` (journeys; master re-ran). Straight after `init`:
`workflow phase-complete --outcome tasks_done` returns
`{"ok": true, "result": {"next_phase": "review", "phase": "review"}, "revision": 1}`
with `batch.id == ""`, `batch.status == "idle"`, `work.prd == null`.
`state restore` is the only way back. Paths: `workflow/transitions.py`,
`workflow_cli.py`. Fix: require an active PRD and a running batch for phase
transitions.

### 4. HIGH — capabilities can never succeed, and `capability retry` dumps a traceback

`verified` (journeys; master re-ran the traceback) / `unverified` for the
runner claim (trace, read). `supervisor_cli.py:68-73 _UnavailableRunner.run`
always raises and is the only runner wired into `run` (`:183`) and `retry`
(`:463`). A required capability therefore always ends in
`batch.status = "attention"`, and retry fails identically.
`ovcaq --json capability retry NAME` on a project with no such capability
prints a Python traceback ending `KeyError: 'NAME'` from
`runtime/capability.py:299`, exit 1, no JSON envelope. Fix: map unknown names
to a usage error; either wire a real runner or hide the verb until one exists.

### 5. HIGH — the supervisor hard-depends on `ps`, misreports its absence, and leaves state dirty

`verified` (live probe in all four lanes). `ovcaq run --no-tui` on a fresh
project exits 2 with `{"error": {"code": "state_io", "message": "[Errno 1]
Operation not permitted: 'ps'"}}` after `start_batch` committed
`batch.id`/`status: running`; `status` then says `run: idle` with no
attention. `process_identity` (`registry.py:126-141`) has no exception
handling, no doctor check, and is monkeypatched in only 2 test files; no test
covers a missing or denied `ps` (minimal Linux images lack procps).
Misconfiguration such as missing tiers is also detected only inside
`_attempt`, after the batch is started and ownership published
(`supervisor.py:339` vs `:152`, `:159`). Fix: catch `OSError` in
`process_identity` and raise a typed error with its own code and remedy; add a
`doctor` check; validate the phase route before `start_batch`; roll the batch
back to idle when the first session never opens.

### 6. HIGH — a public push would publish the owner's agent transcripts and home paths

`verified` (release; master re-ran the counts). 2804 of 3084 tracked files
live under `docs/dev/project-management/`; 1811 under `autopilot/` (543 MB on
disk, 512 Codex session files); `git count-objects` pack 139 MiB; 1127 tracked
files contain `/Users/bob`; `.lock`/`.bak` files are tracked despite the
ignore rule (`autopilot/deferred/202609062243-deferred.json.lock`,
`autopilot-prd00003-paused-preserved/{autocodex.lock,state.json.bak,state.json.lock}`).
Secret-shaped strings: 0 hits. The built sdist and wheel are clean (`docs/dev`
excluded). Fix: move evidence out of the repo and rewrite history before the
first public push; untrack the lock and bak files.

### 7. HIGH — no user-facing install, quickstart, platform statement, or config reference

`verified` (release, journeys, trace). README's only section is
"Development"; no `pip`/`uv tool install`, no first-run sequence. The product
refuses non-macOS at runtime (`capability.py:77-79`, `registry.py:61-62`) and
no doc or classifier says so. README claims "launcher checks" but `doctor`
checks no launcher binary, version or auth. The agent table shape
(`[agents.<name>] command`, `tiers`, `[agents.<name>.options] permission_mode = "auto"`)
appears only in `docs/driver-protocol.md:364`; the first `run` with a bare
`agent = "claude"` fails "Claude permission_mode must be auto" with nothing
to point at. Default phase tiers are the model names `sonnet`/`opus`
(`drivers/__init__.py:18`, imported by neutral `config.py:502`), so a Codex
project without `[agents.codex.tiers]` fails "Unknown agent tier: sonnet".
Fix: README Install, Quickstart, "macOS only", Configuration (full agent
table), Compatibility; reword or implement the launcher-check claim.

### 8. HIGH — no CI has ever run, and the workflow tests the wrong platform

`verified` (release; static). No remote, no tags. `ci.yml` is
ubuntu-only, Python 3.12, `uv sync --all-groups` and `uv run pytest` without
`--locked`; `mise.toml check` uses `--locked`; README says CI uses the same
implementations. The runtime refuses non-darwin, and
`tests/integration/test_control_commit_identity.py:532,555` call
`run_lock_held` with no skip, so the ubuntu job would fail on the product's
own platform guard. `release.yml` builds artifacts only. Fix: `macos-latest`
job with `--locked` and uv pinned to 0.13.0; run it once before any beta.

### 9. MEDIUM — CHANGELOG contradicts the binary and reads as internal jargon

`verified` (release; master re-read). Single `[Unreleased]`, 109 bullets,
no version sections. Line 31 "Import-only package boundaries and a help-only
`ovcaq` command" vs 12 subcommands; line 36 "Create-only initialization
requires an existing runtime directory" vs `init` creating
`docs/dev/project-management/ovcaq/state.json` in an empty dir. No entry
names `init`, `status`, `doctor`, `logs`, `workflow *`, `--json`, `--root`.
Fix: collapse into one user-facing 0.1.0 section organised by command.

### 10. MEDIUM — `doctor` false-fails after `init`, shows raw errno, exits 0

`verified` (release, journeys). After `init`, `doctor` reports
`"permissions": "[Errno 2] No such file or directory: '.../ovcaq/sessions'"`,
same for `writability`, `"ok": false`, exit 0. `init` does not create
`sessions/`; `run` does. Fix: create it in `init` or report "missing, created
on first run"; exit non-zero when `ok` is false.

### 11. MEDIUM — three code paths resolve the state file differently (hold 00021, still live)

`verified` (trace, live). With `[workflow] runtime_root = "rt"` in
`ovcaq.toml`: `state get revision` reads the default path and answers `0`;
`--json status` reports `"state": "missing"` under `rt/`;
`workflow resume-target` fails "cannot open state lock .../rt/state.json.lock".
`init` ignores every config key (`cli.py:334-338, :475`). Paths:
`cli.py:475`, `paths.py:151`, `config.py:244-251`, `config.py:344-351`.
Fix: one resolver, used by `init`, `state`, `status`, `workflow`, `run`.

### 12. MEDIUM — failure classification still misses common Claude diagnostics (hold 00036, partial)

`verified` (trace, in-process probe). Claude `failure_payload`:
`OAuth token has expired` -> `agent`, `HTTP 429 Too Many Requests` -> `agent`,
`Error: read ECONNRESET` -> `agent`, `Rate limit exceeded` -> `agent`; a 429
therefore takes one died-retry and PARKs instead of the bounded WAIT. Codex
(`codex_events.py:298-339`, repaired by 00053) classifies 429/503 correctly
but `OAuth token has expired` and `ECONNRESET` -> `unknown`.
Paths: `drivers/claude_events.py:223-247`.

### 13. MEDIUM — upgrade story is refusal-only and undocumented; the product writes outside the project

`verified` (release). `schema_version: 2` -> exit 6 "newer than 1";
`0` -> exit 1 "must equal 1"; no migration code. Fleet registry at
`~/.local/state/ovcaq/runs` and `~/.config/ovcaq/config.toml` are undocumented
(only the theme path is). No stability or deprecation statement anywhere.
Fix: a README Compatibility section naming both paths and the pre-1.0 policy.

### 14. MEDIUM — test blind spots behind the healthy count

`verified` (tests lane). 22% of the 7257 tests are seven unicode/event
files running in 1 s (`test_unicode_safety.py` 957 cases from 15 functions).
`fake_claude.py` never drives the supervisor; the "claude" drain variant runs
`fake_codex.py`'s scenario with a swapped `__file__`
(`test_supervisor_adapters.py:44-51`). Both providers are proven only against
schema-synthetic fixtures (`tests/fixtures/README.md:24-25`). 35 negative
assertions accept any non-zero exit or any `OSError`, which is how the sandbox
denial slipped past `pytest.raises(OSError)` in
`test_supervisor.py:444`. Coverage lower bound in-sandbox: 88% total;
`runtime/supervisor.py` 46%, `runtime/process.py` 59%, `tui/model.py` 30%
(all depressed by the denial). Fix: see finding 2's test, a `ps`-free
`process_identity` fake for the supervisor suite, one sanitized captured
transcript per provider asserted on `SessionSummary`, and assert error codes
rather than non-zero.

### 15. LOW — error and output polish

`verified` (journeys, release).
- Human output of `state show`, `state validate`, `status`, `doctor` is the
  same one-line JSON as `--json`; `status` never shows batch, phase or PRD.
- No `ovcaq --version`; the error blames a missing subcommand.
- `stop` with no run: "cannot stop the running supervisor: [Errno 2] ...
  run.json" (`runtime_format`), while `attach` says the clean "No matching
  run selection; available: none".
- `workflow select` prints `{"prd": null, "source": "drained"}` exit 0 on a
  missing PRD root, missing state, or corrupt state.
- `park` after a successful `stall` refuses "has no durable recovery proof";
  `docs/operations.md:51` says both retain durable intent.
- Mutating verbs answer only "state revision N"; `pause` on a project with no
  supervisor sets the flag silently.
- Nonexistent `--root`: `state show` exits 2 with a lock-file errno, `status`
  exits 0 with `"state": "missing"`.

### 16. LOW — packaging and metadata

`verified` (release, trace). Wheel ships eight zero-byte modules
(`provision/*.py`, `drivers/command.py`, `runtime/__init__.py`,
`workflow/__init__.py`) and the placeholder `resources/extensions.toml`
("Extension requirements will be declared by a later task"); nothing imports
them. `pyproject.toml` has no `authors`, `urls`, `classifiers`, `keywords`;
version `0.1.0.dev0`; five README links are relative and dead in METADATA, two
of them to files the sdist excludes. `docs/baseline.md` (personal dotfiles
commit, Python 3.14.6, old test failures) ships in the sdist. Local `.venv` is
Python 3.13.16 against the 3.12.13 pin.

### 17. LOW — residuals from the hold backlog

`unverified` (trace, read). Per-class retry budgets still reset in
`Supervisor._decide` (`supervisor.py:611-612`) but `phase_repeat_limit=5`
bounds the loop (00041 partial). The signal scope covers only `_loop`
(`supervisor.py:161`); SIGTERM between `_publish_ownership` and the scope, or
SIGKILL any time, leaves `run.json` and the fleet entry, and
`FleetRegistry.prune` (`registry.py:428`) has no production caller
(00020/00034 residual). `paths.events` is never written; retention still
filters the dead file (`_retention.py:103,278`).

## Hold backlog at HEAD

40 triage stubs sit in `prds/hold/` (ledgers 2026-09-06 and 2026-10-09;
2 CRITICAL, 38 HIGH). Checked against HEAD by the trace lane:

| Hold | Issue | At HEAD | Evidence |
| --- | --- | --- | --- |
| 00042 | no production code starts a batch | fixed (ffe1f21) | live: `run` set `batch.id`, `status: running` before the `ps` stop |
| 00026 | exit collection closes anchor, leaks children | fixed (61511af) | `process.py:147-159` SIGKILLs the group before closing |
| 00022 | purge locks by replaceable pathname | fixed (647cdd3) | `_retention.py:343-370` opens locks with `dir_fd`, re-stats |
| 00040 | capability failure leaves batch running | fixed (ffe1f21) | `commands.py:599-605` sets attention |
| 00030 | `status` ignores FleetRegistry | fixed (ebbb2e1) | `runtime_cli.py:154-165` |
| 00047 | `--json run` without `--no-tui` | fixed (92e15b3) | live: usage error |
| 00020 | signal handling only raises | fixed, residual above | `supervisor.py:161-182` |
| 00033 | read paths take the run lock | fixed | `_run_observation.py:167-213` uses F_GETLK |
| 00041 | retry budgets dodged | partial | finding 17 |
| 00036 | failure classes missed | partial | finding 12 |
| 00021 | three state-file resolvers | live | finding 11 |

The other 29 were not checked. Several stubs still name `dev/local/prds/hold/`
as their location (for example 00022, 00026). Re-triage the folder against
HEAD before spending effort on it; close the fixed ones.

## Deferred and out of scope

- Security lane not run: needs a human `--authorized` assertion or the profile
  line. The path-security triage items (00024-00029) were not re-checked.
- The supervised run (`run`, `attach`, `stop`, TUI) must be exercised outside
  the sandbox before any beta call; see "How to proceed".
- Live Claude and Codex launches were not attempted; all launcher evidence is
  against the fakes or schema-synthetic fixtures.
- The `.venv` Python mismatch was observed, not changed.

## How to proceed

1. On the host, outside the agent sandbox: `./tools/check`. Expect the 759
   sandbox misses to pass; anything else is new.
2. Fix findings 1, 3, 4 (traceback) and 5 (error code, doctor check, batch
   rollback) first: each is a small, local change with an obvious test.
3. Decide the PRD-activation contract (finding 2): either OVCAQ owns
   `work.prd` and the bucket moves, or the external skill does and the docs
   plus `select` say so. Ship the fresh-`init` journey test with it.
4. Strip evidence from the repo and history (finding 6) before creating any
   remote the public can reach; a private remote is safe meanwhile.
5. Write the user README and the 0.1.0 changelog (findings 7, 9, 13), add
   `--version`, fill `pyproject.toml` metadata, drop the empty modules
   (finding 16).
6. Add the macOS CI job and run it once (finding 8).
7. Re-triage `prds/hold/` against HEAD; close the eight fixed items.
8. Then a private beta with one external user before a public one.
