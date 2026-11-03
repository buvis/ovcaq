# Design: Driver failure classes and neutral default tiers

PRD: `docs/dev/project-management/prds/wip/00063-driver-failure-classes-tiers-v1.md`

## Architecture fit

Both capabilities land squarely on the repo's standing boundary rule (AGENTS.md
invariant 4, capsule "Component Boundaries"): **provider code stays at the
edge**. `ovcaq.drivers.claude_events` and `ovcaq.drivers.codex_events` own
native diagnostic tables; `ovcaq.config` and `ovcaq.drivers.base` must stay
free of provider and model identifiers; `ovcaq.runtime` consumes only the
normalized `FailureClass`.

That rule is machine-enforced by `tests/drivers/test_neutrality.py`. Its
`shared_modules()` scans `src/ovcaq/*.py` (so `config.py`) plus
`src/ovcaq/drivers/base.py`, and forbids the literals `claude`, `codex`,
`anthropic`, `haiku`, `opus`, `sonnet`, `gpt-` anywhere in that source. It does
**not** scan `src/ovcaq/drivers/__init__.py`, which is the only reason
`DEFAULT_PHASE_TIERS = {"build": "sonnet", ...}` can live there today. So the
PRD's move of that constant into `config.py` is not a cosmetic relocation: it is
only legal **because** the values become the neutral keys `standard` and `deep`
at the same time. The two halves of Phase 1 task 1 cannot be separated.

The two capabilities are independent. Classification touches only the two
`*_events.py` tables and `runtime/decision.py`'s consumption of
`FailureClass.RATE_LIMIT` (unchanged code, reachable from Claude terminal text
today only via usage-limit prose — `tests/drivers/test_claude_decode.py:524`
already pins a reset-less `rate_limit` — and newly reachable for the 429 and
network strings). Tiers touches
`config.py`, `drivers/base.py`, both drivers, `drivers/edge.py` and
`runtime/supervisor.py`. They are sequenced Classes-then-Tiers only so the test
gate runs once.

### The tier round trip (load-bearing, and not obvious from the PRD)

A resolved model makes **three** hops today, and a design that misses the middle
hop will produce a `default_tiers` that silently never applies:

1. `config.resolve_phase_route` resolves a phase to a tier key, then returns
   `model=selected.tiers[tier]` — the *model*, from `agent_settings(root)`.
2. `drivers/edge.py`'s `_map_model_to_tier` inverts `settings.tiers`
   (`{model: tier}`) and rewrites the `LaunchRequest` back to the *tier key*.
3. `ClaudeDriver.build_launch` / `CodexDriver.build_launch` map that tier key
   forward to a model again via `settings.tiers`.

`resolve_phase_route` reads `agent_settings(root)` directly and never sees the
driver instance, which is exactly why it needs `default_tiers` passed in
(step 1), while the drivers need the merged table on their own `_settings` so
steps 2 and 3 round-trip (the inverse map in step 2 must contain the neutral
model, or the tier key never comes back).

## Module placement

All edits; **no new source files**. One new test file is not needed either —
every named test lands in an existing module.

| Path | Change |
|---|---|
| `src/ovcaq/drivers/claude_events.py` | edit `_FAILURE_MARKERS` |
| `src/ovcaq/drivers/codex_events.py` | edit `classify_failure` alternations |
| `src/ovcaq/config.py` | add `DEFAULT_PHASE_TIERS`, `NEUTRAL_TIERS`; drop the lazy driver import in `_supervisor_phases`; add neutral keys in `workflow_settings`; add `default_tiers` to `resolve_phase_route` |
| `src/ovcaq/drivers/__init__.py` | remove `DEFAULT_PHASE_TIERS` and its `__all__` entry |
| `src/ovcaq/drivers/base.py` | add `default_tiers` to the `AgentDriver` protocol |
| `src/ovcaq/drivers/claude.py` | add `default_tiers`; merge into `_settings` |
| `src/ovcaq/drivers/codex.py` | add `default_tiers`; merge into `_settings`; suppress the `-m` segment for the default literal |
| `src/ovcaq/runtime/supervisor.py` | pass `default_tiers=` at both `resolve_phase_route` call sites (lines 162, 447) |
| `tests/drivers/test_adapter_failure_classes.py` | two table tests |
| `tests/workflow/test_configuration.py` | `neutral_default_tiers_are_always_available`; amend the two assertions at :160 and :165 |
| `tests/drivers/test_driver_v2.py` | `api_two_declares_default_tiers` |
| `tests/drivers/test_claude_launch.py` | `claude_default_tiers_map_standard_and_deep` |
| `tests/drivers/test_codex_launch.py` | `codex_default_tier_omits_model_segment` |
| `tests/runtime/test_adapter_launch_routing.py` | `unconfigured_project_routes_through_driver_default_tiers` |
| `docs/driver-protocol.md`, `docs/operations.md`, `CHANGELOG.md` | documentation |

**Test files the default-key change reaches that the PRD does not name.** The
*symbol* `DEFAULT_PHASE_TIERS` has no test consumer, but its *values* — the
tier keys `sonnet` and `opus` — are asserted literally in seven more files, and
an implementor working only from the PRD's file list will leave them red:

| Path | What must change |
|---|---|
| `tests/workflow/test_supervisor_configuration.py` | the default-tier expectations at `:47-49`, the parametrization at `:69-71`, `:103`, `:123`, and `ResolvedPhaseRoute(..., "sonnet", "other-s", ...)` at `:141`. Its fixture tier tables (`:29`, `:136`) must define `standard`/`deep` (keeping `custom` for the override cases). `:207`, `:214`, `:231`, `:436` use a tier key only as an arbitrary string and need no change beyond consistency. |
| `tests/runtime/test_supervisor_preflight.py` | `HEALTHY_TIERS` at `:19`, the `"Unknown agent tier: sonnet"` message assertion at `:212`, the fixture table at `:222`, the default-tier assertion at `:244`. The unknown-tier parametrization at `:87` (`sonnet-x`, `opusine`) still works as arbitrary unknown strings. |
| `tests/runtime/test_supervisor.py` | the fixture table at `:201`, the phase/tier pairs at `:225-227`, the fixture at `:555` and the explicit `PhaseSettings` at `:565-566`. |
| `tests/runtime/test_supervisor_adapters.py` | the fixture table at `:65` and the expected tier mapping at `:75`. |
| `tests/runtime/test_rework_health.py` | the fixture table at `:43`. |
| `tests/runtime/test_adapter_health.py` | the tier mapping at `:64` and the fixture table at `:290`. |
| `tests/packaging/test_installed_supervisor_cli.py` | **a real break, and the worst kind.** Its fixture table at `:241` is `tiers = { sonnet = "model-s", opus = "model-o" }` and its `[phases.*]` tables set `timeout_seconds` only, so the tier comes from `DEFAULT_PHASE_TIERS`; `_assert_configured_invocations` at `:366` then asserts the exact argv (`model-o` for review, else `model-s`). After the rename the merge resolves from `ClaudeDriver.default_tiers` and the installed CLI emits `--model sonnet`/`--model opus` instead — failing `test_installed_foreground_run_drains_committed_build_review_and_done` and `test_installed_pause_resume_and_invalid_run_use_json_envelopes_from_nested_cwd`. This is exactly the silent-wrong-model pathology § Migration plan describes, caught by a real test. Fix the fixture table to declare `standard`/`deep`. |
| `tests/drivers/test_driver_v2.py` | not a breakage (`tiers={"sonnet": "fixture-model"}` at `:18` is an arbitrary key), but migrate it to `standard` for consistency — the new `api_two_declares_default_tiers` lands in this very module, so leaving a model name in its fixture would be odd. |

