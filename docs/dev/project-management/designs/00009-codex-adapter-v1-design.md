# Codex adapter design

PRD: `docs/dev/project-management/prds/wip/00009-codex-adapter-v1.md`.
Source: accepted implementation plan Phase 7, P07-T01–P07-T07; coverage manifest
and resolved discovery 00001. Source SHA-256 verified:
`43c75d3d94189351a0c0203c06563eced320889ae2d4cb7ae4e0300873e845a5`.

## Architecture fit

Add the second built-in driver at the existing API 2 boundary. Keep observation
protocol 1, state schema 1, and the existing supervisor decision vocabulary.
The current capsule identifies `drivers/codex.py` as empty and
`drivers/edge.py:build_driver` as the only built-in selection boundary. Runtime
already calls `default_prompt`, `build_launch`, `decode`, and `summarize` through
`AgentDriver`; it needs no provider branch. TUI already consumes provider identity,
normalized usage and lanes, and raw evidence through shared models.

This PRD uses sanitized fixtures and fake subprocesses only. Read-only installed
version/help/auth characterization is allowed; no real workflow launch, plugin
installation, plugin-cache write, home-state migration, or companion-repository
edit belongs here. PRD 00010 owns reconciliation and the first real workflow
smoke. The repository owner is the human operator. Existing private raw logs,
metrics, summaries, status/doctor, and explicit log purge provide observability.
No durable schema changes are proposed; state backup/restore and fresh-batch
cutover remain the existing authority. Reverting this feature commit and selecting
the previous driver recovers fixture/fake operation without rewriting state.

## Module placement

- Fill the existing empty `src/ovcaq/drivers/codex.py` with `CodexDriver`.
- Add `src/ovcaq/drivers/codex_events.py` for provider-specific validated item
  projections and failure/reset parsing. Do not import the Claude decoder.
- Edit `src/ovcaq/drivers/edge.py` for built-in selection and widen its return
  annotation to `AgentDriver`. Preserve the existing Claude model bridge.
- Reuse `src/ovcaq/config.py` unchanged: `AgentSettings`, tier maps, opaque
  options, environment overlays, and per-phase literal prompts already exist.
  No default model identifiers enter shared configuration.
- Add versioned evidence under `tests/fixtures/codex/v1/`: JSONL families,
  `provenance.json`, sanitized CLI help/version evidence and `fake_codex.py`.
  Keep the original unversioned synthetic seed labeled as such.
- Add `tests/drivers/test_codex.py`, `tests/drivers/test_codex_decode.py`,
  `tests/drivers/test_codex_failures.py`, `tests/drivers/test_conformance.py`,
  `tests/runtime/test_codex_decisions.py`, and
  `tests/tui/test_codex_projection.py`. Extract only necessary shared test
  harnesses from existing driver/process/decision tests and run them for both
  built-ins; do not duplicate runtime policy.
- Edit `docs/driver-protocol.md` to reflect live API 2/default prompts, the
  Codex launch/usage contract, fixture pin, and operator diagnostics. Update
  `tests/fixtures/README.md` provenance pointers. Documentation is about driver
  protocol, not a second hand-maintained CLI verb inventory.

## Interfaces & contracts

### P07-T01 — installed-version evidence

The initial pin is `codex-cli 0.160.0`, verified by local `codex --version` on
2026-10-04. Local `codex --help` exposes global `--ask-for-approval never`;
`codex exec --help` exposes `--json`, `--sandbox workspace-write`, `-C`, `-m`,
and `-c`. `codex login status` is a read-only authentication check. New
`--approve-for-me` is available but does not replace the PRD's explicit policy.
Save sanitized help/version evidence; do not silently accept a different CLI
contract if the implementation environment changes.

