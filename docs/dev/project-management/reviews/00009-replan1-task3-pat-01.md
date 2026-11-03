# PRD 00009 replan1 task3 evidence

Base8130995c38c9ddef8975c8ae8db5a5e5c0967b74; implementatione6faabc; review regression8bd97c0; repair5abc314.
Logical opus; native initial OpenAI gpt-6.1-sol/high. Concrete sequential gap-validation defect prompted prospective-copy staging and next bounded OpenAI gpt-6-astra/high verification (0d74f21a),38passed. Confirmed mixedreceiver MEDIUM prompted bounded Astra/high repair850cf315,46passed. Sole durable identity commit follows all observation validation.
Pat external Claude Sonnet/high, no tools, session351f8b0d-23f5-45c4-a1e7-ab187f865965; initial12f6def6/resumedf2b3e4e0 both exit0 and parser accepted. No external Codex rung, stale provider thread or claimed model diversity.
Final root verification at5abc314:46passed exit0, two pytest temp-cleanup warnings. Style/split hygiene clean, isolated self-deslop noop. Sustained fixed-width identity memory plateau tested; relative allowance is harness tolerance, not a product bytecap.
This is task evidence, not completion-review approval; fresh all-lens PRD review required.

## Initial findings (verbatim)

MEDIUM | src/ovcaq/drivers/codex_events.py:121-131 | `item_lanes` returns `None` as soon as one receiver has an unsupported status (`interrupted`, `shutdown`, `not_found`) or a malformed state. The decoder then drops the lanes of every other receiver in the same item. A sibling that is natively `completed` or `errored` never gets its terminal `lane.*`, so that lane stays open. The only test with unsupported states uses a single receiver, so this is not caught. | Skip only the bad receiver. Project the valid ones, and emit one `raw.unknown` for the rest. Add a two-receiver test (`completed` plus `interrupted`).

LOW | src/ovcaq/drivers/codex.py:221-241 | `_remember` checks capacity against the in-progress copy, which includes identities added earlier in the same batch. With the budget full, a new terminal tool and its new lane can evict the tool identity that was just remembered. The gap names an item that was only just seen. | Pick the eviction victim only from identities that existed before the batch, or document the edge. This is rare and the gap stays visible.

LOW | src/ovcaq/drivers/codex_events.py:133 | The lane `label` is the constant `"Receiver"`. The contract says native receiver state supplies the label, and every receiver gets the same label. | Derive the label from the receiver ID, for example `f"Receiver {receiver}"`, or note that native state has no label field.

LOW | src/ovcaq/drivers/codex.py:188-195 | `lane_kind` is reassigned inside the loop to turn `LANE_PROGRESS` into `LANE_STARTED`. The check reads `self._identities`, not the batch state. Duplicate receiver IDs in one item both become `lane.started`. | Move the start-versus-progress decision into `_remember`, or de-duplicate receivers in `item_lanes`.

LOW | src/ovcaq/drivers/codex.py:236-241 | The tuple of terminal observation types is an inline literal and needs the `tool.` prefix and `tool_id` assert alongside it. | Add a module constant `_TERMINAL = frozenset({...})`. Keep tool and lane identity extraction in one small helper.


## Adjudication

Main public probe confirmed completed child beside interrupted sibling yields tool.completed/raw only, losing attributed terminal. Eight focused regressions reproduced completed/errored plus unsupported/malformed siblings in both orders. Repair projects valid siblings independently and preserves raw evidence for bad siblings; same reviewer closed it. Initial all-or-nothing assumption is refuted, not retained as allowed behavior.
All LOW findings retained for fresh PRD review: within-record eviction of newly terminal identity, constant neutral display label, duplicate receiver start, and literal type simplification. Native state has no label field; actual attribution is lane_id. No LOW repairs in this bounded cycle.

## Resumed closure (verbatim)

