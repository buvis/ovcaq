# Driver and observation protocol

OVCAQ version 1 separates provider-specific drivers from provider-neutral
observations. The public contracts described here are the implemented exports of
`ovcaq.drivers` and `ovcaq.events`; this document is not a command inventory.

## Driver contract

`AgentDriver` implementations provide:

- `name`, the advertised driver name;
- `default_tiers`, a read-only `Mapping[str, str]` from neutral tier key to
  provider model, required at `DRIVER_API_VERSION` 2;
- `default_prompt(phase)`, the driver's native phase prompt;
- `probe()`, which reports `DriverHealth`;
- `build_launch(request)`, which converts a `LaunchRequest` into a `LaunchSpec`;
- `decode(raw_line)`, which converts one raw line into zero or more
  `Observation` values; and
- `summarize(observations, exit_code)`, which returns a `SessionSummary`.

`LaunchSpec` contains an argv tuple, an environment overlay, a `Path` working
directory, and the raw-output format. The later supervisor deliberately merges
that overlay into its prepared host environment. OVCAQ executes argv directly;
configured commands are never shell-evaluated.

`default_tiers` publishes the models a driver uses for the neutral tier keys
the default phase routes ask for (`ovcaq.config.DEFAULT_PHASE_TIERS` maps
build and done to `standard`, review to `deep`). `ClaudeDriver.default_tiers` maps
`standard` to `sonnet` and `deep` to `opus`. `CodexDriver.default_tiers` maps
both keys to the reserved literal `default`, and `build_launch` omits the `-m`
segment whenever the resolved model equals that literal, which leaves the Codex
CLI on its own configured model.
Both drivers merge as `{**default_tiers, **settings.tiers}`, so a configured
tier always wins and a table that omits a neutral key inherits the driver's
model for it.

A configured table therefore needs only the two neutral keys, plus any
model-name key that a PRD frontmatter floor uses (here `opus`):

```toml
[agents.claude.tiers]
standard = "sonnet"
deep = "opus"
opus = "opus"
```

Extensions expose a `DriverPlugin(api_version, factory)`, where `factory`
implements `DriverFactory`. `discover_drivers` combines built-in drivers with
plugins from the `ovcaq.drivers` entry-point group. Discovery validates the
advertised name, rejects duplicate names (`DuplicateDriverError`), rejects
construction or health failures (`DriverDiscoveryError`), and requires the
plugin API version to equal `DRIVER_API_VERSION`, currently `2`. A different
version is rejected with `IncompatibleDriverError`; version negotiation is not
performed.

The CLI foreground launch path calls the selected driver's `probe()` before
running the supervisor. Both native adapters locate executables using the
effective host environment plus the configured overlay, including `PATH`.
An absent configured `PATH` inherits the host lookup behavior: a missing host
`PATH` uses the standard default search path. With an empty host `PATH`, the
Claude probe is unhealthy; only the Codex subprocess probe searches the current
directory. `AgentSettings` rejects an empty configured `PATH`.
Unhealthy executable, version or authentication evidence rejects the launch
with a bounded, sanitized runtime error before phase execution.
Directly constructed supervisors do not probe their injected drivers.

`DriverFactory` is a zero-argument callable, but a registration may use a
closure to capture configuration and the per-run identifier, for
example `lambda: ClaudeDriver(settings, run_id=run_id)`, where the caller
supplies `run_id`. A decoder has mutable session state, and the supervisor
reuses its driver between sessions. `build_launch` must reset session-local
decoder state while retaining the supplied run identifier. Codex resets its
thread identity, cumulative usage and remembered item/lane identities. A new
session must not inherit earlier usage or failure evidence; summarization uses
the supplied observations, not stale private decoder fields.

Before OVCAQ 1.0, driver ABI and observation-protocol changes may require
coordinated upgrades of core and extensions. Compatibility is deliberately
strict: there are no compatibility shims or dual writers.

## Observation contract

`PROTOCOL_VERSION` is exactly `1`. An `Observation` has a validated UTC
timestamp and identifiers, an `ObservationType`, and a deeply immutable
payload. Observation identifiers, payload strings and keys, and summary
identifiers and failure details reject surrogate code points (`U+D800` through
`U+DFFF`) with `ValueError` before redaction or truncation. `sanitize_json`
performs the same recursive check, including values under sensitive keys;
redaction cannot conceal invalid Unicode. Valid Unicode scalars, including
non-BMP characters, remain accepted. Version 1 observation types are:

- `session.started`, `session.completed`, and `session.failed`;
- `activity.message`;
- `tool.started`, `tool.completed`, and `tool.failed`;
- `lane.started`, `lane.progress`, `lane.completed`, and `lane.failed`;
- `usage.updated`;
- `rate_limit.started` and `rate_limit.cleared`; and
- `raw.unknown`.

During supervised decoding, envelope `run_id` and `session_id` identify the
owning OVCAQ run and session. Before rebinding those IDs, the raw-first decoder
retains each startup observation's original session ID in its sanitized
`source_session_id` payload field. Reduction compares that normalized source
identity independently of envelope ownership: distinct startup identities
produce an `unknown` failure even with terminal completion or a nonzero exit;
repeated identical startup identities do not. Raw and normalized evidence are
retained. This uses observation protocol 1 and driver API 2 unchanged.

A `rate_limit.started` payload has exactly `reset_at` (an RFC 3339 UTC string
or null), `window` (a text limit-window label or null), and `detail` (text).
A provider `allowed_warning` arrives as `activity.message` with payload `kind`
`rate_limit_warning` plus `window`, `reset_at`, and `detail`, and never as
`rate_limit.cleared`. A terminal banner reset applies unless a rejected event
with a credible future reset is still live (not cleared by a later `allowed`).
A later rejected event without a credible reset ends that live limit, so a
banner after `rejected(R) -> rejected(no reset)` applies its own reset. A dated
banner picks its year first (the anchor's year, or the next one once that date
has passed) and resolves to no reset when the date is invalid in that year.

`FailureClass` values are `rate_limit`, `connectivity`, `permission`,
`authentication`, `timeout`, `agent`, and `unknown`. `Usage` represents usage
reported by observations. `session_failure_observation` constructs the public
failure observation form.

Each adapter classifies its own terminal prose, and the two matchers differ.
Claude's `_FAILURE_MARKERS` is an ordered table of lowercased substrings,
tried as permission, authentication, rate limit, connectivity, then timeout;
the first class with any matching substring wins, a string detail that matches
nothing is `agent`, and a non-string detail is `unknown`. It now also carries
`oauth`, `token has expired`, `token expired`, `expired token`,
`not logged in`, `http 401` and `status 401` for `authentication`; `rate limit`,
`rate-limit`, `rate_limit`, `too many requests`, `http 429` and `status 429`
for `rate_limit`; and `econnreset`, `econnrefused`, `etimedout`, `eai_again`
and `getaddrinfo` for `connectivity`. Because the match is a plain substring,
`HTTP 4290` classifies as `rate_limit`.

Codex's `classify_failure` instead wraps each class alternation in `\b(?:...)\b`
and searches case-insensitively, trying authentication, permission, rate limit,
connectivity, timeout, then agent, and returning `unknown` when none matches.
Its authentication alternatives now include `oauth`, `token (?:has )?expired`
and `expired token`, and its connectivity alternatives now include `econnreset`,
`etimedout`, `econnrefused`, `enotfound`, `getaddrinfo` and `eai_again`.
Because of the word-boundary wrapper, `HTTP 4290` stays `unknown` (the digit
breaks no boundary after `429`), and a marker glued into a longer identifier
such as `econnreset_handler` stays `unknown` too.

Use `observation_record` and `observation_from_record` for the serialized
observation representation. `sanitize_text` and `sanitize_json` redact
credential-shaped keys and credential assignments. Unknown previews are
bounded. A preview of a frame longer than its 512-byte window is cut back to
the last whitespace; a window with no whitespace previews as empty when it
contains `sk-` (case-insensitive) and is kept otherwise. A frame's trailing CR
never reaches the preview. Malformed, oversized, unknown, or decoder-failing
frames produce `raw.unknown` observations with bounded sanitized previews and
SHA-256 evidence. The raw-first decoder rejects invalid UTF-8 and checks parsed
native JSON strings and keys recursively for invalid Unicode scalars before
calling the driver. An invalid native string becomes a raw gap before the
driver can mutate thread, usage, item, or lane state. Later valid frames can
still complete the session; a gap alone is not a session failure.

This recovery boundary covers input and ordinary driver decode exceptions.
Raw evidence write/flush errors, normalized observation publication errors,
and process-control exceptions propagate rather than becoming raw gaps. In
particular, failure to publish a gap remains fatal and triggers cleanup of the
live child; it must not be treated as recoverable input damage.