`tests/fixtures/codex/v1/provenance.json` has `schema_version: 1`,
`cli_version: "codex-cli 0.160.0"`, `schema_source`, `captured_at`, and `families`.
Each family entry has `file`, `source_kind` (`captured` or `schema-synthetic`),
`source`, `sanitization`, and `unsupported_fields` (an array of explicit gaps).
For each JSONL family include a SHA-256 under `sha256`. Cite the pinned official
[exec event schema](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/exec/src/exec_events.rs)
and the matching [JSONL event producer](https://raw.githubusercontent.com/openai/codex/rust-v0.160.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs)
for schema-synthetic families; schema_source records both URLs. Include error →
completion recovery and error → identical turn.failed fixtures. A live capture means a controlled existing
`codex exec --json` transcript copied and sanitized into this tree, never a
test reading home logs. Do not launch a real workflow to obtain missing evidence.
If a matching safe transcript is unavailable, say `schema-synthetic` explicitly;
no family may claim a capture that did not occur.

Families are `healthy.jsonl`, `tool-active.jsonl`, `lanes.jsonl`,
`rate-limited.jsonl`, `connectivity-failed.jsonl`, `permission-failed.jsonl`,
`authentication-failed.jsonl`, and `malformed.jsonl`. Collectively cover every
native top-level/item variant in the pinned schema, new/unrecognized fields,
missing/wrong types, truncated JSON, replayed records, absent telemetry, and
redaction sentinels. Preserve the seed's older missing-usage-field shape as a
compatibility/tolerance example, not evidence of the current installed version.

### P07-T02 — launch and model/effort contract

```python
class CodexDriver:
    name = "codex"
    def __init__(self, settings: AgentSettings, *, run_id: str) -> None: ...
    def probe(self) -> DriverHealth: ...
    def build_launch(self, request: LaunchRequest) -> LaunchSpec: ...
    def default_prompt(self, phase: str) -> str: ...
    def decode(self, raw_line: str) -> tuple[Observation, ...]: ...
    def summarize(self, observations: Iterable[Observation], exit_code: int) -> SessionSummary: ...
```

Constructor accepts only options `sandbox`, `approval`, `allow_explicit_model`.
Absent sandbox/approval use `workspace-write`/`never`. Any supplied different
value or wrong type is `ValueError`; `allow_explicit_model` defaults to `False`
and must be an actual bool. Unknown options fail. Commands remain argv tuples,
including wrapper prefix arguments; environment is exactly a copied configured
overlay, with no provider-specific host-variable copies or credential values.
Inherited authenticated launcher storage is managed by the launcher, not OVCAQ.

`request.model is None` omits model flags. A configured tier key resolves through
`settings.tiers`. A model already present among `settings.tiers.values()` is
accepted unchanged (the supervisor supplies a resolved model). An arbitrary
explicit model is accepted only with `allow_explicit_model=True`; otherwise it
raises `ValueError`. No provider model defaults live in shared modules.

Effort `None` omits the override. Map `low`, `medium`, `high`, `xhigh` identically
to native `model_reasoning_effort`. A nonblank unmappable string emits one
`logging.getLogger(__name__).warning` with the requested value and omits that
override; do not silently drop it or guess another level. Blank effort fails.

Exact launch order is:

```python
argv = (
    *settings.command,
    "--ask-for-approval", "never",
    "exec", "--json", "--sandbox", "workspace-write", "-C", str(request.root),
    # when model is configured:
    "-m", resolved_model,
    # when effort is mapped:
    "-c", 'model_reasoning_effort="high"',  # high example; quoted TOML value
    "--", request.prompt,
)
```

The final `--` terminates options so prompts beginning with `-` remain literal
data. Omitted optional segments contribute no arguments. `LaunchSpec.cwd` is
`request.root`, `LaunchSpec.env` is the configured overlay, and
`LaunchSpec.raw_format` is `"codex-exec-json-v1"`. `build_launch` performs no
spawn or provisioning. The shared runner closes stdin and spawns without a
shell; neither prompt shell syntax nor command prefix syntax is evaluated.
Timeout is enforced by the existing request/runtime, not another CLI flag.

`drivers.edge.build_driver(root: Path, name: str | None) -> AgentDriver` selects
`CodexDriver(agent_settings(root, name=name), run_id=uuid4().hex)` for `codex`,
preserves `_ResolvedModelClaudeDriver` for `claude`, and retains the existing
`CommandError(ErrorCode.RUNTIME_FORMAT, ...)` for unsupported agents. No change
to `drivers.base:DRIVER_API_VERSION == 2` or launch record fields.

### P07-T04 — read-only health and failure contract

`probe()` checks executable resolution and runs `(*settings.command, "--version")`
and `(*settings.command, "login", "status")` with configured environment overlay,
stdin `DEVNULL`, no shell, timeout 5 seconds each, and bounded stdout/stderr
capture of 16 KiB per probe. Never call `login` without `status` or print raw
credentials. A missing/nonexecutable binary, timeout, unsupported version,
nonzero version/auth status, or empty version returns `DriverHealth(False,
sanitized actionable detail)`. The supported fixture pin is 0.160.0; a different
version fails with the observed/pinned version and a refresh instruction. Healthy
detail includes the executable, version, and authenticated status only. Probe
must not invoke a model, plugins, network readiness retries, or mutate launcher
global state. Fake version/auth modes exercise every path without real auth.

```python
# src/ovcaq/drivers/codex_events.py
def classify_failure(detail: str) -> FailureClass: ...
def failure_reset(detail: str, now: datetime) -> datetime | None: ...
```

Only `turn.failed.error.message` creates an immediate native `session.failed`.
Top-level `error` is provisional: emit `activity.message` kind `error`, with
sanitized `detail`, classified normalized `failure_class`, and normalized
`reset_at` (UTC string or null); it does not emit session failure or rate-limit
start during decoding. A later successful turn supersedes provisional error
noise. Error → identical turn.failed emits exactly one terminal failure and
one rate-limit start when applicable. Item errors remain nonfatal activity and
never carry the provisional-session-failure metadata. Match
case-insensitively in this precedence: authentication (`401`, unauthorized,
not logged in, invalid/expired credential); permission (`403`, permission denied,
sandbox denied, approval denied); rate limit (`429`, rate limit, quota/usage
limit); connectivity (connection reset/refused, DNS, network unreachable,
server unavailable, `502`/`503`); timeout (timed out, timeout); explicit agent
failure; else unknown. Numeric codes must be bounded tokens, not substrings of
an item ID. Structured failure fields, when actually present and documented,
may supply stronger evidence; unrecognized shapes become raw unknown.
Do not scan normal agent prose, tool stdout, or quoted diagnostic examples as
session failures. Runtime-generated timeout/death observations retain precedence
through the existing reducer/decision path.

`failure_reset` accepts only a native failure detail's explicit timezone-aware
ISO reset timestamp or explicit `retry after <N> seconds`. N must be finite,
nonnegative and yield a future reset no more than 21600 seconds from `now`.
Naive dates, past dates, missing resets, invalid/overflow values, and ambiguous
local clock prose yield `None`. Rate-limit observations always include
`reset_at`, `window: None`, `detail`; absence of reset stays unknown. Recovery
waits remain shared policy. No auto-login or permission weakening.

### P07-T03 — total decoding and usage contract

All observations use protocol 1, provider `codex`, supplied run ID, current
thread as session ID, aware UTC receipt timestamp unless a valid native UTC
timestamp exists, and only normalized payloads. Invalid JSON, recursion errors,
wrong payload shapes, unsupported types/statuses or future records return at
least one `raw.unknown`, with SHA-256 of the original line, sanitized preview
at most 512 characters, and a bounded reason. No malformed provider record
raises to the supervisor. Use validated `Observation`/`Usage` construction;
validate before updating decoder state.

| Native evidence | Normalized result |
| --- | --- |
| `thread.started` | `session.started` with current thread identity |
| `turn.started` | `activity.message` kind `turn` |
| Agent/reasoning items | `activity.message` kind `text`/`thinking`, bounded text and item ID |
| Command/file/MCP/web items | `tool.started`/`tool.completed`/`tool.failed`, item ID as `tool_id`, neutral name and bounded detail |
| Todo items | `activity.message` kind `plan`, bounded step detail |
| Collab items | Tool lifecycle plus receiver-specific `lane.*` only for native evidenced child state |
| Nonfatal error item | `activity.message` kind `error`, never session failure |
| `turn.completed` | `usage.updated` plus `session.completed` |
| `turn.failed` | `session.failed`, plus `rate_limit.started` when classified |
| Top-level `error` | Provisional `activity.message` kind `error` with normalized classification; never immediate terminal |

Recognize `item.started`, `item.updated`, `item.completed`; reject unknown
item kinds/statuses to raw fallback. Tool terminal failure comes from native
failure/decline status, explicit native error, or nonzero command exit; ordinary
command output is never parsed as provider health. File changes are summarized
as paths/kinds; MCP result payloads and web results are bounded/sanitized and
never copied wholesale. Native collab receiver states supply lane ID, `label`,
`detail`, and their actual status; pending/running starts or progresses,
completed completes, errored fails. Interrupted/shutdown/not-found do not imply
successful completion. Missing attribution yields raw evidence rather than a
fabricated lane. Limit remembered item/lane identities to 4096; evict oldest
terminal identities first, then oldest identity, emitting a visible raw-unknown
gap. Out-of-order lane progress may remain visibly unknown in the existing TUI.

Normalized `Usage.input_tokens` means input excluding separately counted cache
reads/writes, matching the existing Claude adapter. Native cached input is
included in native input. For validated `input_tokens >= cached_input_tokens`
and explicit `cache_write_input_tokens == 0`, normalize input to
`input_tokens - cached_input_tokens`, cache-read to `cached_input_tokens`,
cache-creation to `0`, and output to `output_tokens`. Inconsistent inclusive
counts yield unknown input plus a raw-unknown gap, not a silently clamped fact.
When cache-write is positive, the pinned exec schema does not establish its
partition relative to inclusive input: expose its native value as cache-creation,
cache-read as supplied, normalized uncached input as `None`, and an explicit
raw-unknown partition gap. When either required input/cache-read/cache-write
component is missing/invalid, normalized uncached input remains `None`; other
valid components remain available. Do not guess a subtraction without documented
partition semantics. Reasoning is not added to output again. Conformance example:
native input 120/read 100/write 0/output 30 normalizes identically to Claude
input 20/read 100/write 0/output 30. Preserve inclusive native totals in raw
only. `cost_usd` and `tool_uses` remain `None`, never zero or inferred prices. Reject bool, negative, float, nonfinite, or
wrong-shaped counters individually; retain valid counters and emit an unknown
observation for malformed supplied usage. Omitted fields remain `None`.

Every native turn.completed usage is already thread-cumulative in pinned
0.160.0 (`usage_from_last_total` reads ThreadTokenUsage.total). Produce a
session-cumulative snapshot by fieldwise maximum across validated normalized
snapshots for that thread; never sum terminal snapshots, even across additional
turns or starts. Example: native input snapshots 100 then 200 yield 200, never
300. Duplicate/out-of-order completions and implicit-versus-explicit starts do
not change arithmetic. No turn ledger, ordinal, current-turn sum or previous-turn
total is retained. Usage identity is `thread:<id-or-unknown>`; it is observational
only. Known values stay exact (`estimated=False`); partial/unknown components
remain None, and unknown partition/conflicting identity/malformed-counter gaps
are explicitly reported rather than fabricated as exact. A positive cache-write
partition gap uses `estimated=True` conservatively. Native all-zero usage can be
an absent-notification default: if no earlier nonzero valid usage exists, keep
all token fields unknown and emit a raw-unknown absence gap; do not display exact
zero. A later zero snapshot never reduces earlier known maxima. Additional turns
alone do not imply estimates or require stable turn IDs.

Reset mutable decoder session fields when `build_launch` begins a new session:
thread, thread-cumulative usage maxima, remembered items/lanes,
and live-rate-limit state. The supervisor reuses its driver between sessions;
fresh instances cannot be assumed. Preserve supplied run ID. A conflicting
thread within one session remains represented and the shared reducer fails
unknown, rather than merging distinct threads silently. `summarize` consumes
the supplied iterable exactly once. With a native terminal completion/failure,
return `reduce_session(observations, exit_code).summary` unchanged. Without any
terminal, use the latest top-level provisional error's already-normalized
failure metadata to append a synthetic `session.failed` (and `rate_limit.started`
when applicable) to that reduction input; do not parse provider-native prose in
shared code or read stale private decoder fields. With no provisional error,
return the shared reducer result unchanged. Persisted activity/raw evidence and
the resulting summary retain the classification; this synthetic reduction is
not another state writer. No terminal or rate-limit observations are fabricated
for a recovered error → completion stream.

### P07-T05 — native skill invocation and state-only handoff

`default_prompt(phase)` accepts exactly `build`, `review`, `done`; every other
value raises `ValueError`. Return native `$run-autopilot` invocation followed by
the literal contract below. Per-phase configured `AgentSettings.prompts` remain
literal supervisor overrides and must satisfy the same contract in configuration
tests; the driver does not embed external skill files or open plugin caches.
The configured external skill must expose name `run-autopilot`; an installation
with a different native name uses an explicit verified phase prompt override.

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

The prompt states the invariant; shared state transitions remain its authority.
Fake execution proves one successful handoff per launched phase and zero second
phase work in that same session. This is not a real external-plugin smoke.

### P07-T06 — shared conformance and fixture drain

`tests/fixtures/codex/v1/fake_codex.py` supports the exact global/exec argv,
`--version`, and `login status`. It uses only temporary test roots and closed
stdin. Scenario is supplied by non-secret test environment `OVCAQ_FAKE_SCENARIO`;
record received argv/cwd/selected environment in raw output. It must not read
the real home, real auth storage, or plugin state. Workflow mode invokes the
installed test `ovcaq` CLI against the same temporary repository to commit
selection/build/review/done handoffs; never directly writes state.json.
State initialization is through existing store/CLI APIs in the harness.

Parameterize the same semantic driver/raw/process/decision assertions over
Claude and Codex adapters with provider-specific fixture inputs at the edge.
Preserve existing Claude assertions, adapting only harness injection where
needed. Include productive state plus noisy/nonzero exit, unchanged state plus
success prose, all failure classes, reset/no reset, retry bound exhaustion,
phase fingerprints, pause/stop/drain, duplicate run, timeout TERM/KILL, parent
exit, retained raw-first logs, and redacted normalized records. Run real fake
subprocess groups, not only mocked Popen objects. Each timeout/signal test
asserts descendant cleanup and no unrelated process signal.

End-to-end fake drain must traverse build → review → done → drained through
the real shared supervisor, retain one session evidence bundle per phase,
verify phase revisions/committed state, and preserve drained PRD results.
The existing generic capability fake supplies any required post-drain capability
without launcher mutation. Provider strings/model IDs/native JSON parsers stay
absent from runtime/state/workflow/events/TUI/shared root modules; the existing
neutrality scan is not relaxed. Any discovered shared fix must be independently
provider-neutral and run against both adapters before acceptance.

### P07-T07 — provider-neutral projection

Feed normalized Codex records and metrics produced by the actual adapter/fake
supervisor into the existing `ProjectObserver`/panel models. Assert `codex`
identity, actual lane/activity evidence, exact/estimated token labels, unavailable
cost displayed as unknown/omitted, and retained raw-only visibility for unknown
streams or normalization gaps. Unsupported lane/cost/other fields remain visibly
unknown. Do not add provider imports, parsers, model names or policy in the TUI.
No production TUI changes are expected; a necessary projection fix must pass
existing Claude/neutral observer tests unchanged.

## Data flow

Configuration resolves a phase's tier/model/effort. The driver edge constructs
the selected adapter; the supervisor chooses the configured literal prompt or
driver native default. `build_launch` resets session-local state and returns
the immutable argv/environment/cwd specification. `OwnedProcess` owns the group
and closes stdin. `SessionEvidenceWriter` persists raw bytes before
`RawFirstDecoder` frames/decodes them; normalized observations go to the existing
writer/reducer and shared metrics. On process exit, the supervisor rereads
committed state and combines its delta with `SessionSummary` using the existing
decision table. TUI follows registry/state/metrics/normalized/raw evidence.
Neither normalization nor agent prose advances state.

Fake executable workflows use OVCAQ commands at the same boundary as an external
skill would. Installed CLI probes are read-only and separate from fixture test
execution; plugin provisioning remains outside this path.

## Reuse inventory

Sweep used the global rationalizations catalog's verb AND noun synonym sets.
Searches covered `build|create|make|init` + `argv|launch|prompt|command`,
`parse|from_|decode|load|read` + `event|item|observation|thread|usage`,
`validate|check|assert_|verify|is_valid` + `probe|health|auth|failure|rate|permission`,
`render|format|serialize|to_|as_` + `provider|activity|token|cost|raw`, and
`get|find|lookup|resolve|select` + `tier|model|effort`. Positive controls were
`LaunchRequest`, `reduce_session`, `build_driver`, and `ProjectObserver`.

- `src/ovcaq/drivers/base.py:AgentDriver`, `LaunchRequest`, `LaunchSpec`,
  `DriverHealth`: implement the exact live API 2; no parallel driver records.
- `src/ovcaq/config.py:AgentSettings`, `agent_settings`, `resolve_phase_route`:
  reuse configuration precedence, credential rejection, tiers and phase prompts.
- `src/ovcaq/drivers/edge.py:build_driver`: add the second built-in at this
  existing provider edge; preserve Claude resolution behavior.
- `src/ovcaq/events/model.py:Observation`, `Usage`, `sanitize_text`,
  `sanitize_json`: validate/freeze/redact normalized evidence.
- `src/ovcaq/events/reducer.py:reduce_session`: reuse monotonic field maxima,
  exactness semantics, closed failures and conflicting-session handling.
- `src/ovcaq/events/tail.py:RawFirstDecoder`, `NormalizedEventWriter`:
  reuse framing, bounds, raw-first persistence and decoder-failure fallback.
- `src/ovcaq/runtime/process.py:OwnedProcess`, runtime session evidence and
  watchdog: reuse closed stdin, shell-free spawn, groups, TERM/KILL and limits.
- `src/ovcaq/runtime/supervisor.py:Supervisor`, `runtime/decision.py`: reuse
  state-led continuation, retry/pause/park/drain and capability handling.
- `src/ovcaq/tui/model.py:ProjectObserver`, `tui/panels.py`: consume existing
  normalized identity/usage/lanes/raw fallback.
- `tests/drivers/test_claude_process.py`, `tests/runtime/test_supervisor_process.py`,
  `tests/runtime/test_decision.py`, and `tests/tui/test_model.py`: extract small
  fixture injection seams for the same semantic assertions, preserving behavior.
- Codex decoder/health/failure helpers: nothing found in the empty
  `drivers/codex.py`, greps tried the parser/validator verb and noun sets above;
  rerunning `decode|probe|failure` in `drivers/claude.py` proved the search works.
  Its provider-specific parser cannot be reused as Codex logic. The unversioned
  `tests/fixtures/codex/session.jsonl` is a seed only.

## Alternatives considered

1. Smallest diff: one Codex driver with decoding inline and only adapter unit
   tests. It fits the protocol but fails the required shared conformance and
   end-to-end fake/state/signal proof, and tangles status/usage handling.
2. Chosen: a small Codex driver plus provider projection helpers, versioned
   provenance, and shared test harness injection. The extra file/tests buy total
   decoding, accountable telemetry, and proof that the existing runtime/TUI work
   through a genuinely different launcher. No new production abstraction.
3. Generalized provider framework or shared native-event base class. Rejected:
   native formats differ and forcing reuse risks leaking provider semantics.
   Generic extension design is later PRD 00012, not this feature.

## Risks & edge cases

- CLI drift: characterize 0.160.0, preserve version/help/schema provenance and
  fail health on an unreviewed version. Pin refresh is explicit; do not switch
  to auto-approval or bypass sandbox to satisfy an evolving launcher.
- Session decoder reuse: runtime reuses its driver; reset only at session launch,
  preserve run identity and reject conflicting thread evidence.
- Terminal semantics: native tool errors and nonfatal error items do not decide
  session outcome. A committed handoff wins over native exit noise; prose alone
  never counts. Missing turn IDs make multi-turn exact replay attribution
  unavailable; conservative estimated totals expose that gap.
- Resource and privacy limits: existing phase timeout (maximum 86400 seconds),
  raw/retained/free-space limits and decoder frame bounds remain in force.
  Probe output is bounded; item state is capped; text/detail 4096 characters,
  preview 512. No unbounded transcript aggregation or new automatic deletion.
  Fixture sanitization replaces credentials and personal paths; raw runtime
  evidence stays 0600 and is retained until explicit purge.
- Installed skill identity is an external declarative prerequisite, expressed
  exactly as `$run-autopilot` or a verified literal phase override. This PRD
  verifies fake/native prompt contracts, not external content installation.
- Likely next changes: PRD 00010 introduces launcher reconciliation and real
  smokes without moving it into the driver; PRD 00012 adds a generic decoder
  extension through versioned protocols; later Codex event versions expand
  observed kinds using new pinned evidence. API 2/protocol 1 and raw fallback
  permit these changes without provider conditionals in core. Unsupported cost
  and native reasoning breakdowns do not justify pricing or schema inventions.

## Test strategy outline

Plan around seven source obligations, normally one test/implementation task
per owner plus any justified shared harness/protocol task, below the existing
15-task ceiling. Every planned task copies its source task and Phase 7 exit
criteria verbatim; grouped wording cannot waive a fixture or failure case.

First establish fixture provenance and exact installed help contracts; then
write independent tests for launch/health/prompt, decoder/usage/failure and
shared driver/process/decision/projection paths before implementing them.
Adversarial malformed records include deep nesting, wrong scalar/container
types, arbitrary statuses, absent IDs, duplicates/out-of-order records,
unbounded text truncated by existing framing, partial usage and sanitized
secrets. Probe tests cover missing executable, stderr-only auth failure,
oversized output, timeouts, unsupported version and closed stdin.

Conformance runs Claude and Codex through identical semantic assertions and
real subprocess ownership. Final fake drain proves the state-owned lifecycle
and retained evidence; projection tests use those outputs. Tests never read
live provider homes, invoke real models, or mutate launcher-global state.
Check purity via existing provider scans and installed-wheel execution outside
the checkout. Run required package gates: `uv sync --all-groups`, `uv run pytest`,
`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`,
and `uv build`.

## Review log

host mapping: claude=native Sol; codex=external Claude Opus. Author logical
worker-opus uses native gpt-6.1-sol high. Source-pinned identity tokens below
are transport labels, not claims about actual provider/model.

Dispatch 1 actual reviewer: fresh isolated native gpt-6.1-sol high. Prompt:
`docs/dev/tmp/design-00009-dispatch1-prompt.md`; raw findings:
`docs/dev/tmp/design-00009-dispatch1-findings.txt`; complete response also retained in
collaboration transcript. Six section-anchored findings; engaged, no retry.

Question recorded, not fixed: P07-T03 does not choose a normalized terminal
mapping/bookkeeping for interrupted/shutdown/not-found child statuses. All
remain explicitly prohibited from implying successful completion.

Five non-blocker entries are the reviewer's labeled checked-correct doubts,
not unresolved defects: bounded decoder/resources, tool-versus-session failure,
usage replay uncertainty, configured/external boundaries, source/verification
coverage. Their test recommendations remain recorded; no design edits applied.

dispatch 1 (claude): cardinal-sin 0, blocker 0, non-blocker 5, question 1

Dispatch 2 actual reviewer: external Claude Opus, opus alias resolved by raw
init to `claude-opus-5-5`, driver effort `xhigh`. Findings:
`docs/dev/tmp/design-00009-dispatch2-opus-20261004.txt`; receipt at the same path
plus `.receipt.json`; raw JSONL is the receipt's `raw` field. Ten anchored
findings plus six checked-correct notes; engaged, no retry. The reviewer queried
external schema documentation (Context7 0.155.1); author validated the two
blocking conclusions against pinned official rust-v0.160.0 producer/protocol.
No repo production/test reads or writes occurred in the reviewer.

Blockers fixed: top-level error is provisional activity, with terminal failure
owned by turn.failed and terminal-absent fallback classified during reduction;
cache-inclusive native input is split without double counting, with an honest
unknown partition when cache-write inclusion is unproven. Added recovery/duplicate
error fixtures and an explicit Claude/Codex cache-split conformance example.

Non-blockers recorded, not fixed: (1) additional turns currently sum native
thread totals, overcounting, and a zero default can mean absent telemetry;
(2) fake drain cannot prove actual workspace-write writable paths/network/git;
(3) reset parser shapes may lack native message-formatter evidence;
(4) build_launch reset assumes exclusive driver ownership and fresh replay;
(5) exact version pin requires core evidence refresh on every launcher upgrade.

Questions recorded, not fixed: exception/error-code/preflight timing for invalid
routes; tier-key-versus-value precedence and literal phase-model availability;
operator prompt overrides cannot be enforced merely by repository tests.

dispatch 2 (codex): cardinal-sin 0, blocker 2, non-blocker 5, question 3

Dispatch 3 actual reviewer: external Claude Opus, raw init `claude-opus-5-5`,
opus alias/xhigh. Findings: `docs/dev/tmp/design-00009-dispatch3-opus-20261004.txt`;
receipt at that path plus `.receipt.json`; raw JSONL in its `raw` field. Eight
anchored findings plus seven correct notes; engaged, no retry, no tools used.
Both prior blocking repairs verified. The previously recorded cumulative-usage
non-blocker was independently upgraded to blocker: thread totals 100 then 200
must yield 200, not 300. Fixed the contract to thread-wide fieldwise maxima,
no turn ledger, exact known values, and honest unknown all-zero defaults.
Added the explicit two-snapshot counterexample to the copyable contract.
The reviewer ceiling is reached; this last correction was checked by the author
against pinned producer semantics and the 100→200 arithmetic, without a fourth
reviewer dispatch. No cardinal sins or blockers remain open.

New non-blockers recorded, not fixed: probe timeout ownership could orphan
wrapper descendants despite direct-child timeout; real workspace-write may
block outside-root/git/network handoff effects; a prompt exactly `-` still
selects native stdin despite option terminator (blank prompt concern also noted).

New questions recorded, not fixed: multi-turn completed/failed/lost-later-turn
terminal reduction semantics; native-versus-runtime terminal suppression of
provisional fallback; whether pinned exec always serializes cache-write fields;
whether `$run-autopilot` text triggers actual skill loading in exec. Author
observed cache-write exists with serde default and no skip in pinned exec schema;
that evidence is recorded here, not used to thin the question roster or claim
an external skill smoke. Earlier questions and non-blockers remain recorded;
the cumulative-overcount issue alone is resolved after its severity upgrade.

dispatch 3 (codex): cardinal-sin 0, blocker 1, non-blocker 3, question 4

Unresolved questions: the eight recorded questions remain advisory; the eight
real non-blocker observations remain recorded (including duplicate workspace
risk). Five dispatch-1 entries are checked-correct notes labeled non-blocker by
that reviewer. The cumulative-overcount non-blocker from dispatch 2 is now fixed
as dispatch 3's blocker, so seven real non-blocker observations remain open.
