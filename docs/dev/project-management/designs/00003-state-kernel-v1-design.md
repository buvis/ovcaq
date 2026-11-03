# Design: OVCAQ state kernel v1

## Architecture fit

PRD 00003 fills only the Phase-1 state boundary created by PRD 00002. The
dependency direction is `ovcaq.cli -> ovcaq.state.commands ->
ovcaq.state.store -> ovcaq.state.schema`; `ovcaq.state.paths` is a pure helper
used by commands. Nothing under `ovcaq.state` imports workflow, runtime,
drivers, events, TUI, or provisioning.

The state kernel owns a fresh, closed v1 document. It does not import the
personal runtime's flat state, accept unstamped legacy documents, or preserve
unknown legacy keys. `tests/characterization/current_system.toml` remains the
source inventory: every `STATE-001` through `STATE-184` receives exactly one
documented disposition (`retained`, `renamed`, `derived`, `event-only`, or
`retired`) in `docs/state-protocol.md`, enforced by a parity test.

The store is the sole writer. State commands and later workflow/runtime
services receive a `StateStore`; no module calls `os.replace`, writes
`state.json`, or manages the state lock outside `ovcaq.state.store`. Workflow
transition effects remain absent until PRD 00004. The generic recovery verbs
are fenced from transition-owned paths so they cannot become a second workflow
API.

The durability target is macOS for the personal-cutover track. File and parent
directory fsync are required there. An unsupported directory-fsync capability
raises a stable error before OVCAQ claims a successful commit; weakening the
contract is not an implicit fallback.

## Module placement

- Edit `src/ovcaq/state/schema.py`: v1 `TypedDict` contracts, enum constants,
  `new_state()`, whole-document validation, and bounded path-aware errors.
- Edit `src/ovcaq/state/store.py`: `StateStore`, locking, create-only init,
  validated reads, compare-and-set transactions, rotating raw-byte backup,
  restore, atomic publication, permission enforcement, file fsync, and
  directory fsync.
- Edit `src/ovcaq/state/paths.py`: pure dotted/bracket JSON-path parser plus
  get/set/append/delete mutations.
- Edit `src/ovcaq/state/commands.py`: `StateService`, protected-path policy,
  generic recovery operations, compound task/attempt/contract-card operations,
  and command result models.
- Edit `src/ovcaq/state/__init__.py`: export only the installed state-kernel
  surface (`State`, `StateStore`, `StateService`, state exceptions).
- Edit `src/ovcaq/cli.py`: live `ovcaq init` and `ovcaq state ...` parser,
  shared JSON/human output, and stable exception-to-exit mapping. It remains the
  single command registry from which help examples are verified.
- Edit `src/ovcaq/config.py` and `src/ovcaq/paths.py` only for project-root and
  runtime-path resolution required by `init`/`state`; do not add workflow or
  launcher configuration parsing.
- Replace the placeholder `docs/state-protocol.md` with the v1 schema,
  transaction/restore contract, command examples generated or asserted from
  the live parser, and the `STATE-001..STATE-184` disposition table.
- Add `tests/state/test_schema.py`, `test_crosswalk.py`, `test_store.py`,
  `test_durability.py`, `test_paths.py`, `test_commands.py`, and
  `test_installed_state.py`; extend packaging tests only where the installed
  state command needs a wheel smoke.
- Reuse the committed sanitized fixtures in `tests/fixtures/claude/` as
  legacy-disposition evidence. They are never accepted by `validate_state()`
  and no tests read live files under `~/.claude` or `~/.codex`.

## Interfaces & contracts

### Schema surface (`ovcaq.state.schema`)

