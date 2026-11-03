# PRD 00051 build evidence

Repair sources: PRD 00009 cycle 2 R7 (unsafe Unicode publication) and R2 (control-split credential fragment crossing the detail cap). Historical findings and deferred records remain intact. Build work does not establish full-review closure.

## Task 1

Recovered committed implementation b3175de and prior independent test commits a537309, 3e2a46b, 4719234. Prior raw session 4c23a27209ee43eea65aca95bd80e5d1 and native worker rollouts correlate Tess/Ivan dispatches to OpenAI gpt-6.1-sol; requested logical tier opus/high. Actual model fields use observed worker turn_context metadata, not launcher or coordinator identity.

Narrow recovery verification: `env UV_CACHE_DIR=/private/tmp/ovcaq-uv-cache mise exec -- uv run pytest -q --tb=line tests/events/test_unicode_safety.py` -> exit 0, 957 passed in 0.23s. Prior raw evidence records clean style and split-hygiene gates. Implementation commit net size was 29 lines across two files, satisfying the trivial self-deslop skip. Pat output parsed successfully; its three LOW findings (per-character scan cost, cyclic-container nontermination outside the acyclic JSON contract, repeated test tables) remain for full review, without an implementation retry under the LOW-only rule. Devon proved eight weak points; strengthened tests retained their rejection assertions and valid controls. The fixture correction preserved existing credential redaction.

R7 remains open at native frame/supervisor boundaries until tasks 2 and 4 and the fresh completion review establish closure. R2 remains open pending task 3 and fresh review.

## Task 2 premise

Tess's pre-edit public RawFirstDecoder probe reproduced startup with an ignored invalid scalar: it emitted session.started and changed adapter identity from null to poisoned-thread while retaining exact raw bytes. This confirms rejection must precede adapter mutation.

## Task 2 recovery (2026-10-10)

Retained partial preflight plus bounded native Ivan continuation dispatch 88705a21. Observed worker turn_context: gpt-6-astra/high (OpenAI), after prior opus context_overrun and concrete unresolved focused failures; logical tier opus preserved. The worker changed only parser exception handling to ValueError/RecursionError and identified a fixture blocker. Tess dispatch 052a95f0 (observed gpt-6.1-sol/high) added explicit zero cache-write input to the healthy synthetic completion, preserving every assertion; 250 focused cases passed. Tests committed 8d53aad; production e2f26b6. Existing native usage policy unchanged.

Four-check fixture quality review: behavioral names, genuine durable/semantic assertions, error/boundary cases, no implementation tautologies. Mechanical tautology and fixture style gates clean. Task full style gate reports RawFirstDecoder._complete 52 lines; one bounded style dispatch 8b7d88dc pending. Pat prompt 807562cd prepared but never dispatched because correction must precede review. Self-deslop skipped:trivial (implementation net 9 lines, 2 files). Prior Devon ran once, no passing exploit, but eight attempts violated its three-failure stop rule; historical deviation retained, never presented as eight proven weaknesses.

Task 2 gate closure: b46d9e9 moved raw-gap construction outside the tolerant catch into a dedicated helper; style recheck clean; split hygiene clean. Pat (Sonnet/high, tool-free) returned two MEDIUM scope claims and two LOW observations. Both MEDIUM claims are false: the canonical state task explicitly allows events/tail.py and CHANGELOG.md, and the coordinator-authorized separate test file avoided the original file exceeding 800 lines. Pre-edit R7 proof is retained above (startup mutates identity) and red-check-2.txt. Pat received Tess-specific description rather than the canonical production task; retain raw review and this input-selection defect for full review. No claim that the acceptance suite was already run: final phase verification remains mandatory. LOW nested-catch/double-parse and test branching findings retained. Native primary recovery model gpt-6-astra; contributing partial implementation/style/test models remain separate observed evidence for the audit.

Pat corrected-input continuation ceec6c1b received canonical production task plus documented premise and split permission; parsed output has LOW only. The first raw output remains preserved. Acceptance-file coverage must be confirmed in final full-suite evidence, not inferred from narrow 250-case run.

## Task 3