Two call sites checked and needing **no** change: `tests/drivers/test_codex_prompt.py:82`
is the only `resolve_phase_route` call outside `supervisor.py`; it passes
`phase_settings=PhaseSettings("standard", ...)` and its config already declares
`[agents.codex.tiers] standard` at `:65`, so it omits `default_tiers` and thereby
exercises the `default_tiers=None` back-compatibility contract. And
`tests/workflow/test_supervisor_configuration.py:443` (`phase.tier = "opus"`)
only proves the dataclass is frozen; the value is arbitrary.

**Fake drivers must gain `default_tiers`.** `Supervisor` reads
`self._driver.default_tiers`, so every stand-in driver handed to `Supervisor`
needs the attribute or the call raises `AttributeError`. **The supervisor reads
the attribute directly — no `getattr` fallback.** `default_tiers` is a hard
protocol requirement from this PRD on, so a driver missing it fails loudly at
the first route resolution rather than silently routing on configuration alone.

**A runtime `AttributeError` is the only signal.** mypy does not help here:
`pyproject.toml` sets `files = ["src/ovcaq"]`, so tests are outside the checked
set. The four fakes below are therefore the complete guard, and the list has to
be right:

| Fake | Why it matters |
|---|---|
| `tests/runtime/test_supervisor.py:85` (`class Driver`) | its `harness` is imported by `test_supervisor_preflight.py`, `test_rework_health.py`, `test_rework_thread_conflict.py` and `test_supervisor_adapters.py` |
| `tests/runtime/test_supervisor_process.py:49` (`class ProcessDriver`) | own `Supervisor` construction |
| `tests/integration/test_observer_terminal_cleanup.py:152` (`class Driver`) | `Supervisor(...)` at `:282`, `supervisor.run()` at `:291` |
| `tests/integration/test_supervisor_live_telemetry.py:41` (`class LiveDriver`) | `Supervisor(...)` at `:222`, `supervisor.run()` at `:232` |

Each gains, **exactly**:

```python
    default_tiers: Mapping[str, str] = field(default_factory=dict)
```

plus `Mapping` in each file's `collections.abc` import — none of the four
imports it today (`tests/runtime/test_supervisor.py:9`,
`test_supervisor_process.py:10`, `tests/integration/test_supervisor_live_telemetry.py:9`,
`test_observer_terminal_cleanup.py:13`). All four carry
`from __future__ import annotations`, so the omission is ruff F821 rather than
an import-time crash — still a failing gate.

Two reasons the value and the default are not free choices:

- All four fakes are dataclasses whose trailing fields already have defaults, so
  the new field needs one; a bare `= {}` raises `ValueError: mutable default` at
  class creation. It must be `field(default_factory=dict)`.
- The default must be **empty**. `tests/runtime/test_supervisor_preflight.py:195`
  (`test_preflight_resolves_routes_for_the_driver_agent`) exists to prove an
  unresolvable neutral tier fails preflight: it points the driver at agent
  `remote` whose table is `{ haiku = "model-h" }` and asserts
  `Unknown agent tier: sonnet` (becoming `standard`). Under
  `{**default_tiers, **selected.tiers}` that negative survives **only** while the
  fake's `default_tiers` is empty. A fake carrying `standard`/`deep` would make
  preflight succeed and silently void the test.

Two further stand-ins are annotated as `AgentDriver` but never reach
`Supervisor` — `tests/drivers/test_contract.py:34` (`FakeDriver`, used as
`driver: AgentDriver` at `:283` and `:310`) and
`tests/drivers/test_discovery.py:25` (`RegistryDriver`, returned from a
`-> AgentDriver` factory at `:68`/`:158`). They become protocol-incomplete and
**no gate catches it** (mypy does not scan tests; nothing calls the attribute).
Left as optional tidy-ups, named here so the omission is deliberate rather than
missed.

## Interfaces & contracts

### `src/ovcaq/config.py`

Module-level, provider-neutral (no model name may appear):

```python
# Neutral tier keys every driver maps to its own models.
DEFAULT_PHASE_TIERS = {"build": "standard", "review": "deep", "done": "standard"}
NEUTRAL_TIERS = frozenset(DEFAULT_PHASE_TIERS.values())
```

`NEUTRAL_TIERS` is `frozenset({"standard", "deep"})` derived from the table, not
a second hand-written literal, so the two can never drift.

`_supervisor_phases` keeps its body unchanged except that the line

```python
        from ovcaq.drivers import DEFAULT_PHASE_TIERS
```

is **deleted** — the constant is now module-local. (There is no `config` ↔
`drivers` import cycle to credit the lazy import with:
`src/ovcaq/drivers/__init__.py` imports only `ovcaq.drivers.base`, which imports
only `ovcaq.events`. The deferred import bought nothing; the move simply removes
it.)

`workflow_settings` changes exactly one expression. Line 310's

```python
        frozenset(tiers if available_tiers is None else available_tiers),
```

becomes

```python
        frozenset(
            NEUTRAL_TIERS.union(tiers)
            if available_tiers is None
            else available_tiers
        ),
```

**Contract:** the neutral keys are added **only on the default path**. An
explicit `available_tiers=` argument is still honoured verbatim, including the
empty collection. `workflow_settings(root, available_tiers=[]).available_tiers`
stays `set()`; `available_tiers=["custom"]` stays `{"custom"}`.

`resolve_phase_route` gains one keyword-only parameter and consults a merged
table:

```python
def resolve_phase_route(
    root: Path,
    phase: str,
    *,
    agent: str | None = None,
    phase_settings: PhaseSettings | None = None,
    default_tiers: Mapping[str, str] | None = None,
) -> ResolvedPhaseRoute:
```

Inside, after `resolved` is built, the existing two lines

```python
    if resolved.tier not in selected.tiers:
        raise ConfigurationError(f"Unknown agent tier: {resolved.tier}")
```

become

```python
    tiers = (
        dict(selected.tiers)
        if default_tiers is None
        else {**default_tiers, **selected.tiers}
    )
    if resolved.tier not in tiers:
        raise ConfigurationError(f"Unknown agent tier: {resolved.tier}")
```

and the `ResolvedPhaseRoute` is constructed with `tiers[resolved.tier]` in place
of `selected.tiers[resolved.tier]`.

