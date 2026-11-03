# Design: Supervisor process identity and start preflight (PRD 00062)

## Architecture fit

Three modules, all inside existing boundaries; no new package and no new layer.

- **Identity** lands in `ovcaq.runtime.registry`, which the capsule names as the
  owner of "the authoritative run lock, fleet registry, process groups". Process
  identity is already its export; this PRD changes only how the fact is
  obtained. The failure gains a name in `ovcaq.errors`, the shared taxonomy
  module that imports nothing and is therefore safe to import from `registry`.
- **Preflight** lands in `ovcaq.runtime.supervisor` (`Supervisor.run` ordering)
  and `ovcaq.state.commands` (`StateService`, the compound-command surface whose
  every write goes through `StateStore.transaction`). It introduces no second
  state writer, honouring the "`StateStore.transaction()` is the only durable
  writer" invariant.
- **Safety** lands in `ovcaq.runtime.capability` (`CapabilityService.retry`) and
  surfaces through `ovcaq.supervisor_cli`, the typed-envelope boundary.

The work is provider-neutral: no driver, no model id, no launcher string. It
fits the current implementation rather than the three-layer target, because
process ownership stays with OVCAQ under every layer of that target
(`AGENTS.md` ownership invariant 3).

## Module placement

| Path | New or edit | What changes |
|---|---|---|
| `src/ovcaq/errors.py` | edit | `ErrorCode.PROCESS_PROBE`, its `EXIT_CODES` entry |
| `src/ovcaq/runtime/registry.py` | edit | libproc reader replaces the `ps` subprocess; drop `subprocess` import if it becomes unused |
| `src/ovcaq/runtime/capability.py` | edit | sixth probe fact, `_NAMES`, membership check in `retry` |
| `src/ovcaq/runtime/supervisor.py` | edit | `preflight()`, its call site, early-failure branch |
| `src/ovcaq/state/commands.py` | edit | `StateService.revert_batch_start` |
| `tests/runtime/conftest.py` | **new** | `forbid_ps` autouse fixture |
| `tests/runtime/test_supervisor_preflight.py` | **new** | preflight and early-failure tests |
| `tests/runtime/test_fleet_registry.py` | edit | identity tests now run under `forbid_ps`; add probe-failure and zombie tests |
| `tests/runtime/test_capability.py` | edit | five-fact test renamed to six |
| `tests/runtime/test_process.py` | edit | `_descendant_stopped` stops spawning `ps`; the now-dead `ps` launch filter goes |
| `tests/runtime/test_supervisor_process.py` | edit | `stopped` stops spawning `ps` |
| `tests/runtime/test_runtime_cli.py` | edit | doctor fact test |
| `tests/runtime/test_supervisor_cli.py` | edit | unknown-capability usage envelope |
| `tests/runtime/test_capability_lifecycle.py` | edit | no-required-capability premise pin |
| `tests/state/test_supervisor_commands.py` | edit | `revert_batch_start` preconditions |
| `docs/operations.md`, `docs/state-protocol.md`, `CHANGELOG.md` | edit | fact and error documentation |

`src/ovcaq/supervisor_cli.py` is listed by the PRD under Safety but needs **no
change** - see `## Interfaces & contracts`, Safety, for why, and
`## Alternatives considered` for the option that would have changed it.

## Interfaces & contracts

### Identity

`src/ovcaq/errors.py`:

```python
class ErrorCode(StrEnum):
    ...
    PROCESS_PROBE = "process_probe"


EXIT_CODES: dict[ErrorCode, int] = {
    ...
    ErrorCode.PROCESS_PROBE: 12,
}
```

`12` is unused today (the highest assigned exit code is `11`,
`ErrorCode.RESOURCE_LIMIT`).

`src/ovcaq/runtime/registry.py` - module constants, exact names and values:

```python
PROC_PIDTBSDINFO = 3
PROC_BSDINFO_SIZE = 136
PBI_STATUS_OFFSET = 4
PBI_PID_OFFSET = 12
PBI_START_TVSEC_OFFSET = 120
PBI_START_TVUSEC_OFFSET = 128
SZOMB = 5
```

```python
def _libproc() -> ctypes.CDLL:
    """Load libproc, or raise the typed probe failure."""
```

It loads with `ctypes.CDLL(path, use_errno=True)`, following `_rename.py:14`,
because the return value alone cannot distinguish a dead pid from a denied one
(see `process_identity` below).

