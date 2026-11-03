# Review capability pause — PRD 00009, cycle 1

Completion review did not run. No reviewer output, rubric verdict, receipt, or convergence is claimed.

Preflight: phase/next_phase were review, cycle 1, full lane; all 18 tasks completed and stored counts match. Schema/resume preflight succeeded. No existing cycle review artifact or pause was present.

The installed completion-review step 1 Codex-rung guard fires: all 18 tasks have an attempt whose implementor is codex. It requires the separate Eve/Fable lens alongside Bob. Step 5 permits a native Claude substitute after Eve failure. The native host API supports only GPT models and cannot dispatch either native Claude Fable or that native Claude substitute. No impossible dispatch was fabricated. The host-authorized external Claude Opus Bob supplies independent provider review, but does not explicitly replace the separate Eve requirement; the host contract retains required Eve/Fable constraints and forbids fake Eve evidence.

Per the host contract's required-capability failure rule, statectl persisted phase/next_phase paused with pause_reason.site=reviewer_capability. Build state, cycle, cap, tasks, and work_start_sha remain preserved. No repairs or launcher mutations occurred.

Recovery requires the operator to provide the capability or explicitly authorize a concrete substitute for the separate Eve lens. Resume through the existing state CLI, then end recovery and run autocodex in a fresh review session. Keep Alice, Blake, Bob and the authorized additional lens; preserve all rubrics, coverage and Bob receipt requirements.