```python
SCHEMA_VERSION: Final[int] = 1
TIMESTAMP_FORMAT: Final[str] = "UTC RFC 3339: YYYY-MM-DDTHH:MM:SS[.ffffff]Z"
MAX_STATE_BYTES: Final[int] = 16 * 1024 * 1024
MAX_COMMAND_PAYLOAD_BYTES: Final[int] = 2 * 1024 * 1024
MAX_STRING_BYTES: Final[int] = 1024 * 1024
MAX_CONTRACT_CARD_BYTES: Final[int] = 64 * 1024
MAX_JSON_DEPTH: Final[int] = 32
MAX_TASKS: Final[int] = 512
MAX_ATTEMPTS_PER_TASK: Final[int] = 64
MAX_REVIEW_CYCLES: Final[int] = 32
MAX_REVIEW_ITEMS: Final[int] = 1024
MAX_CAPABILITIES: Final[int] = 64
MAX_OPEN_MAP_ITEMS: Final[int] = 256

Phase = Literal["build", "review", "done", "paused"]
NextPhase = Literal["build", "review", "done", "paused", ""]
BatchStatus = Literal["idle", "running", "attention", "completed"]
TaskStatus = Literal["pending", "in_progress", "completed"]
AttemptOutcome = Literal[
    "completed", "aborted", "review_flagged", "rework_failed", "escalated"
]
CapabilityStatus = Literal["pending", "running", "failed", "succeeded", "skipped"]
ReviewCategory = Literal["fix", "verify", "known"]
ReviewItemStatus = Literal["pending", "resolved"]
ReviewerStatus = Literal["available", "unavailable", "disabled", "passed", "failed"]
DecisionStatus = Literal["applied", "deferred", "escalated"]
RecoveryKind = Literal["park", "stall"]
RecoveryStep = Literal["intent", "moved", "recorded"]

class State(TypedDict):
    schema_version: int                 # exactly SCHEMA_VERSION
    revision: int                       # bool forbidden; >= 0
    batch: BatchState
    work: WorkState
    tasks: list[TaskEntry]
    review: ReviewState
    control: ControlState
    recovery: RecoveryState

class BatchState(TypedDict):
    id: str                             # non-empty; empty only in new_state()
    status: BatchStatus
    started_at: str | None
    completed_at: str | None
    completed_prds: list[CompletedPrd]
    parks_consecutive: int              # >= 0
    catchup: CatchupCache
    capabilities: dict[str, CapabilityEntry]

class CatchupCache(TypedDict):
    completed_at: str | None
    head_sha: str | None

class CompletedPrd(TypedDict):
    filename: str
    cycles: int
    autonomous_decisions: int
    escalated_decisions: int
    tasks_completed: int
    tasks_total: int

class WorkState(TypedDict):
    prd: str | None
    phase: Phase
    next_phase: NextPhase
    completed_phases: list[Literal["review"]]
    work_start_sha: str | None
    repo_root: str                       # absolute repository root
    design_doc: str | None
    contract_card: str | None
    tasks_total: int                    # always len(tasks)
    tasks_completed: int                # completed entries; 0 <= value <= total
    extensions: dict[str, JSONValue]    # keys match "plugin/name"; opaque JSON

class TaskEntry(TypedDict):
    id: int                             # >= 1; unique
    name: str                           # non-empty
    description: str
    active_form: str
    status: TaskStatus
    blocked_by: list[int]               # unique IDs, no self-reference
    tier: str | None                    # provider-neutral routing tier
    files_touched: int | None           # >= 0
    public_contract_edit: bool | None
    estimates: TaskEstimates
    attempts: list[AttemptEntry]
    metadata: dict[str, JSONValue]

class TaskEstimates(TypedDict):
    input_tokens: int | None            # >= 0
    context_peak: int | None            # >= 0

class AttemptEntry(TypedDict):
    number: int                         # >= 1; contiguous within task
    tier: str
    driver: str                         # configured driver name, not an enum
    outcome: AttemptOutcome
    review_cycle: int | None            # >= 1 when present
    cause: str | None
    pipeline: Literal["minimal", "lean", "full"] | None
    cleanup_outcome: str | None
    started_at: str
    finished_at: str                   # attempts are terminal historical records
    commit_sha: str | None
    escalation: EscalationEntry | None
    metadata: dict[str, JSONValue]

class EscalationEntry(TypedDict):
    reason: Literal["gate_failure", "review_flag", "rescue"]
    from_tier: str
    diagnosis: Literal["spec_gap", "solid_spec"] | None
    repair_used: bool

class ReviewState(TypedDict):
    cycle: int                          # >= 0
    cap: int                            # >= 1
    cycles: list[ReviewCycle]
    decisions: list[DecisionEntry]
    doubts: list[DoubtEntry]
    rubric_verdicts: list[RubricVerdict]
    rework_task_ids: list[int]
    lenses: dict[str, Literal["pending", "running", "completed", "failed"]]
    extensions: dict[str, JSONValue]

class ReviewCycle(TypedDict):
    cycle: int
    review_file: str
    reviewers: dict[str, ReviewerStatus]
    issues_found: int
    follow_up_tasks: int
    deferred: int
    recurring_issues: list[str]
    decision_gate: DecisionGate | None
    rework_commits: list[str]
    rework_notes: list[str]
    fix_audit: list[str]
    test_run: TestRun | None

class DecisionGate(TypedDict):
    decision: str
    detail: str
    decided_at: str

class TestRun(TypedDict):
    command: list[str]
    exit_code: int
    summary: str

class DecisionEntry(TypedDict):
    id: str
    kind: str
    summary: str
    rationale: str
    cycle: int | None
    created_at: str
    status: DecisionStatus

class DoubtEntry(TypedDict):
    id: str
    description: str
    category: ReviewCategory
    justification: str | None
    status: ReviewItemStatus
    source: str | None

class RubricVerdict(TypedDict):
    rule_id: str
    verdict: Literal["pass", "fail"]
    source: str | None

class ControlState(TypedDict):
    pause_requested: bool
    pause_reason: Notice | None
    attention: Notice | None

class Notice(TypedDict):
    site: str
    detail: str
    created_at: str

class RecoveryState(TypedDict):
    operation: RecoveryOperation | None
    replan_count: int
    phase_fingerprint: str | None
    phase_repeats: int

class RecoveryOperation(TypedDict):
    id: str
    kind: RecoveryKind
    step: RecoveryStep
    prd: str
    site: str
    detail: str
    source: str
    destination: str
    created_at: str

class CapabilityEntry(TypedDict):
    required: bool
    launcher: str
    plugin: str
    version: str
    failure: Literal["attention"]
    status: CapabilityStatus
    attempts: list[CapabilityAttempt]

class CapabilityAttempt(TypedDict):
    id: str
    status: Literal["running", "failed", "succeeded"]
    started_at: str
    finished_at: str | None
    session_id: str | None
    detail: str | None

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]

def new_state(*, repo_root: Path) -> State: ...
def validate_state(value: object) -> State: ...
def validate_timestamp(value: object, path: str) -> str: ...
```

