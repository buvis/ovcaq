# PRD00053 interactive recovery authorization

On 2026-10-10 the operator replied `approve` to the proposed one-time exception:
finish queued tasks 11–14, then run a fresh full provider review in a separate
session, keeping rework cap 2 unchanged and preserving existing receipts.

This authorizes clearing `tail_sweep_provenance_contract` and resuming the queued
tail sweep. It overrides installed phase-review Tail sweep step 4 only for this
PRD: do not finalize against pre-sweep review receipts. Complete the existing
tasks and required work checks, then hand off and STOP. The next fresh session
must regenerate implementation-model evidence and dispatch all Alice, Blake and
Bob lenses through the host's actual-provider routing. Preserve the original
cycle-2 review and raw receipts; use unique post-sweep output paths and retain
both review rounds in the audit. Do not overwrite or relabel old receipts.

Keep cycle and rework_cap at 2. This is a one-time post-sweep verification,
not authorization for another repair loop or an increased cap. If that review
requires further implementation, pause for an operator decision. Converge only
with valid fresh receipts bound to the final unchanged implementation snapshot.

Recovery handoff: resume at review / Tail sweep step 3 with pending tasks
11–14. Read this authorization before interpreting the installed no-review rule.
Pass this file through autocodex `--scope` so every fresh session receives it.
