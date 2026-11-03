NO FINDINGS

The delta resolves the CLOSURE finding at `src/ovcaq/drivers/codex.py:205`. The chained ternary is replaced by `source = record if event == "error" else record.get("error")`, followed by `detail = source.get("message") if isinstance(source, dict) else None`. Behavior is unchanged in both branches:
- **`event == "error"`:** `source` is `record`, so `detail` is `record.get("message")` as before.
- **Other events:** `source` is `record.get("error")`, so `detail` is `error["message"]` when `error` is a dict, otherwise `None`.

I found no new issues in this delta.