**Contract:** `default_tiers=None` reproduces today's behaviour byte for byte,
including the `Unknown agent tier: <tier>` message text. Configured tiers always
win over default tiers (`{**default_tiers, **selected.tiers}` — configuration
last). `ResolvedPhaseRoute`'s field names, order and types are unchanged.

### `src/ovcaq/drivers/base.py`

`AgentDriver` gains one attribute declaration, directly under `name`:

```python
class AgentDriver(Protocol):
    name: str
    default_tiers: Mapping[str, str]
```

`Mapping` is already imported in this module. **No model name, driver name or
provider word may appear here or in any comment on it** —
`tests/drivers/test_neutrality.py` scans `base.py`. `DRIVER_API_VERSION` stays
`2`: the attribute is additive and both bundled drivers implement it.

### `src/ovcaq/drivers/claude.py`

```python
class ClaudeDriver:
    name = "claude"
    default_tiers: Mapping[str, str] = MappingProxyType(
        {"standard": "sonnet", "deep": "opus"}
    )
```

**Import delta, required:** `claude.py` has neither name and no
`from __future__ import annotations`, so a class-body annotation is evaluated
eagerly and the block above raises `NameError` at import as written. Add
`Mapping` to the existing `from collections.abc import Iterable` (`:9`) and add
`from types import MappingProxyType`. Also add `replace` to
`from dataclasses import asdict` (`:10`) for the merge below.

A class-level read-only mapping (`types.MappingProxyType`), so neither the class
attribute nor an instance can mutate the shared table. `sonnet` and `opus` are
the aliases the Claude CLI accepts.

In `__init__`, as the last statement before `self._settings` is assigned:

```python
        settings = replace(
            settings, tiers={**self.default_tiers, **settings.tiers}
        )
```

using `dataclasses.replace`; `AgentSettings` is a frozen dataclass whose
`__post_init__` re-validates and re-freezes `tiers` into a `MappingProxyType`.
Configured tiers win. `build_launch` is otherwise unchanged: `standard` and
`deep` are now in `settings.tiers`, so the existing
`if model in settings.tiers: model = settings.tiers[model]` branch resolves them
and the `Unknown Claude model tier` error is unreachable for them.

### `src/ovcaq/drivers/codex.py`

```python
CODEX_DEFAULT_MODEL = "default"


class CodexDriver:
    name = "codex"
    default_tiers: Mapping[str, str] = MappingProxyType(
        {"standard": CODEX_DEFAULT_MODEL, "deep": CODEX_DEFAULT_MODEL}
    )
```

**Import delta, required:** same as Claude for the two mapping names — add
`Mapping` to `from collections.abc import Iterable` (`:9`) and add
`from types import MappingProxyType`; `codex.py:10` already imports `replace`,
so do **not** add it again (ruff F811).

Same `replace(...)` merge in `__init__` as Claude.

In `build_launch`, the model segment at line 168 becomes conditional on the
literal as well as on `None`:

```python
                *(
                    ("-m", model)
                    if model is not None and model != CODEX_DEFAULT_MODEL
                    else ()
                ),
```

**Contract:** when the resolved model is the literal `default`, `argv` carries
no `-m` segment at all and the Codex CLI uses its own configured model. A
configured `[agents.codex.tiers]` value is emitted verbatim and is never
swallowed — the suppression keys on the exact literal `default`, not on
"came from a default table". `default` is therefore a **reserved tier value**
for the Codex driver.

### `src/ovcaq/runtime/supervisor.py`

Both existing calls gain one argument and nothing else:

```python
                resolve_phase_route(
                    self._root,
                    phase,
                    agent=self._driver.name,
                    phase_settings=self._settings.phases[phase],
                    default_tiers=self._driver.default_tiers,
                )
```

(line 162, in `preflight`) and

```python
        route = resolve_phase_route(
            self._root,
            phase,
            agent=driver.name,
            phase_settings=self._settings.phases[phase],
            default_tiers=driver.default_tiers,
        )
```

(line 447, in `_attempt`, where the local `driver = self._driver` already
exists). The supervisor reads the attribute off the protocol; it names no
provider and no model, so it stays neutrality-clean.

### `src/ovcaq/drivers/claude_events.py`

`_FAILURE_MARKERS` keeps its tuple-of-pairs shape, its entry order and
`failure_payload`'s first-match-wins precedence. Only marker tuples grow:

```python
_FAILURE_MARKERS = (
    ("permission", ("permission denied", "operation not permitted")),
    (
        "authentication",
        (
            "authentication",
            "unauthorized",
            "invalid api key",
            "oauth",
            "token has expired",
            "token expired",
            "expired token",
            "not logged in",
            "http 401",
            "status 401",
        ),
    ),
    (
        "rate_limit",
        (
            "hit your session limit",
            "hit your usage limit",
            "hit your weekly limit",
            "usage limit reached",
            "http 429",
            "status 429",
            "too many requests",
            "rate limit",
            "rate-limit",
            "rate_limit",
        ),
    ),
    (
        "connectivity",
        (
            "enotfound",
            "dns",
            "socket hang up",
            "connection refused",
            "connection reset",
            "api unavailable",
            "econnreset",
            "etimedout",
            "econnrefused",
            "eai_again",
            "getaddrinfo",
        ),
    ),
    ("timeout", ("timed out", "timeout")),
)
```

**Contracts that must hold:**

- `failure_payload` matches **lowercased substrings**; the comparison is
  `marker in lowered`. So every numeric marker carries its context word
  (`http 401`, `status 401`, `http 429`, `status 429`) and a bare `401` or `429`
  never classifies. **This honours only the context-word half of hold 00056.**
  A substring matcher has no word-boundary notion, so `"HTTP 4290"` and
  `"HTTP 429000"` *do* contain `http 429` and will classify as `rate_limit`,
  where Codex's `\b(?:...)\b` wrapper pins exactly those as `UNKNOWN`
  (`tests/drivers/test_adapter_failure_classes.py:174-183`). **Accepted, not
  overlooked:** matching the Codex guarantee would mean converting the Claude
  table from substrings to regexes, which is a rewrite of
  `failure_payload`'s matcher rather than the table extension the PRD asks
  for, for a string shape (`HTTP 4290`) that no provider emits. The asymmetry is
  pinned by a named negative row (§ Test strategy) so it stays a decision rather
  than a surprise.
- `failure_payload`'s signature, its `"agent"` fallback for an unmatched string,
  its `"unknown"` for a non-string, and the literal
  `"Malformed terminal error evidence"` detail are all unchanged.
- Precedence is positional: `authentication` precedes `rate_limit` precedes
  `connectivity` precedes `timeout`. `etimedout` sits under `connectivity`,
  which is reached before the `timeout` entry, so `connect ETIMEDOUT` yields
  `connectivity` rather than `timeout`.

### `src/ovcaq/drivers/codex_events.py`

