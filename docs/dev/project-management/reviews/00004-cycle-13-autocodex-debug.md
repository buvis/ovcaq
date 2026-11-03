# Autocodex cycle 13 failure diagnosis

## Failure Capture
- Session / task: `c7620370024841cfb09a0c827bb0d4ce`, PRD `00004-workflow-core-v1.md`, review cycle 13.
- Goal in progress: complete the mandatory Alice, Blake and independent Claude Bob review before any review/rework transition.
- Error: Claude Bob returned exit 1 and API 429 before inference; five-hour quota rejected, reset epoch `1788803400` (2026-09-07 19:50 Europe/Prague). No output or receipt was published.
- Last successful step: Alice and Blake completed their isolated reviews; coordinator retained two open Medium ancestry findings and one settled Medium finding.
- Last failed tool / command: `driver.py --cd /Users/bob/git/src/github.com/buvis/ovcaq reviewer -f .../bob-prompt-00004-cycle-13.md -o .../00004-cycle-13-bob-output.txt`.
- Repeated pattern seen: one Bob dispatch, no retry storm; coordinator heartbeats continued while the remaining review/evidence work completed, then a deliberate pause.
- Context pressure: no context-overflow event established; the coordinator finished with `turn.completed`. Its aggregate usage was 5,810,995 input tokens, 5,643,520 cached input tokens and 25,990 output tokens; these are cumulative session usage, not context occupancy.
- Environment assumptions to verify: exact repository and installed host paths, committed phase/cycle/cap, current time versus structured reset, and which process owns quota recovery.

## Recovery Action
- Diagnosis chosen: external provider quota exhaustion plus a missing reviewer quota-recovery path. The pause preserves the required independent provider review correctly.
- Smallest action taken: read the host contract and installed Resume rules; inspect the immutable provider JSONL, wrapper/helper code and state; run the read-only canonical `resume-target` command (`paused: await user`).
- Why this is safe: no provider retry, production change, state mutation or review certification is needed to establish the cause.
- What evidence would prove the fix worked: a simulated structured 429 waits until the supplied reset, retries with fresh raw evidence, and publishes a receipt only after a complete successful D1-D5 review; unrelated pauses remain untouched. Live recovery still requires successful provider evidence after reset.

## Agent Self-Debug Report
- Session / task: interactive diagnosis of cycle 13.
- Failure: mandatory external Bob unavailable before inference.
- Root cause: `driver.Events.accept` discards `rate_limit_event`; `driver.review` treats every unsuccessful result as generic failure. `CodexLoop._failed` handles only coordinator errors, and `_decide` honors committed pause state first. A successful Codex coordinator reporting a failed Claude reviewer cannot reach the existing Codex quota wait.
- Recovery action: installed structured Claude quota handling in the personal launcher after sandbox approval. The helper waits until the provider's reset plus five seconds, bounded by the existing quota wait and enclosing session deadlines. It stops on an operator pause, preserves each attempt's raw output, and retains the successful full-rubric receipt requirement. Host instructions and operator documentation describe this behavior. Pre-existing launcher edits were preserved.
- Result: partial; launcher fix installed and verified, PRD recovery blocked by a current weekly quota rejection.
- Token / time burn risk: Bob used zero inference tokens; restarting a full review before reset repeats native review work without restoring the independent reviewer. Polling the exhausted provider before reset is unnecessary.
- Follow-up needed: after Claude becomes available, obtain the required interactive resume decision, preserve cycle 13/cap 2/batch/base and all evidence, and hand off review to a fresh session. Do not rerun reviewers before quota availability is established.
- Preventive change encoded: structured Claude quota rejection/reset recognition, bounded interruptible waiting, fresh attempt logs and unchanged receipt gates.

## Verification and current blocker

- Installed autocodex suite: **62 passed**. Ruff and formatting checks passed. Installed file hashes match the tested patch. The new tests first reproduced the missing retry, then passed with the fix, including a real subprocess reset/retry and immutable attempt logs.
- Patch: `00004-cycle-13-autocodex-quota-fix.patch`. This changes personal launcher files under `~/.config/autocodex`; no OVCAQ production code changed.
- The first minimal live availability probe timed out during API retries in the restricted sandbox. Its raw evidence remains in `00004-cycle-13-quota-probe-dcbf5c3a297344d9af803f23a32c1064.jsonl`.
- The approved probe outside the sandbox received **API 429, weekly quota exhausted**, with structured reset epoch **1789290000**, or **2026-09-13 11:00 Europe/Prague**. Raw evidence: `00004-cycle-13-quota-probe-320271445b74460a89c74f223f220515.jsonl`; summary: `00004-cycle-13-quota-probe.json`.
- These were availability probes, not reviews. Neither creates Bob's review output, receipt or rubric verdicts. The weekly reset exceeds the configured wait budget; no further provider retry is justified now.
- Recorded on 2026-09-09: keep phase/next_phase paused, cycle 13, cap 2, batch identity, task statuses, review evidence and original base unchanged. Update only the pause explanation and contract card through the existing state CLI so recovery sees the current weekly blocker.

## Authorized resume — 2026-09-13

The operator answered “yes, proceed” to resuming cycle 13 after a fresh quota
check. The external Claude Opus availability probe returned exit 0 and
`QUOTA_OK`; evidence is retained at
`00004-cycle-13-quota-probe-f207a50780484eb984a954ab2599fd78.summary.json`
and its adjacent raw JSONL/stderr. This establishes availability at probe time,
not a completed Bob review.

Recovery result: success. Clear the reviewer-unavailability pause through the
existing state CLI and queue phase/next_phase review; preserve cycle 13, cap 2,
batch/base, task statuses and historical review evidence. State schema and
13/13 counts were validated. No PRD repairs or review work ran in this session.
The pending full review is handed off in
`dev/local/plans/fast-track-handoffs/00004-workflow-core-v1/review-13-resume.md`.
