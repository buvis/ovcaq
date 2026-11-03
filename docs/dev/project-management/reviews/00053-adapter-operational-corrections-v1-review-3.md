---
prd: docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
review: 3
date: 2026-10-13
head_sha: e75b50ada7b87191491d921f30c82d900d4a91b5
reviewers: alice,blake,bob
agents:
  alice: available
  blake: available
  bob: available
  carl: disabled
dispatch_rows:
  bob: ff674c46
---

# Review: 00053-adapter-operational-corrections-v1

Diff range: `7819970d7f807d6fad07b115af4f0df1fbc4a248..e75b50ada7b87191491d921f30c82d900d4a91b5`

codex_rung_guard: not fired
provider_review_guard: satisfied
autocodex_alice_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle3-20261013-evidence/alice-output.txt.receipt.json
autocodex_blake_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle3-20261013-evidence/blake-output.txt.receipt.json
autocodex_bob_anthropic_receipt: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/project-management/autopilot/reports/00053-cycle3-20261013-evidence/bob-output.txt.receipt.json

The model-provider guard supersedes the legacy launcher guard. No Eve review ran. All three full-PRD lenses ran in fresh isolated external sessions with Anthropic claude-opus-5-5/xhigh; implementation authors were OpenAI gpt-6.1-sol and gpt-6-astra. Blake received only the PRD and source rubric, with repository access.

Carl: disabled by operator authorization retained from the recovery handoff.
Consensus engine: legacy.
Implementation audit: reports/00053-adapter-operational-corrections-v1-implementation-models.json (51 exact raw evidence rows, fingerprint f7645598a37e4569b5c80a3cf51803c1daa121e9bcbdd80e9148faf8541c3486).
Reviewed: 24/24 completed tasks. Whole-state schema and task counts validated.

## Subsequent operator disposition — 2026-10-13

The operator approved R1/R3 repairs, cap 3→4 for one fresh complete review, and normal finalization if that review is clean. Authorization and raw repair evidence: `reports/00053-cycle3-recovery-20261013/`. Tasks 25/26 implement that decision in commits `da0d4fc`, `f2ef1e2`, and `d9644c8`; task 25 has independent tests and a resolved Pat closure. Bare number/reason phrases acquire no new contract. Prior mixed-prefix/count, lifecycle and PATH/cwd deferrals remain settled.

The historical pending-disposition text below records the original review, not the current authorization. Original reviewer outputs, receipts and verdicts remain unchanged. These repairs still require the authorized fresh cycle-4 full roster and successful full verification before finalization.

## Consolidated Findings

