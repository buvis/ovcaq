# Autocodex session death — 2026-09-16

Diagnosed 2026-09-17 from local metrics, session evidence, state, and launcher code.

## Failure Capture

- Session / task: PRD `00005-runtime-substrate-v1.md`, build/rework; sessions
  `3bab0f649699430bb4a1ac195a18fd9e` and `b4601574019247f895417ccfcc3e714c`.
- Goal in progress: complete authorized repair tasks 12–21, then hand off for
  fresh-session review.
- Error: `session died (session failed or made no committed progress)`.
- Last successful step: task 19 completed; task 20 regression tests committed as
  `bd8ba62`; implementation dispatched and waiting on its agent.
- Last failed tool / command: task 20's expected red test run reported 31 failed,
  128 passed. The session continued afterward; this did not terminate it.
- Repeated pattern seen: both sessions ended at the two-hour wall cap while
  waiting for an agent; neither emitted a terminal turn event.
- Environment assumptions to verify: installed launcher cap, exit status,
  failure retry budget, durable task progress, and surviving worktree edits.
  All verified below. Last reported contexts were approximately 96K and 160K
  tokens against a reported 258,400-token window; no quota/context error ended
  either captured event stream.

## Evidence and Root Cause

`dev/local/autopilot/autocodex-metrics.jsonl`, lines 47–48:

| Session | Local start | Recorded wall seconds | Return code | Capped | Decision |
| --- | --- | ---: | ---: | --- | --- |
| `3bab0f…` | 06:49:48 | 7215.104 | -15 | true | continue |
| `b46015…` | 08:50:04 | 7200.059 | -15 | true | died |

The first metric includes the 15-second retry delay. The second run stopped at
approximately 10:50:04 local time.

- Installed autopilot `0.5.2/skills/run-autopilot/cli/routing.py:231` uses
  `_AUTOPILOT_SESSION_MAX`, default 7200 seconds, for build sessions.
- `~/.config/autocodex/driver.py:189` calls `stop_group` at that deadline.
  `stop_group` sends SIGTERM, then SIGKILL to remaining group members. Return
  code -15 records the main process's SIGTERM exit.
- `driver.py:146` makes capped results unsuccessful even when work progressed.
- `~/.config/autocodex/adapter.py:325` routes unsuccessful results to `_failed`.
  Line 348 permits one retry by default. Both capped sessions consume this
  budget; task progress does not reset it on that path.
- `adapter.py:363` falls back to the generic error because no provider error
  event exists. It does not include the recorded cap reason in that message.

The first session completed tasks 12–14; the second completed tasks 15–19.
State remains build/build with 19/21 tasks complete, task 20 in progress, and
task 21 pending. Uncommitted edits remain in `CHANGELOG.md`,
`src/ovcaq/runtime/session.py`, and `src/ovcaq/runtime_cli.py`.

## Recovery Action

- Diagnosis chosen: launcher-enforced wall timeout followed by retry exhaustion.
- Smallest action taken: correlated metrics with the exact termination and
  decision branches; inspected durable progress and worktree status.
- Why this is safe: read-only diagnosis; only this report was added. No workflow
  state, implementation, processes, or launcher configuration changed.
- What evidence would prove the fix worked: a subsequent run completes or hands
  off before its deadline and records a successful normalized session result.

## Agent Self-Debug Report

- Session / task: the two PRD 00005 build sessions above.
- Failure: forced termination at the per-session deadline, then no retries left.
- Root cause: fixed wall cap applies regardless of productive activity; timeout
  is classified as generic session failure and obscured in terminal output.
- Recovery action: diagnosis only; no restart requested or performed.
- Result: partial — cause confirmed, workflow still incomplete.
- Token / time burn risk: roughly four hours of productive work were interrupted;
  unfinished task 20 implementation must be reconciled on resume.
- Follow-up needed: resume from existing state and inspect partial task 20 edits.
  A bounded temporary override is `_AUTOPILOT_SESSION_MAX=14400 autocodex`.
- Preventive change to encode later: report wall timeout explicitly and arrange
  a graceful build handoff before the hard cap. Keep retries bounded and retain
  all required work/review gates.
