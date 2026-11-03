# PRD 00009 replan task 1 per-task review

Provider: external Claude, model sonnet alias, effort high via explicit CLAUDE_CODE_EFFORT_LEVEL. Installed 0.8.0 wrapper supports tool-less -t and session -S/-R but lacks --effort; the installed Claude 2.1.289 binary explicitly recognizes this effort override. Existing wrapper guards and permissions were preserved. Command used -t empty and no -a/-y. Session: 3ec4c260-080b-4f6c-9fe2-b10999b06a9e. Prompt: docs/dev/tmp/replan09-review1-prompt.txt. Reviewed HEAD: 67bc872d8a1f1e9c350473dda4b961cb9930688f. Verification: 49 passed, exit0.

## Raw Pat findings

MEDIUM | src/ovcaq/drivers/codex.py:144 | `self._session_id = thread_id` runs before the `Observation(...)` call, and that call sits outside any guard. The contract says validate before updating decoder state, and that no malformed record raises. If `Observation` rejects the identity (an oversized or control-character `thread_id` is not among the 49 tests) or the payload, `decode` raises to the supervisor with the bad thread already stored. The plan `items` list also has no count bound; only each step's text is capped at 4096. | Build the `Observation` into a local first. Wrap construction in `try/except ValueError` and fall back to the `raw.unknown` observation, built with the previous session ID. Commit `self._session_id` only after construction succeeds. Add tests for an over-long or control-character `thread_id` and a very large `todo_list`.

LOW | src/ovcaq/drivers/codex.py:131 | `decode` computes the SHA-256 and the sanitized preview for every line, then discards them on the success path. The nested `if` chain is also hard to follow. | Move the fallback payload into a small `_raw_unknown(raw_line)` helper and call it only on the fallback path. Optionally flatten the dispatch with early returns.

LOW | src/ovcaq/drivers/codex_activity.py:1 | The task's Location lists `codex.py` and `codex_events.py`, but the diff adds `codex_activity.py`, which is outside the implementor-writable set. `codex_events.py` is not touched. | Put the projection in `codex_events.py` as scoped, or get the new module's location approved in the PRD.

LOW | src/ovcaq/drivers/codex_activity.py:12 | The `message` or `text` detail key is picked by `item_kind == "error"`, and then the kind is checked again in the next condition. The `message_id` sanitize-and-truncate expression is duplicated in the text and plan branches. | Resolve the kind once, for example with a small `{native: (kind, key)}` table. Compute `message_id` once above both branches.

## Coordinator adjudication

MEDIUM identity-rejection claim discarded after direct probes: the shared Observation identifier validator accepts nonempty strings, including a 20,000-character ID and control-character ID. Decoder checks the same state-field predicate before assignment. Neither cited input raises. No rejected identity is committed in the cited paths. This is not a demonstrated malformed-input failure; fresh PRD review may reassess the validate-before-commit ordering against the full decoder.

The 10,000-step plan also decodes successfully. Its per-step text is bounded, but no count cap is present. The task/design does not specify a plan-count maximum; the current slice does not retain a plan ledger, and raw framing bounds supervisor inputs. This concern remains visible for fresh PRD review rather than inventing a new threshold in this task.

LOW helper-location objection discarded: the source style-gate repair explicitly widens the allowlist to the violating file parent for sibling modules. codex_activity.py was created by that authorized style-fix dispatch, not by the initial task implementor. Its placement remains visible in the review range.

Other LOW simplifications (eager raw hashing/preview, nested branches, duplicated item metadata/kind dispatch) are retained for PRD review. No confirmed task-owned correctness defect remained, so the per-task fix/re-review arm did not fire. This is not PRD completion approval.
