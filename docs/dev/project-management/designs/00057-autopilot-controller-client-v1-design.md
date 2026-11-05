# Design: OVCAQ external workflow-controller client (PRD 00057)

## Architecture fit

Per `docs/dev/project-management/designs/autopilot-optional-supervision.md` and the canonical
`agent-plugins` design (`00011-autopilot-standalone-design.md`, "Contract A: controller and
callers"), OVCAQ is a **consumer** of an external Autopilot controller it does not implement
or bundle. This PRD builds only the consumer side of Contract A: a typed transport client
(`workflow_client`) plus a read-only prerequisite checker (`tools/autopilot-prerequisites`).
No workflow policy, no second state authority, no publication or cutover. The existing
`src/ovcaq/state` and `src/ovcaq/workflow` packages remain the sole durable writer until
PRD 00058 removes them after installed-controller equivalence (held, out of scope here).

The client sits beside, not inside, the existing `ovcaq.config` / `ovcaq.paths` layer: it reads
its own `[workflow]` config keys through the same precedence chain (`config.py`'s
`user`/`project` merge) that `workflow_settings()` already uses, and it spawns the controller
exactly the way `drivers.base.LaunchSpec` and `runtime.capability` spawn subprocesses — explicit
argv tuple, no `shell=True`, bounded timeout, captured output.

## Module placement

New files only; no edits to existing production modules (contract A is late behind existing
settings/paths/no sibling collision with current `supervisor_settings`/`agent_settings`):

- `src/ovcaq/workflow_client.py` — the transport: `ControllerConfig`, `ControllerClient`,
  `ControllerContract`, `ControllerError` family, `apply()`/`contract()`/`snapshot()`.
- `src/ovcaq/config.py` — **edit**, additive only: extend `WorkflowSettings` with three new
  optional fields (`controller_argv`, `contract_bundle`, `actor_file`) and a small reader
  function `controller_settings()`. No existing field, signature, or default changes; existing
  callers of `workflow_settings()` are unaffected because the new fields default to `None`.
- `tools/autopilot-prerequisites` — a standalone executable Python script (same convention as
  `tools/check`, `tools/onboard`): read-only, no import of `src/ovcaq` production state writer.
  It imports `ovcaq.workflow_client` for the typed probe helpers only.
- `tests/workflow_client/test_transport.py`
- `tests/workflow_client/test_contract.py`
- `tests/workflow_client/test_prerequisites.py`
- `tests/fixtures/workflow/controller-v1.json` — canonical producer fixture bundle (fake, since
  AP 00018 has not shipped yet — confirmed: `agent-plugins` repo currently has no
  `controller/` implementation, only the two design docs and backlog PRDs 00012-00021).
- `docs/operations.md` — **edit** (already exists, added by commit `cee9b94`); append a section
  documenting the new `[workflow]` config keys (`controller_argv`, `contract_bundle`,
  `actor_file`) and `tools/autopilot-prerequisites` usage, per the PRD's structural
  decomposition. Do not recreate the file.
- `CHANGELOG.md` — **edit** (already exists, added by commit `cee9b94`); append one `### Added`
  line under `[Unreleased]` noting the internal controller-client module exists, with no
  user-facing behavior yet (nothing invokes it). Do not recreate the file.

## Interfaces & contracts

### `src/ovcaq/workflow_client.py`

```python
from __future__ import annotations

PROTOCOL_MAJOR = 1

class ControllerError(RuntimeError):
    """Base class for every typed Contract A failure."""

class IncompatibleContractError(ControllerError):
    """protocol_major mismatch, an unadvertised required capability, or a
    schema_digest/fixture_digest that does not match the pinned contract_bundle
    (controller_bundle_digest, PRD Phase 0 acceptance criterion)."""

class ControllerTimeoutError(ControllerError):
    """The controller subprocess did not return within timeout_seconds."""

class ControllerOutputError(ControllerError):
    """stdout exceeded the output bound, or was not parseable JSON."""

class RevisionConflictError(ControllerError):
    """error_code == "revision_conflict" in a typed apply response."""

class RejectedRequestError(ControllerError):
    """error_code in {"invalid_request", "wrong_binding", "missing_capability",
    "rejected_evidence", "recovery_required"}; carries `.error_code` and `.retryable`."""
    def __init__(self, error_code: str, retryable: bool, detail: str) -> None: ...


@dataclass(frozen=True, slots=True)
class ControllerConfig:
    """Explicit, validated inputs — never derived by sibling discovery."""
    argv: tuple[str, ...]              # [workflow].controller_argv; no shell, no PATH lookup magic
    contract_bundle: Path              # [workflow].contract_bundle; read-only, pre-pinned
    actor_file: Path | None            # [workflow].actor_file; required for apply(), not contract()/snapshot()
    project_root: Path
    timeout_seconds: int = 30
    max_output_bytes: int = 1_048_576  # 1 MiB; a fresh guess sized for a small JSON response, not an inherited precedent (see _run())

    def __post_init__(self) -> None:
        # argv: nonempty tuple of nonempty str, mirrors drivers.base.LaunchSpec validation
        # contract_bundle: must exist and be a regular file (reuse ovcaq.paths._checked_path)
        # timeout_seconds: 1..300 (contract/snapshot/apply are all short-lived CLI calls,
        #   not long driver sessions — 300s backstops a hung controller without blocking a
        #   whole OVCAQ phase on it)
        # max_output_bytes: > 0
        ...


@dataclass(frozen=True, slots=True)
class ControllerContract:
    protocol_major: int
    package_version: str
    schema_digest: str
    fixture_digest: str
    operations: frozenset[str]
    capabilities: frozenset[str]


@dataclass(frozen=True, slots=True)
class ApplyResult:
    ok: bool
    revision: int | None
    result: Mapping[str, object] | None
    error_code: str | None
    retryable: bool


@dataclass(frozen=True, slots=True)
class MutationEnvelope:
    """Mirrors Contract A's mutation envelope exactly — field names and nullability."""
    protocol_major: int
    operation: str
    request_id: str
    expected_revision: int
    project_id: str
    workflow_id: str | None       # null only for workflow.open on an absent store
    actor_id: str | None          # null only for that same bootstrap case
    lease_epoch: int | None       # null only for that same bootstrap case
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        # Enforce the PRD's one documented exception: workflow_id/actor_id/lease_epoch
        # may be null only when operation == "workflow.open" and expected_revision == 0.
        # Every other operation requires all three non-null. This is the one piece of
        # Contract A semantics this client validates locally (fail fast, not at the
        # controller round trip) because getting it wrong is a guaranteed rejected_evidence.
        ...


class ControllerClient:
    def __init__(self, config: ControllerConfig) -> None: ...

    def contract(self) -> ControllerContract:
        """Run `argv --json contract`. No project root, no mutation. After parsing,
        read `self._config.contract_bundle`, compute its own schema_digest/
        fixture_digest the same way the bundle's manifest declares them (sha256 of
        the bundle's canonicalized JSON, per Contract A's digest-pinning convention),
        and compare against the live controller's advertised `schema_digest`/
        `fixture_digest`. A mismatch raises IncompatibleContractError naming both
        digests (controller_bundle_digest, PRD Phase 0 acceptance). Caches the
        validated ControllerContract on `self` for the instance's lifetime (see
        ## Data flow and ## Alternatives) so repeat calls on the same instance are
        free; a new instance always re-validates — there is no cross-instance or
        on-disk cache."""

    def snapshot(self, *, workflow_id: str) -> Mapping[str, object]:
        """Run `argv --json snapshot --project-root <project_root>`.
        Read-only; returns the raw typed snapshot payload (producer-schema shaped,
        this client does not reinterpret workflow semantics)."""

    def apply(self, envelope: MutationEnvelope) -> ApplyResult:
        """Run `argv --json apply --project-root <project_root>
        --actor-file <config.actor_file> --request <tmpfile>` where <tmpfile> holds
        the JSON-encoded envelope (0600, deleted after the call whether it succeeds
        or raises — never left on disk with an actor_id/payload in it). The
        --actor-file flag is mandatory per Contract A ("Other apply calls require
        --actor-file PATH; actor ID and scope must match that credential") — the
        controller reads the credential from that path itself and matches it
        against the envelope's actor_id; this client never reads the credential's
        bytes or echoes them anywhere (only the path is ever an argv token).
        Requires config.actor_file to be set; raises ControllerError if not, before
        spawning anything (an apply with no credential is a programmer error, not a
        controller round trip to discover)."""

    def _run(self, args: Sequence[str]) -> Mapping[str, object]:
        """Shared subprocess boundary for all three calls above. `cwd=project_root`
        is always set (even for contract(), which passes no `--project-root` argv
        flag — cwd and the flag are independent; "No project root" in contract()'s
        docstring means no flag, not no cwd).
        - argv = (*self._config.argv, *args) — no shell, no shlex, no str
          concatenation; argv[0] may be a bare command name, resolved via the same
          list-argv PATH lookup (no shell) `agent_settings()`'s `command` field
          already relies on today — not a new ambient-lookup risk.
        - subprocess.run(argv, cwd=project_root, capture_output=True, text=True,
          timeout=config.timeout_seconds, check=False). `capture_output=True`
          buffers all of stdout/stderr in memory before returning — there is no
          streaming hook point, so `max_output_bytes` is a **post-hoc length
          check** on `result.stdout`/`result.stderr`, not a true streaming
          truncation. This is an accepted tradeoff for this PRD: `timeout_seconds`
          already bounds wall-clock, and a contract/snapshot/apply JSON response is
          expected to be small (the 1 MiB default is a fresh guess for this client,
          not inherited from any existing bounded-read precedent — no call site in
          this repo today enforces an output-size bound, so there is nothing to
          match "the same order of magnitude" as). A genuinely hostile or runaway
          controller that floods stdout before exiting is not defended against by
          this check; it is caught only once the process exits (by `timeout_seconds`
          if it never exits, or by the length check once it does).
        - exit code or raise? — exit 0, output within bound, valid JSON -> parse;
          exit 0 and unparseable JSON, or output over max_output_bytes ->
          ControllerOutputError (PRD: "never invent acceptance from stdout
          prose"); nonzero exit -> ControllerError with the captured stderr tail
          (length-checked the same way) as detail; TimeoutExpired ->
          ControllerTimeoutError.
        - secrets: actor_file's contents are never read by this client at all — only
          the *path* is ever passed, as the `--actor-file` argv token (see apply()).
          The controller reads the credential and matches it against the envelope's
          actor_id on its own side; this client has no code path that opens
          actor_file, so it cannot leak its bytes into a log line or exception
          message by construction.
        """
```

### Retry / idempotency (PRD "preserve request identity on retry")

`apply()` performs no retries itself — retrying is the caller's decision (OVCAQ's own
supervisor retry policy belongs in `runtime.decision`, not here). What this client guarantees
is that **the same `MutationEnvelope` passed to `apply()` twice produces the same `request_id`
on the wire** — `request_id` is a required field the caller must set once and reuse across
retries; the client does not mint or mutate it. This matches Contract A's "same request/payload
replay returns the original result even after revision advances."