- Non-darwin `sys.platform`, a `find_library("proc")` that returns `None`, an
  `OSError` from `ctypes.CDLL`, or a missing `proc_pidinfo` attribute all raise:

```python
raise CommandError(
    ErrorCode.PROCESS_PROBE,
    f"process identity probe is unavailable on {sys.platform}; run `ovcaq doctor`",
)
```

The message MUST contain the platform name and the literal text `ovcaq doctor`.

```python
def process_identity(pid: int) -> ProcessIdentity | None:
    """Observe a live process and its start token without signalling it."""
```

- `pid <= 0` returns `None` **before** loading libproc, unchanged from today.
- The out-buffer is `buffer = ctypes.create_string_buffer(PROC_BSDINFO_SIZE)`.
  It must be a mutable ctypes buffer: `bytes` is immutable and a `bytearray` is
  rejected by a `c_void_p` argtype with `ctypes.ArgumentError`.
- Calls `proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, buffer, PROC_BSDINFO_SIZE)` with
  `argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint64, ctypes.c_void_p,
  ctypes.c_int]` and `restype = ctypes.c_int`, matching the real signature
  `int proc_pidinfo(int pid, int flavor, uint64_t arg, void *buffer, int buffersize)`.
  A `create_string_buffer` instance is accepted by the `c_void_p` argtype.
- **A returned size of `0` is ambiguous and MUST be disambiguated by `errno`.**
  Measured on this host: `proc_pidinfo(1, 3, 0, buf, 136)` returns `0` with
  `errno == EPERM` for a live root-owned process, and returns `0` with
  `errno == ESRCH` for an absent pid. Call `ctypes.set_errno(0)` immediately
  before the call and read `ctypes.get_errno()` immediately after a `0` return:
  - `ESRCH` (and `errno == 0`, which some kernels return for an absent pid)
    returns `None` - the kernel does not know the pid.
  - **Any other errno, notably `EPERM` and `EACCES`, raises**
    `CommandError(ErrorCode.PROCESS_PROBE, ...)` naming the errno and its
    `os.strerror` text. A denied probe must never read as "the process is
    dead": that is precisely the silent-prune failure mode
    `## Alternatives considered` item 1 is rejected for, and it would be a
    regression against `ps -p 1 -o lstart=`, which succeeds across users today.
- Returned size other than `0` or `PROC_BSDINFO_SIZE` raises
  `CommandError(ErrorCode.PROCESS_PROBE, ...)` with the same message shape,
  naming the size.
- Fields are read from `buffer.raw` with `struct.unpack_from("=I", buffer.raw,
  OFFSET)` for the two uint32 fields and `struct.unpack_from("=Q", buffer.raw,
  OFFSET)` for the two uint64 fields (`registry.py` already imports `struct`).
  The fields are naturally aligned, so no padding is lost at those offsets.
- A `pbi_pid` that differs from the requested `pid` raises
  `CommandError(ErrorCode.PROCESS_PROBE, ...)` naming both pids.
- `pbi_status == SZOMB` returns `None`.
- Otherwise returns
  `ProcessIdentity(pid=pid, started=f"{pbi_start_tvsec}.{pbi_start_tvusec:06d}")`.

`ProcessIdentity` and `process_matches` keep their current signatures and
bodies. The `started` **token format changes** from the `ps lstart` string to
`"<sec>.<usec>"`; see `## Risks & edge cases`.

`tests/runtime/conftest.py` (new):

```python
@pytest.fixture(autouse=True)
def forbid_ps(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any `ps` spawn raise PermissionError, as the seatbelt profile does."""
```

It wraps `subprocess.Popen.__init__`; when the first element of the resolved
argv is `ps` or `/bin/ps` it raises
`PermissionError(errno.EPERM, "ps is denied")` before delegating. Every other
spawn (the capability probes spawn `sys.executable`) passes through unchanged.
Patching `Popen.__init__` covers `subprocess.run` too, since `run` builds a
`Popen`.

**Two existing test helpers spawn `ps` themselves and the autouse fixture would
fail them**, so this PRD rewrites both:

- `tests/runtime/test_process.py:321-330` (`_descendant_stopped`)
- `tests/runtime/test_supervisor_process.py:233-241` (`stopped`)