`new_state()` sets `schema_version=1`, `revision=0`, an empty/idle batch,
`work.phase=work.next_phase="build"`, `work.repo_root` to the resolved absolute
root, empty collections, `review.cycle=0`, `review.cap=3`, and null optional
values. An empty batch ID is valid only while `batch.status == "idle"`; a
running/attention/completed batch requires a non-empty ID. `batch.completed_at`
is required only for `completed`. A capability may be `skipped` only when
`required == false`; a completed batch requires every required capability to be
`succeeded`.

Validation is total and closed at every owned object: required fields must be
present and unknown fields fail with their full dotted path. `metadata` and
`extensions` are the only open maps; their values are recursively validated as
finite JSON (string keys, maximum nesting depth `MAX_JSON_DEPTH`). Extension keys must match
`^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9_.-]*$`. Integers reject booleans. Counts,
IDs, revisions, and cycles enforce the bounds shown above. Timestamp strings
must parse as UTC RFC 3339 with `Z`; no naive/local offsets are accepted.
Strings must encode as UTF-8; lone surrogates fail with a path-aware schema
error. UTF-8 string byte lengths, owned collection sizes, open-map cardinality, task/
attempt/review/capability counts, command payload bytes, and canonical state
bytes enforce the named constants before deep copy or publication.

Cross-field validation enforces task-ID uniqueness, valid `blocked_by` targets,
no self-block, contiguous attempt numbers, `work.tasks_total == len(tasks)`,
`work.tasks_completed == count(status == "completed")`, unique decision/doubt/
capability-attempt IDs, unique review-cycle ordinals, and
`review.rework_task_ids` membership in `tasks`. Task attempts are terminal
history: `finished_at` is required, must not precede `started_at`, and no running
outcome exists. Capability invariants are a matrix: `pending` has no attempts;
`running` has a latest `running` attempt with null `finished_at`; `failed` and
`succeeded` have a latest same-status attempt with a non-null finish time;
`skipped` has no attempts and requires `required == false`; all prior attempts
are terminal and timestamps are ordered. A completed batch requires a non-empty
ID/completion time and every required capability succeeded; non-idle batches
require a non-empty ID. A malformed, missing-version, non-object, oversized, or
future-version document fails before any mutator runs.

### Store surface (`ovcaq.state.store`)

