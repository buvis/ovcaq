# Incomplete review attempt — PRD 00008 cycle 2

Reviewed HEAD: `7b47cef26fc8fa97fae726e4317629ee5053dc71`.
Diff range: `5544b1fc9c27838f8941c2266867a6c34ef10902..7b47cef26fc8fa97fae726e4317629ee5053dc71`.

Status: paused, reviewer_fail. This is not the canonical review-2 artifact and
must not trigger the existing-review skip or convergence. No follow-up tasks,
repairs, cap changes, or phase-done transition were dispatched.

Autocodex Bob receipt: unavailable; helper publication failed before receipt.
Bob substitution: external Claude Opus supplied the intended independent voice,
but this attempt is invalid and does not certify the codex-rung guard (12
Codex-implemented tasks). Eve was not dispatched or claimed. Prior cycle's
D verdicts were cleared from current state; this incomplete cycle has none.

Bob helper used approved network access and ended with exit 1:
`File exists: .../docs/dev/tmp/bob-output-2.txt`. The path was not unique.
Raw result and all R/D verdicts are preserved in
`00008-tui-python-launcher-v1-bob-invalid-2.md`; JSONL and stderr paths there
identify this run. The existing output file was not overwritten or consolidated.
The shared Bob context also erroneously included the design document; a
corrected PRD-only prompt was staged but never dispatched after terminal failure,
as the host requires pause. Recovery must use a unique fresh output path.

Carl: unavailable, helper exit 3, nested dispatch refused; guard retained.
Pack: unavailable, engram reported unregistered repository.

Tests: 4579 passed, 0 failed, 0 skipped (suite run this cycle; two cleanup warnings).
Ruff lint/format, mypy, sync and build pass. See verification-2.md and replay-2.md.
Fail-first replay was skipped after its 600-second timeout, and its temporary
worktree was removed. No previous failed verification checks existed.

Seven native findings remain unclassified (one High, six Medium). Raw reports
below preserve all R/B verdicts. The coordinator verified the cited ownership,
selection formatting and launch branches by reading current source. Bob's
invalid findings are not merged into a final table. Full gate, coverage and
convergence cannot certify an incomplete mandatory lens; no clean verdict is
claimed. State schema and counts remain valid at 14/14 completed tasks.

## Alice

Provider: Codex; native gpt-6.1-sol / high; isolated /root/alice_review2; complete assembled Alice persona and R rubric.

[ALICE] 🟠 If the selected supervisor finishes during an evidence read, ownership revalidation sets state=None and ended=True; ProjectObserver permanently caches the unknown frame and both viewers return failed/1 despite valid completed or paused terminal evidence. Reobserve the attested terminal state before caching. | File: src/ovcaq/tui/model.py:334 | Task: 2
[ALICE] 🟡 The launch handshake immediately rejects an inconsistent observation, but normal cleanup unlinks run.json while run.lock remains held. A parent that captured the registry entry before cleanup can therefore reject a successfully completing child; wait within the existing deadline for its terminal outcome. | File: src/ovcaq/supervisor_cli.py:343 | Task: 7
[ALICE] 🟡 Successful immediate boundary pauses still become launch failures: the supervisor returns exit 0 for PAUSE, while the launcher accepts only completed batches. Preserve the exact-owner proof and recognize the accepted paused/detached success outcome. | File: src/ovcaq/supervisor_cli.py:266 | Task: 7
[ALICE] 🟡 Missing or ambiguous selection errors interpolate unsanitized registry run IDs and roots; CLI failure output prints them directly, allowing ESC/OSC/BEL injection despite sanitized fleet rows. Apply display_text when formatting available selections. | File: src/ovcaq/tui/discovery.py:44 | Task: 8
[ALICE] 🟡 Session changes clear the usage dictionary and events require the exact current session, so its 256-session eviction branch is unreachable. Remove that branch and MAX_USAGE_SESSIONS without changing behavior. | File: src/ovcaq/tui/model.py:549 | Task: 1

R1: fail
R2: pass
R3: pass
R4: fail
R6: pass
R7: fail
R8: pass
R9: fail
R10: pass
R11: pass
R12: pass
R13: pass

## Blake

Provider: Codex; native gpt-6.1-sol / high; isolated /root/blake_review2; complete assembled Blake persona and B rubric; PRD-only.

B1: fail
B2: pass
B3: fail
B4: pass
B5: fail
B6: pass
B7: pass
B8: pass
B9: pass
B10: pass
B11: pass
B12: pass
B13: pass
B14: fail
B15: fail
B16: fail
B17: pass
B18: pass
B19: pass

[BLAKE] 🟡 Post-drain capability failure guidance disappears immediately: ProjectApp exits after refreshing the final frame, restores the alternate screen, and returns without printing retained evidence or the retry command. At 80×24 those details are below the viewport; the finished run is also unavailable for reattachment through the live-only fleet. Preserve readable final diagnostics before returning. | File: src/ovcaq/tui/app.py:388 | Task: P06-T04
[BLAKE] 🟡 Pause/resume/stop verification reads run.json through unbounded, symlink-following Path.read_text(). Replacing that observational file with a FIFO blocks verification indefinitely and freezes synchronous TUI controls; a FIFO reproduction confirmed the hang. Use bounded, nonblocking regular-file validation and reject invalid metadata visibly. | File: src/ovcaq/supervisor_cli.py:215 | Task: P06-T05

Verification: 421 focused tests passed with process inspection enabled.