Both run `subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], ...)` only to
decide "absent or zombie", which `process_identity(pid) is None` now answers
directly. Each helper becomes that call; no new API is needed. Separately,
`tests/runtime/test_process.py:59-69` filters `ps` spawns out of its recorded
launch list; once nothing under `src/ovcaq` spawns `ps` that filter is dead
code and is removed in the same task.

### Doctor fact

`src/ovcaq/runtime/capability.py`:

```python
_NAMES = (
    "platform",
    "advisory_lock",
    "process_group",
    "group_signal",
    "directory_fsync",
    "process_identity",
)


def _probe_process_identity() -> CapabilityResult:
    """Report whether the kernel identity probe resolves this process."""
```

- Returns `CapabilityResult("process_identity", "supported", <the started
  token>)` when `process_identity(os.getpid())` returns an identity.
- Returns `CapabilityResult("process_identity", "degraded", str(error))` when it
  raises `CommandError`, and
  `CapabilityResult("process_identity", "degraded", "probe returned no identity")`
  when it returns `None`.

`probe_platform` appends `_probe_process_identity()` after
`_probe_directory_fsync()`, so the fact is sixth and the order stays stable. The
non-darwin early return already iterates `_NAMES`, so it yields six
`unsupported` facts with no edit. `require_process_capabilities` needs no edit
either: it compares against `len(_NAMES)` and `set(_NAMES)`, so widening the
tuple widens the requirement. `ovcaq doctor --json` reports `ok: false` whenever
any fact is not `supported`, which already covers a degraded identity fact.

### Preflight

`src/ovcaq/runtime/supervisor.py`:

```python
    def preflight(self) -> None:
        """Validate identity and every phase route before any state write."""
```

- Raises `CommandError(ErrorCode.PROCESS_PROBE, ...)` by propagation when
  `process_identity(os.getpid())` raises.
- Raises
  `CommandError(ErrorCode.USAGE, "process identity is unavailable for this process")`
  when the probe returns `None`.
- For each `phase` in `("build", "review", "done")` calls
  `resolve_phase_route(self._root, phase, agent=self._driver.name,
  phase_settings=self._settings.phases[phase])` and converts a
  `ConfigurationError` into `CommandError(ErrorCode.USAGE, str(error))`,
  preserving the original message (`"Unknown agent tier: <tier>"`).
- Returns `None` on success.

Call site in `Supervisor.run`, immediately after
`require_no_emergency_failure(self._paths)` and before
`reconcile_metrics(self._paths)`:

```python
            require_no_emergency_failure(self._paths)
            self.preflight()
            reconcile_metrics(self._paths)
```

`preflight` is outside the `try/except _STATE_ERRORS` block, so a `CommandError`
propagates out of `run`, out of `supervisor_cli._run`, and into the error
envelope with its own exit code. No transaction has run at that point, so
`revision` and `batch.status` are untouched.

### Early-failure revert

`src/ovcaq/state/commands.py`:

```python
    def revert_batch_start(
        self, batch_id: str, *, expected_revision: int | None = None
    ) -> State:
        """Return a batch this run started, and never served, to its defaults."""
```

Inside the transaction, raise
`ValueError("batch is not a fresh started batch")` unless **all** hold:
`batch["status"] == "running"`, `batch["id"] == batch_id`,
`state["work"]["prd"] is None`, `batch["completed_prds"] == []`. On success set
`batch["id"] = ""`, `batch["started_at"] = None`, `batch["status"] = "idle"` -
the `new_state` defaults (`schema.py:291-294`). The revision still advances,
because every transaction increments it.

`Supervisor.run` gains, around ownership publication:

- Before the `start_batch` block, record
  `was_idle = batch["status"] == "idle" or not batch["id"]` and, after a
  successful `start_batch`, the `batch_id` that call committed.
- **Scope: `self._publish_ownership()` only.** Wrap that call. On any exception
  it raises, **first** run the record cleanup below - on BOTH legs, before the
  `was_idle` branch - and **then** either
  `StateService(self._store).revert_batch_start(batch_id, expected_revision=...)`
  when `was_idle` is true, or `self._state_failure("startup")` when it is
  false. Both legs return `SupervisorOutcome(1, decision, 0)`; the decision
  reason carries the failure detail. The site string is the existing
  `"startup"` (`supervisor.py:158`), not a new one.