```python
Mutator: TypeAlias = Callable[[State], State | None]
BoundaryHook: TypeAlias = Callable[[DurabilityBoundary], None]

class DurabilityBoundary(StrEnum):
    BACKUP_TEMP_FSYNCED = "backup_temp_fsynced"
    BACKUP_REPLACED = "backup_replaced"
    BACKUP_DIR_FSYNCED = "backup_dir_fsynced"
    STATE_TEMP_FSYNCED = "state_temp_fsynced"
    STATE_REPLACED = "state_replaced"
    STATE_DIR_FSYNCED = "state_dir_fsynced"

class StateStore:
    def __init__(
        self,
        path: Path,
        *,
        boundary_hook: BoundaryHook | None = None,
    ) -> None: ...

    @property
    def path(self) -> Path: ...

    def read(self) -> State: ...
    def initialize(self, initial: State) -> State: ...
    def transaction(
        self,
        mutator: Mutator,
        *,
        expected_revision: int | None = None,
    ) -> State: ...
    def restore(self, *, expected_revision: int | None = None) -> State: ...
```

`read()` takes `LOCK_SH` on the same sidecar lock, reads at most
`MAX_STATE_BYTES + 1`, and fully validates before returning a deep copy. The
shared lock prevents readers from observing the writer's publish/repair window.
It is never the read half of a mutation. `initialize()` is create-only, requires parent
directories to exist, validates revision 0, publishes with mode `0600`, fsyncs
the file and parent directory, and raises `StateExistsError` without modifying
an existing file. Lock and backup files are also `0600`; runtime directories
created by `ovcaq init` are `0700`.

`transaction()` opens `<state>.lock`, takes `fcntl.flock(..., LOCK_EX)`, reads
at most `MAX_STATE_BYTES + 1` and validates the current bytes, rejects a
mismatched `expected_revision`,
deep-copies current state, calls the mutator exactly once, validates the full
result and its canonical byte size, and overwrites its revision with
`current.revision + 1`. Mutators may
edit their argument and return `None`, or return a replacement object. The
store then publishes the raw pre-transaction bytes to `<state>.bak`, fsyncs the
backup's parent directory, publishes canonical UTF-8/indent-2/newline JSON to
state, and fsyncs the state parent directory before releasing the lock.

An ordinary mutator/validation/I/O exception before the first publication
leaves state and backup byte-identical. If an exception is injected after a
publication, the store restores the captured pre-call state and backup bytes
under the still-held lock and fsyncs the repair before re-raising. SIGKILL
cannot run repair; kill tests therefore require the next `read()`/transaction
to observe either the fully old or fully new valid state, never mixed/partial
JSON, and require `restore()` to have a valid rollback candidate. Temporary
files are named in the target directory and cleaned best-effort.

`restore()` runs under the same lock. It validates both current and raw backup,
checks `expected_revision`, treats restore as a new commit, sets the restored
document's revision to `current.revision + 1`, rotates the raw current bytes into
the backup, and uses the same publication/fsync path. A missing, malformed,
future, or schema-invalid backup raises `BackupError` and changes neither file.

Directory fsync opens the parent with `os.O_RDONLY`, calls `os.fsync`, and
closes it. `EINVAL`, `ENOTSUP`, and all other failures become
`DurabilityUnsupportedError`/`StateIOError`; they are never swallowed. The
`boundary_hook` exists only for deterministic tests and is called at the six
named boundaries. Store-owned temp names use the exact prefix
`.state.json.ovcaq-` and suffix `.tmp`; a locked mutation removes only stale
files matching that pair before allocating its own temp file, so SIGKILL debris
cannot grow without bound or target unrelated files.

### JSON paths (`ovcaq.state.paths`)

```python
PathToken: TypeAlias = str | int

def parse_path(path: str) -> tuple[PathToken, ...]: ...
def get_path(value: JSONValue, tokens: Sequence[PathToken]) -> JSONValue: ...
def set_path(root: State, tokens: Sequence[PathToken], value: JSONValue) -> None: ...
def append_path(root: State, tokens: Sequence[PathToken], value: JSONValue) -> None: ...
def delete_path(root: State, tokens: Sequence[PathToken]) -> None: ...
```

The grammar is dotted simple keys, signed bracket indices, and bracketed JSON
string keys, for example `review.decisions[-1].status` and
`work.extensions["acme/foo.bar"]`. Quoted keys use JSON string escaping and are
required for keys containing `.`, `[`, or `]`; parsing round-trips the decoded
key as one string token. Empty paths, empty keys, malformed brackets/JSON
strings, and root replacement/deletion fail. Negative indices use normal Python
indexing after explicit bounds checks. `set_path` may create missing
intermediate object keys only; it never synthesizes arrays. `append_path`
creates a missing final object key as an empty list, otherwise requires a list.
Protection checks operate on parsed tokens, never raw string prefixes. Every
mutation is still subject to whole-state validation in
`StateStore.transaction()`.

