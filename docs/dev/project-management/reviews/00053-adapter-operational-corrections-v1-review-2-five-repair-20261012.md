---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 2
round: five-repair-20261012
date: 2026-10-12
head_sha: eb1065f7fd21b8b39ccd1d07274d571959bdcaae
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: c08c8a89
---

# Review: 00053 adapter operational corrections

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..eb1065f7fd21b8b39ccd1d07274d571959bdcaae`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-five-repair-review-20261012-evidence/alice-output.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-five-repair-review-20261012-evidence/blake-output.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-five-repair-review-20261012-evidence/bob-output.txt.receipt.json

The model-provider guard supersedes the legacy Codex rung guard. Eve did not run; Carl is disabled by operator scope. All three independent processes served claude-opus-5-5 with requested xhigh effort. Full PRD coverage; fresh sessions, no resumed implementation/reviewer threads. Blake received only the PRD and blind rubric. Complete raw outputs and receipts remain immutable.

20/20 tasks complete; cycle and cap remain 2. All five authorized closures are present. No repair occurred in this review session. Prior reviews, settled decisions, receipts and implementation attempts remain intact.

Staging limitations: engram pack failed because this repository is not registered; fail-first replay was skipped because sandbox denied .git/worktrees creation. Neither is represented as a passed check. No mechanical finding was emitted. Previous-cycle checks queue is empty; Bob's VERIFY bucket is empty.

Verification: review-stage reused the recorded build at deb7300 (7155/0/0), with only workflow-store commits afterward. Blake independently ran the acceptance set (275 passed), all quality/build gates, and the full suite: first run had one signal-test failure, isolated retry passed 3/3, second full run passed 7155. Retain that flake as a known limitation; do not describe the first run as green.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [2/3] | 🟡 | Task 20 stopped passing a name to `fake_executable`, so its `name: str = "fixture-agent-health"` parameter is now dead: all 9 callers use the default. This file is new in this PRD, so the leftover comes from the repair itself. Fix: drop the parameter and write `executable = directory / "fixture-agent-health"` | tests/runtime/test_adapter_health.py:33 | 20 | ALICE, BOB |
| R2 | [2/3] | ⚪ | Carried Pat18 LOW: `workflow_fixture` writes the Claude wrapper file and returns its path, but its name is a noun. Action functions should start with a verb, e.g. `write_workflow_fixture` (call sites tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33). The new helpers `configured_workflow` (tests/runtime/test_adapter_launch_routing.py:24) and `configured_driver` (tests/drivers/test_codex_launch.py:30) have the same shape. Against renaming: the older helpers in the same file (`adapter_harness`, `workflow_agent`) also use nouns, so a rename would break from the file's current style | tests/runtime/test_supervisor_adapters.py:40 | 18 | ALICE, BOB |
| R3 | [1/3] | ⚪ | The numeric grammar only accepts `HTTP[/x.y]`, `HTTP status [client\|server error (]`, `status [code][:]` and `error code[:]`. Other explicit HTTP or error forms used to classify through the bare number and now return `unknown`. Confirmed by running the classifier: "HTTP Error 503: Service Unavailable" gives unknown (was connectivity), "HTTP Error 429: Too Many Requests" gives unknown (was rate_limit), "Error 403: Forbidden" gives unknown (was permission), "status=429" gives unknown. The tests pin `status=429` and `Error 429:` as UNKNOWN. Codex's own Rust forms (`unexpected status N ...`, `last status: N`, reqwest `HTTP status ... error (N ...)`) are covered, so the risk is limited to non-native formats. | src/ovcaq/drivers/codex_events.py:300 | general | BLAKE |
| R4 | [1/3] | ⚪ | With an empty host PATH, the Claude probe reports unhealthy because `shutil.which(path="")` returns None. The launch would still find the command in the project root, because subprocess treats an empty PATH as the current directory. The Codex probe reports healthy in the same environment, so the two adapters disagree. This is documented as intentional and fails safe (false unhealthy), but it does not "resolve under the launch environment". | src/ovcaq/drivers/claude.py:82 | general | BLAKE |
| R5 | [1/3] | ⚪ | Flaky test: `test_installed_foreground_signals_return_shell_status_and_stop_the_driver[15]` failed once under full-suite load (returncode 1, expected 143). It passed in isolation (3/3) and in a second full run (7155 passed). Not traced to this diff, but this PRD's exit gate depends on `uv run pytest` passing. | tests/packaging/test_installed_supervisor_cli.py:591 | general | BLAKE |
| R6 | [1/3] | ⚪ | A 16 MB binary review artifact is committed to the tracked project-management tree. This is permanent history bloat for evidence that could be regenerated or summarized. | docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-diff-00053-postrepair-20261012.diff.gz | general | BLAKE |
| R7 | [1/3] | ⚪ | `test_claude_probe_rejects_sh_hidden_by_overlay_path` repeats the `[claude]` case of `test_probe_rejects_host_executable_hidden_by_overlay_path` (tests/runtime/test_adapter_health.py:213). Both put the command on the host PATH, use an overlay without it, and hit the same `shutil.which(..., path=overlay) is None` branch, and both fail on the base code. This is the same kind of padding task 20 removed from line 90 | tests/runtime/test_adapter_health.py:181 | 3 | BOB |

### Auto-dismissed (ledger)

- [BLAKE] ⚪ The probe and the spawn resolve relative names against different directories. Both probes run with no `cwd`: Codex Popen and Claude `shutil.which` use the supervisor's working directory. The spawn uses `cwd=spec.cwd`, which is the project root. So a relative command (`./bin/codex`), a relative PATH overlay entry (`bin:/usr/bin`), or Codex's empty-PATH current-directory lookup can be healthy at probe and missing at launch, or the reverse, when `ovcaq --root X run` starts outside X. This breaks the exit criterion "health checks and actual spawn agree". Suspected from subprocess semantics, not reproduced. | File: src/ovcaq/drivers/codex.py:47 — Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.
- [BLAKE] ⚪ The normal subagent lifecycle (wait → completed, then close_agent → shutdown) emits `raw.unknown` with reason "Malformed or unsupported Codex record" on every healthy run, which sets the TUI raw indicator (tui/model.py:548). Late running/errored/completed updates on terminal lanes are dropped silently. The two cases are inconsistent, and a healthy close looks like a malformed record. The tests pin this behavior (test_adapter_outcomes.py:89). | File: src/ovcaq/drivers/codex.py:378 — Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.

## Decision Gate

- R1: actionable Medium. All nine callers omit name; the parameter became unused after task20. Remove it and inline the fixed name, subject to another operator authorization.
- R2: actionable Low. Carry Pat18's verb-led naming issue; review the new configured_workflow/configured_driver action helpers as part of the same bounded naming cleanup. Existing untouched noun helpers are not a reason to expand scope.
- R3: deferred contract question. Native diagnostic forms are covered; status=429 and Error 429 are deliberately pinned unknown. Additional non-native HTTP Error forms require explicit grammar scope. Preserve the production grammar during this bounded test/prose pass.
- R4: settled limitation. Empty-PATH behavior is explicitly documented, pinned and fail-safe; directory-dependent resolution is part of the existing deferred probe/launch cwd question. No new probe redesign is authorized.
- R5: known out-of-scope test flake. One SIGTERM full-suite failure, isolation and second full suite green. It is not traced to this PRD; preserve exact evidence for separate investigation.
- R6: discarded. The operator expressly requires preserving previous raw evidence, reviews and receipts. This compressed diff is retained review evidence, not an authorized history cleanup target.
- R7: actionable Low. Both tests reject a command hidden by overlay PATH through the same Claude lookup branch. Retain the parametrized both-provider test when removing the dedicated sh case, subject to authorization.

No unresolved Critical or High. Three distinct actionable Medium/Low findings remain. The operator's bounded authorization requires a pause before further implementation; no tasks were queued and finalization is withheld.

## Alice

Provider: Anthropic; model: claude-opus-5-5; requested effort: xhigh; session: 01b025ed-c063-4a98-bda6-a62160e03591

[ALICE] 🟡 Task 20 stopped passing a name to `fake_executable`, so its `name: str = "fixture-agent-health"` parameter is now dead: all 9 callers use the default. This file is new in this PRD, so the leftover comes from the repair itself. Fix: drop the parameter and write `executable = directory / "fixture-agent-health"` | File: tests/runtime/test_adapter_health.py:33 | Task: 20
[ALICE] ⚪ Carried Pat18 LOW: `workflow_fixture` writes the Claude wrapper file and returns its path, but its name is a noun. Action functions should start with a verb, e.g. `write_workflow_fixture` (call sites tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33). The new helpers `configured_workflow` (tests/runtime/test_adapter_launch_routing.py:24) and `configured_driver` (tests/drivers/test_codex_launch.py:30) have the same shape. Against renaming: the older helpers in the same file (`adapter_harness`, `workflow_agent`) also use nouns, so a rename would break from the file's current style | File: tests/runtime/test_supervisor_adapters.py:40 | Task: 18
R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass
## Blake

Provider: Anthropic; model: claude-opus-5-5; requested effort: xhigh; session: a199a0c6-fcf8-4a3b-a331-e2f795b53d2c

```
Gates (run 2026-10-12): acceptance set 275 passed | full suite run 1: 1 failed/3473 passed (-x), run 2: 7155 passed
ruff check: All checks passed | ruff format --check: 236 files already formatted | mypy: no issues in 61 files | uv build: sdist+wheel built
Prod diff since 7819970: claude.py +4, codex.py +8, codex_events.py +20/-?, edge.py +25 (43 ins / 14 del); DRIVER_API_VERSION=2, PROTOCOL_VERSION=1, SCHEMA_VERSION=1 unchanged; no pyproject/uv.lock/tui changes
```

[BLAKE] ⚪ The numeric grammar only accepts `HTTP[/x.y]`, `HTTP status [client|server error (]`, `status [code][:]` and `error code[:]`. Other explicit HTTP or error forms used to classify through the bare number and now return `unknown`. Confirmed by running the classifier: "HTTP Error 503: Service Unavailable" gives unknown (was connectivity), "HTTP Error 429: Too Many Requests" gives unknown (was rate_limit), "Error 403: Forbidden" gives unknown (was permission), "status=429" gives unknown. The tests pin `status=429` and `Error 429:` as UNKNOWN. Codex's own Rust forms (`unexpected status N ...`, `last status: N`, reqwest `HTTP status ... error (N ...)`) are covered, so the risk is limited to non-native formats. | File: src/ovcaq/drivers/codex_events.py:300 | Task: general
[BLAKE] ⚪ The probe and the spawn resolve relative names against different directories. Both probes run with no `cwd`: Codex Popen and Claude `shutil.which` use the supervisor's working directory. The spawn uses `cwd=spec.cwd`, which is the project root. So a relative command (`./bin/codex`), a relative PATH overlay entry (`bin:/usr/bin`), or Codex's empty-PATH current-directory lookup can be healthy at probe and missing at launch, or the reverse, when `ovcaq --root X run` starts outside X. This breaks the exit criterion "health checks and actual spawn agree". Suspected from subprocess semantics, not reproduced. | File: src/ovcaq/drivers/codex.py:47 | Task: general
[BLAKE] ⚪ With an empty host PATH, the Claude probe reports unhealthy because `shutil.which(path="")` returns None. The launch would still find the command in the project root, because subprocess treats an empty PATH as the current directory. The Codex probe reports healthy in the same environment, so the two adapters disagree. This is documented as intentional and fails safe (false unhealthy), but it does not "resolve under the launch environment". | File: src/ovcaq/drivers/claude.py:82 | Task: general
[BLAKE] ⚪ The normal subagent lifecycle (wait → completed, then close_agent → shutdown) emits `raw.unknown` with reason "Malformed or unsupported Codex record" on every healthy run, which sets the TUI raw indicator (tui/model.py:548). Late running/errored/completed updates on terminal lanes are dropped silently. The two cases are inconsistent, and a healthy close looks like a malformed record. The tests pin this behavior (test_adapter_outcomes.py:89). | File: src/ovcaq/drivers/codex.py:378 | Task: general
[BLAKE] ⚪ Flaky test: `test_installed_foreground_signals_return_shell_status_and_stop_the_driver[15]` failed once under full-suite load (returncode 1, expected 143). It passed in isolation (3/3) and in a second full run (7155 passed). Not traced to this diff, but this PRD's exit gate depends on `uv run pytest` passing. | File: tests/packaging/test_installed_supervisor_cli.py:591 | Task: general
[BLAKE] ⚪ A 16 MB binary review artifact is committed to the tracked project-management tree. This is permanent history bloat for evidence that could be regenerated or summarized. | File: docs/dev/project-management/autopilot/reports/00053-postrepair-review-20261012-evidence/review-diff-00053-postrepair-20261012.diff.gz | Task: general

B1: pass
B2: pass
B3: pass
B4: pass
B5: pass
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: pass
B15: pass
B16: pass
B17: pass
B18: pass
B19: pass
## Bob

Provider: Anthropic; model: claude-opus-5-5; requested effort: xhigh; session: 6359730c-f431-4db6-9d3f-3e4f5c91ff3d

[BOB] ⚪ `fake_executable` keeps a `name: str = "fixture-agent-health"` parameter that no caller passes. Task 20 removed its only caller, the `command_name` parametrization, so the parameter is now speculative generality | File: tests/runtime/test_adapter_health.py:33 | Task: 20
[BOB] ⚪ Carried Pat18 LOW: `workflow_fixture` is a noun, but the function writes the Claude wrapper script, so it performs an action and should have a verb-led name. The sibling helper `configured_workflow` in tests/runtime/test_adapter_launch_routing.py:24 has the same shape | File: tests/runtime/test_supervisor_adapters.py:40 | Task: 18
[BOB] ⚪ `test_claude_probe_rejects_sh_hidden_by_overlay_path` repeats the `[claude]` case of `test_probe_rejects_host_executable_hidden_by_overlay_path` (tests/runtime/test_adapter_health.py:213). Both put the command on the host PATH, use an overlay without it, and hit the same `shutil.which(..., path=overlay) is None` branch, and both fail on the base code. This is the same kind of padding task 20 removed from line 90 | File: tests/runtime/test_adapter_health.py:181 | Task: 3

R1: pass
R2: pass
R3: pass
R4: pass
R6: pass
R7: pass
R8: pass
R9: pass
R10: pass
R11: pass
R12: pass
R13: pass

FIX:
- `fake_executable` has an orphaned `name` parameter — tests/runtime/test_adapter_health.py:33 — drop the parameter and inline `directory / "fixture-agent-health"` at line 36.
- `workflow_fixture` names an action with a noun — tests/runtime/test_supervisor_adapters.py:40 — rename it to a verb-led name such as `make_workflow_fake`, and update the call sites at tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33 plus the import at tests/runtime/test_adapter_launch_routing.py:13.
- A duplicate Claude hidden-by-overlay test — tests/runtime/test_adapter_health.py:181 — delete `test_claude_probe_rejects_sh_hidden_by_overlay_path`. The parametrized `test_probe_rejects_host_executable_hidden_by_overlay_path[claude]` already pins this behavior.
VERIFY:
- (none)
KNOWN:
- (none)

```
D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
```
## Carl

Disabled by operator scope.

Verdict: 7 findings
Tests: 7155 passed, 0 failed, 0 skipped (Blake independent second full suite; first-run signal flake retained above)