In `classify_failure`, two alternations grow. The `status` prefix regex, the
`\b(?:...)\b` wrapper, the entry order and the AUTHENTICATION-to-AGENT
precedence are unchanged.

```python
        (
            FailureClass.AUTHENTICATION,
            (
                rf"{status}401|unauthorized|not logged in|"
                r"(?:invalid|expired) credentials?|"
                r"oauth|token (?:has )?expired|expired token"
            ),
        ),
```

```python
        (
            FailureClass.CONNECTIVITY,
            (
                rf"{status}(?:502|503)|connection reset|connection refused|"
                r"connection failed|dns|network unreachable|server unavailable|"
                r"stream disconnected|model is at capacity|"
                r"econnreset|etimedout|econnrefused|enotfound|getaddrinfo|"
                r"eai_again"
            ),
        ),
```

**Contracts that must hold:**

- `classify_failure(detail: str) -> FailureClass` — signature unchanged, return
  type unchanged, `FailureClass.UNKNOWN` fallback unchanged.
- The whole pattern is wrapped in `\b(?:...)\b`, so a numeric status still needs
  its `status` prefix and `"server-429-id"` style identifiers stay unknown.
- `"Authentication failed"` and `"MCP server authentication failed"` must stay
  `UNKNOWN`: the AUTHENTICATION alternation deliberately contains no bare
  `authentication` alternative, and none of the added alternatives matches those
  strings. This is a **pinned negative**, not an omission.
- The four hold-00056 strings are pinned only, not changed:
  `"unexpected status 503 Service Unavailable"` → CONNECTIVITY,
  `"unexpected status 502 Bad Gateway"` → CONNECTIVITY,
  `"unexpected status 403 Forbidden"` → PERMISSION,
  `"exceeded retry limit, last status: 429 Too Many Requests"` → RATE_LIMIT.

## Migration plan (configured projects)

The default tier keys change from `sonnet`/`opus` to `standard`/`deep`, and that
is a **breaking change to the configuration contract**, not just an internal
move. The failure mode is silent, so it needs stating plainly:

A project that today declares `[agents.claude.tiers] sonnet = "model-s", opus =
"model-o"` and sets no `[phases] tier` resolves `build` to tier `sonnet` →
model `model-s`. After this change `build` defaults to tier `standard`, which is
absent from that table, so the merge `{**default_tiers, **selected.tiers}`
resolves it from the **driver's** table and launches `--model sonnet` — a model
alias the Claude CLI accepts — instead of the operator's `model-s`. No error, no
warning, a different model.

**Plan.** The affected surface is bounded and entirely in-repo: OVCAQ has **no
releases** (GitHub shows none) and ships **no root `ovcaq.toml`**, so there is no
installed-operator config to migrate — only the seven test-fixture files listed in
§ Module placement. The migration is therefore documentation plus fixtures:

1. Every fixture table in those six files declares `standard` and `deep`
   (keeping any `custom`/extra keys the override tests need). Done as part of
   Phase 1 task 1, not deferred.
2. The upgrade note is **split between the two docs on purpose**, because the
   PRD's own Phase 2 acceptance criteria contradict each other otherwise. The
   PRD requires `rg -n "sonnet|opus" docs/operations.md` to find **nothing**,
   while its Risks section says to document the `opus` frontmatter mapping in
   `docs/operations.md`. Both cannot hold if the note names the old keys. The
   split, which satisfies the acceptance check and the intent:
   - `docs/operations.md` carries the **neutral** half: a
     `[agents.<agent>.tiers]` table must now define `standard` and `deep`; a
     table defining neither neutral key silently falls through to the driver's
     own models; and a PRD frontmatter floor applies only when its value is a
     tier key in that table (stated as a rule, with a neutral placeholder, not
     with a model name). The edit site is `docs/operations.md:80-81`, whose
     "Frontmatter receives keys from `[agents.<agent>.tiers]` for the configured
     top-level `agent`" stops being the whole truth once `workflow_settings`
     unions the neutral keys: **amend that sentence**, do not merely append
     below it.
   - `docs/driver-protocol.md` carries the **concrete** half: the old default
     keys, the per-driver `default_tiers` tables, the reserved Codex `default`
     literal, and a worked `[agents.<agent>.tiers]` example mapping a model-name
     floor. `driver-protocol.md` is not scanned by the PRD's check, and
     provider-specific model names are exactly what a driver-protocol document
     is for.

   Flagged rather than resolved by editing the PRD: this design never edits a
   PRD. If a planner prefers to keep the migration prose in
   `docs/operations.md`, the PRD's `sonnet|opus` acceptance line must be amended
   first — a deliberate decision, not a quiet one.
3. `CHANGELOG.md` records this as a **Changed** (breaking) entry naming the old
   and new key names, per the PRD's Phase 2 task.

**Rejected:** emitting a warning when a configured tier table defines neither
neutral key. It is new validation code for a condition that, with no releases
and no shipped config, has exactly zero real instances today, and the merge is
*meant* to let a partial table fall through to driver defaults — that is the
whole feature. Recorded here rather than built, so the decision is on the
record rather than made by silence.

**Rollback.** No persistent state and no schema version are touched: the state
file, `ResolvedPhaseRoute`, `PhaseSettings` and `DRIVER_API_VERSION` are all
unchanged, and no stored value is rewritten. To be precise rather than
reassuring: `state.json` *does* persist tier strings —
`src/ovcaq/state/schema.py:131` (`tier`), `:124` (`from_tier`), `:152`, written
by `src/ovcaq/state/commands.py:223` and `:334-335` — but those carry **PRD
frontmatter** tiers, not phase tiers, and this change neither reads nor
rewrites them. Rollback is `git revert` of the
tiers commits plus restoring the fixture tables; nothing on disk needs
repairing afterwards.

## Data flow

**Classification.** A provider's terminal text reaches
`claude_events.failure_payload` (producing a `failure_class` string in the
observation payload) or `codex_events.classify_failure` (producing a
`FailureClass`). The decoder publishes a normalized observation;
`events/reducer.py:_session_summary` records the class on the `SessionSummary`;
`runtime/decision.py:_failure_decision` branches on it. **`decision.py` is not
edited**, so the whole behavioural payoff is which branch a string now takes.
The real branch map (`src/ovcaq/runtime/decision.py:197-232`):

| class | decision |
|---|---|
| `RATE_LIMIT` | WAIT, **conditionally**: only while `retries.rate_limit < policy.rate_limit_retries` **and** `summary.rate_limit_reset_at` is an aware instant within `policy.rate_limit_wait_seconds`. Otherwise HALT, `"No bounded rate-limit retry remains"`. |
| `CONNECTIVITY` | WAIT unconditionally for `policy.connectivity_wait_seconds` while retries remain, then HALT `"Connectivity retries exhausted"`. |
| `PERMISSION`, `AUTHENTICATION` | HALT, `"Session requires operator access"`. No retry. |
| anything else, unsuccessful | RETRY up to `policy.died_retries`, then PARK (or HALT with no PRD), `"Unsuccessful session retries exhausted"`. |

