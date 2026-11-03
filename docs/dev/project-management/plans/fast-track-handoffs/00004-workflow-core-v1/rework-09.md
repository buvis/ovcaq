# FT-04F9 → FT-04R10 repair handoff

Date: 2026-09-05, Europe/Prague. The five bounded repairs are committed.
Run completion review only in a **fresh FT-04R10 session**. This work session
did not run completion review, close the PRD, or start another PRD.

## Verify before changing anything

- Repository: `/Users/bob/git/src/github.com/buvis/ovcaq`, branch `master`.
- Expected HEAD: `72562f6fd12fb039e91e4c7b1be29758d1901ec8`.
- Commit: `fix(workflow): serialize ledger publication and verify output paths`.
- Commit timestamp: `2026-09-05T22:20:36+02:00`.
- Git status must be empty. Stop on mismatch; never reset/clean another session's work.
- Verified clean repair starting HEAD: `78f916c366f74105b76e6f07d80a7a1aeb251e9f`.
- Full implementation base: `b43bf2c94d5eb0fddafca55542ef2570b45e8d52`.
- R8 repair base: `8ef6c0d8ab111c33cd0b49ac50e71fb79a9512a7`.
- Repair diff: seven files, +357/-45. No production module was added.
- PRD remains `dev/local/prds/wip/00004-workflow-core-v1.md`.

## Read first

Read repository/global AGENTS.md, the WIP PRD, the accepted implementation plan
(read only), coverage manifest, discovery 00001, and both characterization TOMLs.
Preserve P02-T01–P02-T10, all 55 owned rows, and every phase exit.

- `dev/local/reviews/00004-workflow-core-v1-fast-review-09.md` and its
  `-evidence.md` companion: authoritative findings and complete source obligations.
- `review-09.md`: bounded repair authorization and settled decisions.
- `rework-08.md`, `rework-08-probes.json`, `rework-08-sizes.json`: prior preservation evidence.
- `rework-09-contract-and-sizes.json`: fresh 55-row join, source hashes, changed-file sizes.
- The regression, verification, and probe evidence below; older evidence remains intact.

## Repairs

| Finding | Final change | Behavioral evidence |
|---|---|---|
| R9-01, High, P02-T06/T07 | Lock the opened deferred-directory inode during reads and final snapshot comparison/native replacement. Keep the sidecar ownership checks and all existing boundaries. Refuse contention promptly with a contextual retry error. Compare the original ledger snapshot under that same lock, including when a displaced sidecar was restored. | Three new `tests/workflow/test_ledger_publication.py` cases: nested and real-process syscall rivals; restored-sidecar stale snapshot. Successful records survive, failed native publication retains evidence, and retry yields exactly one record per ID. All six unchanged R8 named-boundary nested/process cases pass. |
| R9-02, P02-T08 | Retain every opened output directory from configured root through leaf; verify identities during traversal, publication, identical replay, and successful context exit. Reuse the existing descriptor/path identity validator. | Sixteen `tests/workflow/test_report_identity.py` cases cover report/audit/archive, root/leaf and every audit ancestor, native replacement and identical-replay fsync. Refusal preserves state and displaced payload; valid configured-path retry and rerender reproduce exact bytes. |
| R9-03, P02-T09 | Normalize TOML RecursionError into ConfigurationError with the source path. The installed JSON CLI returns usage/exit 1 without stdout or traceback. | Four new `tests/packaging/test_input_integrity.py` cases cover project/user scopes and recognized/ignored keys with 2,000 nested arrays; config and state bytes remain unchanged. |
| R9-04, P02-T08 | Share `_section_span` between section removal and extraction. | Complete section, duplicate-collapse, missing-section, heading-boundary, unrelated-content and golden assertions pass unchanged. |
| R9-05 | `_run` delegates to `_run_unchecked`, retaining its assertion diagnostic. | Complete packaging directory and installed module-origin checks pass; argv/cwd/environment/capture/text/60-second timeout are unchanged. No delegation-only test was added. |

The directory lock cannot split when the sidecar pathname moves: both open
descriptors lock the same directory inode. It excludes rival reads as well as
publication, so a replacement-sidecar writer cannot prepare stale data inside
the original final check/replace interval. Snapshot comparison under that lock
also refuses a stale write if the original sidecar was restored after a rival
commit. This is kernel serialization plus a serialized content check, not an
additional unsynchronized pathname check. Contention may require retry, including
another batch sharing the deferred directory. Normal same-ledger writers retain
the original blocking sidecar lock.

The named BEFORE_PUBLISH and post-replace boundaries remain outside the short
directory critical section: their already-successful competitors still survive.
Saga original-artifact identities, publication guards, strict decoding, fsyncs,
exact/conflicting replay and original recovery intent all remain in force.

## Fail-first and verification evidence

Before production edits, the 22 new native-race, publication-chain and installed
TOML cases all failed: `rework-09-red.txt` retains the output. Both race failures
explicitly show successful `second` missing from the ledger. This is the later
native interval, not only the previously passing BEFORE_PUBLISH control.

A further restored-sidecar regression failed against the initial directory-lock
repair (`1 failed, 2 deselected in 0.02s`, DID NOT RAISE); the serialized snapshot
comparison then made it pass. These 23 new cases explain 1315 → 1338 full tests
and 427 → 450 workflow/packaging tests.

All commands used mise-managed uv, on Darwin/Python 3.13.13/pytest 9.1.1.
The final verified source/test tree is the committed tree.

