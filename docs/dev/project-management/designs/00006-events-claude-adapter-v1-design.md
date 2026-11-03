# Design: OVCAQ event protocol and Claude adapter

## Architecture fit

Phase 4 fills the already-reserved `ovcaq.events` and `ovcaq.drivers` boundaries without moving lifecycle policy out of `ovcaq.workflow` or process ownership out of `ovcaq.runtime`. The dependency direction remains `events <- drivers <- runtime`: normalized types and reduction are provider-neutral; a driver translates one provider's launch and stream contracts; the later supervisor composes the driver with `OwnedProcess`, `SessionPaths`, and state-led decisions. No event, decoder result, or final agent prose mutates authoritative workflow state.

Raw evidence remains the lossless source. `runtime.session.SessionEvidenceWriter` accepts each byte chunk before any decoder or framer sees it. A bounded Phase 4 framer then emits complete logical lines (plus the final EOF residue), asks the selected driver for zero or more normalized observations, and appends sanitized JSON records to the session's existing `normalized.jsonl`. Unknown, malformed, undecodable, oversized, or future provider lines become `raw.unknown`; they never abort ingestion. The raw file remains byte-identical and mode `0600`, while normalized objects are sanitized at construction so no serializer can bypass redaction.

The clean event protocol and driver plugin ABI both start at version 1. Readers reject future event versions, and discovery rejects a plugin whose declared `api_version` is not exactly the host's `DRIVER_API_VERSION`; there is no best-effort cross-version loading. During pre-stability development, an incompatible change increments the version, requires plugins to publish a matching entry point, and may require a fresh batch. The later public-release PRD may add compatibility ranges and deprecation windows, but version negotiation is never deferred. Phase 4 adds no state migration because provider-native data never enters `state.json`.

## Module placement

- `src/ovcaq/events/model.py` — new immutable normalized value types, closed observation/failure vocabularies, validation, protocol-wide sanitization, deep-frozen payload conversion, and deterministic observation/summary JSON-record conversion.
- `src/ovcaq/events/reducer.py` — new provider-neutral usage accumulator and total session reduction from normalized observations plus process exit code.
- `src/ovcaq/events/tail.py` — new bounded raw-first stream framer and normalized JSONL writer over private session paths; it persists only already-sanitized protocol objects.
- `src/ovcaq/events/__init__.py` — intentional public exports for the version-1 protocol.
- `src/ovcaq/drivers/base.py` — new launch/health protocol types, `AgentDriver`, versioned `DriverPlugin`, and duplicate-/version-safe built-in/entry-point discovery with no provider names or formats.
- `src/ovcaq/drivers/claude.py` — new Claude-only argv/environment builder, health preflight, stream decoder, task/lane attribution, terminal classification, and credible rate-limit parsing.
- `src/ovcaq/drivers/__init__.py` — registers the built-in Claude factory at the provider edge; `base.py` remains neutral. Existing zero-byte `codex.py` and `command.py` remain untouched for their later PRDs.
- `src/ovcaq/config.py` — extend the existing merged user/project agent table reader so model strings and non-secret environment additions come from the selected agent configuration rather than shared routing constants.
- `src/ovcaq/runtime/session.py` — the create-only/private/bounded append mechanics live in `SessionEvidenceWriter`, the only evidence-writer class. Raw and normalized persistence compose that primitive without introducing parallel writer identities.
- `tests/events/{test_model.py,test_reducer.py,test_tail.py}` — protocol validation, total reduction, ordering, redaction, persistence, and malformed/unknown cases.
- `tests/drivers/{test_registry.py,test_claude.py,test_neutrality.py}` — discovery, exact launch/config behavior, fixture decoding, classification, scripted fake execution, and provider-boundary guards.
- `tests/fixtures/claude/*.jsonl` — sanitized, version-named healthy, tool-active, lane/subagent, rate-limited, connectivity/auth/permission/agent-failed, malformed, and unknown streams. Replace the current illustrative fixture only after preserving its covered shape in the matrix.
- `docs/driver-protocol.md` — version-1 observation/driver contracts, raw-first/redaction guarantees, extension-point discovery, and the explicit pre-stability compatibility stance.