So the per-diagnostic consequences of this PRD, stated honestly:

- **Auth expiry** (`OAuth token has expired`): was `agent` → died-retries →
  **PARK a healthy PRD**. Becomes `authentication` → **HALT for operator
  access**. This is the headline win, and it is the exact pathology recorded in
  the project memory `false-park-auth-revoked`: a revoked token parked whatever
  PRD was current. HALT names the real cause instead.
- **Network faults** (`ECONNRESET`, `ETIMEDOUT`, `getaddrinfo`): was `agent` →
  died-retries → PARK. Becomes `connectivity` → a **bounded wait and retry**,
  which is the one genuine new wait path. Codex already had these for some
  strings; Claude did not.
- **A 429 with a live rate-limit observation**: Claude's
  `rate_limit_payload` already emits `RATE_LIMIT_STARTED` with `reset_at`, and
  `reducer.py:116-119` sets `summary.rate_limit_reset_at` from it independently
  of the failure class — so this case gets the **bounded wait**, as intended.
- **A 429 in terminal text with no live-limit observation**: was `agent` →
  died-retries → PARK. Becomes `rate_limit` with `reset_at is None` → **HALT
  immediately**, zero retries. **Accepted deliberately**: a rate limit is not
  cured by retrying a session, and halting loudly beats burning
  `died_retries` sessions and then mislabelling a healthy PRD as sick. It is a
  behaviour change the PRD's framing does not spell out, so it is recorded here
  rather than discovered in review. Making the reset-less `RATE_LIMIT` path wait
  on a policy default instead of halting would mean editing
  `decision.py:197-213`, which is outside this PRD's file list — **follow-up
  work, not silently assumed**.

One further delta worth naming: `reducer.py:120` upgrades only `UNKNOWN`/`AGENT`
to `RATE_LIMIT` when a live limit exists, and overwrites `failure_detail` with
the live-limit detail while doing so. Once Claude classifies a 429 as
`rate_limit` directly, that upgrade no longer fires, so the preserved
`failure_detail` is the **terminal text** rather than the live-limit summary.
`reset_at`, and therefore the wait, are unaffected. Cosmetic, and arguably
better evidence; named so it is not read as a regression.

**Tiers, unconfigured project.** `supervisor_settings` →
`_supervisor_phases` → `DEFAULT_PHASE_TIERS` (now from `config.py`) gives
`PhaseSettings.tier` = `standard` for build and done, `deep` for review. The
supervisor calls `resolve_phase_route(..., default_tiers=driver.default_tiers)`;
with no `[agents.<agent>.tiers]`, the merged table is the driver's own, so the
tier resolves instead of raising `Unknown agent tier: sonnet`, and
`route.model` is the driver's model (Claude `sonnet`/`opus`, Codex `default`).
`edge._map_model_to_tier` inverts the driver's **merged** `_settings.tiers` and
rewrites the request back to `standard`/`deep`; `build_launch` maps it forward
again and emits `--model sonnet` (Claude) or no `-m` at all (Codex).

**Tiers, configured project.** Identical, except `{**default_tiers,
**settings.tiers}` lets the configured value win at every hop, so a project that
maps `deep` to a larger Codex model gets `-m <that model>`.

**Frontmatter floor.** `workflow_cli` passes
`settings.available_tiers` into `frontmatter.parse`, which accepts
`default_model:` only when the value is in that set. Adding the neutral keys
there makes `default_model: standard` and `default_model: deep` work with no
configuration at all.

## Reuse inventory

Searched with `rg` over `src`, `tests`, `docs` and `tools`. Verb/noun synonym
pairs tried: classify/map/match/detect × failure/error/diagnostic/marker;
default/fallback/neutral × tier/model/route/phase; merge/overlay/combine ×
tiers/settings. `~/.claude/rules-library/rationalizations.md` was not consulted
(host-local file, outside this repo); the synonym sets above are my own, as the
skill's fallback allows.

- **`_FAILURE_MARKERS` + `failure_payload`** (`src/ovcaq/drivers/claude_events.py:223`)
  — the existing table-and-loop with first-match-wins precedence. Reused as is;
  only marker tuples are added. No new helper.
- **`classify_failure`** (`src/ovcaq/drivers/codex_events.py:298`) — the existing
  ordered `(FailureClass, pattern)` tuple with a shared `status` prefix regex and
  a `\b(?:...)\b` wrapper. Reused as is; only alternations are added.
- **`FailureClass`** (`src/ovcaq/events/model.py:60`) — the `StrEnum` already has
  every class this PRD needs (`RATE_LIMIT`, `CONNECTIVITY`, `PERMISSION`,
  `AUTHENTICATION`, `TIMEOUT`, `AGENT`, `UNKNOWN`). **No new enum member.**
- **`_map_model_to_tier`** (`src/ovcaq/drivers/edge.py:16`) — already inverts
  `settings.tiers`. Needs no edit: merging the defaults into `_settings` in each
  driver's `__init__` is what makes it see the neutral keys. This is the reuse
  that avoids a second mapping layer.
- **`dataclasses.replace` on `AgentSettings`** (`src/ovcaq/config.py:95`) — the
  frozen dataclass re-validates and re-freezes `tiers` in `__post_init__`, so a
  merge needs no bespoke immutable-copy helper. `replace` is already imported in
  `edge.py`, `runtime/supervisor.py` and `codex.py`
  (`src/ovcaq/drivers/codex.py:10`, `from dataclasses import asdict, replace`).
  **Only `claude.py` needs the import added** (`:10` imports `asdict` alone);
  adding it to `codex.py` would be a duplicate (ruff F811).
- **`types.MappingProxyType`** — already the codebase's read-only-mapping idiom
  (`config.py`, `drivers/base.py`). Used for `default_tiers`; no new wrapper
  type.
- **`tests/drivers/test_neutrality.py`** — the existing AST-and-source scanner
  that enforces the whole point of this PRD. Needs no edit; it is the gate.
- **`PhaseSettings` / `ResolvedPhaseRoute`** (`src/ovcaq/config.py:434`, `:451`)
  — reused unchanged; no field is added to either.
- Nothing found for a pre-existing "merge default tiers" or "driver default
  model table" helper. Greps tried: `rg -n "default_tiers" src tests docs`
  (empty, and the pattern is proven by the later non-empty search for
  `DEFAULT_PHASE_TIERS` in the same tree), `rg -n "DEFAULT_PHASE_TIERS" tests
  docs tools` (empty — the *symbol* has no test or doc consumer, but its
  *values* do: `rg -n "sonnet|opus" tests` finds the seven files listed in
  § Module placement, so the move is **not** internal),
  `rg -n "fallback_model|allow_explicit_model" src/ovcaq`
  (found only the Claude/Codex option checks, which are a different concern).

## Alternatives considered