Pre-edit exact R2 cap probe returned 4096 characters ending in sk-abcdefghijkl; redaction false. Tess 9e3966b3 wrote helper/error/turn-failed/rate/lane normalized JSONL cases; one quality retry d095ed43 replaced shared-production classification oracle with independent fixed expectations (authentication, permission, connectivity, timeout, unknown before control removal). Each authored run: 14 failed, 22 passed, with two pytest cleanup warnings. Mechanical shape and style gates clean; manual four-check gate preserves behavior names, real payload/byte assertions, cap/control/reset edges and independent oracles. Test commit 40e4aee. Receiver fixture/API clarifications came from existing public tests, no implementation files supplied to Tess. Devon f5dea3de dispatched once; outcome pending.

Devon task3 f5dea3de proved eight passing exploits (each 36 passed, exit0): literal credential whitelist, lost suffix, x-only cap, dropped newline, dropped tab, Bearer bypass, OSC bypass, and dropped short text. All original production bytes restored; SHA256 f308ed6b63d0e706b866d32b9f05d6df0cc02f5051de117949c9a0c807418646. Full wrong functions and exact output retained in docs/dev/tmp/devon-3-output.md. Tess strengthening80f1d04e must answer all eight; no second Devon dispatch.

Tess80f1d04e answered all eight weaknesses as strengthened; no in-contract dismissals or missing numbered points. Strengthened tests committed6d8e2b9; coordinator red-check18failed66passed, proving restored existing behavior still fails. Shape/style gates clean. Source R2 remains under repair until implementation and fresh review; no token in these tests is a real credential.

Task3 implementatione9f21f7 from Ivan447f65fc (observed native gpt-6.1-sol/high, OpenAI) passes84focused cases. Controls removed on full original string, sanitize_text runs next,4096cap last. Classification/reset paths unchanged. Reflow, style and split gates clean; self-deslop skipped:trivial (net2lines,2files). Ivan reported initial cat/no-timeout read deviations before prompt prohibition visible; later anchored search and narrow test used60/300second subprocess budgets; retained, not treated as compliance proof. Pat62e2d96d pending.

Pat task3 parsed LOW-only output. Retained concerns about expected-string assertions and receiver-cap exact-value oracle for full review. Dropping y-boundary rows is contradicted by Devon candidate3 proving x-only cap bypass; preserve these independent regression cases. No correctness/security defect reported.

## Task 4

Ivan7c69386f native OpenAI gpt-6.1-sol/high authored test-only real-subprocess coverage, committed dd0b86c. Initial restricted run failed before meaningful execution because production ps was denied; approved exact-command retry retained. First approved run:1passed1failed due overstrict cleanup spy; source-method inspection established post-exit group-anchor cleanup is inert to the exited child. Final independent liveness-aware assertions:2passed, existing cleanup warnings retained. No real inference/network. Tests retain exact raw bytes, reloadable gap/healthy/terminal evidence, healthy usage and zero-return normal-exit sentinel. Separate injected normalized gap writer EIO propagates identical exception, cleans actual live PID, suppresses normal sentinel and retains raw/failure summary. Existing genuine failure tests untouched. Style gate flagged111/59line functions; bounded single style dispatch a2610e60 pending. self_deslop skipped:test-only; Pat skipped:test-only outside rework.

Task4 bounded style fix0be8e4c preserves27assertions and exact wire bytes;2passed, style/split/reflow clean. Initial test commit omitted the pre-commit reflow invocation (untracked file has no reflow hunks); record this procedural deviation. No claims of full-review closure.

## Task 5

Ivan a12a9adf native OpenAI gpt-6.1-sol/high aligned protocol against scalar checks, raw preflight, fatal publication/process-control path and control→redaction→bound ordering. Corrected coordinator nonexistent native_events anchor to drivers/codex_events.py:57. Existing Fixed entries retained plus distinct runtime continuity/publication cleanup entry, no version bump. Static source/document consistency and scoped diff check passed; focused runtime acceptance already2passed in task4. Reflow clean; self_deslop skipped:trivial (net20lines); style clean/no Python; split skipped:no-tests; Pat skipped:docs-only. Fresh full completion review remains pending for both source R7/R2.

## Final verification (first run)

