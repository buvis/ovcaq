# OVCAQ fast-track implementation plan

Status: active | Prepared: 2026-08-27 | Scope: PRDs 00003–00014

## Decision

Finish the OVCAQ backlog without `run-autopilot`, `autoclaude`, or the saved
autopilot phase machine. The accepted
[`implementation-plan.md`](implementation-plan.md), the
[`implementation-plan-coverage.md`](../prds/implementation-plan-coverage.md)
manifest, and each PRD remain the architecture and acceptance contracts. This
plan replaces only their execution method.

The fast track uses:

- one cohesive implementation owner per session;
- explicit, file-backed handoffs between fresh top-level sessions;
- two implementation slices per ordinary PRD instead of one agent task per
  source-task ID;
- deterministic verification before review;
- a fresh review coordinator that dispatches all mandatory review lenses to
  isolated subagents in parallel;
- one consolidated rework session per review cycle, grouped by root cause;
- manual, verified PRD lifecycle moves after evidence passes.

This keeps all 119 source tasks, 23 migration items, 15 personal-acceptance
items, architecture invariants, and review lenses. It removes the orchestration
machinery currently being reconstructed from the critical path.

## Starting point

- PRD 00002 is complete.
- PRD 00003 is in `wip` at `9bd52bb` with 20 of 25 recorded tasks complete.
- Its cycle-2 review records 13 actionable findings already grouped into five
  pending repair areas: schema boundaries, supplied task IDs, config collisions,
  the `batch.mode` crosswalk, and dead test assignments.
- PRDs 00004–00009 are in `backlog`.
- PRDs 00010–00014 are in `hold` pending their numerical dependencies and
  explicit external-action gates.
- `dev/local/autopilot/state.json` is frozen as forensic evidence for PRD 00003.
  Fast-track sessions do not mutate it, resume it, or derive later progress from
  it.

## Authority and progress

Use these sources in order:

1. `AGENTS.md` and user-global instructions.
2. `dev/local/plans/implementation-plan.md` for architecture and sequence.
3. `dev/local/prds/implementation-plan-coverage.md` for source-ID ownership.
4. The active PRD for scope, dependencies, risks, and acceptance.
5. Existing design/review artifacts for that PRD.
6. The latest fast-track handoff for session-local progress.
7. The committed repository and current verification output.

Final agent prose is never progress authority. Every session writes a handoff to:

```text
dev/local/plans/fast-track-handoffs/<prd>/
  01-build.md
  02-build.md
  review-01.md
  rework-01.md
  review-02.md
  closeout.md
```

Only files that exist are authoritative. Number additional build/rework/review
files monotonically. These handoffs are disposable execution scaffolding and are
removed with this plan after the full backlog is complete; review reports under
`dev/local/reviews/` remain durable.

## Hard rules

1. Never invoke an autopilot skill, command, wrapper, state transition, or saved
   task list while executing this plan.
2. Work on one PRD at a time in numerical dependency order. Read-ahead and
   fixture research may overlap; production implementation may not cross an
   unmet PRD dependency.
3. Start every implementation, review, and rework slice in a fresh top-level
   session. Do not continue after printing its handoff.
4. One session owns one cohesive subsystem boundary. Do not recreate the
   one-task/one-agent plan that caused coordination overhead.
5. Pair implementation, tests, and owned documentation in the same slice.
6. Preserve the architecture invariants in `AGENTS.md`: one state writer,
   state-over-prose decisions, provider code at the edge, raw evidence,
   observer-only TUI, external capabilities, and shell-free argv.
7. Keep each PRD's `Pxx-Tyy` obligations and exit criteria mapped to passing
   tests or inspected artifacts. Grouping work never waives an ID.
8. Commit each implementation or rework slice conventionally. Do not mix PRDs
   in one commit.
9. The worktree must be clean at every session handoff except for deliberate
   ignored `dev/local/` handoff/review artifacts.
10. Never perform real launcher-global apply, companion publication, destructive
    cutover, tag, or package publication without the explicit approval required
    by PRDs 00010, 00011, and 00014.