**A. Smallest diff: widen `available_tiers` and the shipped sample config only.**
Create a root `ovcaq.toml` (the repo ships none) declaring
`standard`/`deep`, and leave
`DEFAULT_PHASE_TIERS` where it is. Zero protocol change, no `resolve_phase_route`
signature change. Rejected: it fixes nothing for *another* project, which is the
PRD's stated user ("operators running Codex or Claude without a hand-written
tier table"), and it leaves `sonnet`/`opus` sitting in a shared module, which is
the boundary defect. The failure mode this PRD removes — `Unknown agent tier:
sonnet` on a config-free project — would survive untouched.

**B. Chosen: neutral keys in `config.py` + per-driver `default_tiers`, merged
into driver settings, threaded through `resolve_phase_route`.** Larger by one
protocol attribute, one keyword parameter and two one-line constructor merges.
What the extra size buys: model names leave the neutrality-scanned surface for
good (enforced, not promised); a third-party driver can ship its own defaults
through the documented protocol attribute rather than demanding a config file;
and the configured-wins precedence is expressed once, as
`{**default_tiers, **settings.tiers}`, at each of the two places that resolve a
tier.

**C. Resolve defaults entirely inside `build_launch`, no `resolve_phase_route`
change.** Each driver falls back to its own table when a tier is unknown.
Rejected: `resolve_phase_route` would still raise `Unknown agent tier` *before*
`build_launch` is ever reached — `Supervisor.preflight` calls it for all three
phases precisely to fail fast — so the bug would persist at the earlier gate.
It would also split tier knowledge across two layers with no single place to
read the precedence.

## Risks & edge cases

- **Marker over-reach (Claude).** `failure_payload` matches plain lowercased
  substrings, so `oauth` and `rate limit` can match prose. `oauth` sits in the
  `authentication` tuple, which is reached before `rate_limit` and
  `connectivity`, so a string naming both an OAuth problem and a 429 classifies
  as `authentication` — deliberate, and the table test must pin it. The negative
  rows (bare `401`, bare `429`, an unmatched sentence staying `agent`, a
  non-string staying `unknown`) are what keep this honest.
- **`etimedout` vs the `timeout` class.** `connectivity` precedes `timeout`
  positionally, so `connect ETIMEDOUT` is `connectivity`. The PRD's own error
  case asserts exactly this. A future reorder of `_FAILURE_MARKERS` would flip
  it silently; the table test is the guard.
- **Codex `getaddrinfo` and the `\b` wrapper.** `getaddrinfo ENOTFOUND api.x`
  matches on two alternatives; both are CONNECTIVITY, so order does not matter
  here. But `eai_again` contains an underscore, which is a word character, so
  `\beai_again\b` behaves as intended only when the token is not glued to
  adjacent word characters. Worth a positive row with realistic surrounding
  text.