- **The first `_attempt()` is deliberately NOT wrapped.** It runs inside
  `self._loop()` (`supervisor.py:162` → `257`), which already catches
  `_STATE_ERRORS` and converts them to `self._state_failure("supervisor.loop")`
  rather than raising, so a new branch could never see them; and the `finally`
  at `supervisor.py:170-182` already runs `cleanup_run_records(...)` for any
  exit after `_publish_ownership` returned, so adding a second removal there
  would be redundant. Catching the remaining non-state exceptions would convert
  arbitrary crashes into a quiet exit 1, which is worse than the traceback.
  Consequence, stated plainly: a first attempt that fails after ownership was
  published leaves `batch.status` running, and the existing
  `supervisor.loop`/`session.*` failure paths own that case, not this PRD.
- No `_served` flag is needed: the trigger is simply "`_publish_ownership`
  raised". The cleanup below does need to know how far publication got, and
  that is recorded on the two attributes named there, not on a new flag.
- A revert that itself raises `ValueError` or a state error falls back to
  `self._state_failure("startup")`; the run still exits 1.
- **The rollback covers the filesystem side too, not only `state.json`.**
  `_publish_ownership` (`supervisor.py:221-248`) writes the run metadata with
  `publish_run_metadata` **before** `FleetRegistry.publish`, and the existing
  `cleanup_run_records` call lives in the `finally` of the block entered only
  *after* `_publish_ownership` returns (`supervisor.py:170-182`) - so on this
  path it never runs, and its `entry` would be unbound anyway. A state-only
  revert would therefore leave an orphan run record claiming an owner that does
  not exist, which is the same class of lie the PRD exists to remove.

  So `_publish_ownership` publishes what it has written as it goes: it assigns
  `self._metadata = metadata` immediately after `publish_run_metadata`
  (`supervisor.py:244`) instead of at the end, and assigns a new
  `self._fleet_entry = entry` immediately after `FleetRegistry.publish`
  (`supervisor.py:245`). Both are initialised to `None` in `__init__` and reset
  to `None` at the top of `run()`.

  The early-failure branch then removes, best-effort:
  - both attributes set → `cleanup_run_records(self._paths, self._metadata,
    self._fleet_entry)` (`session.py:434`).
  - metadata only, which is the common case because `publish_run_metadata` runs
    first → an explicit unlink of `self._paths.run_metadata`.
    `cleanup_run_records` cannot serve here: it requires both records and
    returns `False` without deleting anything when the entry does not match
    (`session.py:438-441`).
  - neither set → nothing to remove.

  `FleetRegistry.remove(run_id, expected=...)` (`registry.py:409`) is available
  if a future path needs the entry removed alone; it is not needed here,
  because the entry is never published before the metadata.

  This cleanup runs on **both** legs - the fresh-batch revert and the
  resumed-batch `_state_failure` - before either touches state. Filesystem
  cleanup first, state last: a crash between the two then leaves a batch marked
  running with no records, which the next `run` reconciles, rather than a
  cleaned state with a record that outlives it. A removal failure does not
  prevent the state step; the run still exits 1.

### Safety

`src/ovcaq/runtime/capability.py`:

```python
    def retry(self, name: str, runner: CapabilityRunner) -> State:
        """Run exactly one new attempt for a failed or stale capability."""
        if name not in self._store.read()["batch"]["capabilities"]:
            raise CommandError(ErrorCode.USAGE, f"unknown capability: {name}")
        ...
```

The check runs **before** `self.reconcile(name)`, which is where the KeyError is
raised today (`capability.py:299`). The message is exactly
`unknown capability: <name>`.

`supervisor_cli._retry` needs no change: it catches only `ValueError`
(`supervisor_cli.py:464`) and `CommandError` is not one, so the error reaches
the CLI envelope with `code: "usage"` and exit 1. Raising a `ValueError` there
instead would be re-typed to `runtime_format` by that same handler and would
violate the PRD's required envelope.

## Data flow

1. `ovcaq run` → `supervisor_cli._run` builds the driver and the `Supervisor`.
2. `Supervisor.run` takes the run lock, publishes terminal evidence, checks for
   an emergency failure, then calls `preflight()`.
3. `preflight()` asks `registry.process_identity(os.getpid())`, which calls
   `proc_pidinfo` through ctypes and returns a `(pid, "sec.usec")` token, and
   asks `config.resolve_phase_route` for each of the three phases. Any failure
   becomes a `CommandError` that travels back out to the CLI envelope with no
   state write behind it.
4. On success the existing path runs: capability reconciliation, `start_batch`,
   `_publish_ownership` (which embeds the same token in the fleet entry and the
   run metadata), then the attempt loop.
