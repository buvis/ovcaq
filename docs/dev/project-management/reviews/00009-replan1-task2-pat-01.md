# PRD 00009 replan 1 task 2 evidence

Task base: 67bc872d8a1f1e9c350473dda4b961cb9930688f. Initial implementation: 3a3b578. Validation-order repair: 8130995.
Logical worker tier opus; initial native OpenAI gpt-6.1-sol/high. Confirmed MEDIUM contract-order defect triggered the host-authorized bounded OpenAI gpt-6-astra/high repair. No external Codex rung or stale thread ID.
Pat: external Claude Sonnet/high, tools empty, session e50b5bbc-fe85-4d54-8ca7-e91ece1c9a98. Initial dispatch08ccb85a and resumed deltafdba3a0d both exited0; parse_review accepted both.
Final root narrow verification at8130995: 181 passed, exit0; two pytest temp-cleanup warnings. Style and split hygiene clean; isolated self-deslop noop.
This is task evidence, not completion review approval. Fresh PRD review remains mandatory.

## Initial Pat findings (verbatim)

MEDIUM | src/ovcaq/drivers/codex.py:179-180 | `_remember_tool` evicts the oldest identity and records the new one before `self._observation(...)` builds and validates the `Observation`. The contract says "validate before updating decoder state". If construction rejects the payload (for example an overlong `tool_id` or an empty `detail`), the eviction has already happened and the visible gap `raw.unknown` is never emitted. The tests only use short valid ids, so they don't catch it. | Build `observation` first, then call `_remember_tool`. If the gap is needed, build the gap observation before committing. Mutate `self._tools` only after every observation for the record is constructed.

LOW | src/ovcaq/drivers/codex.py:191-200 | `_remember_tool` writes `self._tools[tool_id] = terminal`. A late `item.updated` or `item.started` for an id already marked terminal flips it back to live, so it is evicted later than it should be. | `self._tools[tool_id] = terminal or self._tools.get(tool_id, False)`.

LOW | src/ovcaq/drivers/codex.py:178 | `assert isinstance(tool_id, str)` exists only to satisfy typing and is stripped under `-O`. `item_tool` already has `item_id` as a `str`. | Return `(kind, tool_id, name, detail)` from `item_tool`, or a small typed result, and drop the assert and the `payload["tool_id"]` round-trip.

LOW | src/ovcaq/drivers/codex.py:193 | The literal `4096` is the identity cap. The same number is the detail bound in `codex_events.py`. | Name the cap (`_MAX_TOOL_IDENTITIES`) and use `>=`.

LOW | src/ovcaq/drivers/codex_events.py:~16-92 | The `[:4096]` detail bound is repeated four times. `json.dumps(sanitize_json(detail), ensure_ascii=False)[:4096]` is duplicated in `mcp_detail` and `web_detail`. | Add `_MAX_DETAIL = 4096` and a small `_bounded_json(detail)` helper used by both.

LOW | src/ovcaq/drivers/codex_events.py:~108-125 | `item_tool` rebuilds the `projections` dict on every call. The `failed` expression is nested with mixed `or`/`and` and a conditional tuple in the status check, which is hard to read. | Hoist `projections` to a module constant. Compute `allowed` and `failed` as named locals, with a per-kind helper if needed.

LOW | src/ovcaq/drivers/codex.py:~125 (`_item_observations`) | Only tool item ids are tracked in `_tools`. The task says to limit remembered "item/lane identities" to 4096, and activity items (messages, reasoning, plan) are not counted. This is consistent with this slice, but the cap is not item-wide. | Confirm in the PRD-level review that tool-only tracking is intended, or fold activity ids in when lanes land.


## Adjudication

The explicit validate-before-state order was violated, irrespective of the reviewer's rejection examples (the current Observation model accepts long IDs and empty detail). Repair constructs all observations before identity insertion/deletion. The same reviewer closed it on the committed delta below. All LOW findings are retained for fresh PRD review, including terminal regression, cap scope, typing and simplification claims. No LOW repair in this bounded pass.

## Resumed Pat verdict (verbatim)

NO FINDINGS

The MEDIUM finding at `codex.py:179-180` is resolved. The delta builds `observation` first, then builds the gap `raw.unknown` observation, and only then runs `del self._tools[evicted]` and `self._tools[tool_id] = ...`. If either construction raises, `self._tools` is untouched.


## Devon proved weak points (verbatim)