`reduce_session` retains the observations and deterministically produces a
`Reduction` containing a `SessionSummary`. `summary_record` serializes that
summary. Summaries report outcome, failure, reset, and usage information; they
never select workflow phases. Provider-native data never enters workflow state.
Lifecycle decisions use committed state and normalized results, not prose or a
summary choosing the next phase.

Every `usage.updated` observation is a cumulative snapshot for its session,
never a per-turn delta. Message-derived totals are estimated; a terminal result
snapshot is exact and contains only fields reported by the provider. Reduction
merges each numeric field independently by maximum, including cost, so duplicate
and out-of-order snapshots cannot reduce or double-count totals. An exact
snapshot clears `estimated` only for winning values it exactly replaces; the
aggregate remains estimated while any fieldwise maximum has no exact
replacement.

## Codex exec contract

The supported evidence pin is **codex-cli 0.160.0**, with raw format
`codex-exec-json-v1`. The [versioned provenance](../tests/fixtures/codex/v1/provenance.json)
distinguishes captured version/help stdout from schema-synthetic JSONL. Captured
help replaces the generic launcher-home config directory with `[LAUNCHER_HOME]`;
provenance records this artifact-safety substitution. Its
official sources are the pinned [exec event schema](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/exec/src/exec_events.rs)
and [JSONL producer](https://github.com/openai/codex/blob/rust-v0.160.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs).
The fixtures are not live workflow or authentication transcripts, and fake
phase execution is not an external-plugin smoke test. Future native records
may remain raw-only rather than silently extending this contract.

### Launch and configuration

`CodexDriver(settings: AgentSettings, *, run_id: str)` accepts only `sandbox`,
`approval` and `allow_explicit_model` options. Sandbox and approval default to
`workspace-write` and `never`; other values or wrong types fail with
`ValueError`. `allow_explicit_model` defaults to `False` and must be a bool.
Unknown options fail. Configuration stores the command as an argv tuple,
including any wrapper prefix arguments.

The launch order is exactly:

```python
argv = (
    *settings.command,
    "--ask-for-approval",
    "never",
    "exec",
    "--json",
    "--sandbox",
    "workspace-write",
    "-C",
    str(request.root),
    # Optional model segment:
    "-m",
    resolved_model,
    # Optional mapped effort segment (high example):
    "-c",
    'model_reasoning_effort="high"',
    "--",
    request.prompt,
)
```

An absent model omits its segment. The supervisor resolves the selected model
once, and the driver built by `build_driver` preserves that resolved value even
when it also matches a configured tier key. Direct `build_launch` requests retain
tier-key precedence: a configured tier resolves through `settings.tiers`; an
already resolved tier value is accepted unchanged. An arbitrary explicit model
requires `allow_explicit_model=True`. Shared modules provide no provider model
default. Absent effort omits its segment. `low`, `medium`, `high` and `xhigh` map
identically to `model_reasoning_effort` with a quoted TOML value. Blank effort
fails; another nonblank value logs one warning containing the requested value
and omits the override without guessing.

`LaunchSpec.cwd` is `request.root`; its environment is a copy of the configured
overlay, without provider-specific host-variable or credential copies. The
launcher manages inherited authenticated storage. `build_launch` neither
spawns nor provisions. The shared runner closes stdin and spawns without a
shell; wrapper arguments and prompt shell syntax remain literal data. The
final `--` also protects prompts beginning with `-`. Runtime enforces the
request timeout without another CLI flag.

### Decoding and terminal evidence

Codex observations use protocol 1, provider `codex`, the supplied run ID and
current thread as session ID before supervised ownership rebinding. The native
thread ID then survives in startup `source_session_id` payloads. Pinned native
records have no timestamp, so the adapter uses aware UTC receipt time.
Validated observations contain normalized,
sanitized payloads. Malformed JSON (including recursion errors), wrong shapes,
unsupported item kinds/statuses and future records fall back to `raw.unknown`
with an original-line SHA-256, sanitized preview of at most 512 characters and
a bounded reason. Raw evidence remains available even when projection fails.

| Native evidence | Normalized projection |
| --- | --- |
| `thread.started` | `session.started` with thread identity |
| `turn.started` | `activity.message`, kind `turn` |
| Agent/reasoning items | `activity.message`, kind `text`/`thinking`, bounded text and item ID |
| Command/file/MCP/web items | Tool lifecycle with item ID as `tool_id`, neutral name and bounded detail |
| Todo items | `activity.message`, kind `plan`, bounded steps |
| Collaboration items | Tool lifecycle and receiver-attributed lane evidence when available |
| Nonfatal error item | `activity.message`, kind `error`; no session failure |
| `turn.completed` | `usage.updated` and `session.completed` |
| `turn.failed` | `session.failed`, plus `rate_limit.started` when classified |
| Top-level `error` | Provisional error activity with normalized failure metadata |

The adapter recognizes `item.started`, `item.updated` and `item.completed`.
Tool failure requires native failure/decline status, explicit native error or
nonzero command exit. Ordinary command output is not provider-health evidence.
File detail summarizes paths and change kinds; MCP and web detail is sanitized
and bounded to 4096 characters, rather than retained as wholesale results.
Codex diagnostic details processed by `bounded_detail` redact credentials before
and after removing recognized C0 controls (except tab, LF and CR), DEL and 7-bit
CSI sequences, then apply the 4096-character bound. Lone ESC is masked as a
removable control before redaction so a new redaction marker cannot become CSI.
This preserves original credential boundaries and redacts tokens reconstructed
by those recognized forms before truncation. Broader display-time character
removal is outside this diagnostic-helper contract.

Collaboration requires `agents_states` keys matching native receiver thread
IDs. Pending/running receivers start or progress a lane, completed receivers
complete it, and errored receivers fail it. Remembered completed and failed lanes
remain terminal under late receiver updates. Late pending/running, completed and
errored updates for terminal lanes do not emit lane observations.
Interrupted, shutdown and not-found receivers emit `lane.failed` only for
remembered unfinished lanes; these close statuses for terminal or unstarted
receivers, and missing attribution, remain raw unknown evidence.
Lane payloads supply `label` and bounded `detail`; a completed collaboration
tool does not prove receiver completion.
The checked-in `lanes.jsonl` deliberately mismatches these identities and
therefore supplies raw missing-attribution evidence, not successful lanes.
The separate checked-in `lanes-matched.jsonl` uses matching receiver/state IDs
to demonstrate attributed running-lane evidence. Both fixtures are
schema-synthetic, not live provider smoke evidence or OVCAQ task correlation.
At most 4096 item/lane identities are remembered; eviction prefers the oldest
terminal identity, then the oldest identity, and emits a visible raw gap.

`summarize` consumes its supplied iterable once. If native terminal evidence
exists, it returns the shared reduction summary unchanged. Otherwise the latest
top-level provisional error's normalized metadata supplies a synthetic
`session.failed` to reduction, plus `rate_limit.started` when applicable. This
does not mutate workflow state or parse native prose in shared code. A recovered
error followed by completion adds no synthetic failure or rate limit. With no
terminal or provisional error, the shared reducer remains authoritative;
zero process exit alone does not prove success. Conflicting thread identities
remain represented and reduce to unknown failure rather than merged success.
Each valid thread header emits exactly one `session.started`. A conflicting
header resets usage and queues a raw gap for the next `turn.completed`, using
that completion record's digest and sanitized preview.

The diagnostic "Selected model is at capacity" is classified as `connectivity`
and uses the supervisor's bounded WAIT/retry policy, including retry exhaustion.
Genuine rate or quota limits retain `rate_limit` precedence. Numeric diagnostic
codes require HTTP, status or error context (for example `HTTP/2 503`, `status=429`,
`Error 401:`); ordinary counts alone remain `unknown`. Existing rate-limit reset
parsing is unchanged.

### Usage and unknown telemetry

Normalized input excludes separately counted cache reads/writes, matching the
Claude adapter. Native input includes cached input. With valid inclusive input,
cache read and an explicit zero cache write, normalized input is inclusive
input minus cache read. Native `120 input / 100 read / 0 write / 30 output`
therefore becomes `20 input / 100 read / 0 creation / 30 output`.
Reads exceeding inclusive input produce unknown uncached input and a raw gap.
Positive cache writes expose their native value as cache creation and retain
valid cache reads, but leave uncached input unknown with a partition gap and
`estimated=True`: the pinned schema does not establish the write partition.
Missing/invalid partition components also leave uncached input unknown.

Counters are validated individually as nonnegative integers, rejecting bools,
floats, nonfinite and wrong-shaped values. Valid components survive malformed
neighbors; omitted components remain unknown and malformed supplied usage emits
a raw gap. Reasoning tokens are not added to output again. `cost_usd` and
`tool_uses` remain `None`, without inferred prices or invented zeroes. Inclusive
native totals survive in private raw evidence only.

The pinned producer's `usage_from_last_total` reads thread-cumulative totals.
Codex takes fieldwise maxima across validated normalized snapshots for that
thread, never sums terminal snapshots: native input snapshots 100 then 200
yield 200, not 300. Replays, out-of-order completions and additional turns do
not change that arithmetic or require a turn ledger. Usage identity is
`thread:<id-or-unknown>` and is observational only. Known counters are exact
unless a partition gap marks them estimated; unknown fields remain `None` and
gaps remain visible. Default all-zero native telemetry yields unknown fields
and an absence gap; a later zero snapshot cannot reduce earlier known maxima.

### Native phase prompt and projection

`default_prompt` accepts exactly `build`, `review` and `done`, rejecting other
phases with `ValueError`. It returns this literal native invocation and contract:

```text
$run-autopilot
Read the committed OVCAQ state to determine the current phase. Use `ovcaq state`
and `ovcaq workflow` commands for all durable mutations. Perform only the
current phase, commit exactly one successful phase handoff through the OVCAQ
workflow command, then exit the session. Never edit state.json directly. Do not
start a second phase in this session. Completion is determined by committed
state, not your final message. Do not install, upgrade, or modify launcher
plugins or marketplace content.
```

The external skill must expose the native name `run-autopilot`. A different
installed name requires an explicit verified phase prompt override.
`AgentSettings.prompts` are literal supervisor overrides subject to the same
handoff contract; the driver does not embed skill files or open plugin caches.
State transitions determine successful handoff and phase completion. One
launched session performs one phase and exits after one successful committed
handoff, with no second-phase work in that session.

`ProjectObserver` and panels consume normalized observations and metrics to
show provider identity, attributed lanes and exact/estimated usage. Normalized
tool lifecycles and text, thinking, error, warning and plan activity render
alongside lanes. Tool names persist through terminal events that omit them;
tool details come from normalized `detail`. Messages prefer non-null `text`
(including an empty string), falling back to `detail` only when `text` is absent
or null. Plans join steps with `done:`/`pending:` markers into a detail summary
bounded to 512 characters, including an ellipsis when truncated. Activity
is restricted to the selected run and session and retains at most 256 identities;
message updates use their full IDs, while messages without IDs remain distinct.
The panel shows the newest 20 activity entries newest-first, then at most the
first 20 lanes, with separate omission counts. Details remain bounded literal
text without interpreting markup.
Unavailable cost is unknown or omitted. Unsupported fields and
normalization gaps retain raw-only visibility; out-of-order lane progress can
remain unknown.
Native receiver IDs do not establish OVCAQ task correlation. The TUI adds no
provider parser, model names or lifecycle policy.

## Evidence and permissions

Session output is raw-first: OVCAQ writes and flushes each raw record before
framing or decoding it. Normalized JSONL contains only validated, sanitized
observations. The private raw file preserves the provider-native evidence needed
for recovery and debugging after a host crash, including records that could not
be decoded.

Raw output can contain provider-native content or credentials. Its file mode is
`0600`; access must remain restricted to the operator account. Sanitization of
normalized data does not make the raw evidence safe to share.

Claude v1 accepts only `permission_mode="auto"`. A missing or unsafe permission
mode is a configuration failure. A runtime failure classified as `permission`
is an operator alert, not an instruction for the workflow to change phase.

## Operator runbook

When a session fails or becomes unknown:

1. Read the normalized `SessionSummary` and observations to identify the outcome
   and `FailureClass`.
2. If decoding is incomplete, inspect the session's private raw evidence as the
   operator account. Keep it restricted because it may contain credentials.
3. Treat `permission` failures as alerts. For Claude, confirm the configured
   permission mode is exactly `auto`; do not weaken the mode to force progress.
4. Correct the relevant configuration, credentials, connectivity, or extension
   version. An API-version mismatch requires coordinated upgrades, not a shim.
5. Retry through the applicable lifecycle command. Never edit `state.json`
   directly, and never infer or choose a phase from an agent message or summary.

The public driver surface is `DRIVER_API_VERSION`, `AgentDriver`,
`DriverDiscoveryError`, `DriverFactory`, `DriverHealth`, `DriverPlugin`,
`DuplicateDriverError`, `IncompatibleDriverError`, `LaunchRequest`, `LaunchSpec`,
and `discover_drivers`. The public event surface is `PROTOCOL_VERSION`,
`FailureClass`, `Observation`, `ObservationType`, `Reduction`, `SessionSummary`,
`Usage`, `observation_from_record`, `observation_record`, `reduce_session`,
`sanitize_json`, `sanitize_text`, `session_failure_observation`, and
`summary_record`.
