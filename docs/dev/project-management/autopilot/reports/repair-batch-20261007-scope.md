# Authorized repair batch — 2026-10-07

The operator asked to execute the proposed follow-up: checkpoint the completed
batch, fix the Unicode HIGH, resolve the version mismatch, triage other necessary
fixes, run verification and fresh full reviews, then reassess held PRD 00010.
The checkpoint is commit 99c0076. This scope persists across fresh autocodex sessions.

## Execution scope

- Use the installed run-autopilot workflow under the autocodex host contract.
- Drain only the four approved backlog PRDs 00051, 00052, 00053 and 00054 in order.
  Their sequence is repair work for completed phases, before provisioning.
- Preserve strict reviewed CLI version policy. Do not accept arbitrary patch
  releases, change global binaries, relax launcher permission settings or run
  real provider inference as a substitute for fixture/fake tests.
- Skip optional Carl for every cycle of this repair batch, as authorized by the
  operator's acceptance of the proposed plan. Do not export review context to
  Gemini/Copilot. Keep Alice, Blake and Bob, their full rubrics, isolated contexts,
  actual implementation-company routing and immutable receipts in every cycle.
- Keep the work/review/finalize fresh-session boundaries. Read the installed
  skills; do not approximate the work or review pipeline.
- No automatic cap increase. Follow the installed cap policy, but a cap-deferred
  finding is unresolved: never report that the intended repair succeeded merely
  because a PRD moved to done or the backlog drained.
- Keep all other held PRDs held. 00010 is for reassessment, not implementation,
  publication or launcher-global provisioning during this batch.
- Preserve historical review/deferred evidence. Record each repaired source ref
  and closure evidence in the new PRD review/report; do not erase old findings.

## Final reassessment

After the four PRDs, update a durable report named
`docs/dev/project-management/autopilot/reports/repair-readiness-20261007.md`.
Report the current review outcome for every in-scope source finding, unresolved
findings and any remaining quality-gate failures. Reassess PRD 00010 against
current code and its actual preconditions. If still held, identify concrete
remaining work and approval boundaries rather than claiming the product is done.

00010 currently requires external companion releases, concrete publication/apply
plans and explicit destination-specific approval. Its provisioning modules are
currently empty and tests/provision does not exist. Do not infer completion from
PRDs 00002–00009 having moved to done. Later external work must first produce its
reviewable implementation and exact plans, as required by that PRD.

Retain the architecture plan; it still governs unimplemented phases. Clean only
batch-owned stale temporary assets/worktrees through the documented lifecycle.

## Unresolved questions

None for this repair scope. Provisioning/apply/publication decisions belong to
the later concrete 00010 work, outside this batch.