1. test_4097th_identity_emits_visible_raw_gap_and_launch_resets_capacity - build_launch can return None and ignore the entire LaunchRequest while clearing capacity - assert a LaunchSpec and verify argv, cwd, environment, and raw format. Evidence: docs/dev/tmp/devon2-sandbox/attempt-1/codex.py and pytest-output.txt (96 passed; exit_code=0).
2. test_native_status_projects_each_supported_item_event / assert_tool - every supported tool can be named the constant 'tool' - assert exact meaningful names for each native kind and MCP server/tool pair. Evidence: docs/dev/tmp/devon2-sandbox/attempt-2/codex.py and pytest-output.txt (96 passed; exit_code=0).
3. test_mcp_large_result_and_sensitive_metadata_are_bounded_and_sanitized / test_web_large_results_and_sensitive_url_are_bounded_and_sanitized / test_command_stdout_never_becomes_provider_health - empty details satisfy all boundedness and secrecy checks while discarding useful command, result, and action data - assert a safe recognizable sentinel survives in each detail, together with a concrete maximum length. Evidence: docs/dev/tmp/devon2-sandbox/attempt-3/codex.py and pytest-output.txt (96 passed; exit_code=0).
4. test_invalid_and_future_records_never_raise_and_keep_raw_evidence / test_raw_preview_sanitizes_synthetic_credentials / assert_unknown - every preview may be the empty string, eliminating readable raw evidence - require a nonempty sanitized preview for nonempty raw input and check recognizable nonsensitive content survives. Evidence: docs/dev/tmp/devon2-sandbox/attempt-4/codex.py and pytest-output.txt (96 passed; exit_code=0).
5. test_raw_preview_sanitizes_synthetic_credentials - sanitizer can redact only the exact SECRET fixture literal and expose every other credential - parameterize multiple unpredictable credential values and sensitive keys, checking each value is absent while safe context survives. Evidence: docs/dev/tmp/devon2-sandbox/attempt-5/codex.py and pytest-output.txt (96 passed; exit_code=0).
6. test_started_updated_completed_preserve_one_native_tool_identity - a remembered ID can silently change from command_execution to file_change/MCP/web because identity preservation is tested only within one kind - reuse the same ID with a different kind and assert raw-only conflict evidence without overwriting remembered identity. Evidence: docs/dev/tmp/devon2-sandbox/attempt-6/codex.py and pytest-output.txt (96 passed; exit_code=0).
7. test_nonzero_command_exit_is_tool_failure_even_with_completed_status - a nonzero exit code can be ignored whenever native status is in_progress, yielding tool.started for known failure - cross-product nonzero exit codes with native statuses and all supported item event types, asserting failure dominance. Evidence: docs/dev/tmp/devon2-sandbox/attempt-7/codex.py and pytest-output.txt (96 passed; exit_code=0).
8. test_web_lifecycle_uses_item_events_without_native_status / test_wrong_native_shapes_and_unknown_statuses_return_only_raw / test_missing_required_native_tool_field_stays_raw - action={} or unknown action types and incomplete open/find/search objects can normalize as valid tools because only non-object actions are rejected by assertions - add missing/wrong nested action.type, url, pattern, query/queries cases and require raw-only observations. Evidence: docs/dev/tmp/devon2-sandbox/attempt-8/codex.py and pytest-output.txt (96 passed; exit_code=0).



## Tess dispositions and correction evidence

Test target: /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py
Exit code: 1

Only correction in this retry: launch.raw_format now equals the pinned public codex-exec-json-v1. The prior jsonl oracle was erroneous and contradicted the completed launch contract. No other test changes.

1. strengthened: test_4097th_identity_emits_visible_raw_gap_and_launch_resets_capacity asserts LaunchSpec, argv tuple/fixture prefix/opaque prompt, cwd, configured environment and pinned codex-exec-json-v1 raw format. Full exact argv remains owned by the completed launch slice.
2. in-contract: assert_tool requires a nonempty neutral name. Exact neutral name strings and extra payload keys are explicitly unspecified, so constant neutral tool remains allowed.
3. strengthened: test_command_stdout_never_becomes_provider_health, test_mcp_large_result_and_sensitive_metadata_are_bounded_and_sanitized and test_web_large_results_and_sensitive_url_are_bounded_and_sanitized require recognizable safe detail context and relative large-input bounds. No unspecified numeric ceiling was invented.
4. strengthened: assert_unknown requires readable previews for tested printable nonempty records; test_raw_preview_sanitizes_variable_synthetic_credentials_and_keeps_safe_context requires recognizable safe context to survive.
5. strengthened: test_raw_preview_sanitizes_variable_synthetic_credentials_and_keeps_safe_context parametrizes token/password and uses fresh synthetic UUID credentials, rejecting fixture-literal-only redaction.
6. in-contract: cross-kind ID conflict and overwrite policy is unspecified; raw-only conflict and retaining the earlier kind would invent forbidden identity-conflict behavior.
7. strengthened: test_nonzero_command_exit_dominates_every_native_status_and_item_event covers all three nonzero exits, four native statuses and three item events, requiring tool.failed.
8. strengthened: test_web_action_rejects_malformed_tag_and_present_optional_field_types covers missing/null/nonstring tags and wrong present query/queries/url/pattern types. test_web_lifecycle_uses_item_events_without_native_status accepts pinned optional/null fields and unknown string variants as Other.

