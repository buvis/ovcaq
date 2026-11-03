# Cycle 13 native review corrections and probe evidence

These are superseded raw responses, preserved separately from the final reviewer
sections. Alice was asked to substantiate coverage and correct inconsistent
binary verdicts; Blake was asked to substantiate the alleged fixed ceiling.
Neither received sibling findings.

## Alice initial response

[ALICE] 🟡 Runtime directory creation walks from `/` and read-opens/fsyncs every ancestor, so a valid configured runtime beneath a search-only ancestor fails with “not a real directory”; a targeted `0111` ancestor probe reproduced the failure | File: src/ovcaq/workflow/_files.py:252 | Task: P02-T06/P02-T09

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: pass
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

Alice subsequently stated that her first coverage mapping was identification-only,
not a completed reconciliation. A further read-only pass completed the 55-row
reconciliation and added the root self-step finding; its complete final output
and corrected raw rubric are in `00004-cycle-13-alice-output.txt`.

## Alice probe (reported exact command and output; not rerun)

```bash
PYTHONPATH=src python3 - <<'PY'
import os, tempfile
from pathlib import Path
from ovcaq.workflow._files import _ensure_directory_chain
base=Path(tempfile.mkdtemp(dir='/private/tmp'))
restricted=base/'search-only'; restricted.mkdir(mode=0o700); (restricted/'existing').mkdir(); os.chmod(restricted,0o111)
try:
    try: _ensure_directory_chain(restricted/'existing'/'runtime')
    except Exception as e: print(type(e).__name__, repr(str(e)))
    else: print('SUCCESS')
finally: os.chmod(restricted,0o700)
PY
```

```text
OSError 'runtime directory is not a real directory: /private/tmp/tmp2uu0d1ev/search-only'
```

Source-tree probe via `PYTHONPATH=src`, not installed-wheel execution. The module
origin was not printed independently. The probe directory was subsequently
removed by Alice with scoped `rmdir` calls and an existence check returned `removed`.

## Blake initial response (withdrawn)

[BLAKE] 🟠 `check-plan` exposes an unspecified `--ceiling` override, letting callers bypass the fixed 15-task plan-size policy with a large value and accepting nonsensical negative ceilings instead of rejecting invalid input | File: src/ovcaq/workflow_cli.py | Task: P02-T04
B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
B6: fail
B7: fail
B8: pass
B9: pass
B10: fail
B11: pass
B12: pass
B13: pass
B14: pass
B15: fail
B16: pass
B17: fail
B18: pass
B19: pass

Blake withdrew the finding based on source inventory TEST-012 and returned all
nineteen B verdicts as pass. See `00004-cycle-13-blake-output.txt`; the discard
reason is also durable in the settled-decisions ledger.

## Process completion

- Alice: final response received; probe directory removed.
- Blake: final corrected response received.
- Bob: process session 38802 returned exit 1; immutable failure JSONL retained.
- Carl: runner returned exit 3; no model inference or published output.
- Watcher: command session 39333 completed; final WAITING, no active process.