| Ref | Consensus | Severity | Issue | File | Task | Found By |
|-----|-----------|----------|-------|------|------|----------|
| R1 | [3/3] | ⚪ | CHANGELOG.md:43 says the change will "avoid quadratic backtracking when Codex failure diagnostics contain long whitespace runs after a status prefix". That status prefix was added earlier in this same unreleased PRD (codex_events.py:300), and the pre-PRD base had no such regex. Compared with the base, users see no change. Task 16 deleted an earlier entry of the same kind ("describes no change from the pre-PRD base"). Delete this entry too. The `fix` commit type seems to have forced the entry, so a follow-up `docs` commit can remove it | CHANGELOG.md | 24 | ALICE, BLAKE, BOB |
| R2 | [1/3] | ⚪ | Cannot statically verify: Phase-2 exit gate `uv run pytest` at HEAD c119229. The last full suite to pass was at 9b8c55a, with 7159 passed. The only full run since then is in docs/dev/project-management/autopilot/reports/00053-recovery-20261013/verification.json: 6425 passed, 555 failed, 172 errors, on a host that denies `ps`. That host also failed the PRD-named routing check 8 of 8 with PermissionError. This cycle's test gate exited 2 and printed no counts. Commits 693e7ae through c119229 (tasks 18-24) have only narrow runs, so the earlier settled "resolved by current-HEAD verification" no longer applies to this HEAD | N/A | general | BOB |
| R3 | [1/3] | 🟡 | Some explicit status-code messages now classify as `unknown`. Before this change they classified correctly. Probed: `status=429`, `Error 429: Too Many Requests`, `HTTP error 503`, and bare reason-phrase forms like `429 Too Many Requests` and `503 Service Unavailable`. The spec allows numbers only in explicit HTTP/status/error-code context, and `status=429` and `Error 429:` are exactly that. Worse, tests/drivers/test_adapter_failure_classes.py:115 locks `status=429` and `Error 429:` in as `unknown`, so the wrong answer is now enforced as the expected class. Impact: a real 429 or 503 in these forms goes to the generic retry-then-PARK path instead of the bounded WAIT or rate-limit path. The native Codex forms ("unexpected status N", reqwest, HTTP/x) are covered. | src/ovcaq/drivers/codex_events.py:300 | Phase 0 task 1 | BLAKE |
| R4 | [1/3] | 🟡 | 58 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_adapter_failure_classes.py | general | mech-check |
| R5 | [1/3] | 🟡 | 17 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_adapter_outcomes.py | general | mech-check |
| R6 | [1/3] | 🟡 | 10 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_codex_decode_terminals.py | general | mech-check |
| R7 | [1/3] | 🟡 | 7 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_codex_failures.py | general | mech-check |
| R8 | [1/3] | 🟡 | 61 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_codex_launch.py | general | mech-check |
| R9 | [1/3] | 🟡 | 14 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/drivers/test_codex_rework_decode.py | general | mech-check |
| R10 | [1/3] | 🟡 | 18 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/runtime/test_adapter_health.py | general | mech-check |
| R11 | [1/3] | 🟡 | 4 touched tests pass against pre-change code; assess compatibility controls against PRD intent (fresh fail-first replay) | tests/runtime/test_adapter_launch_routing.py | general | mech-check |

### Auto-dismissed (ledger)

- [BLAKE] 🟡 Some explicit status-code messages now classify as `unknown`. Before this change they classified correctly. Probed: `status=429`, `Error 429: Too Many Requests`, `HTTP error 503`, and bare reason-phrase forms like `429 Too Many Requests` and `503 Service Unavailable`. The spec allows numbers only in explicit HTTP/status/error-code context, and `status=429` and `Error 429:` are exactly that. Worse, tests/drivers/test_adapter_failure_classes.py:115 locks `status=429` and `Error 429:` in as `unknown`, so the wrong answer is now enforced as the expected class. Impact: a real 429 or 503 in these forms goes to the generic retry-then-PARK path instead of the bounded WAIT or rate-limit path. The native Codex forms ("unexpected status N", reqwest, HTTP/x) are covered. | File: src/ovcaq/drivers/codex_events.py:300 — The old classifier did not match authentication failed; cycle1 deliberately removed that added pattern to retain existing word diagnostics. This is known original behavior, not a lost required diagnostic. Existing authentication fixtures use literal invalid-credentials/unauthorized oracles.
- [BLAKE] ⚪ The normal native lane flow (wait → completed → close_agent `shutdown`) now emits a `raw.unknown` for every completed lane. That sets the TUI raw-evidence flag (src/ovcaq/tui/model.py:548) on routine sessions. It is documented, but it will show up as noise on every multi-lane run. | File: src/ovcaq/drivers/codex_events.py:233 — Intentional documented raw-evidence rule: unsupported terminal close statuses on finished lanes retain RAW_UNKNOWN while preserving terminal identity. Exact tests and protocol document it. UI gap-noise redesign is outside this PRD; deleting evidence would contradict the reviewed contract.
- [BLAKE] ⚪ Probe and spawn can resolve a command from different directories. The probe resolves relative commands with a directory part (and, for Codex, commands under an empty host PATH) against the supervisor's own cwd (src/ovcaq/drivers/codex.py:186, src/ovcaq/drivers/claude.py:83). The spawn resolves them against `spec.cwd` = request.root (src/ovcaq/runtime/process.py:118). With `--root` different from cwd, the probe can pass while the spawn fails. Absolute paths are unaffected, as the spec requires. | File: src/ovcaq/drivers/codex.py:186 — Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.

