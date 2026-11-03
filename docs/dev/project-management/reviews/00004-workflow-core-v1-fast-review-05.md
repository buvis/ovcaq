---
prd: dev/local/prds/wip/00004-workflow-core-v1.md
session: FT-04R5
review_kind: fast-track
cycle: 5
date: 2026-09-04
base_sha: b43bf2c94d5eb0fddafca55542ef2570b45e8d52
head_sha: c512a4ad7d67af75b413ee8c9612b088d21fb4f4
verdict: changes_requested
decision_required: true
closeout_ready: false
must_fix_root_causes: 3
rework_bundles: 0
reviewers:
  alice: available
  blake: available
  bob: available
---

# Fast review 05: 00004 workflow core v1

Complete updated PRD range reviewed:
`b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4`.
The range contains 40 changed files and 6,094 additions / 33 deletions. Review
covered the complete implementation range, not only FT-04F4.

Raw reports:

- `dev/local/reviews/00004-workflow-core-v1-fast-alice-05.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-blake-05.md`
- `dev/local/reviews/00004-workflow-core-v1-fast-bob-05.md`

## Verification at reviewed head

The coordinator began from a clean worktree at exact HEAD
`c512a4ad7d67af75b413ee8c9612b088d21fb4f4`.

| Check | Result |
|---|---|
| `mise exec -- uv sync --all-groups` | passed; 25 packages resolved, 24 checked |
| `mise exec -- uv run pytest tests/workflow/test_sagas.py tests/packaging/test_installed_cli.py -q` | passed; 50 tests in 2.03s |
| `mise exec -- uv run pytest` | passed; 1,095 tests in 11.24s |
| `mise exec -- uv run ruff check .` | passed |
| `mise exec -- uv run ruff format --check .` | passed; 92 files already formatted |
| `mise exec -- uv run mypy src/ovcaq` | passed; 47 source files |
| `mise exec -- uv build` | passed; sdist and wheel built |
| `git diff --check b43bf2c94d5eb0fddafca55542ef2570b45e8d52..c512a4ad7d67af75b413ee8c9612b088d21fb4f4` | passed |
| focused FT-04F3/FT-04F4 closure matrix | passed; 27 selected / 97 deselected in 1.49s |
| accepted-plan SHA-256 | exact match: `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5` |
| frozen autopilot-state SHA-256 | exact match: `ed37670c08931fe703e21a7730f7d29bd1e242ae29d273cefd4abe506a23162f` |

No verification failure was waived. Alice, Blake, and Bob also independently
ran the full suite at the reviewed head and each observed 1,095 passing tests.

## Mandatory isolated lenses

| Lens | Raw verdict | Raw correctness claims | Consolidated contribution |
|---|---|---:|---|
| Alice — consensus/architecture | changes requested | 3 | characterized metrics/report migration promoted; frontmatter and tier-map claims remain outside the settled Phase 2 application boundary |
| Blake — blind/PRD-only | changes requested | 3 | defer intent/frontmatter/configuration claims not promoted |
| Bob — doubt/de-slop, R1–R5 | changes requested | 5 functional plus 4 de-slop | report-identifier crash promoted; cap/tier/defer/frontmatter claims not promoted; R1–R4 fail, R5 pass |

All three lenses received fresh isolated packets and reviewed the complete
range. Alice received AGENTS, the accepted plan and required architecture
inputs, the PRD, current implementation/tests, and range diff. Blake received
AGENTS for governance and the PRD as the only requirements source. Bob received
AGENTS, the PRD, current implementation/tests, the range diff, and the full
doubt/de-slop rubric. None received a prior review, rework handoff, commit
message/log, coordinator conclusion, or another lens's output. No lens was
omitted, merged, substituted, or thinned.

## FT-04F4 and retained FT-04F3 closure audit

### FT-04F4: lifecycle-directory identity loss

**Not closed across the complete saga.**

The new device/inode checks correctly close the declared after-intent
rename-away cases for both WIP and hold. `_verify_move()` checks the configured
pathname against its open descriptor before artifact inspection, after rename,
and around both lifecycle-directory fsyncs
(`src/ovcaq/workflow/records.py:438-508`). The new real-filesystem regressions
prove after-intent substitution fails at `intent`, retains tasks/recovery, does
not touch the replacement target, and reconciles after identity restoration
(`tests/workflow/test_sagas.py:584-634`).

The identity checks end when the descriptor context closes immediately after
`intent -> moved` (`src/ovcaq/workflow/records.py:672-736`). The characterized
`AFTER_MOVE_BEFORE_APPEND` and `AFTER_APPEND_BEFORE_COMMIT` boundaries then
write the ledger, advance recovery, reset PRD state, and clear recovery without
revalidating either configured lifecycle pathname
(`src/ovcaq/workflow/records.py:737-764`).

