# Cycle 13 — authorized connectivity recovery

2026-09-13. The operator explicitly approved: "ok, resume".

Resume PRD 00004-workflow-core-v1.md at a fresh full review of cycle 13.
Keep batch 202609062243, rework cap 2, all 13 completed tasks, and original
work_start_sha b43bf2c94d5eb0fddafca55542ef2570b45e8d52 unchanged.
Reviewed HEAD remains be5e385bd9714952b4803ee30f7c72e661c278f2.

The failure was reproduced as DNS failure inside Codex's network sandbox.
An approved request outside that sandbox reached the API, and a bounded
probe using the driver's existing Claude argv/environment successfully
ran Claude Opus. The installed ~/.config/autocodex/host.md now tells the
coordinator to request network approval for external Claude dispatches.
Preserve all launcher guards and await each approved dispatch to completion.

Read dev/local/reviews/00004-cycle-13-connectivity-recovery.md for evidence.
The probe created no review receipt and cannot satisfy any review lens.
The earlier incomplete cycle-13 reports remain unchanged and incomplete.
Both Medium ancestry findings remain open: search-only ancestor permissions,
and the redundant root self-step. No PRD repair was performed here.

This is recovery authorization only: no cap increase, waived review lens,
convergence, finalization, or direct repair authorization. Run every mandatory
lens fresh under the resolved host contract and installed review procedure:
isolated native Alice and Blake, external Claude Opus Bob with complete
personas/rubrics including D1–D5 and de-slop; optional lanes follow that procedure.
Retain raw verdicts and a real current-cycle Bob receipt. Apply the existing
cap policy after complete review. Do not infer completion from the probe,
the old reports, or the task count.

The recovery uses the installed statectl mutation API as the sole writer
for one guarded transaction. The phase-done table has no paused-resume
outcome; calling tasks_done, rework, or converged would misrepresent this
recovery. Phase and next_phase become review together, pause_reason is
removed, live lens statuses become pending, and operator authorization is
appended to the existing decision history. All other state is preserved.

STOP this recovery session. The operator runs autocodex to start the fresh
review session; do not dispatch reviewers from this recovery session.