### `src/ovcaq/config.py` additions

```python
@dataclass(frozen=True)
class WorkflowSettings:
    prd_root: Path
    runtime_root: Path
    state_file: Path
    available_tiers: frozenset[str]
    controller_argv: tuple[str, ...] | None = None     # NEW, additive, defaults preserve callers
    contract_bundle: Path | None = None                # NEW
    actor_file: Path | None = None                     # NEW


def controller_settings(root: Path) -> ControllerConfig | None:
    """Read [workflow].controller_argv / contract_bundle / actor_file. Returns None
    when controller_argv is absent (controller integration is opt-in; most OVCAQ
    installs today have no controller configured). Raises ConfigurationError for a
    present-but-malformed value (wrong type, relative/missing contract_bundle) —
    same fail-fast posture as every other _configured_path consumer in this file."""
```

`controller_settings()` lives in `config.py`, not `workflow_client.py`, so `workflow_client`
stays provider-neutral and import-light (no `tomllib`/`_read_config` dependency) and so the
existing single place that already merges user+project TOML keeps merging this table too.

### `tools/autopilot-prerequisites`

```text
usage: autopilot-prerequisites --prd <ID> [--config PATH]

Exit 0: {"ready": true, "prd": "<ID>"}
Exit 1: {"ready": false, "prd": "<ID>", "missing": ["<unmet requirement>", ...]}
Exit 2: unknown PRD ID, or [workflow] config missing a key this PRD's graph needs
```

