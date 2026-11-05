# Autopilot controller, headless OVCAQ and separate Tower

Status: target architecture revised 2026-10-25 at the user's request. This replaces the previous OVCAQ-only workflow writer and bundled-TUI design. Current code has not yet been extracted.

The [canonical three-layer design](../../../../../agent-plugins/docs/dev/project-management/designs/00011-autopilot-standalone-design.md) specifies ownership, all three contracts, failure semantics, delivery graph and cutover gates.

| Owner | Responsibility |
| --- | --- |
| External Autopilot package/controller | Skills, hooks, personas, semantic review preparation; one workflow writer, lifecycle/tasks/lanes/review/custody/verification and record-store commits |
| OVCAQ | Agent-neutral job placement, session/process ownership, mixed-driver collaboration, retries, waves/worktrees, normalized observations and public operations API |
| Tower | Separate Textual/Rich client of OVCAQ; presentation and operator intent only |

Standalone Autopilot is stateful and manually driven between isolated sessions. It uses exactly the same controller as OVCAQ. OVCAQ never bundles plugin content or controller implementation. The controller never spawns coordinators. Tower never imports OVCAQ internals or accesses workflow/registry files.

## Contract ownership

AP00018 owns controller CLI schemas/fixtures/export; AP00019–00021 implement lifecycle/jobs, review/lanes/evidence and record commits. OV00057 consumes the explicit argv/bundle; OV00058 removes the old writer only after installed equivalence. Retain cf8be72 transition/recovery fixes and reconcile OV00062 startup revert before removal. No dual-write mode or importer.

OV00059 owns role-to-driver placement and context isolation. Codex build followed by fresh Claude review is mandatory acceptance, with blind inputs excluding builder narrative. OV00060 owns process/claim reconciliation and headless execution. Controller outages stop new scheduling but never prevent OVCAQ from stopping owned processes. OV00061 owns wave/worktree mechanics; semantic acceptance stays in controller.

User decision, 2026-10-25: Claude-free certification uses Codex + Gemini. OV00059 adds the Gemini driver and actual-provider diversity checks; Codex implements and Gemini supplies the independent doubt voice, including Eve when required. Every resolved role preserves the controller's roster, availability rules and isolated contexts. OV00060 proves real build/review/rework/complete/records/next-PRD/drain without Claude runtime/configuration/credentials or source checkout; AP00017 verifies these managed receipts and its independent standalone certificate. Missing capabilities remain uncertified. Codex-only and Codex-build/Claude-review do not satisfy this gate.

OV00064 owns operations list/snapshot/events/control schemas and public projection. Exact command/envelope/cursor/control semantics are in canonical Contract C. It can develop beside00059/00060 after00058. Shared CLI/config edits must be serialized. Tower00001–00003 consume exported fixtures then installed artifacts. OV00065 removes bundled UI, Textual/Rich dependencies and automatic attach after client parity. No HTTP daemon or broker is required.

## Prerequisites and compatibility

Read-only tools/autopilot-prerequisites is created by00057. Local predecessors must be in done. Cross-repository prerequisites require explicit configured artifacts, installed capability probes and matching producer/digests; never sibling imports or implicit discovery. Configuration: [workflow].controller_argv and contract_bundle; [autopilot].plugin_artifact for00061; [operator].client_artifact for00065. Exit0 ready /1 unavailable, bounded probes, no fetch/write. The old AUTOPILOT_OVCAQ_BIN plugin prerequisite and OVCAQ-owned workflow schema export are superseded.

OV00062/00063 remain unchanged robustness work. AP00016/00017 can finish without OVCAQ. The controller is Python3.12; OVCAQ remains Python3.12. All process/git/workflow tests use temporary roots, never the implementation batch's state. Fake-driver evidence and actual host capability certification remain distinct.

## Cutover

The 2026-10-25 completeness correction also requires AP 00012's independent source inventory and per-behavior/regression evidence map. Assigned owners, preserved headings and unavailable profiles do not satisfy retirement. Review evidence carries explicit clean or failed reviewer results, current input bindings and actual native-job provenance; findings alone do not prove a reviewer ran. The old AP 00012 design approval is superseded by its corrected contract.

Held00010 provisions external portable Autopilot and tests controller compatibility; it bundles neither controller nor TUI. Agoge remains required as previously specified. Held00011 requires standalone, same-controller supervised, mixed-driver, waves and separate-TUI canaries plus every drift disposition. Held00014 verifies independently versioned artifacts. Existing source task IDs and review requirements remain. Source retirement is now tracked by claude-autopilot held PRD 00370, after all required evidence and consumer cutover receipts. No hold, publication, live installation or source retirement is activated here.

## Unresolved questions

None blocking architecture. Tower is the settled name since 2026-11-05; branding does not alter the protocol.