The coordinator reproduced hold rename-away plus symlink replacement at each
later boundary in separate real temporary filesystems. Both operations returned
success with this terminal evidence:

```text
after-move-before-append  success=stall recovery=None tasks=0 configured=False relocated=True ledger=True
after-append-before-commit success=stall recovery=None tasks=0 configured=False relocated=True ledger=True
```

The replacement target remained untouched, but the PRD existed only under
`relocated-hold`; configured hold did not contain it. This is the same
lifecycle-location loss after the new checks have stopped running.

### FT-04F4: competing public state mutations

**Closed.**

Every mutating `StateService` method now enters one guarded transaction that
checks active recovery under the state-store lock
(`src/ovcaq/state/commands.py:51-55,133-146,148-434`). Restore evaluates the
same precondition under its exclusive store lock before reading or publishing
the backup (`src/ovcaq/state/store.py:153-182`). The unit matrix covers all
thirteen public service mutation paths with exact state/backup byte
preservation; saga and installed-wheel tests interrupt after intent, reject
task, contract, and allowed generic mutations, and then reconcile without lost
work. Those cases are included in the passing 27-test closure matrix. No state
layer imports workflow code.

### Retained FT-04F3: filesystem durability before state advance

**Still closed for its exact contract.**

Hold/deferred creation fsyncs the parent owning the new entry; already-moved
replay fsyncs both WIP and hold descriptors before `intent -> moved`; exact
record replay fsyncs the deferred directory before `moved -> recorded`
(`src/ovcaq/workflow/records.py:307-359,409-434,466-508,725-760`). Controlled
post-rename and post-replace interruptions plus parent-creation cases pass in
the focused matrix.

### Retained FT-04F3: explicit recovery kind

**Still closed.**

Recovery intent and deferred records retain explicit `kind`; exact replay
matches it, and reset/park-breaker behavior is selected from it rather than
`wrapper_died` (`src/ovcaq/workflow/records.py:528-550,574-638,747-770`). Exact
stall/park retries and both cross-kind collision directions pass at service and
installed-wheel boundaries with unchanged state/ledger bytes.

## Surviving must-fix roots

### 1. Later saga boundaries can still lose configured lifecycle identity

Severity: **high**.

The reproduced FT-04F4 gap above violates P02-T07 and the requirement that
park/stall remain recoverable at every durable boundary. A successful operation
can clear recovery and reset live work while the PRD is absent from both
configured WIP and hold.

Required repair: retain or re-establish the verified WIP/hold identities through
record publication and the final state commit. Revalidate them at the later
durable boundaries and fail closed without clearing recovery or resetting tasks
when either configured name no longer identifies the verified directory. Add
real-filesystem regressions for hold rename-away/replacement at
`AFTER_MOVE_BEFORE_APPEND` and `AFTER_APPEND_BEFORE_COMMIT`, including identity
restoration and successful replay.

### 2. P02-T08 did not migrate the characterized metrics/report contract

Severity: **high**.

The frozen migration contract assigns `CMD-019`, `CMD-020`, `ART-039`–`ART-041`,
`TEST-018`–`TEST-020`, and `TEST-062` to PRD 00004 and
`src/ovcaq/workflow/reports.py`. `CMD-020` is the deterministic Markdown summary
of loop metric rows; `CMD-019` binds state and metrics into the batch report.
The retained `tests/fixtures/claude/legacy-metrics.jsonl` contains two session
rows and one convergence row, but its only repository reference is the fixture
README.

Coordinator reproduction loaded all three characterized rows and inspected the
public renderers:

```text
render_metrics signature: (state: State) -> str
render_report signature: (state: State, deferred_records: Iterable[...]) -> str
wall_secs rendered: false
cost_usd rendered: false
tokens_out rendered: false
```

The current state-only review-bookkeeping projection and recast goldens do not
exercise or replace the routed metric-row domain. This is a concrete source-ID
and evidence gap, not runtime metric collection work.

Required repair: port the pure characterized metric-row reduction and its report
bindings against the retained sanitized input/goldens, including nonzero and
legitimate empty summary bindings. Keep collection/provider parsing outside the
workflow layer.

### 3. Schema-valid control characters can break deterministic report publication

Severity: **medium**.

`_require_component()` rejects separators and dot components but accepts
newlines (`src/ovcaq/workflow/reports.py:205-215`). State validation and PRD
selection also accept a filename such as `00004-safe\n## Injected.md`.
Coordinator reproduction validated that state, rendered three level-two
headings (`00004-safe`, `Injected.md`, and `Batch Summary`), and then observed
`publish_report()` raise `StopIteration` because `_updated_report()` searches
for the unsplit injected heading (`src/ovcaq/workflow/reports.py:343-363`).

