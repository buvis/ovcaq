CLOSURE | resolved | `test_authentication_is_classified_beyond_the_display_detail_limit` repeats `test_failure_classifies_full_text_before_sanitizing_and_capping_detail`. Delete it. | The diff removes the whole test and its `@pytest.mark.parametrize("event", ["error", "turn.failed"])` decorator.
CLOSURE | resolved | The capacity bound test runs `connectivity_retries` 0, 1, 2 and 3. Drop cases 0 and 1. | The diff removes the `(0, DecisionKind.WAIT)` and `(1, DecisionKind.WAIT)` params. Only `(2, WAIT)` and `(3, HALT)` remain.
CLOSURE | resolved | `test_numeric_diagnostics_require_an_explicit_status_or_error_context` checks only the positive cases. Rename it for the rule it enforces. | The diff renames it to `test_numeric_codes_classify_with_explicit_status_or_error_context`. The body is unchanged.

NO FINDINGS
