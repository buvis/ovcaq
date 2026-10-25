# Architecture

## Three-layer target — 2026-10-25

Current code still bundles workflow state and terminal presentation. The approved
target extracts one canonical workflow controller into external Autopilot and
terminal presentation into separate Lantern (working name). OVCAQ owns headless
session/process orchestration, mixed-driver collaboration, execution records and
the public operations API. Standalone Autopilot uses the same controller with
manually started isolated sessions. The TUI accesses only OVCAQ's API.

Workflow extraction precedes consumer activation; the operations API precedes
external UI integration; installed parity precedes removing bundled Textual/Rich
and automatic attach. Existing behavior remains required under its new owner.
The sections below describe the current implementation, not permission to retain
two workflow writers or to remove code before extraction acceptance.


OVCAQ is a Python CLI/TUI with one durable state writer. Lifecycle decisions use
committed state and normalized session results. Agent messages are observations,
not transition authority.

| Boundary | Responsibility |
| --- | --- |
| `src/ovcaq/state/` | Schema, locked transactions, compound mutations |
| `src/ovcaq/workflow/` | PRD selection, transitions, policy, recovery records |
| `src/ovcaq/runtime/` | Process ownership, supervision, registry, evidence |
| `src/ovcaq/drivers/` | Provider-specific launch, health, decoding |
| `src/ovcaq/events/` | Normalized observations and session reduction |
| `src/ovcaq/tui/` | Presentation of shared models and lifecycle controls |
| `src/ovcaq/provision/` | Reserved boundary; plugin reconciliation is planned |

Raw session output survives normalization. Provider details stay in drivers.
Configured commands are argv arrays executed without shell evaluation. The TUI
observes shared models rather than implementing lifecycle or liveness policy.

Protocol details live in the [state](../../state-protocol.md),
[driver](../../driver-protocol.md), and generated
[operations](../../operations.md) references.

PRD buckets remain the workflow authority. Moving them to spec bundles requires
compatible runner, recording, recovery, review, and cleanup consumers first.
