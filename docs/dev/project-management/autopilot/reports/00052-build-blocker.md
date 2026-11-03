# PRD 00052 build blocker — 2026-10-10

Outcome: premise failed before planning or implementation. The PRD requires
installed exact 0.160.1 compatibility to be rechecked at execution. The read-only
`mise exec -- codex --version` command returned `codex-cli 0.162.1`, exit 0.
Raw stdout/stderr and argv are preserved in
[version evidence](00052-premise-version-20261010.json).

The current adapter still pins `_PINNED_VERSION = "0.160.0"` at
`src/ovcaq/drivers/codex.py:38`. No guard, fake launcher, historical fixture,
global binary, permission setting or provider inference was changed. No task
worker was dispatched and no build or completion review ran for this PRD.

Source 00009 review-2 R8 remains unresolved: the installed version remains
outside the exact reviewed guard. R17's direct capture-cap regression also
remains unimplemented because this PRD stops fail-closed at Phase 0. Prior
00051 quality-gate results do not verify 00052.

The installed work premise gate and recovery stall procedure park 00052 in
hold and hand off to the next approved PRD, 00053. Resume requires an operator
decision on the drift: either provide the specified installed 0.160.1 without
this batch mutating global binaries, or authorize a revised source-backed
characterization PRD for the actual installed version. Never infer patch
compatibility or relax the exact guard. PRD 00010 remains held.

Routing: `autopilot enter` classified fast-track; the installed
`_AUTOPILOT_LANES=off` switch routed full to preserve this repair batch's
mandatory fresh work/review boundaries. The premise failure preceded both.