### Correction to automatic ledger dismissal

R3 is restored from Blake's raw output. The consolidator matched his diagnostic-format finding against an unrelated prior `authentication failed` finding in the same file. That reason does not settle `status=429`, `Error 429:`, or `HTTP error 503`. The automatic dismissal remains verbatim above for audit, but it is **reversed**. R3 awaits operator disposition; no signature or diagnostic grammar change was made.

The completed-lane raw-evidence and relative probe-cwd findings remain settled under the cited intentional evidence contract and out-of-scope probe ownership decision. Existing operator deferrals for completed-lane cache eviction, mixed diagnostic-prefix/count grammar, and relative PATH/cwd remain unchanged.

## Classification and closure evidence

| Ref | Disposition | Evidence / next decision |
|-----|-------------|--------------------------|
| R1 | Operator decision pending (low) | Alice/Bob request deleting the intra-PRD backtracking changelog entry. Blake also requests user-facing PATH wording; retain both details of this merged row. No repair authorized after this review. |
| R2 | Resolved by fresh verification | Full suite: 7151 passed, 0 failed, 0 skipped; routing/supervisor: 8 passed; all quality/build gates exit 0 at reviewed HEAD. See evidence/verification.json and raw logs. Alice's multiline gate observation is also resolved by the same evidence; its claim that a partially written log was cut off does not describe the completed run. No gate timeout change is justified by that observation. |
| R3 | Operator decision pending (medium) | Restored after false ledger match. Expand explicit diagnostic spellings only after an operator scope decision; no new repair, cap increase, or finalization is authorized here. |
| R4–R11 | Discarded as compatibility controls | The PRD explicitly requires preserving genuine fixture classifications, direct tier precedence, existing Codex probe behavior, reset grammar, and ordinary routes. Prior ledger reasons cover these same test files. Fresh replay proves 56 touched tests fail at base and reports 189 passing controls; passing controls alone do not establish a tautology. Raw counts and per-file rows retained. |

No unresolved CRITICAL or HIGH finding. Zero production edits made in this review session. The review satisfies the provider/rubric constraint, but **does not authorize finalization**: recovery authorization explicitly requires an operator disposition before any additional repair or finalization.

## Verification

The initial review-stage gate exited 2 without the required summary; its fail-first worktree creation was denied by the calling sandbox. Both limitations were retained in the staged context. Approved retries kept existing guards: fail-first replay completed (245 touched tests, 56 fail at base, 189 pass), exact queued routing checks passed (8), and the full suite passed (7151). No old green record was substituted.

Sync, Ruff lint, Ruff formatting (236 files), mypy (61 source files), and build pass. The two pytest warnings concern temporary-directory cleanup; tests do not fail. Prior red verification and queue results are preserved in evidence/prior-last-verification.json and evidence/prior-checks-2.json.

Engram pack: unavailable (repository not registered); stage recorded the failure and used its explicit no-pack sentinel. No registration change was made.
Mechanical tautology-shape check: no finding lines.
Fail-first replay rows R4–R11 are supplemental coordinator evidence after the original restricted stage; reviewers' immutable prompts/outputs remain unchanged.

## Review coverage

Alice and Bob reviewed the full PRD work range and implementation context, including all changed files, task rows, design, mechanical facts, and settled ledger. Blake independently located implementation from the PRD only. Each output preserves its complete source rubric below; Bob also preserves the full doubt/de-slop buckets and D1–D5. All receipts bind the unchanged cycle-3 implementation snapshot.


## Alice

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; fresh session: 7401d3cc-642c-4aaa-9c3a-a5b449fd77eb. Raw evidence and hashes: alice-output.txt.receipt.json.

The second full-suite run also passed, so nothing in my review changes. Here is the output again:

