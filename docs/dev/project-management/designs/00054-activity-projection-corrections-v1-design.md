# Faithful recent activity design

## Architecture fit

Repair normalized observation projection and Rich presentation in the existing TUI boundary. No provider decoding, lifecycle, persisted schema or public API changes. PRDs 00051–00053 are complete; preserve their safety and terminal behavior.

## Module placement

Edit `src/ovcaq/tui/model.py` and `tests/tui/test_rework_activity.py`; add `tests/tui/test_activity_projection.py`. Edit `src/ovcaq/tui/panels.py`; add `tests/tui/test_activity_window.py`. Update `tests/fixtures/README.md`, `docs/driver-protocol.md` and `CHANGELOG.md`.

## Interfaces & contracts

### Projection

Keep `ProjectObserver._observe_activity(self, event: Observation) -> None`, `ActivityItem` and `ProjectView.activity` unchanged. For `ObservationType.ACTIVITY_MESSAGE`, use `payload['text']` when not None (including empty text), otherwise `payload.get('detail')`; plans continue to summarize `items`. A nonblank string `message_id` updates its existing item using the exact original ID as an internal key. IDs must not be sanitized or truncated for identity; displayed values still pass through `display_text`. Absent, blank or non-string IDs identify distinct consumed records using an observer-local monotonic counter and a separate key namespace. Reset that counter in `_clear()` with activity. `JsonlFollower` delivers each appended record once; do not add content deduplication or random IDs. Repeated polls without new records retain exactly the same items. Preserve re-insertion ordering, eviction at `MAX_ACTIVITY`, session changes and follower reset semantics. Tools use `detail` only; remove the invented `input` fallback. Keep existing plan, literal text and credential sanitization.

### Presentation

Keep `activity_panel(view: ProjectView) -> Panel` and its shared live/plain callers. Render `reversed(view.activity[-20:])` first; then `view.lanes[:20]` in existing order. If activity length exceeds 20 append a literal count line `<n> activity entries omitted`; if lanes length exceeds 20 append `<n> lanes omitted`. Keep `no lanes observed` when lanes are empty and preserve the empty activity behavior. Never mutate or truncate either retained tuple. Pass all dynamic values through existing `display_text` and literal `_panel` Text rendering. No new configuration.

### Documentation

Describe `lanes-matched.jsonl` as checked-in matched-lane evidence. Remove obsolete in-place variant and lanes-only claims. Describe actual normalized tools/messages/plans, text/detail precedence and the newest-first 20 activity plus at most 20 lanes window. Do not claim live provider smoke evidence. Add the user-visible correction to the existing Unreleased changelog section.

## Data flow

Native drivers produce normalized observations; the existing follower cursor feeds only new records into the observer. Real IDs update, ID-less records append, and bounded retained items become immutable ProjectView tuples. Both live and plain renderers consume the same panel with a smaller presentation window. Raw evidence remains unchanged.

## Reuse inventory

Searches `render|project|observe` and `identity|message|activity|cursor` found `src/ovcaq/tui/model.py:ProjectObserver._apply`, `_observe_activity`, `_clear`, `display_text`; reuse cursor/reset and sanitization. `src/ovcaq/events/tail.py:JsonlFollower` already handles record offsets, replacement and truncation; no new replay tracker. `src/ovcaq/tui/panels.py:_panel` already uses literal Rich Text; retain it. `tests/tui/model_support.py:Projection` and `tests/tui/test_model.py:projection` supply observer fixtures. Existing driver decode tests and checked-in native fixtures supply real normalized payloads.

## Alternatives considered

1. Smallest diff: add detail fallback and a consumed-record counter in the observer, slice tuples only in the panel. Chosen: fixes identity without a new event protocol or persisted data.
2. Hash payload/timestamp for anonymous IDs: rejected because identical separately observed errors must remain distinct.
3. Add native IDs or cursor fields to normalized records: rejected as unnecessary provider/event schema work outside scope.

## Risks & edge cases

Empty text wins over detail; blank IDs do not update. Anonymous keys must not collide with real IDs. Long IDs sharing sanitized prefixes remain distinct. File/session resets clear counters and history together, avoiding replay duplicates. MAX_ACTIVITY bounds retained memory; the counter stores only one integer. Future configurable windows can replace constants without changing models; future pagination can read retained tuples; future decoder shapes remain provider edge work. No durable state changes require migration or rollback; ordinary git revert restores presentation behavior.

## Test strategy outline

Independent decoder-to-observer regressions for both adapters, provisional errors/warnings followed by turn markers, repeated identical ID-less records, actual tools/plans, real-ID updates, repeated polls with a real follower, eviction and reset. Rich Console captures verify 20/20 counts/order, omission lines, exact boundaries, literal/safe text, empty states and unchanged retained views. Recheck premises before edits; correct behavior receives coverage and an explicit skip. Run the full documented quality suite once after all tasks.

## Review log

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 1, question 1
Host mapping: fresh native OpenAI gpt-6.1-sol/high; engagement retry completed with anchored checks. Source token `claude` is a compatibility label only. Non-blocker: Architecture fit incorrectly says 00051–00053 complete; 00052 remains held and is not a prerequisite. Question: exact original ID means the normalized payload ID; upstream sanitization cannot be undone. Verified cursor/reset, anonymous namespace, text/detail precedence, ordering/window, sanitization, resource bounds and checked-in fixture truth.

dispatch 2 (codex): cardinal-sin 0, blocker 0, non-blocker 5, question 3
Host mapping: external Anthropic Sonnet/high through real use-sonnet wrapper; source `codex` token is a compatibility label only. Raw findings: `docs/dev/tmp/00054-design-review-2-output.txt`. Non-blockers: explicitly identify the existing bounded key dictionary; pin omitted counts to length minus 20; constrained live height may clip lower rows; clarify existing reinsertion ordering; prerequisite wording. Questions: session identity reset; malformed text/detail and missing key behavior; explicit skip means no production rewrite plus regression coverage. These are recorded without changing design per the source non-blocker/question rule. Existing `_activity` dict is the sole index and evicts keys/items together, and `_clear` clears it on session/reset; preserve those existing behaviors. No open cardinal sins or blockers. Dispatch 2 has section-anchored evidence and more than three findings; no engagement retry or dispatch 3 required.
