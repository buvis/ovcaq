CLOSURE | resolved | "src/ovcaq/tui/panels.py:91: The window size `20` is repeated as a literal six times in `activity_panel`. Replace it with one module constant (e.g. `ACTIVITY_WINDOW = 20`)." | The diff adds `ACTIVITY_WINDOW = 20` and replaces all six literals: `[-ACTIVITY_WINDOW:]`, `[:ACTIVITY_WINDOW]`, both `> ACTIVITY_WINDOW` checks and both `- ACTIVITY_WINDOW` subtractions. Behavior is unchanged: the window is still 20, the omission lines and their placement are the same, and no config was added. The recorded run shows 27 passed.

NO FINDINGS