### Application service (`ovcaq.state.commands`)

```python
GENERIC_WRITABLE_PREFIXES: Final[tuple[tuple[PathToken, ...], ...]] = (
    ("work", "extensions"),
    ("review", "extensions"),
)

class StateService:
    def __init__(self, store: StateStore) -> None: ...
    def show(self) -> State: ...
    def validate(self) -> State: ...
    def get(self, path: str) -> JSONValue: ...
    def set(self, path: str, value: JSONValue, *, unsafe: bool = False,
            expected_revision: int | None = None) -> State: ...
    def append(self, path: str, value: JSONValue, *, unsafe: bool = False,
               expected_revision: int | None = None) -> State: ...
    def delete(self, path: str, *, unsafe: bool = False,
               expected_revision: int | None = None) -> State: ...
    def add_task(self, payload: TaskCreate,
                 *, expected_revision: int | None = None) -> MutationResult: ...
    def start_task(self, task_id: int,
                   *, expected_revision: int | None = None) -> MutationResult: ...
    def append_attempt(self, task_id: int, attempt: AttemptEntry,
                       *, expected_revision: int | None = None) -> MutationResult: ...
    def complete_task(self, task_id: int, attempt: AttemptEntry,
                      *, expected_revision: int | None = None) -> MutationResult: ...
    def set_task_body(self, task_id: int, body: str,
                      *, expected_revision: int | None = None) -> MutationResult: ...
    def set_task_meta(self, task_id: int, patch: TaskMetaPatch,
                      *, expected_revision: int | None = None) -> MutationResult: ...
    def set_task_status(self, task_id: int, status: TaskStatus,
                        *, expected_revision: int | None = None) -> MutationResult: ...
    def clear_tasks(self, *, expected_revision: int | None = None) -> MutationResult: ...
    def set_contract_card(self, text: str,
                          *, expected_revision: int | None = None) -> MutationResult: ...
    def restore(self, *, expected_revision: int | None = None) -> MutationResult: ...

class TaskCreate(TypedDict):
    id: NotRequired[int]
    name: str
    description: NotRequired[str]
    active_form: NotRequired[str]
    blocked_by: NotRequired[list[int]]
    tier: NotRequired[str | None]
    files_touched: NotRequired[int | None]
    public_contract_edit: NotRequired[bool | None]
    estimates: NotRequired[TaskEstimates]
    metadata: NotRequired[dict[str, JSONValue]]

class TaskMetaPatch(TypedDict, total=False):
    tier: str | None
    files_touched: int | None
    public_contract_edit: bool | None
    estimates: TaskEstimates
    metadata: dict[str, JSONValue]

class MutationResult(TypedDict):
    revision: int
    task_id: int | None
```

Generic writes are default-protected: without `unsafe`, the parsed token path
must be a strict descendant of one of `GENERIC_WRITABLE_PREFIXES`; mutation of
the allowlisted container itself is still protected. This makes every present
and future core field, including `work.contract_card`, task fields, batch
identity/capabilities, review history/lenses, control, and recovery counters,
require a compound owner or explicit recovery intent. `--unsafe` bypasses only
ownership protection, never schema/resource validation, locking, revision
checks, backup, or durability.

Task creation preserves a supplied positive, unique integer ID and assigns
`max(existing IDs, default=0) + 1` only when `id` is absent. Compound task
operations resolve by ID, never array position, and finish by recomputing both
task counts in the same transaction. `append_attempt()` leaves task status unchanged;
`complete_task()` appends the attempt and marks the task completed atomically.
Attempt number must equal `len(existing attempts) + 1`. `set_task_meta()` accepts
only the five `TaskMetaPatch` keys; `id`, `name`, `description`, `active_form`,
`status`, `blocked_by`, and `attempts` are command-owned. `set_contract_card()`
stores `text.rstrip("\n")` at `work.contract_card`.

### CLI and error contract (`ovcaq.cli`, `ovcaq.errors`)