5. If `_publish_ownership` raises, the new branch removes whatever records it
   had already written, then either reverts a fresh batch to idle or records an
   attention notice on a resumed batch, and the run exits 1. A first-attempt
   failure is **not** covered here; `_loop`'s own `except _STATE_ERRORS` path
   owns that case.
6. `ovcaq doctor` calls `probe_platform`, which now includes the same probe as a
   sixth fact; a degraded fact flips `ok` to false.
7. `ovcaq capability retry NAME` reaches `CapabilityService.retry`, which
   rejects an unknown name before reading `batch.capabilities[name]`.

## Reuse inventory

- **`src/ovcaq/workflow/_rename.py:14-34`** - the repo's existing ctypes idiom:
  `ctypes.CDLL(..., use_errno=True)`, `AttributeError` on a missing symbol
  converted to a typed failure, explicit `argtypes`/`restype`, `ctypes.get_errno()`.
  The libproc loader follows it exactly; only the library handle differs
  (`find_library("proc")` instead of `CDLL(None)`), because `proc_pidinfo` lives
  in libproc, not libc.
- **`struct`** - already imported by `registry.py:10`; `unpack_from` reads the
  four offsets with no new dependency.
- **`ovcaq.errors.CommandError` / `ErrorCode` / `EXIT_CODES`** - the existing
  typed-error contract (`errors.py:6-53`); the new code is one enum member and
  one exit-code entry, not a new error class.
- **`CapabilityResult` and the `_probe_*` convention** (`capability.py:90-176`) -
  every probe is a nullary function returning one `CapabilityResult`, catching
  its own exceptions and degrading with `str(error)`. `_probe_process_identity`
  copies that shape.
- **`StateService._transaction` and the `mutate` closure style**
  (`commands.py:502-531`, `start_batch`/`complete_batch`) - `revert_batch_start`
  is the mirror image of `start_batch` and uses the same validation-inside-mutate
  pattern `complete_batch` already uses for `raise ValueError("batch is not complete")`.
- **`Supervisor._state_failure`** (`supervisor.py:186-204`) - the attention-notice
  path the resumed-batch branch reuses verbatim; nothing new is written for it.
- Greps run: `rg "ctypes|find_library|libproc|proc_pidinfo" src tests` (one hit,
  `_rename.py`); `rg "process_identity|process_matches" src` (six caller
  modules); `rg "required=True" src/ovcaq` (argparse only - the PRD premise);
  `rg "_NAMES|def retry|exactly_five_facts|require_process_capabilities"`;
  `ls tests/runtime` and `ls tests` (no `conftest.py` at either level, so the
  fixture file is genuinely new). `~/.claude/rules-library/rationalizations.md`
  was not consulted; the synonym sets used were mine (identity/probe/pid/start,
  preflight/validate/check, revert/rollback/reset).
  Nothing found for: an existing preflight hook on `Supervisor`
  (`rg "def preflight" src` - no hits), an existing batch-revert command
  (`rg "revert|rollback" src/ovcaq/state` - no hits).

## Alternatives considered

1. **Smallest diff: catch the `ps` failure and degrade.** Wrap the existing
   `subprocess.run` so a `PermissionError`/`FileNotFoundError` returns `None`
   instead of raising. Three lines, no ctypes, no new error code. **Rejected:**
   it makes every process look dead wherever `ps` is denied, so the fleet
   registry prunes live supervisors and `process_matches` never matches - the
   failure mode moves from loud to silent, which is worse than the bug. It also
   leaves the PRD's `forbid_ps` exit criterion unmet in spirit: the suite would
   pass while the product stayed broken.
2. **Chosen: libproc through ctypes, with a typed probe error.** Costs a 136-byte
   struct contract and a platform gate. Buys a real identity in every sandbox,
   a loud named failure where the probe genuinely cannot run, and the removal of
   the last `ps` dependency under `src/ovcaq` - which is what unblocks the whole
   in-sandbox `tests/runtime` suite and the unattended loop.
3. **`psutil`.** One dependency, cross-platform, correct. **Rejected:** the
   capsule's architecture decision pins "a small runtime dependency set
   (Rich/Textual plus stdlib-first internals)" and is actively shedding
   dependencies, not adding them; and a C-extension wheel adds a build surface
   to a package that currently has none.