Settled code HEAD9e39537. uv sync --all-groups exit0; ruff check . exit1 (PT014 incorrectly flags distinct surrogate literal test rows at unicode_frames.py:160); ruff format --check . exit1 (CAP_REPRODUCER fixture wrapping only); mypy src/ovcaq exit0 (61source files); uv build exit0 (sdist+wheel). Full pytest still running; no counts inferred. Both gate failures require bounded test-only repairs retaining case values/assertions, then rerun only failed commands. Full-suite counts on pre-fix HEAD cannot be recorded against later code HEAD.

Initial full pytest:1failed6883passed,2existing cleanupwarnings,225.84s. Packaging scanner correctly rejected contiguous synthetic TOKEN source in shipped tests/drivers/test_codex_detail_safety.py. Source-only representation repair must preserve identical runtime string, redaction assertions, scanner/build policy and sdist test inclusion. No actual credential exposed.

Final-gate repair task2 dispatch1b8a60e2 observed OpenAI gpt-6.1-sol/high:7f29bdc replaces only literal surrogate expressions with chr(0xD800)/chr(0xDFFF), retaining250cases/IDs/assertions. Own-file lint/format and250tests pass; reflow/style/split clean. Separate attempt2 preserves prior primary Astra implementation evidence. Test-only skips retained; no production change.

Final-gate repair task3 f468da15 observed OpenAI gpt-6.1-sol/high:0961e40 uses explicit concatenation for synthetic TOKEN, preserving exact runtime value/canonical remaining test AST, and formats cap fixture.84helper/native tests plus named packaging check pass85cases; scanner/build policy/sdist tests unchanged. Own-file lint/format/reflow/style/split clean. Earlier97106e99 was prepared-only, replaced when full-suite failure arrived; never dispatched. Source-only test repair no productionchange. Full failed pytest gate rerun at0961e40 pending; full lint and format reruns exit0. Mypy/build remain prior successful commands, with source unchanged by repairs.

## Build exit

Final failed-gate reruns at 0961e40d93bd39af92814eb9e2d32e76a9d01954: pytest exit0, 6884passed/0failed/0skipped, two existing pytest garbage-directory cleanup warnings,227.83seconds; ruff check . exit0; ruff format --check . exit0,232files. Initial successful sync/mypy(61source files)/build retained; repairs changed only test expressions/formatting. No queued review-check file exists. last-verification.json records actual bounded wrapper commands and final pytest counts. The mandatory record-store metadata commit will move HEAD; fresh review must obey the verification record SHA check, never rewrite it to an untested SHA.

Explicit source schema/counts validated,5/5completed, no pause; autopilot dirty empty. No extra worktrees/branches exist. Removed only the batch-owned empty adversarial placeholder /private/tmp/ovcaq-devon-3-validator.py; retained raw evidence, task reports, historical reviews, deferred records and architecture plan. All dispatched native agents and external Pat processes awaited.

Task gates:
1: style_gate: clean, split_hygiene: clean
2: style_gate: fixed:b46d9e9 (initial), clean (final repair), split_hygiene: clean
3: style_gate: clean, split_hygiene: clean
4: style_gate: fixed:0be8e4c, split_hygiene: clean
5: style_gate: clean, split_hygiene: skipped:no-tests

Assumption ledger remains docs/dev/project-management/meta/assumptions.md: initial Tess generic-exception/list-equality assumptions corrected to ValueError/serialized payload comparisons; valid-control total_tokens redaction assumption corrected to existing credential policy. Subsequent workers report none.

Source PRD00009 cycle2 R7 now has scalar/native preflight/real-child continuity and fatal writer propagation build evidence; R2 has reconstructed-credential/cap/control preservation and redaction-order build evidence. Neither source finding is closed by this build: fresh full Alice/Blake/Bob review must retain source refs and closure evidence. Pat LOW findings and documented workflow deviations remain for that review.

Model provenance: native raw implementation rollouts copied byte-for-byte into autopilot/implementation-logs; original autocodex-sessions evidence retained. Primary task2 attempt1 gpt-6-astra plus contributing sol test/style/partial work and attempt2 sol are preserved, not rewritten. Task3/4/5 and independent test workers observed gpt-6.1-sol. Before review, correlate all contributing attempts/session IDs/work range, populate audit from actual observed metadata with exact line hashes, then driver review-route. Exclude read-only Pat/Devon/coordinator model claims; inspect any retained contributing partial code rather than infer provider from launcher. No completion review invoked in build session. Carl is operator-skipped; no Eve claim or provider guard assertion made here.