| Command | Observed result |
|---|---|
| `mise exec -- uv sync --all-groups` | Exit 0; 25 resolved, 24 checked |
| Focused new/R8 ledger, report and installed-input regression files | 52 passed in 2.66s before adding the restored-sidecar case |
| `mise exec -- uv run pytest tests/workflow/test_ledger_publication.py tests/workflow/test_ledger_integrity.py -q` | 15 passed in 0.15s, including restored-sidecar protection |
| `mise exec -- uv run pytest tests/workflow/ tests/packaging/ -q` | 450 passed in 12.03s; zero failures/skips |
| `mise exec -- uv run pytest` | 1338 passed in 26.06s; zero failures/skips |
| `mise exec -- uv run ruff check .` | All checks passed |
| `mise exec -- uv run ruff format --check .` | 116 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | No issues in 51 source files |
| `mise exec -- uv build` | sdist and wheel built |
| `git diff --cached --check` | Passed before commit |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..HEAD` | Passed after commit |

The first complete directory/full runs had one sdist-allowlist failure because
the two new tests were not yet in Git's index (449/1337 other tests passed).
Staging them fixed the distribution-input mismatch; the unchanged allowlist
and both complete suites then passed. Cache/index sandbox failures were retried
through the required escalation path. No check was waived.

Every changed function is at most 49 lines; `_files.py` is 403 lines and
`reports.py` is 711. No inherited size exception was expanded or restructured.

## Cycle-09 probes, observed after repair

Run the original scripts with `mise exec -- uv run python dev/local/reviews/<file>`.
The three original script files and their old result files were not edited.

- `00004-cycle-09-probes.py`: exit 0, 19 observations retained in
  `rework-09-cycle-09-probes.json`. The earlier-boundary rival still succeeds
  and survives retry. The native-interval rival is refused; the old probe
  propagates that refusal through the injected syscall, then retries `first`.
  Both operations' retry behavior is explicitly checked by the new tests.
- `00004-cycle-09-publication-probes.py`: exit 0, all three surfaces refuse
  directory replacement and retain displaced payloads. Exact output is in
  `rework-09-publication-probes.json`.
- `00004-cycle-09-adjudication-probes.py`: exit 1 from the old harness's
  `assert rival.returncode == 0`. Its bare child-library call now raises
  `OSError: deferred publication busy; retry`, so its success assumption is
  obsolete. `rework-09-adjudication-raw.json` preserves both tracebacks; do not
  report this raw harness run as passing or confuse it with an unhandled CLI
  error. The new real-process regression catches that expected refusal,
  continues the original native replacement, verifies lock-loss evidence,
  and retries both IDs exactly once.
- The other adjudication functions ran separately without alteration: exit 0,
  `rework-09-adjudication-supplement.json`. Frontmatter ownership and initially
  missing-source/null-artifact refusal remain as settled.
- The exact saved installed TOML command was rerun against the rebuilt wheel:
  exit 0, `rework-09-installed-config.json`. Both scopes produce usage JSON,
  preserve configuration, and have no traceback; both recorded module origins
  are in the temporary installation's site-packages. The four installed tests
  additionally preserve existing authoritative state and cover ignored keys.

Expected identity/resource/contention refusals remain distinct from unhandled
errors. No other unexpected post-repair probe error was observed.

## Preservation, artifacts and next review

Plan SHA-256 remains `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.
Inventory SHA-256 remains `d2a839b6c3b43c00c66114e0f20fe0d85b6169449562a72cf41ae30768eefdb9`.
All ten source tasks, all 55 owned rows and phase exits remain required for R10.
Retain terminal drain, conflicting-stall refusal, nonzero and unknown totals,
equal-key ordering, active-batch metrics, explicit recovery kind, original
artifact identities, lifecycle/ledger fences, control-character refusal,
provider neutrality and parser-derived docs. Existing R8 tests were not rewritten.

R8-K1/R8-K2 and R9-K3/R9-K4 remain KNOWN. The mandatory full implementation-base
replay remains skipped on missing packaging_support; it was not retried. Keep
the existing bounded R8 repair-base replay (56 collected, 46 failed, ten valid
preservation cases passed) and its chronological TDD limitation. This session's
23 fail-first cases do not establish universal implementation-base binding.

Review the **full implementation range** in a new session. Run every required
isolated lens: Alice consensus, Blake PRD-only, Bob doubt plus de-slop with full
rubrics and D1–D5 (the installed names for the requested R1–R5 obligations).
Keep the coordinator-only lock root despite zero prior lens votes. Do not retry
or bypass the external Bob/Carl nested-wrapper guards or claim native model diversity.

Do not add an importer, aliases, launcher markers, provider/model policy,
abort/rollback API, or duplicate durable frontmatter policy. Initially absent
source keeps null artifact and failure evidence; later unidentified replacements
remain refused. Linux qualification retains its downstream owner. No unrelated
autopilot state, implementation-plan edit, capsule refresh, PRD closeout or next PRD.

No worktree, branch, or executed plan was created. Only the original checkout
is registered; stashes and final Git status are empty. Disposable probe roots
and child processes were context-managed/reaped. Older ignored evidence and
other sessions' artifacts remain. Build artifacts and this handoff/evidence
under ignored `dev/local/` are intentionally retained.

Built artifact SHA-256s:
- sdist: `e633eb9803b311210106b7673db408c63e27205ec2669184421e43fd10bc19ec`
- wheel: `f3e6b76240f72608ecf9d4761ff172e2502ee358c9cd79d152324ad9b1fe657a`

Unresolved questions: none.
