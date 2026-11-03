CLOSURE | resolved | `src/ovcaq/drivers/codex_activity.py:6`: "`codex_activity.py` is a third module (43 lines) outside the design's module placement (codex.py + codex_events.py)... Fold `item_activity` into codex_events.py" | The diff deletes `codex_activity.py`, adds `item_activity` to `codex_events.py` with the body unchanged, and points the `codex.py` import at `codex_events`. It also drops `ovcaq.drivers.codex_activity` from `DECLARED_MODULES` in `packaging_support.py`. The packaging run reports 8 passed.

NO FINDINGS
