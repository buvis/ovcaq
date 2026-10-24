# Workflow readiness repair — 2026-10-25

Status: implementation complete for this slice; full verification and fresh review pending.
Base: `cee9b9432e4cbd93dae936ca426ac97dfc105116`.
Scope: findings 1 and 3 from the local 2026-10-18 product-readiness review.
This does not close a PRD or authorize provisioning, cutover, or publication.

## Implemented behavior

- Stall and park reject absent source artifacts and conflicting destinations
  before committing recovery intent. Rejection preserves state and backup bytes.
- Source file and lifecycle directory identity remain guarded through durable
  intent publication, using the existing state-store publication guard.
- Explicit state restoration accepts an older unbound intent only when its step
  is `intent` and its artifact is null. Such an intent cannot pass the move's
  identity check. Bound recovery and advanced steps remain fenced. Restoration
  does not move PRD files; the failed intent remains in the rotated backup.
- Phase transitions require a running batch and an active PRD, except a drain
  from build can omit the PRD. The supervisor still owns batch finalization.
- The fake launcher handoff fixture now starts its batch through `StateService`
  before invoking phase transitions. It previously exercised an idle batch.
- The parser-generated operator reference and state protocol describe the changes.

Related existing source obligations: P01-T08 (restore), P02-T03 (transitions),
P02-T07 (recovery saga), P02-T10 (generated workflow documentation).

## Verification observed in this session

- Baseline: workflow and state suites, **1,583 passed**.
- Regression-first run: **35 failed, 35 passed** before production changes.
  Failures exposed missing preconditions, unguarded intent publication, and
  refusal to restore an unbound intent.
- Final targeted command: `./tools/run-tests tests/workflow tests/state tests/packaging/test_installed_workflow_preconditions.py tests/packaging/test_installed_sagas.py tests/drivers/test_codex_fake.py::test_command_backed_workflow_handoffs -q --tb=short`
  — **1,645 passed in 18.56 seconds**.
- Ruff lint and formatting passed; mypy passed for 61 source files.
- `./tools/build` produced both the source distribution and wheel.
- `./tools/check` was attempted and interrupted at **3,292 passed, 91 failed,
  27 errors**, after 127.25 seconds. The environment denies execution of `ps`;
  process-ownership tests fail or wait for children that cannot initialize.
  One failure was the idle fake-launcher fixture, subsequently corrected and
  covered by the final targeted run. The other failures were not individually
  adjudicated. This is **not** a passing full verification gate.
- Tests used the existing uv environment's Python 3.13.16. Mise resolves the
  declared Python pin to 3.12.13; testing that exact interpreter remains pending.
- No independent review ran in the implementation session.

## Reconciliation of the readiness report

The original report refers to an earlier repository history. Its findings are
inputs, not current truth. Labels below distinguish reproduced failures from
source inspection and work outside this slice.

| Finding | Current disposition | Evidence or next owner |
| --- | --- | --- |
| 1 — refused stall leaves unrecoverable intent | Reproduced and repaired here; review pending | Recovery-precondition and installed CLI regressions |
| 2 — missing PRD activation and bucket transitions | Read-confirmed; next workflow slice | `workflow select` is read-only; completion records a summary without moving the PRD; no supported activation command |
| 3 — idle batch accepts phase handoff | Reproduced and repaired here; review pending | Transition-precondition and fresh-init installed CLI regressions |
| 4 — capability runner and unknown-name traceback | Read-confirmed; runtime/provisioning work | CLI still wires `_UnavailableRunner`; `CapabilityService.reconcile` indexes an unchecked name |
| 5 — process identity and startup preflight | Environment failure reproduced; runtime repair pending | `ps` is denied; `process_identity` propagates spawn errors; batch startup precedes ownership publication |
| 6 — tracked internal evidence | Original current-tree claim is stale | No pre-existing project-management files are tracked at the base. History/publication exposure was not audited; this report is intentionally tracked |
| 7 — install/config/platform guidance | Still incomplete; release documentation work | README remains development-focused; do not claim a public installation journey before its implementation |
| 8 — CI/platform mismatch | Workflow mismatch remains; remote-run claim unverified | CI is still Ubuntu-only; a remote now exists. Current hosted results were not queried |
| 9 — changelog readiness | Defer release curation | Development history is not a release note or evidence of missing implementation by itself |
| 10 — doctor on a fresh init | Read-confirmed; initialization/diagnostics slice | Init creates the runtime directory; doctor checks an absent sessions directory |
| 11 — inconsistent state-path resolution | Read-confirmed; configuration slice | State CLI uses `state_path(root)` while workflow/runtime use configured paths |
| 12 — failure classification gaps | Reproduced; adapter repair pending | Four Claude diagnostics classify as `agent`; OAuth expiry and ECONNRESET classify as `unknown` for Codex |
| 13 — compatibility and upgrade documentation | Documentation pending; no importer requested | Project migration stance explicitly requires fresh state before stability |
| 14 — fresh-init supervised journey | Still unproven | Existing fake-launcher handoff tests seed active PRD state; add a complete public-command journey with the activation slice |
| 15 — output/error polish | Defer to owning CLI work | No blanket rewrite or speculative API change in this repair |
| 16 — placeholder modules and metadata | Intentional held features; release metadata pending | Provisioning and command-driver modules belong to held PRDs; do not delete their reserved boundaries opportunistically |
| 17 — residual runtime findings | Unverified; retain for runtime review | No new proof of signal-window or retry behavior in this slice |

Classification probe results, using synthetic diagnostic text:

| Diagnostic | Claude | Codex |
| --- | --- | --- |
| OAuth token has expired | agent | unknown |
| HTTP 429 Too Many Requests | agent | rate_limit |
| Error: read ECONNRESET | agent | unknown |
| Rate limit exceeded | agent | rate_limit |

## Held work and prerequisites

`backlog/` and `wip/` contain no PRDs. `hold/` contains 44 records: five roadmap
PRDs (00010–00014) and 39 triage/repair records. Their presence is not proof of
39 live defects. No record was moved or declared complete during this repair.
For example, 00056's bare-status cases are already implemented and their tests
passed during the full-suite attempt. The remaining records require individual
adjudication before promotion or closure.

Provisioning remains held behind prerequisite correctness and reviewed launcher
compatibility. The installed read-only probe returned `codex-cli 0.164.0`;
the adapter still pins `0.160.0`. Held PRD 00052 targets `0.160.1` and therefore
needs its evidence/scope reconciled with the actual installed version before
changing the fail-closed guard.

The coverage manifest records accepted plan SHA-256
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
The local plan now hashes to
`c0cbaddc0dd8b087b2f0d3c0f604e104cddc52aa0feba6a5a2690d4bf4960bd2`.
The cause was not established. Do not refresh the digest blindly or begin a new
implementation-plan PRD before reviewed reconciliation, as required by the
coverage manifest.

## Next actions

1. Complete host verification through warrant because Seatbelt denies `ps`.
2. Review this repair in a fresh session with all mandated isolated lenses.
3. Reconcile the plan digest before starting another implementation-plan PRD.
4. Implement the public activation/completion lifecycle and fresh-init journey.
5. Repair configured state resolution, runtime diagnostics/preflight, and adapter failures in their owning slices.
6. Reconcile held defects and launcher compatibility, then begin PRD 00010.

Unresolved questions: none requiring a user preference; host verification requires
the existing approval mechanism, and the plan-digest difference needs investigation.