Required repair: define and reuse a conservative control-character-free grammar
for identifiers used as lifecycle basenames, report headings, or report
filenames, and make report section lookup fail with a domain error rather than
an internal iterator exception. Cover selection, state/public rendering, and
installed-command publication.

## Reconciled but not promoted

- Frontmatter returns catchup/design/gate/ambiguity policy in its structured
  application result; the v1 crosswalk derives realized state from
  `batch.catchup`, `work.design_doc`, and `control.pause_reason`. Synthesizing
  completed catchup/design or a pause solely while parsing policy would conflate
  policy with outcome. Durable runtime consumption remains later integration
  scope, so the three repeated frontmatter claims do not overturn the settled
  Phase 2 boundary.
- Active-agent tier-map injection and project configuration loading begin at the
  runtime/configuration edge. The pure frontmatter API accepts
  `available_tiers`, and the lifecycle resolver accepts configured relative or
  absolute roots without provider leakage. Installed runtime wiring remains a
  later PRD responsibility; Alice/Blake/Bob's tier/config claims are not
  promoted.
- The accepted transition row is `review + rework -> review (cycle + 1)`.
  Review-cap pause/enforcement is supervisor decision policy, so Bob's cap claim
  is not promoted.
- The coordinator reproduced Blake/Bob's defer interleaving: a defer that read
  PRD A can publish its record after an overlapping mutation selects PRD B.
  This history remains linearizable at defer's committed read while the two
  operations overlap. Phase B explicitly requires idempotent operation IDs for
  defer and reserves intent/move/record/reset/commit for park/stall; before-
  publish and after-publish replay tests pass. A revision handshake would be
  additional concurrency hardening, not a demonstrated P02-T06 failure.
- Successful WIP-to-done movement, successor activation, retained `work.prd`,
  and task/outcome cross-validation remain caller/supervisor responsibilities
  under the accepted closed transition table. No new evidence invalidated those
  settled dispositions.
- Bob's R1 duplicated installed setup, R2 impossible null branch, R3
  single-caller `_workflow_context`, and R4 paraphrasing docstrings are concrete
  cleanup candidates but do not violate a release gate or acceptance criterion.
  They remain nonblocking; R5 passed with no framework-only tests found.
- Concurrent report writers, exact-replay revision increments, and exact Python
  3.12 full-suite execution remain nonblocking depth. The required project gate
  passed on the configured Python 3.13.13 environment, and Bob separately
  compiled all 47 source files with Python 3.12.

## Acceptance and source-ID audit

| Obligation | Evidence at reviewed head | Status |
|---|---|---|
| P02-T01 selection/lifecycle paths | ordering, hold exclusion, configured pure resolver, invalid-directory tests | pass within settled runtime-configuration scope |
| P02-T02 frontmatter | parsing/default/warning/application tests; pure tier-map seam | pass within settled runtime-consumption scope |
| P02-T03 transition table | every accepted/rejected row and full effects | pass |
| P02-T04 resume/plan policy | resume matrix, recovery precedence, plan shape/ceiling | pass |
| P02-T05 reset/completion summary | owner preservation, CAS, deterministic summary/idempotence | pass |
| P02-T06 defer ledger | operation-ID conflict/deduplication and atomic publication replay | pass |
| P02-T07 stall/park saga | FT-04F3 guarantees and mutation fencing pass; later lifecycle identity fails | **fail** |
| P02-T08 reports | serial projection/idempotence tests pass; routed metrics contract absent; control-character publication crashes | **fail** |
| P02-T09 legacy-root replacement | provider/legacy runtime string guards pass | pass |
| P02-T10 generated docs | parser/reference/protocol inventory equality tests pass | pass |

Four PRD acceptance criteria retain passing evidence. Recoverability at every
durable boundary and stable consumption by PRD 00005 remain blocked by P02-T07
and P02-T08.

## Verdict and mandatory stop

Verdict: **changes requested**. PRD 00004 is **not closeout-ready**. The complete
gate is green, public mutation fencing closes, and both FT-04F3 repairs remain
closed, but one FT-04F4 lifecycle root survives and two concrete P02-T08 roots
remain.

No repair cycle is authorized by this review-only session. No implementation or
test was edited; no autopilot state or implementation plan was mutated; the PRD
was not moved or closed; the capsule was not refreshed; and no later PRD was
started. `decision_required` is true, `closeout_ready` is false, and no rework
bundle was created. Stop after the review handoff.
