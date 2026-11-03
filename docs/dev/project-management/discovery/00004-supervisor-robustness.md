# Discovery: Supervisor robustness

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

The supervisor's process identity check runs `/bin/ps`. Where `ps` is missing
or denied (minimal containers, the agent sandbox), `ovcaq run` exits 2 with
`state_io` and the bare text `[Errno 1] Operation not permitted: 'ps'`. By then
it has already started the batch, so `batch.status` stays `running` with no
supervisor and `status` reports `idle`. Misconfiguration such as a missing tier
is also found only after the batch starts and ownership is published. Common
Claude diagnostics (expired OAuth, HTTP 429, ECONNRESET) classify as `agent`,
so a rate limit takes a died-retry and parks the PRD instead of waiting. Default
phase tiers are the model names `sonnet` and `opus`, so a Codex project without
a tier table fails with "Unknown agent tier: sonnet". Capabilities can never
succeed, because the only runner wired into `run` and `capability retry`
always raises.

## Requirements

### Must have

- Process identity without `ps`: read start time and zombie status through
  `proc_pidinfo(PROC_PIDTBSDINFO)` on macOS. Keep the same `ProcessIdentity`
  contract. If the probe is unavailable, raise a typed error with its own error
  code and a remedy, never `state_io`.
- `doctor` reports the process-identity probe as a capability check.
- Validate the agent, driver options, and the phase route for every phase
  before `start_batch`. A failure leaves state unchanged.
- If the supervisor fails before its first session opens, it returns the batch
  to idle (or marks attention) in the same transaction family, so `status` and
  state agree.
- Claude failure classification maps expired or invalid auth to
  `authentication`, 429 and "rate limit" to `rate_limit`, and ECONNRESET,
  ETIMEDOUT, and DNS errors to `connectivity`. Codex gains the auth and
  ECONNRESET cases it misses (hold 00036).
- Default phase tiers become neutral keys (for example `standard` and `deep`).
  Each driver maps them to its own models.
- `capability retry` with an unknown name is a usage error with JSON envelope,
  never a traceback.
- Until a real capability runner exists (PRD 00010), `run` never declares a
  required capability it cannot execute.

### Nice to have

- Per-class retry budgets survive class changes instead of resetting (hold
  00041 partial; `phase_repeat_limit` bounds it today).
- `FleetRegistry.prune` runs on supervisor start for entries whose identity no
  longer matches, so SIGKILL leftovers clear themselves (hold 00020 and 00034
  residuals).

### Out of scope

- Linux process identity (`/proc`). That is PRD 00013.
- The agoge capability runner itself. That is PRD 00010.

## Constraints

- Provider strings stay under `src/ovcaq/drivers/`; the neutrality tests must
  keep passing without new exemptions.
- No shell evaluation; any helper stays an argv array or a `ctypes` call.
- Process tests use real subprocesses as well as unit fakes (AGENTS.md).

## Codebase Context

- **Relevant code**: `src/ovcaq/runtime/registry.py:126-141`
  (`process_identity` runs `ps`, no exception handling), `:428`
  (`FleetRegistry.prune`, no production caller);
  `src/ovcaq/runtime/supervisor.py:145-156` (`start_batch`), `:159`
  (`_publish_ownership`), `:161` (signal scope starts), `:339`
  (`resolve_phase_route` inside `_attempt`), `:611-612` (retry state reset);
  `src/ovcaq/drivers/claude_events.py:223-247`; `src/ovcaq/drivers/codex_events.py:298-339`;
  `src/ovcaq/drivers/__init__.py:18` (`DEFAULT_PHASE_TIERS`) imported by
  `src/ovcaq/config.py:502`; `src/ovcaq/supervisor_cli.py:68-73`
  (`_UnavailableRunner`), `:183`, `:463`; `src/ovcaq/runtime/capability.py:299`
  (`KeyError` on unknown name).
- **Conventions**: typed errors in `src/ovcaq/errors.py` map to stable exit
  codes; doctor checks live in `src/ovcaq/runtime/capability.py:36-42` and
  `src/ovcaq/runtime_cli.py`.
- **Similar implementations**: legacy `claude-autopilot`
  `skills/run-autopilot/cli/procinfo.py` (2026-10-13) reads process facts
  through `sysctl(KERN_PROCARGS2)` and `proc_pidinfo` with `ctypes`, with SDK
  constants verified in its docstring.

## Success Criteria

- With `subprocess.run` patched to raise `PermissionError` for `ps`, the
  supervisor suite passes, because nothing calls `ps`.
- In a sandbox that denies `ps`, `./tools/check` has zero failures from the
  process probe.
- A missing tier fails `run` with a clear message and state revision unchanged.
- Each listed Claude and Codex diagnostic maps to its class in a table test.

## Risks

- **ctypes struct layout drift**: pin constants and struct offsets to SDK
  headers, as legacy `procinfo.py` does, and test against the current process.
- **Start-time token format change**: fleet entries store the `ps lstart`
  string today. Switching tokens invalidates live entries; no OVCAQ run is live
  yet, so a fresh start is acceptable.

## Open Questions

- Neutral tier key names: `standard`/`deep`, or phase-named keys?
- Should an unrunnable required capability fail preflight, or should the
  capability manifest stay empty until PRD 00010?

## Discovery Log

### Q1: Is the `ps` failure only a sandbox artifact?

**Answer**: No. Minimal Linux images ship without procps, and hardened macOS
profiles deny it. The 2026-10-18 test audit counted 759 test failures from this
one call. The fix makes the product portable and the suite runnable anywhere.
