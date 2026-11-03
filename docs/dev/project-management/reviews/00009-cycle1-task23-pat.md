# Task23 per-task review

Historical nonconforming personal-wrapper review: requested sonnet/high, observed claude-sonnet-5-5, session 9db5aab5-8416-4a5f-ab4d-c6ac463d7b28. The wrapper ignored tools/resume flags. Zero tools were observed; the delta ran fresh. Superseded below. Raw outputs retained.

## Initial output (verbatim)

CLOSURE | resolved | 🟡 codex.py:212 Native failure `detail` is never bounded | `detail = bounded_detail(detail)` runs after `classify_failure` and `failure_reset`. The helper sanitizes and then applies `[:4096]`, and the same value feeds the `activity.message`, `session.failed` and `rate_limit.started` payloads. A regression test covers this.
CLOSURE | resolved | 🟡 codex_events.py:99 `decode` raises on NaN/Infinity in MCP `result` or web `results` | `_item_observations` is wrapped in `except (ValueError, RecursionError)`, which sets a specific `payload["reason"]`. The tests cover NaN, Infinity, -Infinity and 1200-deep nesting for both tool kinds.
CLOSURE | resolved | ⚪ codex_events.py:262 `failure_reset` trailing punctuation, and `classify_failure` misses "usage limits", "quota limits", "rate limiting" | `absolute[1].rstrip(".,)")` handles the punctuation. The patterns now read `rate[- ]limit(?:s|ed|ing)?`, `quota (?:limits?|exceeded)` and `usage limits?`. Parametrized tests cover each case.
CLOSURE | resolved | 🟠 codex_events.py:245 Checked-in `connectivity-failed.jsonl` does not classify as connectivity | The connectivity pattern now includes `connection failed`. A new fixture test asserts `failure_class == "connectivity"` literally instead of calling `classify_failure` to build the expected value.
CLOSURE | resolved | 🟠 codex_events.py:230 Classifier not based on real Codex 0.160.0 error text | The patterns now cover `stream disconnected`, `quota exceeded`, `model is at capacity`, `sandbox error`, `internal error` and `agent loop died`. A test asserts the independent expected class for each message.
CLOSURE | unresolved | 🟡 codex.py:205 Simplification: chained ternary for `detail` | The diff does not touch the `detail` derivation. The hunks show only the added `bounded_detail` line, and the chained ternary is not in them.
CLOSURE | resolved | ⚪ codex_events.py:44 `turn_usage` keeps a single `gap` string and later branches overwrite it | Both later branches now do `"; ".join(reason for reason in (gap, "...") if reason)`. A test checks the malformed reason survives alongside the partition reason.
CLOSURE | resolved | ⚪ codex_events.py:154 `interrupted`/`shutdown`/`not_found` map to raw.unknown with no lane end event | `item_lanes` now maps these statuses to `errored` when the receiver is in `started_lanes`, taken from `self._identities`. A test asserts exactly one `lane.failed` for each status.
CLOSURE | resolved | ⚪ codex.py:254 `gap = gap or "Conflicting thread identity"` drops the conflict reason | The line is now `"; ".join(reason for reason in (gap, "Conflicting thread identity") if reason)`. A test covers a thread conflict plus a usage gap.

LOW | src/ovcaq/drivers/codex.py:205 | The chained-ternary `detail` simplification from the findings block is still not applied. | Use `source = record if event == "error" else record.get("error")` and `detail = source.get("message") if isinstance(source, dict) else None`.
LOW | src/ovcaq/drivers/codex_events.py:53 | The `"; ".join(r for r in (gap, "...") if r)` pattern is repeated three times in `codex_events.py` and once in `codex.py`. | Add a small `join_reasons(*reasons)` helper and call it from the four places.
LOW | src/ovcaq/drivers/codex_events.py:17 | `bounded_detail` strips control characters with its own regex after `sanitize_text`, which may already strip them. | If `sanitize_text` already removes these characters, drop the extra regex. Otherwise leave it as is.

## Delta output (verbatim)

NO FINDINGS

The delta resolves the CLOSURE finding at `src/ovcaq/drivers/codex.py:205`. The chained ternary is replaced by `source = record if event == "error" else record.get("error")`, followed by `detail = source.get("message") if isinstance(source, dict) else None`. Behavior is unchanged in both branches:
- **`event == "error"`:** `source` is `record`, so `detail` is `record.get("message")` as before.
- **Other events:** `source` is `record.get("error")`, so `detail` is `error["message"]` when `error` is a dict, otherwise `None`.

