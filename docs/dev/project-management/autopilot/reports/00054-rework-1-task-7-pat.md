CLOSURE | resolved | "The checks `elif started.payload.get("detail")` and `if terminal.payload.get("detail")` are always true for decoded Codex tools... Make these assertions unconditional." | The diff changes `elif started.payload.get("detail"):` to `else:`. It also removes the `if terminal.payload.get("detail"):` guard and dedents its assertions, so they now run unconditionally.

CLOSURE | resolved | "Some tests still pair provider `claude` with shapes the Claude decoder never emits: `kind: error` with `text` and `message_id`, and `kind: plan` with `items`." | The synthetic `_event("claude", ...)` calls are gone. The message test now decodes real fixture frames. The Claude cases are limited to `text` and `thinking`, and `error` is Codex-only. The plan test is Codex-only and decodes a real Codex frame.

LOW | tests/tui/test_rework_activity.py:~189 and ~253 | The message and plan tests each repeat the read-fixture, `json.loads(lines[n])`, mutate, decode and `replace(..., session_id="session-1", lane_id=None)` sequence. | Pull it into one small helper, for example `_decode_frame(provider, fixture, line, mutate)`. The helper could sit beside the existing `_decoded_tools`.

LOW | tests/tui/test_rework_activity.py:~253 | The plan test unpacks `(event,) = (... for event in decoder.decode(...))` with no `ACTIVITY_MESSAGE` filter, though the message test has one. If the fixture line ever decodes to extra events, the unpack fails with a confusing error. | Add `if event.type == ObservationType.ACTIVITY_MESSAGE` for consistency.

The recorded run reported 21 passed with 2 existing cleanup warnings. I did not check that the Codex plan fixture at line 21 of `tool-active.jsonl` has a decoder-emitted `items` shape, since that file is outside this prompt.
