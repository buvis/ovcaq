# PRD 00009 replan1 task4 evidence

Base5abc3140465092feb57f0caa1c74faa4c27c052f; test6496bd0; corrected oracle8d4cf77; implementation55666d7.
Logical opus; native OpenAI gpt-6.1-sol/high (Ivan36bcaca6),87passed exit0. Root narrow also87passed exit0, two pytest temp-cleanup warnings. Style/split hygiene clean; isolated self-deslop noop.
Pat external Claude Sonnet/high, tools empty, session9b24488c-0e5d-4b90-8b2e-af28a8a42ec1; dispatch816d9a19 exit0, parse_review accepted LOW only. All raw findings below remain fresh PRD review evidence. No external Codex rung or fake provider thread.
This is task evidence, not completion-review approval.

## Pat findings (verbatim)

LOW | src/ovcaq/drivers/codex_events.py:~39 | The absent-telemetry check `all(value == 0 for value in counts)` includes the optional `reasoning_output_tokens`. A native record of input/cached/write/output all `0` with reasoning omitted yields `None` for reasoning, so the check is false. That record is reported as exact zero with no gap, where the contract says to keep token fields unknown. The 87 tests don't cover this shape, and pinned 0.160.0 likely always sends reasoning, so this is edge-case exposure. | Test only the known counters: `known = [v for v in counts if v is not None]; if known and all(v == 0 for v in known)`. Add one test with reasoning omitted.

LOW | src/ovcaq/drivers/codex.py:~150-173 | The `thread.started` branch assigns `kind = SESSION_STARTED` but never uses it, because the branch now returns early. It also builds a throwaway observation just to `replace(..., session_id=...)`, and it does `usage = Usage() if conflict else self._usage; self._usage = usage` (a no-op in the non-conflict case). | Drop the dead `kind` assignment. Write `if conflict: self._usage = Usage()` in place of the `usage` temporary. Consider letting `_observation` take an optional `session_id` so both `replace` calls go away.

LOW | src/ovcaq/drivers/codex_events.py:~28-36 | The `gap` variable is overwritten by later branches (invalid counter, then partition gap, then read-above-inclusive). Which message survives depends on branch order, and the `name in native or name in names[:3]` condition is hard to read. | Collect reasons in a list and join them, or at least name `names[:3]` as `required`. Behavior stays the same.

LOW | src/ovcaq/drivers/codex.py:~195-200 | `values[name] = values[name] or value` for `estimated` is a special case inside the max-merge loop. It sets a sticky estimated flag, which is acceptable, but the sticky behavior is undocumented and only the reset test touches it. | Add a one-line comment saying the flag is sticky by design until `build_launch`. Optionally add a test where a positive-write snapshot is followed by a write-0 snapshot.


## Adjudication and assumptions

LOWs are carried without repair under the source per-task policy. The omitted-reasoning/all-zero shape is a real tolerance edge claim outside the pinned complete native shape; fresh PRD review must judge its absence semantics. No universal absence proof is claimed. The claimed dead kind assignment is actually used in the started observation call; replacement/temporary simplification remains a LOW suggestion. Sticky estimated status is a recorded assumption: remains true after an estimated contributing snapshot until launch/current-thread boundary; changed thread resets the current snapshot while prior identity survives in observations.

## Devon bounded result and limitation (verbatim summary)

Tests are robust.

Scope and result: Task 4 supplied tests/public interfaces only; no copied production bodies, live implementation, history, acceptance, or architecture read. This phrase is the prompt-required outcome after three failed attempts. It means no passing exploit was proved; it is not a claim that every possible implementation shortcut is ruled out.

Actual runner counts: 3 invocations; 3 failed attempts; 0 passing exploits. All processes exited; none timed out or remain running. Mandatory failed-attempt limit reached, so no fourth attempt was run. abort_reason: failed_attempt_limit, not context_overrun.

Attempt 1: exit 1, 84 passed / 3 failed / 87 collected, 2 warnings, 0.27s. Wrong launch returns an empty argv and bogus raw format, ignoring the configured launcher/environment/prompt; shared public LaunchSpec validation rejects empty argv. The conflicting-thread summary also fails the test's nonempty failure_detail assertion.
Attempt 2: exit 1, 86 passed / 1 failed / 87 collected, 2 warnings, 0.04s. Wrong launch uses /usr/bin/false with empty environment instead. Added failure event has excessive keys; public Observation validation rejects it. No complete-suite pass.
Attempt 3: exit 1, 86 passed / 1 failed / 87 collected, 2 warnings, 0.08s. Wrong launch remains /usr/bin/false. Tried candidate failure payloads through normal Observation construction and caught normal validation exceptions. Although usage assertions pass, conflicting-thread reduction still has failure_detail=None and fails. No complete-suite pass. Parent supplied the exact public failure payload shape after this invocation; the failure_class/detail pair was already among these candidates. No dependency bodies were inspected to investigate further.

Weak points:
None proved. No passing wrong implementation or passing output exists. Proposed launch assertion gap remains unproved under the full-suite requirement.

Shortcuts caught:
1. test_build_launch_resets_identity_maxima_and_estimation_for_session_reuse - empty launch argv is rejected by shared public constructor validation.
2. test_conflicting_threads_remain_visible_and_reducer_fails_unknown - raw gap and conflicting identity without a nonempty reducer failure detail do not satisfy this test.
3. test_conflicting_threads_remain_visible_and_reducer_fails_unknown - an incorrectly shaped failure event is rejected; candidate valid shapes still failed the reducer-detail assertion.

Raw evidence (runner-retained wrong implementations and complete output):
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-1/codex.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-1/codex_events.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-1/pytest-output.txt
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-2/codex.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-2/codex_events.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-2/pytest-output.txt
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-3/codex.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-3/codex_events.py
/Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/devon4-sandbox/attempt-3/pytest-output.txt

Full attempted body (attempt 1; there is no passing body):
```python
import hashlib
import json
import re
from datetime import UTC, datetime

from ovcaq.drivers.base import LaunchSpec
from ovcaq.events.model import Observation


class CodexDriver:
    def __init__(self, settings, *, run_id):
        self.settings = settings
        self.run_id = run_id
        self.reset()

    def reset(self):
        self.session_id = None
        self.maxima = dict.fromkeys(("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        self.estimated = False
        self.completed = 0

    def b

Three failed actual runner attempts, zero proved passing exploit; stopped at mandated limit, no fourth run. The impossible truthy shared-reducer failure_detail oracle blocked the final attempt. Root and Ivan confirmed shared reducer deliberately clears detail for conflicting IDs; Tess corrected only that oracle to exact failure_class unknown in a source quality retry. This means Devon did not establish resistance to other shortcuts after correction. Preserve this limitation for all-lens review; do not call it a proved pass. Raw attempted code/output retained under docs/dev/tmp/devon4-sandbox/attempt-{1..3}; wrong targets restored to placeholders. The source-required procedure ran and no second Devon was launched.