4. **`sysctl KERN_PROC_PID` through ctypes** instead of libproc. Equivalent
   information, but the `kinfo_proc` struct is far larger, less stable across
   releases, and requires an `oid` array; `proc_bsdinfo` is the narrower,
   better-pinned contract for exactly the two fields needed.

## Risks & edge cases

- **Start-token format change.** `started` goes from a `ps lstart` string
  (`"Sat Oct 25 19:45:00 2026"`) to `"<sec>.<usec>"`. Tokens persisted before the
  upgrade - in `fleet.json` entries and session metadata - will never match the
  new form, so a supervisor already running across the upgrade reads as dead and
  its records get cleaned up. This is a one-time effect on a pre-release product
  with no live installation; it is called out in CHANGELOG.md rather than
  migrated. No stored token is parsed, only compared, so nothing crashes.
- **Struct layout drift.** The four offsets and the 136-byte size are pinned as
  named constants and asserted against the running process; the `pbi_pid`
  equality check turns a silent layout shift into a loud `process_probe`.
- **Pid reuse.** Microsecond resolution plus whole-token comparison in
  `process_matches` means a recycled pid cannot match - this is strictly better
  than the one-second `lstart` resolution it replaces.
- **Callers that expected `None` now see an exception.** `FleetRegistry.snapshot`
  (`registry.py:396`), `runtime/process.py`, `runtime/_run_observation.py`,
  `supervisor_cli.py:329` and `capability.py:307` all call into the probe. A
  genuine probe failure now surfaces as `process_probe` instead of pruning live
  entries as dead. The PRD calls this intended fail-loud behaviour; the cost is
  that `ovcaq status` on a non-darwin host now errors rather than printing an
  empty fleet. Linux support (PRD 00013) is where that stops being acceptable.
- **`forbid_ps` is scoped to `tests/runtime`.** Nothing outside that directory is
  proven ps-free by this PRD. If another suite later spawns `ps`, the fixture
  will not catch it; the honest claim is the PRD's own - "the whole tests/runtime
  directory passes".
- **Likely next changes, and what this boxes in.** (a) PRD 00013 Linux identity:
  `process_identity` must become a platform dispatch, so the libproc call stays
  behind `_libproc()` rather than being inlined, and `PROCESS_PROBE` is named for
  the probe, not for Darwin. (b) PRD 00063's driver-edge failure classification
  will want to distinguish a probe failure from a driver failure - a distinct
  error code is exactly what makes that possible. (c) A future "preflight more
  things" request: `preflight()` is a single nullary method with no arguments
  and no state access, so adding a check is additive. What this design does box
  in: the three hard-coded phases in `preflight` will need to follow `_PHASES` if
  a fourth phase is ever added; using `config._PHASES` directly was rejected
  because it is private.
- **The early-failure branch covers one call, not the whole startup.** Scoped to
  `_publish_ownership`, it leaves a first-attempt failure after publication to
  the existing loop-failure paths, where the batch stays `running`. That is a
  narrower fix than "a fresh batch never stays running without a supervisor"
  sounds, and the gap is deliberate (see `## Interfaces & contracts`); a later
  PRD that wants the wider guarantee has to reckon with `_loop`'s own
  `except _STATE_ERRORS` and its `finally` cleanup first.

## Test strategy outline

- **Identity, under `forbid_ps`** (`tests/runtime/test_fleet_registry.py`):
  `test_process_identity_requires_alive_pid_and_matching_start` and
  `test_child_identity_stays_live_until_process_exit` pass unchanged in body;
  new `process_probe_unavailable_is_typed` monkeypatches `find_library` to
  return `None` and asserts `CommandError`, `code == ErrorCode.PROCESS_PROBE`,
  `exit_code == 12`, and `"ovcaq doctor" in str(error)`; new
  `zombie_process_has_no_identity` spawns a child, waits for it, and asserts
  `None` before reaping.
- **Doctor** (`tests/runtime/test_capability.py`,
  `tests/runtime/test_runtime_cli.py`):
  `test_platform_probe_returns_exactly_six_facts_in_a_stable_order` replaces the
  five-fact test (rename, not delete); `doctor_reports_process_identity_fact`
  asserts the fact is present and that a monkeypatched failing probe flips
  `ok` to false.
