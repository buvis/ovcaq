# Phase 0 downstream reconciliation

Reviewed: 2026-08-25  
Result: reconciled; one downstream wording clarification applied

## Inputs

- Accepted implementation plan SHA-256:
  `43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`
- `tests/characterization/current_system.toml`
- `tests/characterization/migration.toml`
- `dev/local/prds/implementation-plan-coverage.md`
- PRDs 00003 through 00014

The frozen inventory has 603 IDs. The migration manifest maps all 603 exactly
once across 31 routes: 456 migrate, 55 externalize, and 92 retire. Its recorded
inventory digest matches the committed inventory bytes. The executable contract
tests independently enforce counts, ownership, set equality, provenance, and
the mandatory easy-to-miss surfaces. TEST-062's batch-summary binding maps to
the existing workflow reporting destination and causes no downstream scope
change.

## PRD review

| PRD | Routes / IDs | Reconciliation result |
|---|---:|---|
| 00003 state kernel | 4 / 153 | No scope change. Its clean-v1 crosswalk must still disposition all 184 legacy state fields, including IDs routed to later owners. The ownership audit moved 16 generic task-abort, cap-rotation, planning, attempt, and recovery fields into core schema ownership. Five hook marker rows are external sidecars, never `state.json` fields or external durable writers. Thirty Qwen/Codex-specific and historical guard fields are retired rather than copied into v1. |
| 00004 workflow core | 8 / 55 | No change. Selection, frontmatter, policy, lifecycle transitions, resume, filesystem sagas, reports, and parser-derived command coverage match the eight workflow targets. |
| 00005 runtime substrate | 6 / 51 | No change. Project discovery, process ownership, registry/liveness, watchdog, raw session retention, and installed diagnostics match the six provider-neutral runtime targets. Automatic `purge-devlocal` remains retired; the PRD's explicit preview-first `ovcaq logs purge` is a new safe replacement, not a port of that drain hook. |
| 00006 events and Claude adapter | 2 / 30 | No change. Claude-native argv/event/failure behavior stays at `drivers/claude.py`; malformed, non-JSON, unknown, and raw-survival reduction maps to the provider-neutral reducer. |
| 00007 supervisor | 2 / 69 | Contract clarification applied. The current personal `notify_out` OS-script behavior is retired. Source task P05-T05's notification outcome is implemented as provider-neutral durable attention projected by the TUI, not by copying the script. Supervisor and capability mappings otherwise match the PRD. |
| 00008 TUI and Python launcher | 2 / 94 | No change. Python TTY/job-control replacement maps to the CLI; tracon projections and presenter behavior map to the TUI. The `render_stream` split is explicit: raw/malformed/unknown normalization belongs to 00006, while summary fallback and presentation belong to 00008. |
| 00009 Codex adapter | 0 / 0 | No change. The current runtime has no first-party Codex driver to migrate. The sanitized synthetic seed fixture and the PRD's fixture/fake, installed-version argv, decoder, health, and conformance obligations remain forward requirements; old workflow-review probe state is not mistaken for the new adapter. |
| 00010 provisioning | 2 / 59 | No change. Fifty-five workflow-skill, reviewer, hook, enforcement-sidecar, and related test IDs remain external launcher marketplace content. Four current plugin observation/drift IDs migrate into core reconciliation. The wheel retains identifiers/protocol requirements only. |
| 00011 personal cutover | 5 / 92 | No change. Retirement is explicit for 34 Fable helper/ledger/budget IDs, 16 legacy aliases/shims/migration-only artifacts, 30 provider-specific or historical state keys, eight `notify_out` IDs, and four automatic `purge-devlocal` IDs. Removal remains gated by both real canaries and the approved target ledger. |
| 00012 generic driver API | 0 / 0 | Explicit no-change. No current generic-driver or installed-extension behavior exists to migrate; its argv-template, raw-only, third-party entry-point, conformance, and diagnostics work remains forward scope. |
| 00013 Linux support | 0 / 0 | Explicit no-change. The characterized personal runtime is macOS-only, so Linux state/process/XDG/terminal/launcher obligations remain new platform proof rather than migration rows. |
| 00014 public release | 0 / 0 | Explicit no-change. Stable policies, complete docs, security review, reproducible release artifacts, cross-platform clean installs, and publication authorization remain forward release gates. Phase 0 artifact scans are an input, not a substitute. |

## Coverage-manifest review

The accepted plan digest, Phase 0–12 ownership, 119 source-task count, migration
rows M01–M23, personal acceptance rows A01–A15, public command ownership,
architecture invariants, and closeout responsibilities remain consistent with
the frozen evidence. Current-behavior ownership by PRD is:

| Owner | Routes | IDs |
|---|---:|---:|
| 00003 | 4 | 153 |
| 00004 | 8 | 55 |
| 00005 | 6 | 51 |
| 00006 | 2 | 30 |
| 00007 | 2 | 69 |
| 00008 | 2 | 94 |
| 00010 | 2 | 59 |
| 00011 | 5 | 92 |

Zero current IDs for 00009 and 00012–00014 are intentional and do not waive
their forward source tasks or exit criteria. The coverage manifest and accepted
implementation plan require no edits. Changing the accepted plan would require
a new reviewed digest; no such change was made.

## Conclusion

Downstream contracts are consistent after the PRD 00007 notification wording
clarification. No unexplained conflict remains, and no implementation PRD gains
or loses a source task, phase exit criterion, or authorization boundary.