## Interfaces & contracts

`src/ovcaq/events/model.py`:

```python
PROTOCOL_VERSION: Final[int] = 1

class ObservationType(StrEnum):
    SESSION_STARTED = "session.started"
    ACTIVITY_MESSAGE = "activity.message"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    LANE_STARTED = "lane.started"
    LANE_PROGRESS = "lane.progress"
    LANE_COMPLETED = "lane.completed"
    LANE_FAILED = "lane.failed"
    USAGE_UPDATED = "usage.updated"
    RATE_LIMIT_STARTED = "rate_limit.started"
    RATE_LIMIT_CLEARED = "rate_limit.cleared"
    SESSION_COMPLETED = "session.completed"
    SESSION_FAILED = "session.failed"
    RAW_UNKNOWN = "raw.unknown"

class FailureClass(StrEnum):
    RATE_LIMIT = "rate_limit"
    CONNECTIVITY = "connectivity"
    PERMISSION = "permission"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    AGENT = "agent"
    UNKNOWN = "unknown"

@dataclass(frozen=True, slots=True)
class Usage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    tool_uses: int | None = None
    cost_usd: float | None = None
    estimated: bool = False

@dataclass(frozen=True, slots=True)
class Observation:
    protocol_version: int
    timestamp: datetime
    provider: str
    run_id: str
    session_id: str | None
    lane_id: str | None
    type: ObservationType
    payload: Mapping[str, FrozenJSONValue]

@dataclass(frozen=True, slots=True)
class SessionSummary:
    success: bool
    session_id: str | None
    failure_class: FailureClass | None
    failure_detail: str | None
    rate_limit_reset_at: datetime | None
    usage: Usage | None

def observation_record(observation: Observation) -> dict[str, JSONValue]: ...
def observation_from_record(record: object) -> Observation: ...
def summary_record(summary: SessionSummary) -> dict[str, JSONValue]: ...
def sanitize_text(value: str) -> str: ...
def sanitize_json(value: JSONValue) -> JSONValue: ...
```

`FrozenJSONValue` is a recursively immutable scalar/tuple/read-only-mapping representation. `Observation.__post_init__` sanitizes, copies, and deep-freezes the payload; `SessionSummary.__post_init__` sanitizes and bounds `failure_detail`. Both serializers call the same sanitizer again as defense in depth. The sanitizer recursively replaces values for case-insensitive keys matching `token`, `secret`, `password`, `authorization`, `api_key`, `cookie`, or `credential`, and replaces only pinned credential-shaped substrings in free text. It is the sole normalized-protocol persistence boundary used by observation construction, `raw.unknown` previews, normalized JSONL, and summary publication. Validation also requires an aware UTC timestamp, a non-empty provider/run ID, protocol version 1, and a lane/session identifier only when non-empty. `Usage` rejects booleans, negative counters, negative/non-finite cost, and `estimated` values other than `bool`. Serialization emits RFC 3339 UTC timestamps and ordinary JSON arrays/objects in deterministic key order; deserialization rejects future versions.

Every `usage.updated` payload has exactly `usage` (a serialized `Usage`) and `identity` (`str | None`). `identity` is a normalized provider event identity used only for deduplication. Every `session.failed` payload has `failure_class` and `detail`. Every `rate_limit.started` payload has exactly `reset_at` (`RFC 3339 UTC str | None`), `window` (`str | None`), and `detail` (`str`). Every `raw.unknown` payload has `reason`, `raw_sha256`, and a redacted/truncated `preview`; it never embeds the unredacted line.

`src/ovcaq/events/reducer.py`:

```python
@dataclass(frozen=True, slots=True)
class Reduction:
    observations: tuple[Observation, ...]
    summary: SessionSummary

def reduce_session(
    observations: Iterable[Observation], exit_code: int
) -> Reduction: ...

def session_failure_observation(
    *,
    timestamp: datetime,
    provider: str,
    run_id: str,
    session_id: str | None,
    failure_class: FailureClass,
    detail: str,
) -> Observation: ...
```

Every `usage.updated` record is a cumulative session snapshot, never a delta. The stateful provider decoder converts per-message snapshots/deltas into that normalized form before emission. Reduction preserves observation order and folds snapshots as follows: an identical non-null `identity` plus identical payload is a no-op; a repeated identity with changed payload and every anonymous/distinct-identity snapshot merges each numeric field by maximum, never addition. `None` contributes no value. Cost is likewise a cumulative maximum. An exact (`estimated=False`) snapshot clears the aggregate estimate flag only when it supplies every currently non-null field at an equal-or-greater value; otherwise the fieldwise maximum remains estimated because some winning value lacks exact replacement. An estimated snapshot never downgrades an exact dominating aggregate. This makes duplicate delivery and out-of-order cumulative snapshots deterministic and monotonic.

Terminal reduction is deterministic. The first non-null `session.started.session_id`, or otherwise the first non-null terminal session ID, binds the stream; a different later non-null session ID makes the summary fail as `unknown` because mixed sessions cannot be trusted. Duplicate equal terminals are idempotent. Across conflicting terminals for the bound session, any `session.failed` wins over every `session.completed`; among failures the last failure supplies class/detail, so a supervisor-appended synthetic termination is authoritative. With completions only, the last completion supplies final usage. Post-terminal activity/lane/tool observations do not change outcome, but later usage still participates in the monotonic fold. A later rate-limit event never turns an explicit completion into failure; it upgrades only a missing terminal or an `unknown`/`agent` failure. `rate_limit.cleared` clears only a prior live limit. Without a terminal, exit code zero yields unsuccessful `unknown`, while nonzero yields `agent`. No branch chooses a workflow phase.

Timeout and signal ownership stay in runtime. When `ProcessExit.timed_out` is true, the later supervisor appends `session_failure_observation(..., failure_class=FailureClass.TIMEOUT, ...)` after stream ingestion and before summarization; cancellation/ownership failures can use the same provider-neutral constructor with their closed class. The events package never imports `ProcessExit` or watchdog code.

`src/ovcaq/drivers/base.py`:

```python
@dataclass(frozen=True, slots=True)
class LaunchRequest:
    root: Path
    phase: str
    prompt: str
    model: str | None
    effort: str | None
    timeout_seconds: int
    session_dir: Path

@dataclass(frozen=True, slots=True)
class LaunchSpec:
    argv: tuple[str, ...]
    env: Mapping[str, str]
    cwd: Path
    raw_format: str

@dataclass(frozen=True, slots=True)
class DriverHealth:
    healthy: bool
    detail: str

class AgentDriver(Protocol):
    name: str
    def probe(self) -> DriverHealth: ...
    def build_launch(self, request: LaunchRequest) -> LaunchSpec: ...
    def decode(self, raw_line: str) -> Iterable[Observation]: ...
    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary: ...

DriverFactory: TypeAlias = Callable[[], AgentDriver]

DRIVER_API_VERSION: Final[int] = 1

@dataclass(frozen=True, slots=True)
class DriverPlugin:
    api_version: int
    factory: DriverFactory

def discover_drivers(
    builtins: Iterable[DriverPlugin],
    *,
    entry_points: Iterable[EntryPoint] | None = None,
) -> Mapping[str, AgentDriver]: ...
```