```python
def build_parser() -> argparse.ArgumentParser: ...
def main(argv: Sequence[str] | None = None) -> int: ...

class ErrorCode(StrEnum):
    USAGE = "usage"
    INVALID_STATE = "invalid_state"
    STATE_IO = "state_io"
    FUTURE_SCHEMA = "future_schema"
    STATE_EXISTS = "state_exists"
    INVALID_BACKUP = "invalid_backup"
    REVISION_CONFLICT = "revision_conflict"
    INVALID_PATH = "invalid_path"
    PROTECTED_PATH = "protected_path"
    DURABILITY_UNSUPPORTED = "durability_unsupported"
    RESOURCE_LIMIT = "resource_limit"
```

The live parser exposes exactly:

```text
ovcaq [--root PATH] [--json] init
ovcaq [--root PATH] [--json] state show
ovcaq [--root PATH] [--json] state validate
ovcaq [--root PATH] [--json] state get PATH
ovcaq [--root PATH] [--json] state set [--unsafe] [--expected-revision N] PATH JSON
ovcaq [--root PATH] [--json] state append [--unsafe] [--expected-revision N] PATH JSON
ovcaq [--root PATH] [--json] state delete [--unsafe] [--expected-revision N] PATH
ovcaq [--root PATH] [--json] state task add [--expected-revision N] FILE
ovcaq [--root PATH] [--json] state task start [--expected-revision N] ID
ovcaq [--root PATH] [--json] state task attempt [--expected-revision N] ID FILE
ovcaq [--root PATH] [--json] state task complete [--expected-revision N] ID FILE
ovcaq [--root PATH] [--json] state task set-body [--expected-revision N] ID FILE
ovcaq [--root PATH] [--json] state task set-meta [--expected-revision N] ID FILE
ovcaq [--root PATH] [--json] state task set-status [--expected-revision N] ID STATUS
ovcaq [--root PATH] [--json] state task clear [--expected-revision N]
ovcaq [--root PATH] [--json] state contract set [--expected-revision N] FILE
ovcaq [--root PATH] [--json] state restore [--expected-revision N]
```

`--root` resolves to an absolute project root; when omitted, discovery walks
from cwd for `ovcaq.toml` or `dev/local/ovcaq/`, then falls back to the Git
top-level. State defaults to `<root>/dev/local/ovcaq/state.json`. `ovcaq init`
creates `ovcaq.toml` only when absent, creates `dev/local/ovcaq/` with mode
`0700`, and create-only initializes `new_state(repo_root=root)`; it never
imports or overwrites `dev/local/autopilot/state.json`. An existing regular
configuration file is preserved; a directory or broken-symlink collision at
`ovcaq.toml` fails before state publication.
Inline JSON and FILE inputs are read through a bounded helper that refuses more
than `MAX_COMMAND_PAYLOAD_BYTES` before JSON parsing or text decoding. State
reads apply `MAX_STATE_BYTES` the same way.

Requested data (`show`, `get`, `validate`) goes to stdout as JSON; mutation
progress goes to stderr. With `--json`, mutation success writes
`{"ok":true,"revision":N,"result":...}` to stdout. JSON errors write
`{"ok":false,"error":{"code":"<ErrorCode>","message":"...","path":null}}`
to stderr and leave stdout empty. Messages include no traceback unless a test
invokes the underlying API.

Exit mapping preserves the useful legacy categories: `0` success; `1` usage,
schema, JSON, path, or protected-path error; `2` missing/corrupt/I/O state;
`6` future schema; `7` create-only conflict; `8` invalid/missing backup; `9`
revision conflict; `10` unsupported durability. Argparse usage also exits `1`,
not its default `2`; `11` is a resource-limit refusal.

## Data flow

1. `ovcaq init` resolves a root, creates only absent project/runtime artifacts,
   builds `new_state()`, and calls `StateStore.initialize()`. No legacy state is
   read.
2. Read commands resolve the same state path and call `StateStore.read()`;
   validation happens before data reaches the formatter.
3. A mutation command parses its JSON/file input before opening the lock,
   rejects protected generic paths before transaction dispatch, and calls one
   `StateService` method.
4. `StateService` builds one mutator. `StateStore.transaction()` acquires the
   lock, validates current state, checks the optional revision, deep-copies,
   invokes the mutator once, recomputes compound derived fields, validates the
   full result, and increments revision.
5. The store publishes the raw pre-transaction bytes as the rotating backup,
   then canonical new state. Each temp file is file-fsynced before rename and
   the directory is fsynced after each rename.
6. The service returns only after the final directory fsync. CLI output reports
   the committed revision. A failure is mapped to a stable symbolic/exit error
   and never inferred from agent prose.
