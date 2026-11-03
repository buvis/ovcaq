# FT-04R3 skeptical review

Reviewed HEAD: `f2453760591875f1faf241ec9c0291303232efd9`  
Complete range: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`  
Verdict: `changes_requested`

## FIX

- **Critical — Reset paths leave a stale active PRD.** Evidence: `src/ovcaq/workflow/records.py:87-121` resets phase and tasks but preserves `work.prd`; this reset is used by both next-PRD transition (`src/ovcaq/workflow/transitions.py:61-63`) and park/stall commit (`src/ovcaq/workflow/records.py:581`). `resume_target` then treats the state as active build work (`src/ovcaq/workflow/resume.py:30-42`), while `workflow select` merely reports a filename without committing it (`src/ovcaq/cli.py:595-598`). Impact: a crash after successful park/stall or `more_prds` can deterministically resume the completed or held PRD, violating state-decides and risking duplicate work. Action: make reset produce an unambiguous no-active-PRD/selection-needed state or atomically activate the selected successor; add restart tests immediately after saga commit and `more_prds`.

- **High — Completion and drain are not fail-closed compound transitions.** Evidence: `more_prds` can erase review/task state without checking that the current PRD was recorded (`src/ovcaq/workflow/transitions.py:61-63`), after which `complete_prd` necessarily rejects because convergence state was cleared (`src/ovcaq/workflow/records.py:146-153`). Drain changes only `work.phase/next_phase` (`src/ovcaq/workflow/transitions.py:65-69`), while final-state archival accepts that as terminal without requiring batch completion (`src/ovcaq/workflow/reports.py:414-426`). `resume_target` also collapses handoff-pending and drained states to the same `"done"` result (`src/ovcaq/workflow/resume.py:44-45`). Impact: command misordering can irreversibly lose the deterministic completion summary, and final archives can describe a still-running batch. Action: require or append the matching completion summary inside the handoff transaction, complete batch fields during drain, and distinguish done/handoff from terminal drain in resume policy. Test every ordering and interruption boundary.

- **High — Park/stall recovery kind is inferred from a caller-controlled site.** Evidence: installed `stall` accepts any `--site` (`src/ovcaq/cli.py:184-190`); saga records omit operation kind (`src/ovcaq/workflow/records.py:700-709`); replay infers park solely from `site == "wrapper_died"` (`src/ovcaq/workflow/records.py:500-510`), and consecutive-park reset uses the same site heuristic (`src/ovcaq/workflow/records.py:583-597`). Impact: `stall --site wrapper_died` commits successfully but cannot replay as a stall, can replay as the wrong kind, and fails to reset the consecutive-park breaker. Action: persist explicit recovery kind in the deferred record and use it for replay/breaker policy, or reject the reserved site for stall. Add all-boundary tests for this collision.

- **High — The configured rework cap has no lifecycle effect.** Evidence: frontmatter commits `review.cap` (`src/ovcaq/workflow/frontmatter.py:178-187`), but rework always increments the cycle and remains in review without consulting the cap (`src/ovcaq/workflow/transitions.py:40-49`). The only cap-pause code merely interprets an already-paused state (`src/ovcaq/workflow/resume.py:14-21`), while all paused transitions are absent from the table (`src/ovcaq/workflow/transitions.py:72-79`). Impact: the configured cap cannot prevent unlimited rework, and the workflow core neither enters nor exits its advertised cap-pause policy deterministically. Action: port the characterized cap boundary and resume/abandon effects into compound workflow mutations, preserving unresolved findings; test below, at, and beyond the cap plus restart behavior.

- **Medium — Installed commands discard required configuration.** Evidence: CLI lifecycle operations hardcode `dev/local/prds` twice (`src/ovcaq/cli.py:554-557`, `src/ovcaq/cli.py:590-600`), despite the configurable path service. The frontmatter command calls `apply_to_store` without the active tier map (`src/ovcaq/cli.py:601-609`), so `default_model` always follows the unavailable-tier branch exposed at `src/ovcaq/workflow/frontmatter.py:126-134`. Impact: custom lifecycle directories cannot be used through installed commands, and valid configured tier floors cannot be applied there. Action: load/inject lifecycle-root and active-agent tier configuration at the CLI boundary, pass both into workflow services, and cover non-default paths and present/absent tiers through the installed executable. This should also remove the duplicate lifecycle resolution and single-caller `_workflow_context` indirection.

- **Medium — Installed-command verification is incomplete.** Evidence: the wheel test proves only command-name presence for the full family (`tests/packaging/test_installed_cli.py:89-112`); behavioral installed-wheel tests cover defer, one stall rejection, frontmatter, and report confinement, while the broad lifecycle test invokes `main()` in-process (`tests/workflow/test_workflow_cli.py:22-28`). Impact: wheel-only import, parser, path, and dispatch defects in select, phase-complete, resume-target, check-plan, successful park/stall, complete-prd, audit, and metrics can pass all gates. Action: exercise every accepted workflow command through the installed console script from a hostile CWD, including success, stable error, CAS, and multi-step lifecycle behavior.

- **Low — Transition target truth is duplicated.** Evidence: each effect writes `work.next_phase` (`src/ovcaq/workflow/transitions.py:31-69`), while `TransitionRow.next_phase` repeats it in the table (`src/ovcaq/workflow/transitions.py:17-20`, `src/ovcaq/workflow/transitions.py:72-79`) and a separate API reads the duplicate (`src/ovcaq/workflow/transitions.py:96-103`). Impact: every new transition has two independently editable target declarations, requiring tests solely to detect drift. Action: make the row’s target authoritative and have application derive the committed value from it, or remove the redundant projection until a real consumer needs it.

## VERIFY

- (none)

## KNOWN

- (none)

R1: fail

R2: fail

R3: fail

R4: fail

R5: fail

## Verification evidence summary

- Confirmed exact reviewed HEAD.
- Supplied fresh gates all passed: dependency sync; `1068 passed`; Ruff lint and format; mypy over 47 source files; sdist and wheel build.
- `git diff --check` passed for the complete range.
- No skip/xfail markers were found in the changed workflow or packaging tests.
- The review made no repository changes.
- Seven residual doubts remain, all classified as FIX.

I reviewed the complete range `b43bf2c94d5eb0fddafca55542ef2570b45e8d52..f2453760591875f1faf241ec9c0291303232efd9`, not only the final rework commit.