`LaunchSpec.argv` is a non-empty tuple of non-empty strings and is always executed with `shell=False`; `env` is an overlay, not a copy of the host environment. Each `ovcaq.drivers` entry point loads one `DriverPlugin`. `discover_drivers` defaults to `importlib.metadata.entry_points(group="ovcaq.drivers")`, loads each entry point once, rejects `api_version != DRIVER_API_VERSION` with `IncompatibleDriverError`, validates `entry_point.name == driver.name`, and rejects any duplicate across built-ins or third parties with `DuplicateDriverError`. Load/probe failures remain visible by driver name; they never silently replace a built-in. An incompatible ABI is a hard discovery failure with the host/plugin versions in its detail, not a partial load.

Discovery and registration do not make a decoder global. `ClaudeDriver` retains mutable usage identities and the latest provider session ID, so the supervisor obtains a fresh instance for every session/run. The existing zero-argument ABI supports this without a registry change: a `DriverPlugin` factory closure captures fresh settings and a fresh `run_id`, such as `lambda: ClaudeDriver(settings, run_id=new_run_id())`.

There is one summary authority: `events.reducer.reduce_session`. The protocol retains `AgentDriver.summarize` because the accepted driver seam calls it, but every conforming implementation must be the thin adapter `return reduce_session(observations, exit_code).summary`; it may not reinterpret failures, usage, terminal order, or workflow state. Driver conformance tests pin that equality. Provider-specific classification happens only while producing normalized observations.

`src/ovcaq/config.py`:

```python
@dataclass(frozen=True, slots=True)
class AgentSettings:
    name: str
    command: tuple[str, ...]
    tiers: Mapping[str, str]
    environment: Mapping[str, str]
    options: Mapping[str, JSONValue]

def agent_settings(root: Path, *, name: str | None = None) -> AgentSettings: ...
```

The selected name is the explicit argument or merged top-level `agent`. User then project tables merge per `[agents.<name>]`; project values win. `command` defaults to `(name,)`, must be an argv array rather than a shell string, and all tier keys/model values and environment keys/values are non-empty strings. `tiers` stays opaque to shared modules. Configuration rejects environment keys containing `token`, `secret`, `password`, `authorization`, `api_key`, `cookie`, or `credential`, and rejects pinned credential-shaped values; credentials remain launcher-managed rather than copied into OVCAQ config or `LaunchSpec`. Explicit configured non-secret environment controls are permitted; the driver has no literal `WARDEN_UNATTENDED` allowlist. Remaining provider-specific keys are exposed through immutable `options` and validated by the provider driver. Existing `workflow_settings(...).available_tiers` delegates to the shared agent-settings reader's tier keys without changing its public result.

`src/ovcaq/drivers/claude.py`:

```python
class ClaudeDriver:
    name = "claude"

    def __init__(self, settings: AgentSettings, *, run_id: str) -> None: ...
    def probe(self) -> DriverHealth: ...
    def build_launch(self, request: LaunchRequest) -> LaunchSpec: ...
    def decode(self, raw_line: str) -> tuple[Observation, ...]: ...
    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary: ...
```

`ClaudeDriver.summarize()` delegates exactly to `reduce_session(...).summary`; it owns no second terminal/failure policy.

`ClaudeDriver.build_launch()` resolves `request.model` as an abstract key through `settings.tiers`; a value not present as a key is accepted as an explicit opaque model only when configuration option `allow_explicit_model=true`. The normal path refuses an absent/unknown model rather than restoring shared model constants. Provider options use `fallback_model` for the optional fallback. Claude v1 is unattended and accepts exactly `permission_mode="auto"`; a missing or different value makes `probe()` unhealthy and every `build_launch()` raise `DriverConfigurationError`. There is no permissive or attended default. The exact argv is:

```text
<settings.command...> -p --permission-mode <permission_mode>
  --model <resolved model> --effort <request.effort>
  [--fallback-model <resolved fallback when distinct>]
  --output-format stream-json --verbose <request.prompt>
```