## Session protocol

### Implementation session

At session start:

1. Read this plan, the active PRD, its source-ID rows in the accepted plan, and
   the latest handoff.
2. Confirm the PRD's dependencies are complete and record `base_sha`.
3. Select only the session slice named below. Make the simplest safe decisions
   within the accepted contract; do not replan the PRD.
4. Implement code, tests, and owned documentation together.
5. Run targeted tests continuously, then the slice gate.
6. Commit the cohesive result.
7. Write the handoff and stop.

Every implementation handoff records:

```text
PRD / session / base_sha / head_sha
source IDs covered
files changed
behavior completed
tests and exact results
decisions made
known risks or failures
next session and exact first action
```

### PRD verification gate

Before review, a fresh verification session runs from the repository root:

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src/ovcaq
uv build
```

Use `mise exec -- uv ...` when `uv` is not on `PATH`. The session also checks the
PRD acceptance list and source-ID coverage. Failures return to a fresh
implementation session; they never enter review as deferred verification.

### Fresh-context review handoff

Review never runs in an implementation or rework session. Start a new review
coordinator session, record the PRD's implementation `base_sha..head_sha`, and
dispatch these three subagents concurrently with isolated contexts:

- **Alice — consensus/architecture:** receives `AGENTS.md`, the accepted plan,
  the PRD, relevant design artifact, diff, and verification results. Checks
  contracts, architecture, integration, tests, and maintainability.
- **Blake — blind/PRD-only:** receives the PRD, diff, and verification results.
  Does not receive implementation handoffs, design rationale, earlier reviews,
  or other reviewers' output. Checks whether the implementation independently
  satisfies the stated product contract.
- **Bob — doubt and de-slop:** receives `AGENTS.md`, the PRD, diff, and
  verification results. Assumes the work is incomplete and applies the full
  R1–R5 doubt/de-slop rubric, including failure paths and generic-code quality.

All three lenses run on every review cycle, regardless of PRD size. If a
reviewer fails, dispatch that lens once more in a new subagent; if still
unavailable, use a new fallback subagent with the same isolated prompt. Never
silently omit a lens.

Each subagent is read-only and returns:

```text
Verdict: pass | changes_requested
Must fix: issue, severity, evidence, violated requirement
Can defer: issue, evidence, rationale
Tests inspected or run
Residual doubts
```

Save raw lens reports as:

```text
dev/local/reviews/<prd-stem>-fast-alice-<cycle>.md
dev/local/reviews/<prd-stem>-fast-blake-<cycle>.md
dev/local/reviews/<prd-stem>-fast-bob-<cycle>.md
```

The coordinator performs no code edits. It deduplicates findings by root cause,
verifies disputed claims against the repository, and writes
`<prd-stem>-fast-review-<cycle>.md`. It creates at most three rework bundles:

1. contract/correctness/security;
2. integration/recovery/portability;
3. tests/docs/maintainability.

Must-fix means a reproduced defect, security/data-loss risk, architecture
invariant breach, PRD/source-ID/acceptance miss, failing gate, or required
evidence gap. Speculation, style preference without a violated rule, duplicate
reports, and out-of-scope enhancements are recorded as deferred instead of
creating more work.

### Rework and convergence

Start rework in a fresh session from only the consolidated review, PRD, and
repository. Fix all must-fix bundles together, rerun targeted and full gates,
commit, write a rework handoff, and stop.

Any code-changing rework is followed by another fresh review coordinator and all
three lenses. The normal budget is one rework cycle. One final rework/review
cycle is allowed when a new or still-reproduced must-fix remains. If a must-fix
survives two rework cycles, stop with its exact evidence for a user decision;
do not create an unbounded review loop.

### Closeout

A PRD closes only when:

- its acceptance criteria and source-ID obligations have evidence;
- the full verification gate passes at the reviewed head;
- Alice, Blake, and Bob have no unresolved must-fix finding;
- durable review artifacts exist;
- the implementation commits are clean and scoped.

Then write `closeout.md`, move the PRD to `dev/local/prds/done/`, verify the
destination exists, refresh the project capsule's Active Work section, and
start the next PRD in a fresh session. Promote a held PRD only when its declared
dependencies and approval preconditions are satisfied.

## Backlog execution map

PRD 00002 is a completed prerequisite. The following sessions cover all
remaining source phases P01–P12 without changing their ownership.

### PRD 00003 — state kernel (P01-T01…P01-T12)

1. **FT-03A — Recorded repair bundle.** Implement the five pending repair areas
   from review cycle 2: schema boundary validation (including lone surrogates,
   absolute repo roots, and typed resource-limit coverage), absent-versus-
   supplied task IDs, config path collisions, `batch.mode` crosswalk semantics,
   and dead assignments. Run all state/packaging tests and full gates.
2. **FT-03R — Fresh review.** Review the complete PRD range from the PRD start
   SHA through FT-03A, not only the last repair commit. Dispatch Alice, Blake,
   and Bob as specified above.
3. **FT-03F — Rework or closeout.** Apply at most three consolidated bundles,
   rerun the complete state/durability/installed-CLI matrix, and obtain a fresh
   three-lens convergence review before moving 00003 to `done`.

Exit: PRD 00004 can consume a complete installed state service with no shim.

### PRD 00004 — workflow core (P02-T01…P02-T10)

1. **FT-04A — Pure rules.** Implement selection, paths, frontmatter, plan
   policy, transition effects, resume, reset, and completion with row-by-row
   tests against characterized behavior.
2. **FT-04B — Sagas and public boundary.** Implement defer/park/stall recovery,
   failpoint replay, reports, workflow CLI, generated docs, and neutrality
   guards as one integrated boundary.
3. **FT-04R — Verify/review/rework.** Run the full gate and all three fresh
   lenses; rework by root cause only.

Exit: workflow is deterministic, provider-neutral, and ready for runtime use.

### PRD 00005 — runtime substrate (P03-T01…P03-T11)

1. **FT-05A — Discovery and ownership.** Implement config/path precedence,
   containment, platform probes, run lock, fleet registry, metadata, and stale
   identity handling.
2. **FT-05B — Processes and evidence.** Implement shell-free process groups,
   signals/watchdog, session/raw evidence, restrictive permissions, retention,
   purge preview/apply, and status/doctor/logs projections. Use real child and
   grandchild subprocess tests.
3. **FT-05R — Verify/review/rework.** Review process safety, collision risks,
   path security, and evidence retention with all three lenses.

Exit: one shared provider-neutral process/session substrate exists.

### PRD 00006 — events and Claude adapter (P04-T01…P04-T09)

1. **FT-06A — Protocols.** Implement immutable normalized observations, total
   reducer, raw fallback, usage semantics, driver contracts/registry, and
   normalized persistence.
2. **FT-06B — Claude edge.** Characterize and implement exact Claude launch,
   environment, JSONL decoding, failure/rate-limit classification, sanitized
   fixtures, fake execution, and provider-neutral import/string guards.
3. **FT-06R — Verify/review/rework.** Review full raw-before-decode and
   provider-boundary behavior through fresh lenses.

Exit: the supervisor can consume only `SessionSummary` and normalized events.

### PRD 00007 — supervisor loop (P05-T01…P05-T09)

1. **FT-07A — Pure decisions.** Implement ordered decisions, progress/fingerprint
   detection, phase routing, tier/effort/timeout configuration, retry bounds,
   and parity-inventory coverage.
2. **FT-07B — Effects and capabilities.** Implement fresh-session execution,
   pause/resume/stop/drain/archive/metrics, foreground `run --no-tui`, park/halt,
   and the generic agoge lifecycle with independent retry.
3. **FT-07R — Verify/review/rework.** Use fake drivers and exhaustive decision
   tables; all three lenses review state-over-prose behavior and retry safety.

Exit: a fake Claude batch drains without Bash.

### PRD 00008 — TUI and Python launcher (P06-T01…P06-T10)

1. **FT-08A — Shared projections.** Implement tolerant fleet/state/event/metric
   read models, panels, unknown telemetry, capability status, and theme/config
   migration using shared runtime models only.
2. **FT-08B — Controls and terminal lifecycle.** Implement attach, scoped
   pause/resume/stop, detach, TTY/no-TUI/plain fallback, and real crash/reattach
   integration; remove duplicate liveness and provider decoding.
3. **FT-08R — Verify/review/rework.** Fresh lenses focus on accidental policy in
   the UI, process ownership, terminal failure, and provider-neutral rendering.

Exit: Python owns run/attach and TUI failure cannot kill work.

### PRD 00009 — Codex adapter (P07-T01…P07-T07)

1. **FT-09A — Launch and fixtures.** Capture/version sanitized installed-Codex
   fixtures and implement exact shell-free argv, sandbox, cwd, prompt, tier, and
   effort mapping.
2. **FT-09B — Decode and conformance.** Implement total Codex decoding/failure
   classification, raw-only gaps, shared conformance, fake full drain, TUI
   projection, and no-Codex-branch guards.
3. **FT-09R — Verify/review/rework.** Run Claude and Codex conformance together;
   review the abstraction rather than only the new adapter.

Exit: both first-party adapters pass the shared fake workflow contract.

### PRD 00010 — external plugin provisioning (P08-T01…P08-T11)

Move from `hold` only after PRD 00009 closes.

1. **FT-10A — Core reconciliation.** Implement packaged requirement metadata,
   generic plan/report, batch pins/drift, doctor/run preflight, and fake
   absent/stale/incompatible cases.
2. **FT-10B — Launcher adapters.** Implement supported Claude and Codex
   marketplace command adapters, read-only check, explicit idempotent apply,
   postcondition verification, and second-apply no-op against fake CLIs.
3. **FT-10C — Companion preparation.** In separate sessions per companion repo,
   create bounded work records and implement compatible workflow/agoge content.
   Record repo paths, commits, tests, target versions, and dry-run publication
   plans. Do not publish yet.
4. **FT-10G — Approval gate.** Present exact companion release targets and
   launcher-global apply actions. Stop until explicitly approved.
5. **FT-10D — Release and real proof.** After approval, publish companion
   versions, apply provisioning, run real Codex handoff and both isolated agoge
   smokes, retain evidence, and inspect the OVCAQ wheel for metadata-only
   packaging.
6. **FT-10R — Multi-repo review.** Fresh Alice/Blake/Bob subagents review the
   OVCAQ range and each companion commit/release record; converge before close.

Exit: both launchers are provisioned, pinned, visible, and smoke-proven.

### PRD 00011 — one-way personal cutover (P09-T01…P09-T13)

Move from `hold` only after PRD 00010 closes.

1. **FT-11A — Safe preflight.** Prove legacy quiescence, install the exact local
   wheel, initialize fresh OVCAQ state, pass doctor/provision checks, select two
   real canary PRDs per launcher, and freeze the evidence/migration ledger.
2. **FT-11B — Claude canary.** Run an independent two-PRD Claude batch through
   build, all three review lenses, continuation, drain, agoge, pins, logs, and
   zero exit.
3. **FT-11C — Codex canary.** Repeat in a separate state tree with different
   PRDs and retain an independent evidence set.
4. **FT-11G — Destructive approval gate.** Present both passing canary records
   plus every exact deletion, archive, global instruction edit, and launcher-
   global target. Stop until explicitly approved.
5. **FT-11D — Migration and review.** After approval, remove the enumerated
   legacy runtime, update only the global instruction source and named personal
   paths, archive/delete old state, run the complete search/acceptance matrix,
   then hand the multi-root diff to fresh Alice/Blake/Bob reviewers.

Exit: installed OVCAQ is the sole personal runtime; the public-release track may
begin.

### PRD 00012 — generic driver API (P10-T01…P10-T06)

Move from `hold` only after PRD 00011 closes.

1. **FT-12A — Generic execution.** Implement closed argv placeholders,
   shell-free raw-only execution, conservative summaries, state-led drain, and
   capability-applicable decision conformance.
2. **FT-12B — External extension proof.** Stabilize entry points/capability
   metadata, build and install the separate sample distribution, add doctor and
   raw-only TUI behavior, and publish executable protocol docs.
3. **FT-12R — Verify/review/rework.** Fresh reviewers inspect injection safety,
   nominal-versus-real extensibility, and honest telemetry degradation.

Exit: a separately installed third-party driver works without core changes.

### PRD 00013 — Linux support (P11-T01…P11-T05)

Move from `hold` only after PRD 00012 closes.

1. **FT-13A — Platform contracts.** Run/fix Linux state durability, locks,
   replacement, registry, processes, signals, XDG paths, terminal lifecycle,
   clean-wheel CI, and capability probes while retaining macOS gates.
2. **FT-13B — Launcher proof and docs.** Run supported Claude/Codex Linux
   smokes, capture versions/evidence, add actionable doctor output, and document
   distributions, terminals, filesystems, and prerequisites.
3. **FT-13R — Verify/review/rework.** Fresh reviewers compare macOS/Linux
   guarantees and reject scattered platform policy or CI-only claims.

Exit: supported Linux environments pass the same provider-neutral contracts.

### PRD 00014 — first public release (P12-T01…P12-T08)

Move from `hold` only after PRD 00013 closes.

1. **FT-14A — Stable contracts.** Finalize state/CLI/driver/event compatibility,
   operator/provisioning/troubleshooting/platform/extension docs, ADRs, and
   executable docs/protocol tests.
2. **FT-14B — Release candidate.** Run the complete quality, security, platform,
   launcher, extension, clean-install, and packaging matrices. Build once,
   audit exact sdist/wheel contents, retain checksums, and verify compatible
   marketplace versions.
3. **FT-14R — Independent release review.** Hand the immutable candidate,
   source-ID/migration/acceptance evidence, security results, artifacts, and
   checksums to fresh Alice/Blake/Bob subagents. Rebuild if any code or artifact
   input changes, then repeat all lenses.
4. **FT-14G — Publication approval gate.** Present exact commit, version, tag,
   artifact checksums, package index, and marketplace pairings. Stop until
   explicitly approved.
5. **FT-14D — Publish and independently smoke.** Publish only the approved
   artifacts/tag, install by public name on supported macOS/Linux, rerun help,
   doctor, provision, both first-party launchers, and sample-driver smokes, then
   publish compatibility documentation.

Exit: every Pxx, Mxx, and Axx row has evidence and the public package reproduces
the approved release candidate.

## Milestone gates

| Milestone | PRDs | Required proof |
|---|---|---|
| State/workflow foundation | 00003–00004 | installed state CLI, deterministic lifecycle, recoverable sagas |
| Runnable Claude core | 00005–00007 | safe process substrate, normalized Claude adapter, Bash-free fake drain |
| Dual-launcher personal product | 00008–00010 | Python TUI/launcher, Codex parity, provisioned real smokes |
| Personal cutover | 00011 | independent Claude/Codex canaries and approved one-way migration |
| Public extensibility/platform | 00012–00013 | installed sample driver and Linux parity |
| Public release | 00014 | immutable reviewed artifacts, approval, publication, independent smoke |

## Completion and cleanup

After PRD 00014 closes:

1. Verify all PRDs 00002–00014 are in `done` and the coverage manifest has no
   missing Pxx, Mxx, or Axx evidence.
2. Confirm the worktree is clean and all required commits/release records exist.
3. Retain `dev/local/reviews/`, designs, source PRDs, release evidence, and the
   final project capsule.
4. Remove `dev/local/autopilot/state.json` and other stale autopilot disposables
   only after the personal-cutover evidence authorizes their removal.
5. Remove this executed plan and `dev/local/plans/fast-track-handoffs/` as stale
   execution scaffolding.
6. Run the mandated work-completion review in a separate fresh session, never in
   the final implementation session.

## Unresolved questions

None.
