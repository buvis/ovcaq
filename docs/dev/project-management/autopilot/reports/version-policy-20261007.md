# Codex reviewed-version policy — 2026-10-07

Retain an exact reviewed-version guard. Replace supported 0.160.0 with 0.160.1
only after characterization verifies installed CLI flags and official tagged
schema/producer compatibility. Do not accept arbitrary patches or suffixes.

## Evidence and limitations

- `src/ovcaq/drivers/codex.py` compares the first output line exactly with
  `codex-cli 0.160.0`; unsupported versions stop before authentication.
- Existing `tests/fixtures/codex/v1/provenance.json` records real October 4
  0.160.0 version/help captures and explicitly schema-synthetic JSONL families.
  Preserve original captures, source URLs, timestamps, and family hashes.
- [Accepted design](../../designs/00009-codex-adapter-v1-design.md) requires
  refreshing evidence when the installed CLI contract changes.
- Parent-session evidence reports installed `mise exec -- codex --version` as
  `codex-cli 0.160.1`; this assessment did not independently execute it.
- Successfully fetched official [0.160.1 release](https://github.com/openai/codex/releases/tag/rust-v0.160.1):
  tag commit `d27764b`, October 5 release, and one listed fix
  [#51121](https://github.com/openai/codex/pull/51121) retaining Windows remote MCP
  startup environment variables. This suggests compatibility; release prose
  alone does not establish exec CLI/schema/producer equivalence.
- Successfully fetched [tagged exec CLI](https://raw.githubusercontent.com/openai/codex/rust-v0.160.1/codex-rs/exec/src/cli.rs):
  it declares JSONL `--json`, with other options flattened from shared CLI code.
  That file alone does not prove all launch flags.
- Successfully fetched [official CLI reference](https://developers.openai.com/codex/cli/reference),
  redirected to ChatGPT Learn developer commands; exact tags remain authoritative.
- Web comparison retrieval failed. Shell curl failed sandbox DNS; escalation
  waited for approval and was aborted. No full tag delta comparison obtained.
  Parent later fetched 0.160.1 exec schema/producer through web successfully;
  both-version content comparison remains an implementation prerequisite.

**Compatibility remains unverified.** No incompatibility established; absence
of one is not proof. Fail closed if exact-version source review cannot complete.

## Required acceptance

1. Capture read-only version/help; compare tagged CLI/shared options/schema/producer
   for both releases, keeping source snapshots/hashes and compatibility decision.
2. New provenance says existing families were revalidated schema-synthetic
   examples; never relabel October 4 captures as October 7 or claim live JSONL.
3. Offline fake probe accepts exact reviewed 0.160.1 and successful auth; rejects
   old/future/prerelease/suffixed/aliased versions before authentication.
4. R17: real offline subprocess asserts helper-returned stdout/stderr each <=16 KiB
   despite oversized output. Final detail truncation alone cannot prove memory cap.

## Provisioning 00010 implications

This refresh removes only the version preflight blocker. 00010 retains ownership
of authentication readiness, marketplace compatibility, explicit apply, batch
pin/drift enforcement and first real Codex handoff/agoge smokes. No inference,
global tooling installation, login mutation, state mutation or provisioning here.
