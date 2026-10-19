# Characterization fixture provenance

These standalone fixtures retain behavioral field shapes without requiring a live personal directory. Copied-and-sanitized legacy evidence preserves selected state and metric shapes from the personal run-autopilot runtime. Synthetic provider contract seeds model only the event shapes needed to bootstrap later adapter work; they are not captured transcripts.

| Filename | Source kind | Logical source | Captured/derived | Sanitization | Intended later consumer |
| --- | --- | --- | --- | --- | --- |
| `claude/session.jsonl` | Synthetic provider contract seed | personal run-autopilot runtime, `scripts/test_render_stream.py` | 2026-08-25 | Recreated representative event shapes with example identifiers, values, and command | Claude event adapter characterization |
| `codex/session.jsonl` | Synthetic provider contract seed | accepted implementation plan, section 2.4 | 2026-08-25 | Recreated documented event shapes with example identifiers, values, and command | Codex event adapter characterization |
| `claude/legacy-state-build.json` | Copied-and-sanitized legacy evidence | personal run-autopilot runtime, `scripts/golden/state-build-pending.json` | 2026-08-25 | Replaced PRD, batch, task identifiers, and task names while retaining lifecycle fields | State-kernel and workflow transition characterization |
| `claude/legacy-state-review.json` | Copied-and-sanitized legacy evidence | personal run-autopilot runtime, `scripts/golden/state-review-cycle2.json` | 2026-08-25 | Replaced PRD, batch, task identifiers, and task names while retaining lifecycle fields | Review-cycle workflow characterization |
| `claude/legacy-state-converged.json` | Copied-and-sanitized legacy evidence | personal run-autopilot runtime, `scripts/golden/state-review-converged.json` | 2026-08-25 | Replaced PRD, batch, task identifiers, and task names while retaining lifecycle fields | Review-convergence workflow characterization |
| `claude/legacy-metrics.jsonl` | Copied-and-sanitized legacy evidence | personal run-autopilot runtime, `cli/golden/metrics-render.jsonl` | 2026-08-25 | Reduced to two session rows and one convergence row; replaced dates, identifiers, names, and measurements | Metrics and TUI model characterization |
| `workflow/reports/deferred.json`, `workflow/reports/expected/*.md` | Migrated-and-normalized workflow render goldens | personal run-autopilot `cli/golden/` reporting fixtures | 2026-09-02 | Recast against committed v1 state and normalized deferred records; removed provider/runtime-only fields | Audit, replaceable batch report, and metrics equivalence |

Later provider PRDs refresh and extend event fixtures from controlled captures. They must remain standalone and sanitized.

## Codex v1 matrix

`codex/v1/` pins `codex-cli 0.160.0`. Version/global help/exec help are
read-only local CLI captures from 2026-10-04 (stdout; environment-specific
stderr warnings omitted).
The captured help substitutes `[LAUNCHER_HOME]` for the generic tilde-prefixed
launcher directory in the config path; provenance records the exact recipe.
JSONL files are **schema-synthetic**, not captured sessions: no safe controlled
transcript was supplied and no model was launched.
[Versioned provenance](codex/v1/provenance.json) records pinned official Rust
schema/producer URLs, per-family SHA-256 hashes, sanitization, and unsupported
fields.

| Family | Coverage |
| --- | --- |
| `healthy.jsonl` | Reasoning, assistant text, warning item, top-level error followed by success, full native usage |
| `tool-active.jsonl` | Commands, file changes, MCP, web actions/results, todo start/update/completion and native status variants |
| `lanes.jsonl` | Native collaboration tools with mismatched receiver/state IDs; raw missing-attribution evidence and absent telemetry encoded as native default zero usage |
| `lanes-matched.jsonl` | Checked-in native collaboration example with matching receiver/state IDs; attributed running-lane evidence and absent telemetry encoded as native default zero usage |
| `rate-limited.jsonl` | Synthetic rate-limit error and identical terminal failure |
| `connectivity-failed.jsonl` | Synthetic connectivity error and identical terminal failure |
| `permission-failed.jsonl` | Declined command and synthetic permission failure pair |
| `authentication-failed.jsonl` | Synthetic authentication failure pair with redaction sentinel |
| `malformed.jsonl` | Unknown fields/types, missing/wrong fields, legacy usage shape, depth 32, replay, redaction and truncated JSON |

Failure messages are examples, not captured provider diagnostics. The native
schema provides no authoritative OVCAQ task/lane correlation, cost or rate-limit
telemetry; these gaps are explicit in each family's provenance. Receiver lanes
require matching native receiver IDs and `agents_states` keys. The mismatches in
`lanes.jsonl` cannot prove successful lanes; the separate checked-in
`lanes-matched.jsonl` supplies schema-synthetic attributed lane coverage, not
live provider smoke evidence or authoritative OVCAQ task correlation. Default
zero usage is not measured zero consumption. `malformed.jsonl` intentionally
contains invalid records; the other families use the pinned schema. The older
`codex/session.jsonl` remains an
unversioned synthetic compatibility seed, including its missing usage fields;
it is not installed-version evidence. Offline integrity checks live in
`tests/drivers/test_codex_fixtures.py` and never inspect launcher homes.

## Codex conformance evidence and limits

The [driver protocol](../../docs/driver-protocol.md) describes driver API 2,
observation protocol 1, and the pinned launch/decoding contract. Fixture and fake
execution exercise build/review/done with the native `$run-autopilot` prompt,
literal configured overrides, and OVCAQ CLI state handoffs: one successful
committed handoff per session, no second-phase work, and no direct `state.json`
edits. Fake execution uses temporary launcher homes and no real model,
authentication storage or plugin mutation. It is not a live external-skill smoke
test; launcher skills and plugins remain external.

Native usage is thread-cumulative. Normalized snapshots take fieldwise maxima,
never sum turns, and exclude separately counted cache reads from input when the
cache-write count is explicitly zero. Missing/invalid partition counters,
positive cache writes and absent all-zero telemetry leave uncached input unknown
with visible normalization gaps; positive writes mark usage estimated. Cost and
tool-use counts remain unknown. Reusing a driver resets its session-local thread,
usage and remembered identities at launch while preserving its run ID.

The activity panel renders normalized tool lifecycles, messages (including text,
thinking, errors and warnings), plan steps and attributed lanes as literal text.
Messages use `text` when non-null, including an empty string, otherwise `detail`;
plans show `done:`/`pending:` step markers, and tools show normalized detail.
The newest 20 activity entries appear newest-first, followed by at most the
first 20 lanes, with separate omission counts. Unsupported records and telemetry gaps
remain visible through bounded sanitized `raw.unknown` observations. Raw
original session output is private evidence and may contain credentials;
normalized sanitization does not make it safe to share. Fixture examples do not
establish captured live diagnostics or measured consumption.