No shell evaluation, prompt file interpolation, or provider-specific argument appears outside this module. The overlay includes the explicit configured non-secret environment controls plus `CLAUDE_UNATTENDED=1` and `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0`; credential-shaped keys/values were already rejected by `agent_settings()`. Host session markers are not copied into the overlay, and the later supervisor deliberately merges the overlay with its prepared host environment. `raw_format == "claude-stream-json-v1"`.

`decode()` is total: it catches JSON, shape, Unicode-replacement, timestamp, and individual block errors and returns one `raw.unknown` observation when no safe typed observation can be emitted. It maps `system/init`, assistant text/thinking, assistant tool use, user tool results, `system/task_*`, background-task snapshots, `rate_limit_event`, and `result` records. Task IDs are lane IDs; `parent_tool_use_id` supplies fallback lane attribution. Provider message IDs and tool/task IDs become normalized identities, never provider-native payload blobs. The driver retains bounded per-session message-usage state so every emitted `usage.updated` record is a cumulative snapshot; result usage/cost produces an exact cumulative snapshot before the terminal observation. Permission denials classify as `permission`; authentication markers classify as `authentication`; rejected rate-limit events and live limit banners classify as `rate_limit`; bounded DNS/socket/API transport markers classify as `connectivity`; explicit timeout evidence classifies as `timeout`; other provider terminal errors classify as `agent`; malformed terminal evidence is `unknown`. Failure detail is sanitized and bounded before it enters an observation or summary. Only an explicit numeric `resetsAt` or a timezone-qualified reset banner parsed to a future instant is credible enough for `rate_limit_reset_at`.

`src/ovcaq/events/tail.py` and `src/ovcaq/runtime/session.py`:

```python
class SessionEvidenceWriter:
    def __init__(self, path: Path, *, max_bytes: int, min_free_bytes: int) -> None: ...
    def write(self, chunk: bytes) -> int: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...

class NormalizedEventWriter:
    def __init__(self, path: Path, *, max_bytes: int, min_free_bytes: int) -> None: ...
    def write(self, observation: Observation) -> int: ...
    def close(self) -> None: ...

class RawFirstDecoder:
    def __init__(
        self,
        *,
        raw: SessionEvidenceWriter,
        normalized: NormalizedEventWriter,
        driver: AgentDriver,
        run_id: str,
        max_frame_bytes: int = 1024 * 1024,
    ) -> None: ...
    def feed(self, chunk: bytes) -> tuple[Observation, ...]: ...
    def finish(self) -> tuple[Observation, ...]: ...
```

`RawFirstDecoder.feed()` first writes the exact chunk bytes and only after that call succeeds adds them to its decoder buffer. Newline-delimited frames are decoded without their delimiter, while the raw file retains it; `finish()` decodes one final non-empty EOF residue. The buffer is bounded by `max_frame_bytes`: after crossing the limit it retains only a bounded redacted preview plus an incremental SHA-256, discards decoder bytes until the next newline, and emits exactly one `raw.unknown` for that oversized frame. Empty chunks and consecutive newlines are deterministic fixture cases. The decoder requires `run_id`, remembers the latest non-null `session_id`, and uses both for its own `raw.unknown` fallback observations. Their SHA-256 is computed from the original raw bytes, not a decoded or sanitized surrogate. Each returned observation is already sanitized by `Observation`; the writer serializes it as one newline-terminated JSON object. If raw persistence fails, framing/decoding is not called. If decoding unexpectedly raises despite the driver contract, ingestion emits `raw.unknown` with a digest and safe reason. If normalized persistence fails, the exception is visible while already-written raw evidence remains intact.

## Data flow