[ALICE] ⚪ CHANGELOG.md:43 says the change will "avoid quadratic backtracking when Codex failure diagnostics contain long whitespace runs after a status prefix". That status prefix was added earlier in this same unreleased PRD (codex_events.py:300), and the pre-PRD base had no such regex. Compared with the base, users see no change. Task 16 deleted an earlier entry of the same kind ("describes no change from the pre-PRD base"). Delete this entry too. The `fix` commit type seems to have forced the entry, so a follow-up `docs` commit can remove it | File: CHANGELOG.md | Task: 24
[ALICE] ⚪ The cycle-3 test gate's "exit 2, no summary line" comes from a cut-off run, not from failing tests. full-suite.log stops at 71%, at the slow watchdog tests in tests/runtime/test_supervisor_process.py. The cycle-2 host verification at c119229 also never went green: it reported 555 failures, all from the sandbox blocking `ps`. Until my runs, HEAD had no green full-suite evidence for the PRD's exit criteria. I re-ran everything at HEAD with `ps` available:
- `uv run pytest`, run twice: 7151 passed, 0 failed, 0 skipped, exit 0 both times (263 s and 252 s)
- `ruff check`, `ruff format --check`, `mypy src/ovcaq` and `uv build`: all exit 0

Record these runs as the phase-2 gate evidence, and give the gate's pytest step a longer limit than it has now | File: N/A | Task: general

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

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; fresh session: c15f89af-b735-4f96-ade8-1ef09313a194. Raw evidence and hashes: blake-output.txt.receipt.json.

Exit gates run on HEAD e75b50a: `uv sync --all-groups` ok, `uv run pytest` 7151 passed with 0 failed or skipped (2 pytest tmp-cleanup warnings), `ruff check` ok, `ruff format --check` 236 files ok, `mypy` found no issues in 61 files, `uv build` built the sdist and wheel. DRIVER_API_VERSION=2, PROTOCOL_VERSION=1 and SCHEMA_VERSION=1 are unchanged. `failure_reset` is untouched. There are no TUI, config or provisioning changes.

[BLAKE] 🟡 Some explicit status-code messages now classify as `unknown`. Before this change they classified correctly. Probed: `status=429`, `Error 429: Too Many Requests`, `HTTP error 503`, and bare reason-phrase forms like `429 Too Many Requests` and `503 Service Unavailable`. The spec allows numbers only in explicit HTTP/status/error-code context, and `status=429` and `Error 429:` are exactly that. Worse, tests/drivers/test_adapter_failure_classes.py:115 locks `status=429` and `Error 429:` in as `unknown`, so the wrong answer is now enforced as the expected class. Impact: a real 429 or 503 in these forms goes to the generic retry-then-PARK path instead of the bounded WAIT or rate-limit path. The native Codex forms ("unexpected status N", reqwest, HTTP/x) are covered. | File: src/ovcaq/drivers/codex_events.py:300 | Task: Phase 0 task 1
[BLAKE] ⚪ The normal native lane flow (wait → completed → close_agent `shutdown`) now emits a `raw.unknown` for every completed lane. That sets the TUI raw-evidence flag (src/ovcaq/tui/model.py:548) on routine sessions. It is documented, but it will show up as noise on every multi-lane run. | File: src/ovcaq/drivers/codex_events.py:233 | Task: Phase 0 task 1
[BLAKE] ⚪ Probe and spawn can resolve a command from different directories. The probe resolves relative commands with a directory part (and, for Codex, commands under an empty host PATH) against the supervisor's own cwd (src/ovcaq/drivers/codex.py:186, src/ovcaq/drivers/claude.py:83). The spawn resolves them against `spec.cwd` = request.root (src/ovcaq/runtime/process.py:118). With `--root` different from cwd, the probe can pass while the spawn fails. Absolute paths are unaffected, as the spec requires. | File: src/ovcaq/drivers/codex.py:186 | Task: Phase 1 task 2
[BLAKE] ⚪ The Unreleased CHANGELOG has a "quadratic backtracking" fix entry for a regression this same PRD introduced and that never shipped. The PATH entry also describes internals (`os.defpath`, current-directory search) rather than what the user sees. | File: CHANGELOG.md:43 | Task: Phase 2 task 1