- **Preflight** (`tests/runtime/test_supervisor_preflight.py`, new):
  `preflight_rejects_unknown_tier_without_state_change` writes a config with an
  unknown tier and asserts `code == usage`, exit 1, and an unchanged
  `state["revision"]`; `preflight_rejects_missing_process_identity_without_state_change`
  monkeypatches the probe to return `None` and asserts the same unchanged
  revision. `test_run_commits_batch_identity_before_first_metric_and_preserves_work`
  must still pass.
- **Revert** (`tests/state/test_supervisor_commands.py`):
  `revert_batch_start_requires_fresh_running_batch` parametrises over each of
  the four preconditions and asserts `ValueError` for each violation and the
  three restored defaults on success.
- **Early failure** (`tests/runtime/test_supervisor_preflight.py`):
  `early_failure_returns_fresh_batch_to_idle` injects a raising
  `FleetRegistry.publish` and asserts `batch.status == "idle"`, no attention
  notice, exit 1, **and that the runtime root holds no orphan run metadata or
  fleet entry afterwards**; `early_failure_on_resumed_batch_records_attention` does the
  same on a batch with a `work.prd` set and asserts the attention notice instead.
- **Safety** (`tests/runtime/test_supervisor_cli.py`,
  `tests/runtime/test_capability_lifecycle.py`):
  `retry_unknown_capability_is_a_usage_error` asserts the JSON envelope
  `code == "usage"`, exit 1, and that no traceback text appears in the output;
  `run_declares_no_required_capability` asserts a fresh `run` reaches its first
  session with `batch["capabilities"] == {}`.
- **Docs**: `rg -n "process_probe" docs/state-protocol.md docs/operations.md CHANGELOG.md`
  finds all three;
  `test_live_parser_inventory_and_generated_operations_include_runtime_commands`
  still passes.
- **Gate**: `./tools/check` in the sandbox. Note the known confound - a ruff
  BLE001 error in `tests/workflow_client/test_kill_group_bounded.py:56` is PRD
  00057's stalled regression and is not this PRD's to fix; judge this PRD's
  gate on `tests/runtime`, `tests/state` and the lint of the files it touches.

## Review log

dispatch 1 (claude): cardinal-sin 0, blocker 2, non-blocker 6, question 3

Blockers fixed in the doc:
- A `proc_pidinfo` return of 0 means EPERM as well as ESRCH; the contract now
  loads libproc with `use_errno=True` and raises `process_probe` on any errno
  but `ESRCH`, instead of reporting a denied live process as dead.
- The early-failure rollback reverted `state.json` only, leaving the run
  metadata and fleet entry `_publish_ownership` had already written; the
  contract now removes those first, state last.

Non-blockers recorded, not fixed:
- `_served` versus `_sessions`/`_metadata`: the detection signal is specified
  twice and `self._metadata is None` is true even for a publish that wrote
  metadata and then failed. Keep `_served` as the single signal.
- The affected-caller list cites `registry.py:396` (that is `_scan`, not
  `snapshot`) and omits `capability.py:372`, `capability.py:447`,
  `supervisor.py:223`, `supervisor.py:392`. A `process_probe` escaping
  `_finalize` lands after a session exists, which the early-failure branch does
  not cover.
- `require_process_capabilities` has no production caller (only `probe_platform`
  is wired, at `cli.py:505`), so "widening the tuple widens the requirement"
  describes a test-only gate.
- `zombie_process_has_no_identity` as written reaps the child it must observe;
  use `os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT)`.
- `revert_batch_start` restores three fields but the cited `schema.py:291-294`
  range covers four; `completed_at`, `parks_consecutive`, `catchup` and
  `capabilities` are neither asserted nor restored.
- "A recycled pid cannot match" overclaims; it makes a false match vanishingly
  unlikely, not impossible.

Questions recorded, not fixed:
- `expected_revision` for `revert_batch_start` is written as a literal ellipsis;
  name the value and define the `REVISION_CONFLICT` behaviour.
- A failed start exits 12 for a raising probe but 1 for a probe returning None
  or an unknown tier; state the intended operator contract.
- On a fresh batch with `capabilities == {}`, every name - including a valid one
  - yields "unknown capability: X".

dispatch 2 (claude-fallback): cardinal-sin 0, blocker 3, non-blocker 4, question 1

codex was dispatched first and could not run: nested `sandbox-exec` is denied
inside this host's seatbelt profile, so every file-access tool in the codex
session failed with `sandbox_apply: Operation not permitted` and it returned no
findings. Dispatch 2 degraded to a fresh Claude reviewer with the identical
prompt.