- **Codex reverse-map collision.** `edge._map_model_to_tier` builds
  `{model: tier}`, so Codex's two neutral keys both mapping to `default`
  collapse to a single entry (`default` → whichever comes last, `deep`). Harmless
  **only because** both keys resolve to the same literal and `build_launch` then
  suppresses the segment either way — the emitted argv is identical for
  `standard` and `deep`. If a future Codex `default_tiers` gives the two keys
  different models, this collision becomes a real bug: the inverse map would
  send one tier's model to the other tier's key. Flagging it rather than
  pre-building a fix (`drivers/edge.py` is out of this PRD's file list).
- **`default` as a reserved Codex tier value.** A project that legitimately has a
  model literally named `default` can no longer pass it through `-m`. Documented
  in `docs/operations.md` as reserved.
- **This repo's own PRDs carry `default_model: opus`.** With neutral
  `available_tiers`, `opus` is still absent unless `[agents.claude.tiers]` maps
  it, so `frontmatter.parse` emits
  `tier 'opus' is unavailable; applying no tier floor`. That is a *warning*, not
  an error, and the floor is simply not applied — but it means OVCAQ-on-OVCAQ
  gets no tier floor until its own config maps `opus`. The worked mapping goes
  in `docs/driver-protocol.md`, with the neutral rule in `docs/operations.md`
  (§ Migration plan item 2 explains why the two are split). Not a code change
  here.
- **`test_configuration.py:165` breaks.** The existing assertion
  `available_tiers == set(agent_settings(root).tiers)` is an *identity* claim
  that the neutral union invalidates. It must become
  `set(agent_settings(root).tiers) | {"standard", "deep"}`. The PRD names only
  the `:160` assertion, so this is the one test edit a careless implementor will
  miss. Lines 161 and 163 (explicit `available_tiers=[]` and `["custom"]`) must
  keep passing **unchanged** — that is what pins the default-path-only contract.
- **`AgentSettings.__post_init__` rejects empty keys and values.** The merge
  passes string→string pairs only, so it cannot trip the validator; but a driver
  shipping an empty `default_tiers` value would raise
  `ConfigurationError: agent tiers must contain nonempty string keys and values`
  at construction. Acceptable: loud at driver build time.
- **Likely next changes, and where this design boxes them in.** (1) *A third
  driver* (discovery 00004's generic driver API, hold PRD 00012) — it inherits
  the pattern cleanly, since `default_tiers` is on the protocol, not in a
  registry. (2) *A third neutral tier* (e.g. `fast`) — `NEUTRAL_TIERS` is derived
  from `DEFAULT_PHASE_TIERS`'s *values*, so a key no phase defaults to would
  **not** reach `available_tiers`; that is the one spot needing a second thought
  then. (3) *Richer failure routing* — adding, say, a bounded wait for
  `AUTHENTICATION` touches only `runtime/decision.py`, which this PRD leaves
  alone, so nothing here blocks it.

## Test strategy outline

Two table tests plus four targeted tests, all in existing modules. Every test is
named for the rule it enforces, per `rules/testing.md`.

- `claude_diagnostics_classify_by_table`
  (`tests/drivers/test_adapter_failure_classes.py`) — parametrized over
  `(text, expected_class)`, driving `failure_payload`. Positive rows: each new
  marker in a realistic sentence. Negative rows: a bare `401` and a bare `429`
  staying `agent`; an unmatched sentence staying `agent`; a non-string returning
  `unknown` with detail `Malformed terminal error evidence`; and `"HTTP 4290"` →
  **`rate_limit`**, pinning the accepted substring-matcher asymmetry against
  Codex (§ Interfaces & contracts, `claude_events.py`) so changing it later is a
  visible test edit rather than a silent drift. Precedence rows:
  `connect ETIMEDOUT` → `connectivity` (not `timeout`); an OAuth-plus-429 string
  → `authentication`.
- `codex_diagnostics_classify_by_table` (same file) — the five new strings plus
  the four hold-00056 strings, and the pinned negatives
  `"Authentication failed"` / `"MCP server authentication failed"` → `UNKNOWN`.
- `api_two_declares_default_tiers` (`tests/drivers/test_driver_v2.py`) —
  `DRIVER_API_VERSION == 2` still, and both bundled drivers expose a
  `Mapping[str, str]` `default_tiers` covering `standard` and `deep`. A mutation
  attempt on it raises `TypeError`.
- `claude_default_tiers_map_standard_and_deep`
  (`tests/drivers/test_claude_launch.py`) — with `tiers={}` configured,
  `build_launch` emits `--model sonnet` for `standard` and `--model opus` for
  `deep`; a configured `standard` still wins.
- `codex_default_tier_omits_model_segment`
  (`tests/drivers/test_codex_launch.py`) — with `tiers={}`, `argv` contains no
  `-m` for either key; with `[agents.codex.tiers] deep = "<model>"`, `-m <model>`
  is emitted verbatim. Also pins the side effect of reserving the literal: an
  explicitly passed `model="default"` with `allow_explicit_model` false now
  passes the `Unknown Codex model` guard (because `default` is in
  `settings.tiers.values()` after the merge) and produces argv with no `-m`.
  **That is intended** — `default` is a reserved tier value, so naming it
  explicitly means the same thing as resolving to it.
- `unconfigured_project_routes_through_driver_default_tiers`
  (`tests/runtime/test_adapter_launch_routing.py`) — a project root with no
  `[agents.<agent>.tiers]` resolves `build`, `review` and `done` without raising
  `Unknown agent tier`, and a configured tier still wins.
- `neutral_default_tiers_are_always_available`
  (`tests/workflow/test_configuration.py`) — `DEFAULT_PHASE_TIERS` equals
  `{"build": "standard", "review": "deep", "done": "standard"}`;
  `available_tiers` contains `standard` and `deep` with and without configured
  tiers; `available_tiers=[]` still yields `set()`.

Note on placement: the PRD names
`claude_diagnostics_classify_by_table in tests/drivers/test_adapter_failure_classes.py`
as the acceptance criterion, so that is where it goes, even though that file
holds only Codex tests today (its name covers both adapters) and a Claude
classification table already exists at
`tests/drivers/test_claude_decode.py:480` —
`test_terminal_error_classifies_evidence_and_bounds_sanitized_detail`, which
drives the full decoder rather than `failure_payload` directly. The two are
complementary, not duplicates: the existing one asserts decode, sanitization
and the 4096 bound; the new one asserts the classification table alone. **The
existing table must keep passing unchanged** — every added marker was checked
against its eighteen rows, and none captures `"provider execution failed"` →
`agent`.

**Existing tests that must keep passing unchanged:** `tests/drivers/test_neutrality.py`
(the boundary gate — it fails loudly if a model name reaches `config.py` or
`drivers/base.py`), `tests/drivers/test_claude_rate_limit.py`,
`tests/drivers/test_claude_decode.py`,
`test_generic_authentication_failure_messages_remain_unknown`,
`test_numeric_status_substrings_in_identifiers_are_unknown`,
`test_failure_precedence_is_independent_of_diagnostic_order`,
`test_configured_supervisor_launches_each_selected_literal_model_and_effort`,
and `tests/drivers/test_adapter_failure_classes.py:145-205` (the pinned
negatives `"processed 429 files"`, `"disk at capacity"`, `"HTTP 4290"`).

The signature change also reaches
`tests/runtime/test_supervisor_preflight.py:540-550`, a monkeypatched
`resolve_phase_route` stand-in whose `def route(...)` signature must accept the
new keyword. That is the
only *stand-in for the function*; the fake **drivers** the change reaches are
listed in § Module placement.

**Gate:** `./tools/check`. Note for the implementor: in-sandbox `tests/runtime`
redness may be the macOS-seatbelt `ps` denial rather than this PRD, and
`./tools/check` was last red on a ruff BLE001 in
`tests/workflow_client/test_kill_group_bounded.py:56` — PRD 00057's deferred
regression (hold stub 00067), not this PRD's. Judge the gate on the named
tests plus no *new* failures.

## Review log

dispatch 1 (claude): cardinal-sin 0, blocker 3, non-blocker 3, question 2

Blockers fixed in the doc:

- B1 — the reuse inventory claimed `DEFAULT_PHASE_TIERS` has no test consumer.
  True of the symbol, false of its values: six test files assert the literal
  tier keys `sonnet`/`opus`. Fixed by adding the second table in § Module
  placement with per-file line references, and correcting the greps-tried line.
- B2 — `self._driver.default_tiers` would `AttributeError` across the runtime
  suite: the fake drivers at `tests/runtime/test_supervisor.py:85` and
  `tests/runtime/test_supervisor_process.py:49` have no such field, and
  `test_supervisor_preflight.py` imports that harness. Fixed by naming both
  fakes and stating that the attribute is a hard protocol requirement with no
  `getattr` fallback.
- B3 — the default tier key change silently launches the driver's own model for
  a project whose `[agents.<agent>.tiers]` uses the old key names. Fixed with a
  new § Migration plan: the breaking change stated plainly, the bounded
  surface (no releases, no shipped root `ovcaq.toml`), fixtures updated in
  Phase 1, an upgrade note in `docs/operations.md` and a breaking CHANGELOG
  entry in Phase 2, the rejected "warn on a table with neither neutral key"
  alternative recorded with its rationale, and a rollback paragraph.

Non-blockers, recorded and fixed because each was a false statement of fact
rather than a deferred concern: `codex.py:10` already imports
`dataclasses.replace` (only `claude.py` needs it); there is no `config` ↔
`drivers` import cycle, so the lazy import bought nothing; a Claude
classification table already exists at `tests/drivers/test_claude_decode.py:480`
— the new test stays where the PRD's acceptance criterion puts it, with the
overlap and the complementary coverage now documented.

Questions from dispatch 1, recorded: reserving the Codex literal `default` also lets an
explicitly passed `model="default"` through the `Unknown Codex model` guard
(now stated as intended and pinned in the test); Alternative A referred to a
root `ovcaq.toml` that does not exist (now says it would have to be created).

dispatch 2: codex unavailable, Claude fallback

The mandatory cross-model dispatch could not run: `codex exec` started, then
every file-reading tool failed with
`sandbox-exec: sandbox_apply: Operation not permitted` and it returned no
findings (nested `codex exec` cannot read files under this host's sandbox — the
condition already recorded in the project memory `implementation-plan-externals`).
Degraded to a fresh Claude reviewer with an identical, sharpened prompt, per the
skill's codex-outage rule.

dispatch 2 (claude-fallback): cardinal-sin 0, blocker 3, non-blocker 3, question 2

Blockers fixed in the doc:

- B4 — the dispatch-1 fake-driver fix was incomplete: two more stand-ins reach
  `Supervisor` and would `AttributeError`
  (`tests/integration/test_observer_terminal_cleanup.py:152`,
  `tests/integration/test_supervisor_live_telemetry.py:41`). Fixed: § Module
  placement now carries all four fakes in a table with their construction
  sites.
- B5 — the PRD's own Phase 2 acceptance criteria contradict each other: it
  requires `rg -n "sonnet|opus" docs/operations.md` to find nothing while its
  Risks section asks for the `opus` mapping to be documented there. Fixed:
  § Migration plan item 2 splits the note — neutral rule in
  `docs/operations.md`, concrete model names and the worked mapping in
  `docs/driver-protocol.md`, which the check does not scan — and flags that
  keeping the prose in `operations.md` instead would require amending the PRD's
  acceptance line as a deliberate decision. The PRD itself is not edited.
- B6 — § Data flow claimed "only `FailureClass.RATE_LIMIT` reaches the bounded
  wait", which is false, and the stated payoff was wrong in a way that hid a
  real behaviour change. Verified against `decision.py:197-232`: `CONNECTIVITY`
  has its own **unconditional** bounded wait, and `RATE_LIMIT` is the
  **conditional** branch that HALTs when `rate_limit_reset_at is None`. So a
  429 found only in terminal text goes from died-retries-then-PARK to an
  immediate HALT. Fixed: § Data flow now carries the real four-row branch map
  and a per-diagnostic consequence list, accepts the reset-less-429 HALT
  explicitly with its reasoning, names the `decision.py:197-213` change that
  would soften it as out-of-scope follow-up rather than assuming it, and
  records the `reducer.py:120` `failure_detail` delta.

Non-blockers: the Claude substring matcher cannot honour hold 00056's
word-boundary half — `"HTTP 4290"` classifies as `rate_limit` where Codex pins it
`UNKNOWN`; accepted with reasoning in § Interfaces & contracts and pinned by a
named negative row rather than left implicit. The fakes' `default_tiers` value
and default were load-bearing and unspecified: prescribed as
`field(default_factory=dict)` (a bare `= {}` raises `ValueError: mutable
default`), with the **empty** default identified as what preserves
`tests/runtime/test_supervisor_preflight.py:195`'s negative. The claim that
"mypy flags the fake against the widened protocol" was false —
`pyproject.toml` sets `files = ["src/ovcaq"]`, so tests are unchecked; the
clause is replaced with a statement that a runtime `AttributeError` is the only
signal, and the two never-constructed protocol-annotated stand-ins
(`test_contract.py:34`, `test_discovery.py:25`) are named as knowingly left
incomplete.

Questions, resolved in the doc: `tests/drivers/test_driver_v2.py:18` is a
seventh literal-key fixture (added to the table, migrate for consistency, not a
breakage); `tests/drivers/test_codex_prompt.py:82` was traced and needs no
change (it supplies `standard` itself and exercises the `default_tiers=None`
contract) — now stated so a planner does not have to re-derive it.

Dispatch 2 also independently verified, with citations, the three-hop round trip
in all four configured/unconfigured × Claude/Codex cases, the Protocol-member
typing question (a class-level annotated `MappingProxyType` assignment matches
the invariant protocol variable and is accepted), every § Module placement line
reference, the Codex regex additions against the `\b` wrapper and every pinned
negative, the Claude marker additions against all eighteen existing table rows,
`test_configured_supervisor_launches_each_selected_literal_model_and_effort`
surviving for both providers, the neutrality-gate scope, the
default-path-only `available_tiers` contract, and the `rg -c` premise of 4.

dispatch 3: codex unavailable, Claude fallback

Dispatch 2 found blockers, so the conditional verification dispatch ran. Codex
remains unusable in this environment for the reason recorded above, so this was
again a fresh Claude reviewer, scoped to verifying the six prior fixes rather
than re-reviewing the whole doc.

dispatch 3 (claude-fallback): cardinal-sin 0, blocker 2, non-blocker 3, question 2

Verdicts returned: fixes 4, 5 and 6 PASS; fix 2 PASS on the fake-driver set and
the preflight reasoning but FAIL on the prescribed snippet; fixes 1 and 3 FAIL
as incomplete on the same missing file.

Blockers fixed in the doc:

- B7 — the breaking-change surface was still incomplete:
  `tests/packaging/test_installed_supervisor_cli.py` declares
  `tiers = { sonnet = "model-s", opus = "model-o" }` at `:241`, sets no phase
  `tier`, and asserts the exact installed-CLI argv at `:366`. Verified directly.
  Two of its tests would fail, and it is the silent-wrong-model pathology
  § Migration plan describes, caught by a real test the doc claimed did not
  exist. Fixed: added to the § Module placement table with its two line
  references, and "six" corrected to "seven" in all three places that counted.
- B8 — the prescribed `default_tiers` block would raise `NameError` at import.
  Verified: `src/ovcaq/drivers/claude.py` and `codex.py` import neither
  `Mapping` nor `MappingProxyType` and carry no
  `from __future__ import annotations`, so the class-body annotation is
  evaluated eagerly. Fixed: both driver sections now state their exact import
  delta, including that `codex.py` already has `replace` (F811) while
  `claude.py` needs it.

Non-blockers fixed: the four fakes' one-liner also needs `Mapping` in each
file's `collections.abc` import (ruff F821, since all four have
`from __future__ import annotations`); § Architecture fit's "newly reachable"
overstated the novelty, since `tests/drivers/test_claude_decode.py:524` already
pins a reset-less `rate_limit` for usage-limit prose; the `:546` anchor for the
monkeypatched stand-in is a range, not that line.

Questions resolved: § Migration plan item 2 now names `docs/operations.md:80-81`
as the sentence to **amend** rather than append below; the rollback paragraph
now states plainly that `state.json` does persist tier strings
(`state/schema.py:131`, `:124`, `:152`) but that they are frontmatter tiers this
change never touches.

Not adopted: dispatch 3 proposed re-anchoring
`tests/workflow/test_configuration.py:160`/`:165` to `:159`/`:164` and
`reducer.py`'s `reset_at` to `:114-116`. Both were read directly in this session
and the existing anchors are right (`:160` is the `== {"fast", "deep"}`
assertion; `reducer.py:116-119` sets `reset_at`, `:120` is the upgrade
condition). Dispatch 3's own numbering is off by one and two respectively, so
the anchors stand. Its *semantic* reading of both sites matched the doc.

Dispatch 3 additionally verified independently: the fake-driver set is complete
(it enumerated all ten `Supervisor(...)` sites in `tests/`; four take fakes,
four take real drivers, and `test_native_telemetry_identity.py:313`'s
`LiveClaudeDriver` subclasses `ClaudeDriver` and so inherits the attribute);
`field(default_factory=dict)` works in all four; the `decision.py` four-row
table matches `:189-232` exactly; a Claude 429 in terminal text really cannot
supply a `rate_limit_reset_at`; no existing test contradicts the newly pinned
`"HTTP 4290"` → `rate_limit`; no releases and no shipped root `ovcaq.toml`
(`git tag`, `gh release list` and `git ls-files '*ovcaq.toml'` all empty); the
docs split satisfies all three of the PRD's Phase 2 checks; and the Codex
reverse-map collision analysis is correct.

No cardinal sins were raised in any dispatch. No blocker remains open.