B1: pass
B2: pass
B3: pass
B4: pass
B5: fail
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

Provider: Anthropic; observed model: claude-opus-5-5; effort: xhigh; fresh session: b92f7ad9-0504-478c-ab81-a1720f1fec81. Raw evidence and hashes: bob-output.txt.receipt.json.

[BOB] ⚪ Cannot statically verify: Phase-2 exit gate `uv run pytest` at HEAD c119229. The last full suite to pass was at 9b8c55a, with 7159 passed. The only full run since then is in docs/dev/project-management/autopilot/reports/00053-recovery-20261013/verification.json: 6425 passed, 555 failed, 172 errors, on a host that denies `ps`. That host also failed the PRD-named routing check 8 of 8 with PermissionError. This cycle's test gate exited 2 and printed no counts. Commits 693e7ae through c119229 (tasks 18-24) have only narrow runs, so the earlier settled "resolved by current-HEAD verification" no longer applies to this HEAD | File: N/A | Task: general
[BOB] ⚪ CHANGELOG.md:43 says "avoid quadratic backtracking when Codex failure diagnostics contain long whitespace runs after a status prefix". That bug was added and fixed inside this PRD. The pre-PRD classifier had no status prefix and no adjacent `\s*` runs, so users never had this problem. Task 16 deleted an entry of the same kind ("describes no change from the pre-PRD base"). "Quadratic backtracking" is also jargon under the writing rules | File: CHANGELOG.md | Task: 24

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

Notes on the cycle-3 changes, all checked by reading the code (none run):
- **Task 24 regex.** In src/ovcaq/drivers/codex_events.py:302, `\s*+:?\s*+` matches the same strings as `\s*:?\s*`. If the first run gave back whitespace, `:?` cannot take it and the second `\s*` would take it straight back, so possessive changes nothing about what matches. It does remove the backtracking. Every other part of `{status}` is linear: `\d+(?:\.\d+)?` has at most one dot group, and the optional ` status…` group has fixed text. Python ≥3.12 (pyproject.toml:12) supports `*+`.
- **Task 24 test.** The 200,000-space check runs in a child process because `re` holds the GIL and an in-process timeout could not fire. The red run (red-24.txt) shows it timing out against the old pattern.
- **Task 23 test.** The merged test in tests/drivers/test_adapter_outcomes.py:208 keeps both discriminator cases and their follow-up close assertion. No helper parameters are left unused.
- **Model mapping.** `_map_model_to_tier` (src/ovcaq/drivers/edge.py:16) handles collisions, duplicate values and the cycle `{a: b, b: a}` correctly: route a → "b" → key a → launches b.
- **Claude probe vs launch.** The Claude PATH lookup (src/ovcaq/drivers/claude.py:82) matches the launch merge `os.environ | spec.env` (src/ovcaq/runtime/supervisor.py:504) and `subprocess`'s `os.get_exec_path` fallback to `os.defpath`.

FIX:
- The changelog entry for the backtracking fix describes no change from the pre-PRD base. Same class as task 16's deletion. — CHANGELOG.md:43 — Delete the line. CHANGELOG.md:46 (numeric-context entry) already covers this classifier change.

VERIFY:
- Phase-2 exit gate is unproven at HEAD c119229. The last recorded full run has 555 failed and 172 errors on a host that denies `ps`, and this cycle's gate exited 2 with no counts. — On a host where `ps` is allowed, run `uv run pytest -q --tb=line` and record the passed/failed/skipped counts with exit 0 against SHA c119229. Then run `uv run pytest -q tests/runtime/test_adapter_launch_routing.py tests/runtime/test_supervisor_adapters.py` as a separate command and confirm 8 passed.

KNOWN:
- (none)

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass

## Outcome

Operator decision required for R1/R3 and finalization. No tasks queued, no implementation provenance changed, cycle/cap remains 3/3.

Verdict: 11 findings
Tests: 7151 passed, 0 failed, 0 skipped (suite run this cycle at e75b50a; full-suite.log, exit 0; 2 cleanup warnings)
