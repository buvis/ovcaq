# PRD 00009 replan 1

Planning only. Source `plan-tasks` 0.8.0 applied after the Task 4 prompt abort; no implementation, worker dispatch, task claim or phase transition occurred in this planning session.

Completed P07-T01 fixtures, P07-T02 launch/edge/model/effort, and P07-T04 health/classifier implementation are preserved and excluded from the new work plan. Durable Task 3 review evidence remains in `00009-task-3-pat-01.md`, `00009-task-3-pat-02-raw.md`, and `00009-task-3-pat-02-corrected.md`; completed does not mean these findings were waived. `work_start_sha` remains `e16ab432e8ce3e64029303b7e7d61bb7777b0894`.

The full PRD, vetted design, accepted source plan, coverage manifest and discovery were read. Accepted plan SHA-256 verified `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`. Functional decomposition and dependency graph are PRD-pinned; no requirement-derived substitute was needed. The decoder's fine-grained sequencing follows the producer/consumer interfaces in that decomposition. No PRD-vs-design contract conflict was found; design API 2, thread-cumulative usage and native invocation refine unspecified PRD details.

## Remaining task coverage

| ID | Remaining coverage | Depends on | Estimate | Tier / reason |
|---|---|---|---:|---|
| 1 | P07-T03a: Decode thread, turn, text and plan records with total raw fallback | — | 60,080 | sonnet / default |
| 2 | P07-T03b: Decode command, file, MCP and web tool lifecycles | 1 | 61,762 | opus / algorithmic_risk |
| 3 | P07-T03c: Project native collab tools and bounded receiver lanes | 2 | 63,703 | opus / algorithmic_risk |
| 4 | P07-T03d: Normalize thread-cumulative usage with honest cache partitions | 3 | 65,630 | opus / algorithmic_risk |
| 5 | P07-T03e: Decode native terminal failures and reduce provisional errors once | 4 | 66,356 | sonnet / default |
| 6 | P07-T05: Provide native skill prompts with one state-only handoff | — | 65,326 | haiku / mechanical |
| 7 | P07-T06a: Add the isolated scripted fake Codex executable | 5, 6 | 57,879 | sonnet / test_port |
| 8 | P07-T06b: Run shared driver, raw-first and real process conformance | 7 | 63,819 | sonnet / test_port |
| 9 | P07-T06c: Prove shared decisions and command-backed build-review-done drain | 8 | 67,080 | sonnet / test_port |
| 10 | P07-T07: Verify Codex identity, activity, usage and raw projection | 9 | 57,874 | sonnet / test_port |
| 11 | P07-T03/P07-T05–T07: Document the live driver contract and evidence | 10 | 67,345 | sonnet / default |

All 11 task descriptions copy their relevant design contract passages, exact source-task acceptance text and all Phase 7 exit criteria; phase-specific PRD exit criteria remain verbatim. The acceptance remains collective while each task's Verify limits its narrow gate. P07-T03 is covered by tasks 1–5; P07-T05 by task 6; P07-T06 by tasks 7–9; P07-T07 by task 10. Task 11 updates the live public protocol, fixture evidence pointers and changelog without reimplementing completed capabilities. Fake drain includes command-backed committed revisions/results/evidence and the existing generic post-drain capability; real launcher provisioning stays PRD 00010.

## Budget and routing

Replan threshold: 75,000 tokens per task. Estimates use the mandated 55,000 overhead plus file bytes, PRD slice and task description bytes, with conservative projected growth for files modified by earlier remaining slices. Range: 57,874–67,345; peak estimate adds the mandated 20,000 response allowance. All file sets are persisted. Every task's tier/reason is actual output from `classify_tier.py`; no frontmatter model floor exists. The source mechanical-row knob was empty. Qwen preflight returned `endpoint_unreachable`; the eligibility split trigger was skipped, context splitting remains active, and qwen eligibility/exclusions were computed for all tasks. Task 6 alone is eligible; task 10 is excluded as `ui`, tasks 2–4 as `tier`, the other multi-file slices as `files`.

Multi-file decoder slices keep orchestration and provider projections together because callers consume the projections and mutable reset state in the same capability; splitting them for eligibility would introduce independently failing intermediate interfaces. Usage/identity eviction also carry algorithmic risk and are exempt from eligibility splitting. Fake executable and its proof are coupled. Shared conformance parameterization and existing Claude assertions/harness injection are coupled; docs/provenance pointers describe the same final contract.

The original Tess payload exceeded 50,000 bytes after one trim (58,707 → 52,393). Remaining decoder descriptions are only 4,875–7,583 bytes. Later dispatches must use complete source templates, focused public signatures, one small sample (the 1,270-byte `test_driver_v2.py` suits initial Tess), and relevant fixture records rather than the full observation implementation or whole decoder/architecture trees. Budget initial Tess context at ≤7,000 bytes public signatures/framework and ≤8,000 bytes sample/context; even the largest remaining decoder spec plus acceptance and the 4,319-byte template stays below 30,000 bytes. For Ivan, AGENTS plus a focused interface/context bundle must stay ≤7,000 bytes, leaving at least 39,000 bytes for the narrow failing-test input under the 3,679-byte complete persona. Test-only/docs-only tasks use Verify/Acceptance checks as FAILING_TESTS per the source, not entire old test suites. Coordinator must measure every actual render ≤50,000 bytes including the source abort guard, trim once at most, and abort if still oversized. New Tess output cannot be pre-certified before it exists; this is an input allocation, not a fabricated measurement. No render telemetry was opened during planning.

## Gate and preserved evidence

All `task-add` writes succeeded through the sole statectl writer, IDs and dependencies captured rather than guessed. `check-plan` exited 0: `unfiled=0`, structural drift skipped because the PRD does not use the gate's exact Repository Structure heading/tree. Eleven tasks remain below the 15-task ceiling and expansion threshold. `phase`/`next_phase` remain build/build; completed implementation and `work_start_sha` were not changed. Consumed `replan-context.md` was removed only after successful persistence and gate.

No planning blocker remains. The completed health scope has unresolved review evidence: unbounded probe-output tempfile and loose version pin are the corrected Pat MEDIUM findings; actionable auth detail, reset punctuation/number/naive-time handling, classifier regression/formatting concerns and changelog clarity remain recorded LOW or earlier raw findings. These are not automatically repaired in the remaining-scope plan. Fresh PRD completion review must consider them after all work and package gates.

Unresolved questions: none requiring planning clarification. The design's eight advisory questions and seven open non-blocker observations remain recorded; shared multi-turn/runtime-terminal semantics follow the current reducer, unsupported child statuses stay raw/unknown, and actual external-skill/writable-path smoke remains PRD 00010.