7. Restore takes the same locked path, validates both documents, publishes the
   restored content as a new revision, and rotates the pre-restore current bytes
   into the backup.

## Reuse inventory

- `/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/schema.py`: reuse bounded,
  path-aware validation errors, bool-not-int handling, and future-version
  classification; replace optional/unknown-field tolerance with the closed
  nested v1 validators above.
- `/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/state.py`: reuse one-lock
  read/mutate/validate/publish ordering, raw-byte backups, same-directory temp
  files, create-only hard-link publication, and validated restore; add deep
  copy, revision/CAS, permission enforcement, directory fsync, repair on raised
  failpoints, and the boundary hook.
- `/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/statectl.py`: reuse
  `parse_path`, `_descend`, task-ID resolution, count recomputation, file-based
  attempt/body/meta inputs, and the distinction between append-attempt and
  task-complete; relocate them behind `StateService` and the live argparse tree.
- `src/ovcaq/cli.py`: reuse the existing parser entry point and installed
  `ovcaq`/`python -m ovcaq` packaging path; extend rather than create a second
  executable.
- `tests/fixtures/claude/legacy-state-*.json` and
  `tests/characterization/{current_system,migration}.toml`: reuse as sanitized
  inventory/disposition evidence, not accepted v1 input.
- `/Users/bob/git/src/github.com/buvis/claude-autopilot/skills/run-autopilot/cli/test_state.py` and the
  statectl/schema suites under that skill: port lock, raw backup, mutation
  failure, future version, restore, task-ID, negative-index, output, and
  concurrent-writer cases without `sys.path` bootstraps. Greps tried:
  `validate|check|require + schema|state|task|attempt`,
  `transaction|mutate|lock|replace|fsync|backup|restore|revision`, and
  `parse|decode|load|read|get|resolve|append|delete + path|json`; the Phase-0
  repo contains no alternative state helpers beyond empty package boundaries.

## Alternatives considered

1. **Smallest diff: copy the flat permissive schema/store/statectl and rename
   the executable.** This would land quickly and preserve more tests byte for
   byte, but it fails the PRD: nested attempt/capability objects remain shallow,
   unknown historical/provider fields leak into public v1, there is no
   monotonic revision/CAS, directory renames are not fsynced, and statectl-style
   generic writes can mutate transition ownership. Rejected.
2. **Chosen: port proven mechanics behind a closed nested `TypedDict` schema,
   `StateStore`, and `StateService`.** This keeps the audited locking and
   publication behavior while making every intentional change explicit. The
   extra size buys total validation, a machine-checked 184-field disposition,
   one installed API, and clean seams for PRDs 00004–00007.
3. **Model state as dataclass/Pydantic objects and serialize them.** Dataclasses
   would add conversion code at every generic-path boundary; Pydantic adds a
   runtime dependency and error/serialization semantics the project does not
   otherwise need. Both obscure the raw JSON mutation contract and make exact
   backup/restore tests harder. Rejected in favor of stdlib dictionaries,
   `TypedDict`, and explicit validators.

## Risks & edge cases

- **Crosswalk omission:** 184 source records are too many for visual review.
  Parse the committed TOML inventory and assert exact ID equality with the
  state-protocol table; duplicates and unknown/missing dispositions fail.
- **Closed schema versus external workflow evolution:** only `metadata` and
  namespaced `extensions` are open. New core fields require a schema-version
  decision; plugin-private values must stay namespaced JSON.
- **Resource exhaustion while holding the writer lock:** state bytes, command
  payloads, strings, open maps, and every high-cardinality owned collection have
  explicit constants enforced before parsing/deep copy where possible. Locked
  cleanup recognizes only the store's exact stale-temp name pair.
- **Crash between backup and state rename:** Python exceptions are repaired
  under lock; SIGKILL can leave either valid publication point. Real child
  process tests kill at every boundary and assert valid old-or-new state plus a
  usable rollback, never a partially decoded file.
- **Restore monotonicity:** restoring old bytes must not rewind `revision`.
  Restore always commits at `current + 1` and rotates the pre-restore current
  bytes into the backup.
- **Directory fsync portability:** personal cutover fails closed when the host
  cannot meet the guarantee. PRD 00013 may add an explicit Linux capability
  policy; this PRD does not silently pre-design it.
- **Generic `--unsafe` misuse:** prefix matching includes ancestors and
  descendants, and docs keep `--unsafe` out of normal skill examples. It never
  bypasses validation/durability.
