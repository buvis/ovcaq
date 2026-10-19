# Architecture

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