1. Configuration merges user/project agent settings. Shared code sees only an agent name, argv command, abstract tier map, environment overlay, and opaque options; `ClaudeDriver` alone interprets Claude options and model names.
2. The later supervisor creates `SessionPaths`, a `SessionEvidenceWriter` for raw bytes, a `NormalizedEventWriter`, and a bounded `RawFirstDecoder`, asks the discovered version-compatible driver for a `LaunchSpec`, and passes its argv/cwd plus a deliberately merged environment to `OwnedProcess.spawn()`.
3. For every stdout byte chunk, `RawFirstDecoder.feed()` appends exact bytes to `raw.jsonl` before buffering or decoding complete newline frames; `finish()` handles the EOF residue. The decoder returns one or more immutable sanitized observations, including safe `raw.unknown` fallback for oversized or malformed frames.
4. The normalized writer appends protocol-versioned records to `normalized.jsonl`; the same sanitizer already guarded object construction and guards summary serialization. Observability may lag or fail without changing state authority; persistence failures remain explicit to the caller.
5. After process exit, runtime appends a provider-neutral synthetic failure observation for an owned timeout/cancellation when required. The driver's mandated thin `summarize()` adapter then calls the single provider-neutral reducer, which deduplicates monotonic usage, applies the terminal-conflict matrix, and returns `SessionSummary`.
6. PRD 00007 will combine committed state plus `SessionSummary` in its decision table. It must not parse Claude JSON, inspect final prose, or infer decisions from normalized activity events.

## Reuse inventory

- `src/ovcaq/runtime/session.py:SessionEvidenceWriter` — reuse its create-only `O_NOFOLLOW`, mode-`0600`, byte-ceiling, free-space-floor, partial-write, fsync, and close semantics; do not create a second weaker append path or writer class.
- `src/ovcaq/runtime/session.py:SessionPaths` — use the existing `raw`, `normalized`, `metrics`, and `summary` paths; no parallel evidence layout.
- `src/ovcaq/runtime/session.py:_publish` and `publish_summary` — retain atomic publication for the final summary; streaming JSONL remains append-only through the bounded writer.
- `src/ovcaq/runtime/process.py:OwnedProcess.spawn` — later integration consumes `LaunchSpec.argv/cwd/env` and preserves `shell=False`, closed stdin, merged stdout/stderr, and process-group ownership.
- `src/ovcaq/config.py:_read_config`, `_table`, `_configured_path`, and the merge pattern in `workflow_settings()` — reuse safe TOML loading, user/project precedence, and domain errors for `agent_settings()`.
- `src/ovcaq/state/schema.py:validate_json_value`, timestamp validation, byte/depth limits, and JSON aliases — reuse validation rules where importing state would not invert dependencies; otherwise mirror the small provider-neutral validation primitive in `events.model` rather than importing workflow/state ownership into events.
- `src/ovcaq/workflow/frontmatter.py` plus `workflow_settings().available_tiers` — preserve abstract tier-key validation; only configuration/driver code resolves a tier to a provider model.
- Installed legacy `run-autopilot/cli/runner.py:build_argv`, `child_env`, `LAUNCH_ENV`, and `prompt_for` — characterization source for exact Claude flags, fallback behavior, unattended variables, and inherited host-marker scrubbing; move provider behavior, do not copy wrapper orchestration.
- Installed legacy `run-autopilot/cli/usage_limit.py` — characterization source for rejected `rate_limit_event`, reset epoch, and timezone-qualified banner parsing.
- Installed legacy `scripts/tracon/stream.py:SessionUsage` and `AgentTracker` — characterization source for message-ID usage deduplication, cumulative result cost/output, `task_*` lane lifecycle, background-task snapshots, and parent-tool fallback attribution.
- `tests/fixtures/claude/session.jsonl` — retain its init/text/tool/result shapes as one sanitized fixture case while expanding the versioned matrix.
- Entry-point discovery search (`entry_points`, `importlib.metadata`) found no existing OVCAQ helper; implement it once in `drivers/base.py`. Redaction searches (`redact`, `sanitize`, `secret`, `credential`) found state/evidence validation but no normalized-protocol sanitizer; implement it once in `events/model.py` and make every protocol constructor/serializer use it.

## Alternatives considered