- **Strict timestamp parsing:** use only UTC `Z`; tests cover leap-day and
  fractional seconds, reject offsets/naive strings, and avoid locale behavior.
- **Likely next changes:** PRD 00004 adds workflow transition commands over
  protected paths; PRD 00005 adds run/registry/session state consumers; PRD
  00007 activates capability transitions. The service/store injections and
  exact nested owners allow those changes without a second writer.
- **No state rollback framework:** the rotating backup and tested restore are
  the defined correction path. The product remains an early one-way cutover;
  no legacy importer or dual writer is introduced.

## Test strategy outline

- Schema table tests cover every required/unknown field, enum, integer bound,
  bool-as-int rejection, timestamp, extension key/value/depth, task graph,
  attempt ordering, counts, review references, capability completion, malformed
  root, missing version, resource limit, and future version. Table-driven tests name the full
  offending path and cap large-value reprs.
- Crosswalk tests parse `STATE-001..STATE-184` from the characterization TOML
  and `docs/state-protocol.md`, asserting exact set equality, one disposition
  per ID, an allowed disposition, and a non-empty v1 target/rationale.
- Store tests characterize raw pre-transaction backup bytes, one-lock ordering,
  mutator deep-copy isolation, mutator/validator/CAS failures, create-only init,
  permission modes, validated monotonic restore, and missing/corrupt/future
  state/backup behavior. State and backup bytes are captured before each
  raised-failure case and compared byte for byte afterward.
- Durability unit tests inject all six `DurabilityBoundary` hooks and spy on
  write/fsync/replace/directory-fsync order. Real multiprocessing tests prove
  two concurrent increments both land. Real subprocess tests SIGKILL workers at
  each boundary and verify old-or-new valid state, monotonic revisions, no temp
  file chosen as state, and a usable backup.
- Resource tests reject over-limit state and command bytes before JSON parsing,
  then cover every collection/string bound and exact stale-temp cleanup without
  deleting similarly named unrelated files.
- JSON-path tests cover dotted keys, signed/negative indices, missing parents,
  append creation, list bounds, malformed brackets, and root mutation refusal.
- Command tests cover every compound verb, task-ID allocation/resolution,
  attempt numbering, derived counts, reserved metadata keys, contract-card
  newline trimming, protected ancestor/descendant paths, `--unsafe`, JSON input,
  and expected-revision conflicts.
- CLI tests assert the live parser's complete state verb inventory, help, stdout
  versus stderr, symbolic JSON errors, exit mapping, root discovery, and
  create-only `ovcaq init`. Documentation examples are extracted and compared
  with the parser rather than maintained as a second handwritten command list.
- Installed-wheel tests run `ovcaq init`, every representative read/mutation,
  restore, and help from an arbitrary cwd containing a decoy `cli/` package;
  they assert no checkout path, `sys.path` bootstrap, live-home fixture, or
  `~/.claude/skills/run-autopilot` literal enters production/distributions.
- Final gate: `uv run pytest`, Ruff check/format, strict mypy, clean sdist/wheel,
  and installed CLI smoke all pass on macOS.

## Review log

- Non-blocker (dispatch 1): `initialize()` does not specify whether a parent-directory fsync failure after create-only publication removes the just-published state or leaves a documented manual recovery path.
- Non-blocker (dispatch 1): the prose defines batch-ID/status and required-capability/completed-batch invariants but the later summary of `validate_state()` cross-field checks does not repeat them.
- Non-blocker (dispatch 1): the real SIGKILL suite needs an explicit parent/child synchronization mechanism to stop the child at each named `boundary_hook` point before the parent sends SIGKILL.
- Question (dispatch 1): clarify whether `clear_tasks()` also clears `review.rework_task_ids`, or intentionally refuses while task references remain.
- Question (dispatch 1): clarify why `CapabilityEntry.failure` stores the single allowed value `"attention"` per capability rather than deriving it when PRD 00007 activates transitions.
- dispatch 1 (claude): cardinal-sin 0, blocker 1, non-blocker 3, question 2
- dispatch 2 (codex): cardinal-sin 1, blocker 4, non-blocker 0, question 0
- Non-blocker (dispatch 3): the test outline should explicitly name a concurrent reader-during-writer-repair interleaving test for the new shared-lock guarantee.
- dispatch 3: codex unavailable, Claude fallback (nested CLI dispatch refused)
- dispatch 3 (claude-fallback): cardinal-sin 0, blocker 0, non-blocker 1, question 0