Dependency graph (verbatim from the PRD, hardcoded as data, not derived):

```python
_GRAPH: Mapping[str, tuple[str, ...]] = {
    "58": ("57", "62"),              # + controller core/jobs/reviews/records artifact
    "59": ("58", "63"),
    "60": ("59",),
    "61": ("60",),                   # + [autopilot].plugin_artifact with AP17 evidence
    "64": ("58",),
    "65": ("60", "61", "64"),        # + [operator].client_artifact with Tower03 evidence
}
```

Each local dependency is checked against `docs/dev/project-management/prds/done/` (exact
`000<id>-*.md` glob, matching autopilot's own `select()` convention) — never `wip/`/`backlog/`,
and never a cross-repo adjacency scan (the PRD and canonical design both forbid "sibling
checkout imports" / "implicit discovery"). Cross-repo artifacts (`[autopilot].plugin_artifact`,
`[operator].client_artifact`) are read from explicit config keys naming a local file path plus
expected digest; the tool hashes the file and compares, never fetches. An unknown PRD ID (not a
key in `_GRAPH`) is exit 2, not "ready" or "unavailable" — this tool only answers for the graph
it was given, and a caller asking about an untracked ID has a bug, not a missing prerequisite.

## Data flow

1. Caller (eventually OVCAQ's own phase routing, not built in this PRD) constructs
   `ControllerConfig` from `config.controller_settings(root)`.
2. `ControllerClient.contract()` is called once at startup to validate `protocol_major` and
   confirm required `operations`/`capabilities` are advertised — raises
   `IncompatibleContractError` before any mutation is attempted.
3. `snapshot()` reads current workflow state for display/decision purposes; no local caching
   beyond what the caller chooses to hold (PRD: "cached workflow snapshots... never become a
   second task/review machine" — this client returns the raw payload and keeps no state of
   its own between calls).
4. `apply()` sends one `MutationEnvelope`; the controller subprocess is spawned, runs to
   completion or timeout, and the typed `ApplyResult` is returned. No daemon, no persistent
   connection — one subprocess per call, matching Contract A's CLI-only transport
   (`--json contract` / `--json snapshot` / `--json apply`).
5. `tools/autopilot-prerequisites` never calls `workflow_client` at all for its *local*
   dependency checks (done-bucket file existence needs no transport); it imports only the
   shared dataclasses/error types if a future cross-repo artifact probe needs to validate a
   contract-bundle digest format consistently with `ControllerConfig`'s own validation.

## Reuse inventory

- `ovcaq.paths._checked_path` / `_trusted_path` — reused directly for `contract_bundle` and
  `actor_file` path validation (symlink-component rejection, absolute resolution) instead of
  reimplementing path safety.
- `ovcaq.config._configured_path` — reused for resolving `controller_argv[0]` is **not** a
  path (it is an argv token, possibly a bare command name the subprocess layer resolves via
  PATH exactly like `agent_settings()`'s `command` field already does) but `contract_bundle`
  and `actor_file` go through `_configured_path` exactly like `state_file`/`prd_root` do today.
- `ovcaq.drivers.base.LaunchSpec.__post_init__` — the validation shape (nonempty argv tuple,
  nonempty string elements, no shell) is the template for `ControllerConfig.__post_init__`;
  not imported (different module boundary — `workflow_client` must not depend on `drivers`,
  since the controller is not an agent driver), but the pattern is copied intentionally.
- `ovcaq.runtime.capability` subprocess calls (`subprocess.run(..., capture_output=True,
  text=True, timeout=..., check=...)`) — the argv/timeout/capture_output idiom is reused in
  `_run()`, but note none of those existing call sites enforce an output-size bound at all;
  `max_output_bytes` is new to this client, not an inherited bounded-read precedent (see
  `_run()`'s note that `capture_output=True` buffers fully before any length check can run).
  Searched for an existing generic "run argv, parse JSON, bound output" helper first
  (`rg -n "capture_output" src/ovcaq`, `rg -n "json.loads" src/ovcaq/runtime`); none is
  factored out as a shared utility today — each call site inlines its own `subprocess.run`
  (`runtime/capability.py`, `runtime/process.py`, `drivers/codex.py`). Nothing to import;
  `workflow_client._run()` is a new, narrowly-scoped instance of the same idiom, not a
  duplicate of an existing shared helper.
- `tools/check`, `tools/onboard` — existing `tools/*` are the convention
  `tools/autopilot-prerequisites` follows (standalone script, no package install step).

## Alternatives considered

1. **Smallest-diff option: a single function, no client class.** `workflow_apply(config,
   envelope) -> ApplyResult` plus two sibling functions, no `ControllerClient` object. Rejected
   because `contract()` must be called once and its result (advertised operations/capabilities)
   checked before every `apply()`/`snapshot()` call in the same process — a stateless function
   trio would force every caller to re-run `contract()` per call (extra subprocess spawn per
   mutation) or thread the contract result through manually. A thin client object that caches
   nothing durable but holds the validated `ControllerConfig` is the smaller real cost.
2. **A persistent controller subprocess (long-lived, request/response over stdin/stdout).**
   Rejected outright by Contract A itself ("No daemon, broker, database service..."); also
   conflicts with "preserve request identity on retry" being meaningful only across separate
   processes — a crashed persistent connection has no replay story.
3. **Chosen: one `ControllerClient`, one subprocess per call, `contract()` cached in-instance
   for the instance's lifetime (not across instances, not to disk).** Matches the CLI-only
   transport exactly, keeps retries simple (new process = clean replay), and is the shape
   `tools/autopilot-prerequisites` and any future OVCAQ phase-routing caller can both use
   without inventing a second transport.

## Risks & edge cases

- **`lost_ack_preserved`** (named PRD scenario): the controller subprocess is killed or the
  pipe breaks after it has durably committed but before stdout is fully read. `_run()` cannot
  distinguish "controller committed, response lost" from "controller never ran" from captured
  output alone — this is exactly why the PRD requires `request_id` reuse on retry rather than
  client-side success/failure inference. Documented explicitly in `apply()`'s docstring: a
  timeout or truncated-output error on `apply()` is **not** proof of non-commitment; the caller
  must retry with the identical envelope (same `request_id`) and trust Contract A's replay
  guarantee, never assume failure and invent a new `request_id`.
- **`incompatible_major`**: a future controller bumping `protocol_major` must fail the very
  first `contract()` call loudly, not surface as a confusing `apply()` rejection three calls
  later. Tested directly (fixture with `protocol_major: 2`).
- **`controller_timeout`**: this PRD's fixed `timeout_seconds` default (30) is a guess tuned
  for "a CLI subprocess answering a snapshot/contract/apply call", not a long agent session;
  flag for the next PRD in this chain (OV 00058/00059) to confirm against a real controller
  once AP 00018 ships, since a fake-executable fixture cannot validate real latency.
- **Likely next changes**: (1) OV 00058 will need `ControllerClient` wired into the actual
  phase-routing call sites that currently call `state.commands`/`workflow` directly — this
  design's `ControllerClient` surface is deliberately caller-agnostic so that wiring is additive,
  not a rewrite; (2) OV 00064's operations API will need its own, separate Contract C client —
  explicitly NOT reusing `ControllerClient` (Contract A and Contract C are different protocols
  with different owners), so this design does not try to generalize the transport prematurely;
  (3) a real controller will likely need the actor-file bootstrap flow (`workflow.open` on an
  absent store) exercised against a **fake** controller executable in Phase 2's integration
  test — this design's `MutationEnvelope.__post_init__` null-field rule is written now so that
  test can exist without a later interface break.
- **Boxed-in by this design**: `ControllerClient` assumes one controller process per call and
  no connection reuse; if a future requirement needs a persistent session (e.g. streaming
  `operations events`), that is Contract C's `ovcaq operations events --after SEQ` (JSONL
  stream), a different contract entirely — not a reason to add streaming here.

## Test strategy outline

- `test_transport.py`: `_run()`'s post-hoc output-length check (over `max_output_bytes` after
  the subprocess exits), timeout -> `ControllerTimeoutError`,
  nonzero exit -> `ControllerError` with captured (bounded) stderr, unparseable-JSON-on-exit-0 ->
  `ControllerOutputError` (never silently treated as success), secrets never appear in any
  raised exception's `str()` (assert `actor_file` contents, if any test fixture gives it real
  content, never appear in a captured exception message).
- `test_contract.py`: `controller_contract_fixtures` — the canonical fixture
  (`tests/fixtures/workflow/controller-v1.json`) round-trips through a **fake controller
  executable** (a small Python script matching the fixture's exit/stdout shape, same technique
  `runtime.capability`'s tests already use for fake runners) into `ControllerContract`;
  `incompatible_major` fixture (protocol_major mismatch) raises `IncompatibleContractError`;
  `lost_ack_preserved` — a fake controller that times out after writing a partial line — asserts
  `apply()` raises a timeout/output error, never a silent `ApplyResult(ok=True, ...)`;
  `MutationEnvelope.__post_init__`'s null-field rule — valid only for `workflow.open` +
  `expected_revision=0`, rejected for every other operation/field combination.
- `test_prerequisites.py`: `missing_artifact` and `unknown_prd` fail without fetch/write
  (assert no network call is reachable — run under a monkeypatched socket-denying fixture or
  simply assert no `urllib`/`requests` import exists in the module); the `_GRAPH` table's
  7-entry dependency closure (58 needs 57+62, 65 needs 60+61+64, etc.) is asserted against the
  PRD text verbatim so a future edit to the PRD's graph is caught by a failing test, not missed
  silently; a done-bucket file present vs absent flips exit 0/1 for each local dependency.
  Separately, two dedicated scenarios assert the non-numeric artifact conditions actually gate:
  PRD 61 reports exit 1/`missing` when `[autopilot].plugin_artifact` is absent or its digest
  does not match AP17 evidence, even with 60 satisfied; PRD 65 reports exit 1/`missing` when
  `[operator].client_artifact` is absent or mismatched, even with 60+61+64 satisfied. These are
  separate from the `_GRAPH` numeric closure so dropping either check silently is itself a
  test failure, not just a documentation gap.
- Integration (Phase 2, "run transport conformance against fake controller"): the
  `controller_contract_fixtures` scenario above IS this conformance run — no adjacent checkout,
  no installed upper-layer UI, `no_plugin_import` asserted by a static check (the module imports
  no `agent-plugins`/`plugins/autopilot` path, grep-enforced in the test itself, same style as
  the existing "provider-neutral modules stay free of provider strings" boundary test
  mentioned in this repo's `AGENTS.md`).
- All tests use temporary roots (`tmp_path`) for `project_root`/`contract_bundle`/`actor_file`;
  never the implementation batch's own `state.json`/runtime tree, per `AGENTS.md`.

## Review log

- Dispatch 1 (Claude): 3 blockers fixed (apply() missing `--actor-file` wiring; contract()
  missing digest-comparison against `contract_bundle`; `CHANGELOG.md`/`docs/operations.md`
  wrongly marked new when they already exist). 1 non-blocker fixed (added dedicated artifact-
  gate test scenarios for PRD 61/65 beyond the numeric `_GRAPH` closure). 1 non-blocker recorded
  only (timeout_seconds=30 default is an acknowledged guess, already flagged in Risks for
  OV 00058/00059 to confirm). 1 question recorded only (whether `ControllerClient` caches
  `contract()` in-instance — resolved by this same dispatch's fix, which now states the cache
  explicitly in both `contract()`'s docstring and `## Alternatives`).
dispatch 1 (claude): cardinal-sin 0, blocker 3, non-blocker 2, question 1

- Dispatch 2: codex unavailable, Claude fallback — the codex subprocess hit its own
  read-tooling sandbox restrictions mid-run (its `sed`/shell reads were blocked by its host's
  own hooks) and returned no parseable findings, only a trailing web-search action with no
  final answer. Took the Claude fallback.
- Dispatch 2 (claude-fallback): 1 blocker fixed (`_run()`'s docstring claimed a true streaming
  output-bound truncation that `subprocess.run(capture_output=True, ...)` cannot deliver —
  corrected to describe the real post-hoc length check, and removed the false "same order of
  magnitude as capability.py's bounded reads" precedent claim, since no existing call site
  bounds output at all). 1 non-blocker fixed (same false-precedent claim, also removed from
  `ControllerConfig.max_output_bytes` and the Reuse inventory). 2 questions recorded only
  (clarified inline: `cwd=project_root` is set for every `_run()` call including `contract()`,
  independent of whether `--project-root` is passed as an argv flag; `controller_argv[0]`'s
  PATH-lookup via list-argv `subprocess.run` is the same no-shell mechanism `agent_settings()`'s
  `command` field already uses, not a new risk — both clarifications folded into `_run()`'s
  docstring).
dispatch 2 (claude-fallback): cardinal-sin 0, blocker 1, non-blocker 1, question 2

- Dispatch 3: codex unavailable, Claude fallback — the codex subprocess again hit its own
  host's Fact-Forcing Gate PreToolUse hook mid-run (blocked a `pwd` call) and returned no
  final findings list. Took the Claude fallback.
- Dispatch 3 (claude-fallback, verification): confirmed all four prior fixes (post-hoc
  output-length check, `--actor-file` wiring, `contract_bundle` digest validation,
  `CHANGELOG.md`/`docs/operations.md` marked as edits) are present and correct. 2 new
  questions recorded only, not fixed: (1) whether `apply()` ever returns
  `ApplyResult(ok=False, error_code=...)` or always raises for every known error_code,
  leaving those `ApplyResult` fields possibly dead when `ok=True` — left for the planning
  stage to resolve as a task-level contract detail, since either choice is buildable; (2) PRD
  58's "controller core/jobs/reviews/records artifact" prerequisite has no defined config key
  or digest probe (unlike 61/65's explicit artifact checks) — this PRD's `_GRAPH` only encodes
  57/62 for PRD 58 because no `[workflow].contract_bundle`-equivalent key exists yet for that
  artifact; left as a known gap for whichever PRD (58 itself, when it lands) defines that key.
dispatch 3 (claude-fallback): cardinal-sin 0, blocker 0, non-blocker 0, question 2
result: ok