Blockers fixed in the doc:
- The ctypes call named no buffer object, and `c_void_p` rejects a `bytearray`;
  the contract now pins `ctypes.create_string_buffer(PROC_BSDINFO_SIZE)` and
  reads fields from `buffer.raw`.
- The autouse `forbid_ps` fixture would have failed two currently-passing
  helpers that spawn `ps` themselves (`tests/runtime/test_process.py:321-330`,
  `tests/runtime/test_supervisor_process.py:233-241`, both verified present);
  both are now in scope and rewritten against the probe, and the dead `ps`
  launch filter at `test_process.py:59-69` goes with them.
- The early-failure branch contradicted the control flow it was inserted into:
  the first `_attempt()` runs inside `_loop`, which already converts state
  errors to a decision, and the existing `finally` already calls
  `cleanup_run_records`. The branch is now scoped to `_publish_ownership` only,
  the `_served` flag is dropped, and the uncovered case is stated.

Non-blockers recorded, not fixed:
- `revert_batch_start`'s preconditions cannot tell a batch this run created from
  a pre-existing idle one: `start_batch` keeps an existing id
  (`commands.py:509`), so the `batch["id"] == batch_id` guard passes for an id
  this run did not mint. Compare the pre-read id to the committed one.
- `_probe_process_identity` catching only `CommandError` lets
  `ctypes.ArgumentError`, `struct.error` or a bare `OSError` escape
  `probe_platform` and crash `ovcaq doctor` - the very command the new error
  message tells the operator to run. Widen the except clause.
- Placing `preflight()` before `reconcile_metrics` skips the torn-metrics repair
  on every failed start. `reconcile_metrics` writes no workflow state, so the
  "no transaction yet" reason does not require that order.
- A `rg` of `src/ovcaq/tui/` found no `process_matches` or `process_identity`
  call, so this finding is **rejected as a false positive** and no caller is
  added for it.

Questions recorded, not fixed:
- Is `errno == 0` on a `0` return really observed on darwin? It is unsourced,
  and treating it as "absent" partly re-opens the conflation the errno fix
  closes. Measure it, or treat it as `process_probe`.

dispatch 3 (claude-fallback): cardinal-sin 0, blocker 3, non-blocker 1, question 1

Verification pass over the five fixes from dispatches 1 and 2. codex was not
re-attempted: its dispatch-2 failure was environmental and reproducible
(nested `sandbox-exec` denied by this host's seatbelt), not transient. All
three blockers were self-inflicted inconsistencies between the fixes, and all
three are now fixed:
- `## Data flow` step 5 still described the pre-narrowing scope ("publication
  or the first attempt"); it now matches the `_publish_ownership`-only scope.
- The filesystem cleanup needed per-run state that the scope fix had just
  declared unnecessary, and named no removal API. `cleanup_run_records`
  (`session.py:434-441`) requires BOTH records and returns `False` without
  deleting when the entry does not match, so it cannot do the metadata-only
  removal the common case needs. The contract now names `self._metadata` and a
  new `self._fleet_entry`, assigned as publication proceeds, and specifies
  `cleanup_run_records` for the both-set case and an explicit unlink of
  `paths.run_metadata` for the metadata-only case.
- The cleanup was attached only to the fresh-batch revert leg, so a resumed
  batch kept the orphan record the fix exists to remove. It now runs on both
  legs, before either touches state.

Non-blocker fixed in passing (one word, and leaving it wrong would have
shipped a second operator-visible site name): the doc said
`_state_failure("supervisor.startup")`; the existing site is `"startup"`
(`supervisor.py:158`).

Question recorded, not fixed:
- `was_idle` and `revert_batch_start`'s preconditions encode two different
  notions of "fresh". If `early_failure_on_resumed_batch_records_attention`
  uses an idle batch with `work.prd` set, it reaches the attention notice
  through the ValueError fallback rather than the resumed-batch leg, so it
  cannot tell the two apart. The test must state which leg it exercises.

Verified correct by this pass (no finding): the errno contract and its
`_rename.py:14-34` precedent; exit code 12 being free; the buffer, the four
offsets, the 136-byte size and the `=I`/`=Q` widths; that both `ps` helpers
compute exactly "absent or zombie" so `process_identity(pid) is None` answers
them, and that the EPERM leg cannot fire on a test's own child; the whole
fix-5 control-flow argument line by line; the `KeyError` site at
`capability.py:296` and the `_NAMES` widening.
