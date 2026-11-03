CLOSURE | resolved | [BOB] F3: Assertion cannot fail as written: delegated_calls counts every fsync and directories counts a labeled subset, so the inequality holds by construction | `assert retry["delegated_calls"] >= len(retry["directories"])` is deleted; the retained ordered-position assertion above it is the only fsync-ordering check left.
CLOSURE | resolved | [BOB] F5: FSYNC_SCENARIO emits state_changed_while_interrupted; no assertion reads it | `assert not evidence["state_changed_while_interrupted"]` now reads the key and enforces authoritative-state preservation.

NO FINDINGS