CLOSURE | resolved | MEDIUM codex_events.py:121-131, `item_lanes` returns `None` on one bad receiver and drops sibling lanes | `item_lanes` now does `has_unknown = True; continue` for each bad receiver and returns `(result, has_unknown)`. `decode` appends one `raw.unknown` and still projects every valid lane. The new `test_bad_receiver_sibling_preserves_attributed_native_terminal` covers completed and errored siblings, unsupported-status and malformed-message states, in both orders.

NO FINDINGS


## Eight Devon proved weak points (verbatim)


1. test_launch_resets_remembered_receiver_identity_and_capacity - build_launch returns argv=("false",), an empty environment, and ignores settings.command/request.prompt while still passing the identity reset assertions - assert the configured argv prefix, prompt delivery, requested cwd/model, environment, and raw format in a dedicated launch-construction test.
2. test_projects_native_collab_tool_lifecycle - every collab tool is named "unrelated-tool" and the test only checks a nonempty string - assert the expected tool name or documented display mapping for all four parametrized tools.
3. test_projects_native_collab_tool_lifecycle - tool detail is always empty, dropping the record's prompt/evidence - supply distinctive prompt text and assert its sanitized content appears in detail.
4. test_attributed_active_receiver_starts_with_current_thread_and_receipt_time - all lane labels are the unrelated constant "Unrelated person" - assert the label identifies the actual receiver through the documented label mapping, including two distinct receivers.
5. test_receiver_evidence_is_sanitized_and_bounded / test_unsupported_child_terminal_states_stay_raw_without_success - raw.unknown previews use raw[:512], leaking credentials on fallback paths; sanitization is only checked for a valid lane record - combine a malformed/unsupported child state with FAKE_CREDENTIAL and a control character, then assert every emitted payload is sanitized and the raw digest remains correct.
6. test_receiver_progress_and_duplicate_states_keep_one_lane_identity / test_multiple_receivers_keep_separate_attribution_and_actual_status - every lane detail is the same hardcoded collection of test substrings, so A includes B's evidence and updates never carry actual messages - use distinct fresh messages and assert each detail contains its own message and excludes other receivers' messages; assert successive details reflect the update.
7. test_shared_identity_budget_emits_visible_gap_at_4097th_identity / test_duplicate_evidence_does_not_consume_extra_identity_capacity - an additional unbounded self.seen set retains every tool/lane key despite correct visible evictions; the overflow tests actually populate it beyond 4096 - enforce the total retained identity count through a public bounded-cache diagnostic or a sustained bounded-memory characterization, rather than inferring the cap only from visible gap text.
8. test_shared_identity_budget_emits_visible_gap_at_4097th_identity / test_identity_eviction_prefers_terminal_over_older_active_identities - eviction raw.unknown observations hash and preview "fabricated unrelated record" instead of the actual triggering record - run assert_raw(overflow, original_raw) on identity-gap observations and assert the preview corresponds to sanitized triggering evidence.



## Tess dispositions (verbatim)

1. strengthened:test_launch_construction_preserves_configured_command_and_request
2. in-contract:exact neutral tool names and display mappings are explicitly
3. strengthened:test_projects_native_collab_tool_lifecycle
4. in-contract:exact label text/prefix/display mapping is unpinned. Receiver
5. strengthened:test_fallback_payloads_redact_credentials_preserving_raw_digest
6. strengthened:test_receiver_progress_and_duplicate_states_keep_one_lane_identity
7. strengthened:test_retained_memory_plateaus_after_identity_budget_saturation
8. strengthened:test_shared_identity_budget_emits_visible_gap_at_4097th_identity

Devon ran nine isolated attempts: eight proved34passed/exit0 and one failed33passed1failed/exit1. Full wrong code/output retained under docs/dev/tmp/devon3-sandbox/attempt-{1..9}; writable targets restored to placeholders. No live production poisoning. Strengthening preserved credential redaction contract without invented blanket C0/ANSI removal and completed raw_format codex-exec-json-v1. Initial configured-model oracle corrected before main red30failed8passed. Final mixedreceiver regression all8failed beside38passing earlier tests before repair.