I found no new issues in this delta.



## Superseding conforming full review

Bundled use-sonnet wrapper, tools disabled, guards intact, CLAUDE_CODE_EFFORT_LEVEL=high. Provider Anthropic; requested sonnet; observed claude-sonnet-5-5; session 841d372a-ed14-4f24-93ea-9a68b9725205; raw source /Users/bob/.claude/projects/-Users-bob-git-src-github-com-buvis-ovcaq/841d372a-ed14-4f24-93ea-9a68b9725205.jsonl. Parser exit 0; all closure rows resolved; LOW findings carried to the next complete review.

CLOSURE | resolved | Native failure `detail` is never bounded (codex.py:212) | `detail = bounded_detail(detail)` runs after `classify_failure` and `failure_reset`. It sanitizes and then applies `[:4096]`, and the capped value feeds all three payloads (`activity.message`, `session.failed`, `rate_limit.started`).
CLOSURE | resolved | `CodexDriver.decode` raises on `NaN` or `Infinity` in an MCP `result` or web `results` (codex_events.py:99) | The `item.*` branch now wraps `_item_observations` in `except (ValueError, RecursionError)` and sets `payload["reason"]`, so the record falls through to `raw.unknown` with a specific reason. The new test covers NaN, Infinity, -Infinity and deep nesting for both tool kinds.
CLOSURE | resolved | `failure_reset` captures `\S+`, so a trailing `.`, `,` or `)` drops a valid deadline, and `classify_failure` misses "usage limits", "quota limits" and "rate limiting" (codex_events.py:262) | `fromisoformat(absolute[1].rstrip(".,)"))` handles the punctuation. The patterns are now `rate[- ]limit(?:s|ed|ing)?`, `quota (?:limits?|exceeded)` and `usage limits?`.
CLOSURE | resolved | Checked-in `connectivity-failed.jsonl` fixture does not classify as connectivity (codex_events.py:245) | `connection failed` is added to the connectivity pattern. The new test does not call `classify_failure` for its expectation: it hard-codes `"connectivity"` and also checks that no `rate_limit.started` is emitted.
CLOSURE | resolved | Failure classifier is not based on real Codex 0.160.0 error text (codex_events.py:230) | The new patterns are `stream disconnected`, `quota exceeded`, `model is at capacity`, `sandbox error`, `internal error` and `agent loop died`. The parametrized test asserts the class and the exact detail for both `error` and `turn.failed`.
CLOSURE | resolved | Simplification: chained ternary for `detail` (codex.py:205) | Replaced by `source = record if event == "error" else record.get("error")` and `detail = source.get("message") if isinstance(source, dict) else None`, exactly as suggested.
CLOSURE | resolved | `turn_usage` keeps a single `gap` string and later branches overwrite it (codex_events.py:44) | Both later branches now join with the earlier gap (`"; ".join(...)`). The test checks that the malformed reason and the partition reason both appear.
CLOSURE | resolved | Codex lane statuses `interrupted`, `shutdown` and `not_found` map to `raw.unknown` with no lane end event (codex_events.py:154) | `item_lanes` takes `started_lanes`. For a lane that was already started, those three statuses become `errored`, which yields `lane.failed`. The test checks one `lane.failed`, no `lane.completed`, and a bounded detail. A lane that was never started still gets `raw.unknown`, which is reasonable because there is nothing to close.
CLOSURE | resolved | `gap = gap or "Conflicting thread identity"` drops the conflict reason when the usage also has a gap (codex.py:254) | The two reasons are now joined, so both are kept. The test checks that both the thread-conflict reason and the cache or partition reason appear.

LOW | src/ovcaq/drivers/codex_events.py:53 | The `"; ".join(reason for reason in (gap, X) if reason)` idiom is written three times (`turn_usage` twice, and `codex.py:253`). | Add one `join_gaps(*reasons: str | None) -> str | None` helper and call it from all three places.
LOW | src/ovcaq/drivers/codex.py:188 | `except (ValueError, RecursionError)` wraps all of `_item_observations`, not only the JSON detail helpers. Any unrelated `ValueError` from item handling is now reported as "Malformed or invalid JSON in Codex item". | Narrow the catch to the `mcp_detail` and `web_detail` calls, or word the reason more generally.