Actual narrow runner output:
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF......... [ 39%]
.....................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF...... [ 79%]
..................................FFF                                    [100%]
=================================== FAILURES ===================================
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
      
      - tool.failed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.failed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
      
      - tool.completed
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.completed'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
E   AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
      
      - tool.started
      + raw.unknown
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_decode_tools.py:78: AssertionError: assert <ObservationT...'raw.unknown'> == 'tool.started'
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f10dc795-7bfb-4578-b8ba-1b0cefc26527
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-f10dc795-7bfb-4578-b8ba-1b0cefc26527'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ef9249d6-643f-4bf7-aee9-b0fefdbad6c2
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-ef9249d6-643f-4bf7-aee9-b0fefdbad6c2'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-running-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-running-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-running-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-success-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-success-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-success-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-failed-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-failed-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-failed-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-declined-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-declined-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[command-declined-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-running-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-running-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-running-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-success-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-success-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-success-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-failed-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-failed-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[file-failed-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-running-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-running-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-running-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-success-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-success-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-success-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-failed-item.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-failed-item.updated]
FAILED tests/drivers/test_codex_decode_tools.py::test_native_status_projects_each_supported_item_event[mcp-failed-item.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[other-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[other-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[other-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-omitted-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-omitted-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-omitted-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-null-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-null-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[search-null-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-omitted-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-omitted-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-omitted-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-null-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-null-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[open-null-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-omitted-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-omitted-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-omitted-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-null-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-null-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[find-null-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[future-as-other-item.started-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[future-as-other-item.updated-tool.started]
FAILED tests/drivers/test_codex_decode_tools.py::test_web_lifecycle_uses_item_events_without_native_status[future-as-other-item.completed-tool.completed]
FAILED tests/drivers/test_codex_decode_tools.py::test_started_updated_completed_preserve_one_native_tool_identity[command_execution]
FAILED tests/drivers/test_codex_decode_tools.py::test_started_updated_completed_preserve_one_native_tool_identity[file_change]
FAILED tests/drivers/test_codex_decode_tools.py::test_started_updated_completed_preserve_one_native_tool_identity[mcp_tool_call]
FAILED tests/drivers/test_codex_decode_tools.py::test_started_updated_completed_preserve_one_native_tool_identity[web_search]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-in_progress--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-in_progress-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-in_progress-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-completed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-completed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-completed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-failed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-failed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-failed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-declined--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-declined-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.started-declined-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-in_progress--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-in_progress-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-in_progress-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-completed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-completed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-completed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-failed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-failed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-failed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-declined--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-declined-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.updated-declined-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-in_progress--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-in_progress-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-in_progress-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-completed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-completed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-completed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-failed--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-failed-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-failed-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-declined--1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-declined-1]
FAILED tests/drivers/test_codex_decode_tools.py::test_nonzero_command_exit_dominates_every_native_status_and_item_event[item.completed-declined-127]
FAILED tests/drivers/test_codex_decode_tools.py::test_explicit_mcp_error_is_tool_failure_even_with_completed_status
FAILED tests/drivers/test_codex_decode_tools.py::test_command_stdout_never_becomes_provider_health
FAILED tests/drivers/test_codex_decode_tools.py::test_file_change_detail_summarizes_all_paths_and_kinds
FAILED tests/drivers/test_codex_decode_tools.py::test_mcp_large_result_and_sensitive_metadata_are_bounded_and_sanitized
FAILED tests/drivers/test_codex_decode_tools.py::test_web_large_results_and_sensitive_url_are_bounded_and_sanitized
FAILED tests/drivers/test_codex_decode_tools.py::test_4097th_identity_emits_visible_raw_gap_and_launch_resets_capacity
FAILED tests/drivers/test_codex_decode_tools.py::test_eviction_prefers_oldest_terminal_then_oldest_live_identity
FAILED tests/drivers/test_codex_decode_tools.py::test_malformed_items_do_not_consume_remembered_identity_capacity
111 failed, 70 passed, 2 warnings in 0.25s

ASSUMPTIONS:
No new assumptions in this correction: codex-exec-json-v1 is explicitly pinned by the retry prompt.
Retained coordinator clarifications: native status governs command/file/MCP, web event governs web lifecycle, and eviction gap identifies its victim without prescribing representation.
Retained useful-detail checks require recognizable safe context without exact formatting; no numeric detail ceiling is supplied.
Retained pinned WebSearchAction optional-field/Other handling comes from the coordinator's rust-v0.160.0 protocol/src/models.rs lines 1840-1866 source clarification.


Native WebSearchAction schema clarification verified from [pinned protocol source](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/protocol/src/models.rs): optional nullable typed fields; unknown string tags map to Other. Wrong tags/types remain raw. The launch raw-format oracle was corrected to completed public codex-exec-json-v1 before implementation; no production format migration.
Raw scratch evidence retains all eight wrong implementations and passing outputs in docs/dev/tmp/devon2-sandbox/attempt-{1..8}; each96passed exit0. Wrong implementations restored to placeholders and live source preserved.