1. Smallest diff: move `runner.py` and tracon's stream parser nearly verbatim into runtime. Rejected because it leaves model constants, Claude event shapes, TUI rendering concerns, and process launching in shared modules; Codex and the supervisor would inherit the false seam this PRD exists to remove.
2. Chosen: a small immutable normalized protocol, a neutral driver interface/registry, one Claude edge, and raw-first ingestion that reuses runtime evidence primitives. This is larger than a parser move, but the extra structure buys total decoding, enforceable provider neutrality, extension-point discovery, redacted normalized evidence, and a `SessionSummary` that PRD 00007 can consume without provider branches.
3. Fully generic declarative event mapping or a generic command driver now. Rejected as premature: provider streams contain provider-specific task, limit, usage, and terminal semantics that need tested code. Generic command support and Codex belong to later PRDs; Phase 4 keeps the protocol extensible without pretending the mappings are identical.

## Risks & edge cases

- Provider stream drift may produce valid JSON with unknown shapes, duplicate message IDs, multiple cumulative result records, partial final lines, non-UTF-8 bytes, or a terminal record after prior error noise. Total decode plus raw digest/preview fallback and terminal precedence must be fixture-pinned.
- Raw-first ordering can regress if a future supervisor decodes in its read loop before writing. The integration helper owns the ordering and a spy-decoder test observes the raw inode contents at decode time.
- Redaction can both miss novel credential shapes and over-redact ordinary text. Key-based rules are mandatory, value-pattern rules are narrow and tested, and raw evidence stays private for forensic recovery.
- Entry points can be malformed, expensive, ABI-incompatible, or duplicate built-ins. Discovery loads each once, reports the named failure, rejects incompatible API versions and duplicates, and never silently lets installation order choose the driver.
- A missing explicit permission mode must fail loudly in every launch mode. Defaulting to permissive behavior would be an authorization defect; `probe()` and `build_launch()` share one validation path.
- Usage streams mix per-message snapshots and cumulative terminal values. Identity deduplication and monotonic maxima prevent double counting; estimated values stay marked until exact terminal totals arrive.
- Likely next change 1, PRD 00007: the supervisor will stream an `OwnedProcess` through ingestion and use `SessionSummary`. The design exposes launch, ingest, reduce, and summary seams without embedding continuation policy.
- Likely next change 2, PRD 00008: the TUI will tail normalized records and display capability gaps. Deterministic record conversion and explicit `raw.unknown` let it degrade without importing the Claude decoder.
- Likely next change 3, PRD 00009: a Codex driver will register the same protocol with missing cost fields. Optional usage fields and entry-point-safe discovery avoid Claude-shaped assumptions.
- This PRD changes no authoritative schema and deletes no evidence, so no state migration or rollback framework is needed. Rollback is the normal commit revert; retained raw logs permit re-normalization after decoder bugs.
- The operator is the human owner for the personal-cutover runtime. `ovcaq doctor`, normalized evidence, raw evidence, and explicit unhealthy probe details provide the operational visibility needed before PRD 00007 launches real sessions.

## Test strategy outline

