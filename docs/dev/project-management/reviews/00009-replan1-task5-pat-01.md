# PRD00009 replan1 task5 evidence

Base55666d7; tests da46d1d; implementation fe4e71b; style f16c711. Native sonnet Sol medium, bounded same-tier retry fixed direct-summary bypass to required synthetic shared reduction. Root47passed exit0; style worker47passed exit0. Fresh self-deslop noop. One style fix exhausted: decode53lines remains FUNCTION violation (limit50), style_gate failed retained. Split hygiene clean. Pat external Claude Sonnet/high tools empty session05d0e2ae-b7e4-4c25-bdd6-77956abf66a9, dispatch067cf512 exit0 parseraccepted LOWonly. No completion-review approval; all LOWs and style failure retained for fresh all-lens gate.

## Pat raw

LOW | src/ovcaq/drivers/codex.py:395 | `summarize` reads `FailureClass(str(payload["failure_class"]))` and `payload["detail"]` from supplied observations. A supplied `activity.message` of kind `error` with an unknown class value or no `detail` would raise `ValueError` or `KeyError`. Only the decoder produces this shape today, and I can't see whether `Observation` validates it. | Use `payload.get("detail")` and skip the fallback, or treat the class as `unknown`, when the metadata doesn't parse.

LOW | src/ovcaq/drivers/codex.py:379-423 | `summarize` runs about 45 lines. It mixes the terminal check, the reverse scan and construction of two synthetic observations at 4 to 5 levels of nesting. | Extract `_provisional_fallback(observation) -> list[Observation]`. `summarize` then becomes: reduce, return the summary if a terminal exists, otherwise find the latest provisional error and re-reduce.

LOW | src/ovcaq/drivers/codex.py:200-207 | `detail` comes from a nested conditional expression (`record.get("message") if event == "error" else error.get("message") if isinstance(error, dict) else None`) that is hard to read. | Use an `if event == "error": ... else: ...` block.

LOW | src/ovcaq/drivers/codex.py:206-243 | The `if event == "error"` branch and the terminal branch share the classify/reset computation. The method returns `None` to signal "fall through to raw", and the caller then rebuilds `(self._observation(kind, payload, timestamp),)`. | Split into `_provisional_error(detail, ts)` and `_native_failure(detail, ts)`, and dispatch on the event in `decode`. This removes the interleaved branching.

LOW | CHANGELOG.md:11 | The new bullet is followed by a blank line, while the other bullets in the same list have none. | Remove the blank line.


## Adjudication

No LOW repairs per policy. Supplied malformed provisional metadata tolerance is a review concern; exact normalized metadata input is tested. No stale private fields. No external Codex rung or reviewer thread claimed.
