# Discovery: Environment Provider contract (Ponks and Seats)

## Classification

Depth: minimal | Date: 2026-11-04 | Status: open (idea, moved from buvis/docs)

Source: `buvis/docs` `src/agents/components.md` (OVCAQ environment paragraphs
and the Koolna target) and `src/agents/taxonomy.md` (section "Ponks and
Seats"), moved on 2026-11-04 so the public reference keeps only vocabulary and
ownership. Terms (Ponk, Seat, Toolset, Workspace, Execution Boundary, Leg,
Dispatch) follow the
[agent operations taxonomy](https://github.com/buvis/docs/blob/master/src/agents/taxonomy.md).

## Problem

OVCAQ launches sessions on the local machine today. The target architecture
schedules work through a provider-neutral Environment Provider contract:
OVCAQ schedules against capabilities and capacity, requests Seats, and uses
the access the provider supplies. Environment location and deployment
mechanics belong to the provider; OVCAQ does not provision Kubernetes
resources or configure local environments. Koolna (`container-images`) is
the Kubernetes provider, but its repository-oriented environment model does
not yet establish Seat isolation, and no local provider is specified. Neither
side of the contract exists.

## Requirements

### Must have (from buvis/docs)

Provider contract:

- A provider exposes capabilities, capacity, Toolsets, Seat allocation,
  access, and its isolation guarantees through one contract. The same
  scheduling logic applies regardless of where an environment runs.
- Dispatch schedules against available resources and compatible Toolsets.
  Seats need not consume equal resources or require a fixed slot model.
- Parking retains workflow state and the required workspace data, but may
  release compute and its Seats. Resuming revalidates or allocates the
  required Seats. Completion releases execution capacity; workspace retention
  is a separate cleanup policy.
- Each concurrently running Agent uses a separate Seat. A Flight's concurrent
  Legs therefore use separate Seats and isolated workspaces. Seats allocated
  to a Flight are not shared with other Flights during that allocation.
- Successive Legs may reuse a Seat when its context, files, credentials, and
  processes meet the next assignment's isolation requirements. Reuse never
  carries the previous Agent's identity or bypasses a required fresh context.
  Reviewers receive only the evidence their review policy permits. A resumed
  Flight may use different Seats.
- Repository storage may be shared only when it preserves the required Seat
  isolation. Linked worktrees share Git metadata; cloning once per Ponk is
  an optimization, not a requirement.
- Seat isolation is enforced, not inferred from a UI label. A local sandbox
  with access to other Flights' files must not claim cross-Flight isolation.
- Local machines and Kubernetes are target environments. A Ponk need not map
  to one pod. A Seat can serve successive sessions, with only one Agent active
  at a time. Choose the deployment from the required isolation.
- Record the Toolset revision used by each Leg. Updates must not silently
  change active Legs; apply them at a safe boundary or drain the environment.

Provider obligations (Koolna today, a local provider later):

- Organize environments into Ponks and isolated Seats. Deployment granularity
  follows the required isolation and capacity.
- Verify filesystem, credential, process, network, and resource boundaries
  before claiming isolation.

### Out of scope

- Koolna's provider implementation; it belongs to `container-images` once the
  contract is fixed.
- Plugin provisioning into sessions (PRD 00010).

## Constraints

- OVCAQ owns execution and keeps provider code at the edge (AGENTS.md
  invariants 3 and 4).
- Standalone Autopilot starts isolated sessions in an available workspace
  without any provider; the contract must not become a prerequisite for that
  mode.

## Open Questions

- Q: Does the contract need to exist before a second provider does? There is
  one target provider (Koolna) with Seat integration pending and no local
  provider, so today it is an interface with zero implementations. The local
  case (`run-agent` Seatbelt sandbox plus Git worktrees) is the daily one and
  may come first, with the contract extracted from two working providers.
- Q: Which repository owns the contract definition: OVCAQ as consumer, or a
  shared package?

## Discovery Log

### Q1: Where does this come from?

**Answer**: The buvis/docs agent operations pages (draft dated 2026-11-02)
carried these requirements in the public component reference and taxonomy.
The 2026-11-04 review moved spec-shaped content into owning repositories;
the docs keep the domain table, glossary, and ownership rows.