- Model tests construct every observation/failure enum, reject future versions, naive timestamps, invalid identifiers, booleans/negative/non-finite usage, and prove payload mutation after construction cannot change an observation.
- Reducer table tests cover exact/estimated monotonic usage, duplicate and absent identities, cumulative cost, terminal precedence, rate-limit start/clear, credible and non-credible reset times, success with noisy exit, nonzero exit without terminal, and zero exit without terminal.
- Tail tests use real mode-`0600` files and a spy driver to prove bytes are present before buffering/decode, byte identity survives invalid UTF-8/chunk splits/partial EOF, delimiters and consecutive blank lines are deterministic, oversized frames stay bounded and emit one fallback, malformed decoder output becomes `raw.unknown`, normalized and summary serializers share sanitization, and raw/normalized limit or fsync failures preserve prior evidence.
- Registry tests inject entry-point objects for successful factories, incompatible/invalid API versions, mismatched names, duplicate built-in/third-party names, duplicate third parties, load failures, and deterministic discovery order.
- Config/launch tests cover user/project precedence, default `(selected_name,)` command, argv-array rejection for shell strings, credential-shaped environment rejection, explicit configured non-secret environment controls, opaque tier lookup, distinct/equal `fallback_model`, explicit model opt-in, exact argv ordering, exact environment overlay, host-marker absence, `raw_format="claude-stream-json-v1"`, cwd, prompt literals, exact auto-only unattended permission mode, missing executable, and no `shell=True` path.
- Claude fixture parametrization covers healthy text, tool success/failure, task and subagent lanes, background snapshots, usage/cost deduplication, rate-limit start/clear/rejection, connectivity, permission, authentication, timeout, agent failure, malformed JSON, non-object JSON, unknown subtype/block, missing IDs, duplicate IDs, and truncated input.
- A scripted executable fake Claude is launched as a real owned subprocess using the driver's `LaunchSpec`; its stdout is ingested raw-first and summarized. The acceptance test asserts exact argv/env/cwd received by the fake, byte-identical raw evidence, redacted normalized records, a successful `SessionSummary`, and clean process-group collection.
- Provider-neutrality tests AST-scan imports and casefolded source strings in `events`, `runtime`, `tui`, and `drivers/base.py` for `claude`, `anthropic`, `codex`, and provider model IDs. Provider-specific fixtures/tests and `drivers/claude.py` are the only Phase 4 exceptions.
- Required gates: focused event/driver/runtime/config tests, full `pytest`, Ruff check/format, strict mypy over `src/ovcaq`, and wheel build/install smoke tests including fixture/package inclusion.

## Review log

- Question: conflicting terminal observations need an explicit first/last and success/failure precedence rule, including session-ID selection and post-terminal rate-limit handling (`## Interfaces & contracts`, `events/reducer.py:reduce_session`).
- Host substitution: source Claude subagent dispatch ran as isolated native Codex Sol.
dispatch 1 (codex): cardinal-sin 2, blocker 4, non-blocker 0, question 1
- Non-blocker: sanitizer key matching should explicitly pin exact versus substring behavior and include `access_token`/header variants (`## Interfaces & contracts`, `events/model.py:sanitize_json`).
- Non-blocker: add a decreasing cumulative-usage fixture to make the intentional maximum-without-error behavior visible (`## Interfaces & contracts`, `events/reducer.py:reduce_session`).
- Question: confirm `AgentDriver.decode` cardinality for callers; the typed protocol currently answers with `Iterable[Observation]`, while the Claude implementation narrows to `tuple[Observation, ...]` (`## Interfaces & contracts`, `drivers/base.py:AgentDriver.decode`).
- Host substitution: source mandatory Codex review dispatch ran as external Claude Sonnet through `use-sonnet`.
dispatch 2 (claude): cardinal-sin 0, blocker 3, non-blocker 2, question 1
- Non-blocker: `AgentDriver.summarize` is test-pinned rather than structurally final, so a plugin can violate the single reducer authority until conformance catches it (`## Interfaces & contracts`, `drivers/base.py:AgentDriver.summarize`).
- Question: specify whether observations with a mismatched session ID remain in `Reduction.observations`, are dropped, or are tagged (`## Interfaces & contracts`, `events/reducer.py:reduce_session`).
- Question: name the human owner/runbook for driver ABI-version and permission-mode alerts rather than leaving “operator” implicit (`## Risks & edge cases`, `docs/driver-protocol.md`).
- Non-blocker: a host crash can leave a byte-complete raw file whose final in-memory partial frame was never normalized; document that recovery relies on raw evidence and emits no invented completion (`## Interfaces & contracts`, `events/tail.py:RawFirstDecoder`).
- Host substitution: source conditional Codex verification dispatch ran as fresh external Claude Sonnet through `use-sonnet`.
dispatch 3 (claude): cardinal-sin 0, blocker 0, non-blocker 2, question 2
