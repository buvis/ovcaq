from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Never, cast

from ovcaq.cli_io import (
    _decode_json,
    _decode_text,
    _json_file,
    _read_payload,
    _runtime_timestamp,
    _WorkflowResult,
)
from ovcaq.config import ensure_project_config, supervisor_settings
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.paths import (
    discover_project_root,
    ensure_runtime_directory,
    state_path,
)
from ovcaq.runtime.capability import probe_platform
from ovcaq.runtime.registry import FleetRegistry, FleetRun
from ovcaq.runtime.session import observe_run
from ovcaq.runtime_cli import _dispatch_runtime
from ovcaq.state.commands import (
    StateMutationConflictError,
    StateService,
    TaskCreate,
    TaskMetaPatch,
)
from ovcaq.state.schema import (
    AttemptEntry,
    JSONValue,
    ResourceLimitError,
    SchemaError,
    TaskStatus,
    new_state,
)
from ovcaq.state.store import (
    BackupError,
    DurabilityUnsupportedError,
    FutureSchemaError,
    RevisionConflictError,
    StateError,
    StateExistsError,
    StateIOError,
    StateResourceLimitError,
    StateStore,
)
from ovcaq.supervisor_cli import (
    LaunchError,
    completed_run,
    dispatch_supervisor,
    launch_supervisor,
)
from ovcaq.workflow_cli import (
    WORKFLOW_INPUT_NOTES,
    _add_workflow_commands,
    _dispatch_workflow,
)


class _ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> Never:
        detail = f"{self.format_usage().strip()}\n{self.prog}: error: {message}"
        raise CommandError(ErrorCode.USAGE, detail)


def _add_expected_revision(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-revision", metavar="N", type=int)


def _add_generic_mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--unsafe", action="store_true")
    _add_expected_revision(parser)


def _add_generic_state_commands(state_commands: Any) -> None:
    state_commands.add_parser("show", help="show the state document")
    state_commands.add_parser("validate", help="validate the state document")

    get_parser = state_commands.add_parser("get", help="read a state path")
    get_parser.add_argument("path", metavar="PATH")

    for name in ("set", "append"):
        mutation = state_commands.add_parser(name, help=f"{name} a state value")
        _add_generic_mutation_options(mutation)
        mutation.add_argument("path", metavar="PATH")
        mutation.add_argument("value", metavar="JSON")

    delete = state_commands.add_parser("delete", help="delete a state value")
    _add_generic_mutation_options(delete)
    delete.add_argument("path", metavar="PATH")


def _add_task_commands(state_commands: Any) -> None:
    task = state_commands.add_parser("task", help="mutate workflow tasks")
    task_commands = task.add_subparsers(dest="task_command", required=True)

    add = task_commands.add_parser("add", help="add a task")
    _add_expected_revision(add)
    add.add_argument("file", metavar="FILE", type=Path)

    start = task_commands.add_parser("start", help="start a task")
    _add_expected_revision(start)
    start.add_argument("task_id", metavar="ID", type=int)

    for name in ("attempt", "complete"):
        attempt = task_commands.add_parser(name, help=f"{name} a task attempt")
        _add_expected_revision(attempt)
        attempt.add_argument("task_id", metavar="ID", type=int)
        attempt.add_argument("file", metavar="FILE", type=Path)

    body = task_commands.add_parser("set-body", help="replace a task body")
    _add_expected_revision(body)
    body.add_argument("task_id", metavar="ID", type=int)
    body.add_argument("file", metavar="FILE", type=Path)

    meta = task_commands.add_parser("set-meta", help="update task metadata")
    _add_expected_revision(meta)
    meta.add_argument("task_id", metavar="ID", type=int)
    meta.add_argument("file", metavar="FILE", type=Path)

    status = task_commands.add_parser("set-status", help="set task status")
    _add_expected_revision(status)
    status.add_argument("task_id", metavar="ID", type=int)
    status.add_argument("status", choices=("pending", "in_progress", "completed"))

    clear = task_commands.add_parser("clear", help="clear all tasks")
    _add_expected_revision(clear)


def _add_contract_and_restore_commands(state_commands: Any) -> None:
    contract = state_commands.add_parser("contract", help="mutate the contract card")
    contract_commands = contract.add_subparsers(
        dest="contract_command",
        required=True,
    )
    contract_set = contract_commands.add_parser("set", help="replace the contract card")
    _add_expected_revision(contract_set)
    contract_set.add_argument("file", metavar="FILE", type=Path)

    restore = state_commands.add_parser("restore", help="restore the state backup")
    _add_expected_revision(restore)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="ovcaq",
        description="Orchestration, Visibility, and Control for Agent Queues",
    )
    parser.add_argument("--root", metavar="PATH", type=Path)
    parser.add_argument("--json", action="store_true")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="initialize OVCAQ state")

    state = commands.add_parser("state", help="inspect or mutate OVCAQ state")
    state_commands = state.add_subparsers(dest="state_command", required=True)
    _add_generic_state_commands(state_commands)
    _add_task_commands(state_commands)
    _add_contract_and_restore_commands(state_commands)
    _add_workflow_commands(commands)

    commands.add_parser("status", help="show state, run, and retained evidence health")
    doctor = commands.add_parser("doctor", help="check runtime health and capabilities")
    doctor.add_argument("--acknowledge-emergency", action="store_true")
    logs = commands.add_parser(
        "logs", help="locate or follow retained session evidence"
    )
    logs.add_argument("--session", dest="log_session", metavar="ID")
    logs.add_argument("--kind", choices=("raw", "normalized"))
    logs.add_argument("--follow", action="store_true")
    log_commands = logs.add_subparsers(dest="logs_command")
    purge = log_commands.add_parser("purge", help="preview or apply evidence removal")
    selector = purge.add_mutually_exclusive_group(required=True)
    selector.add_argument("--session", metavar="ID")
    selector.add_argument("--before", metavar="RFC3339", type=_runtime_timestamp)
    purge.add_argument("--apply", action="store_true")
    _add_supervisor_commands(commands)
    return parser


def _add_supervisor_commands(commands: Any) -> None:
    run = commands.add_parser(
        "run", help="launch and attach, or supervise in the foreground with --no-tui"
    )
    run.add_argument("--no-tui", action="store_true")
    run.add_argument("--agent", metavar="NAME")
    attach_parser = commands.add_parser("attach", help="attach the TUI to a live run")
    attach_parser.add_argument("--run-id", metavar="ID")
    pause = commands.add_parser("pause", help="request a pause at the next boundary")
    pause.add_argument("--reason", metavar="TEXT")
    commands.add_parser("resume", help="clear pause; interactively launch or attach")
    commands.add_parser("stop", help="signal the verified foreground supervisor")
    capability = commands.add_parser("capability", help="manage batch capabilities")
    capability_commands = capability.add_subparsers(
        dest="capability_command", required=True
    )
    retry = capability_commands.add_parser("retry", help="retry a failed capability")
    retry.add_argument("name", metavar="NAME")


def _leaf_command_parsers(
    parser: argparse.ArgumentParser,
) -> tuple[argparse.ArgumentParser, ...]:
    subparser_actions = tuple(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    if not subparser_actions:
        return (parser,)
    if len(subparser_actions) != 1:
        raise RuntimeError("command parser has multiple subparser actions")
    parents = (parser,) if not subparser_actions[0].required else ()
    return parents + tuple(
        leaf
        for child in subparser_actions[0].choices.values()
        for leaf in _leaf_command_parsers(child)
    )


def command_inventory(
    parser: argparse.ArgumentParser | None = None,
) -> tuple[str, ...]:
    """Return every installed leaf command usage from the live parser."""
    live_parser = build_parser() if parser is None else parser
    root_usage = " ".join(live_parser.format_usage().split()).removeprefix("usage: ")
    global_prefix = root_usage.partition(" {")[0].replace(" [-h]", "")
    return tuple(
        f"{global_prefix}{usage.removeprefix('ovcaq')}"
        for leaf in _leaf_command_parsers(live_parser)
        if (
            usage := " ".join(leaf.format_usage().split())
            .removeprefix("usage: ")
            .replace(" [-h]", "")
        )
    )


def render_state_protocol_command_inventory(
    parser: argparse.ArgumentParser | None = None,
) -> str:
    """Render the state-protocol command inventory from the live parser."""
    lines = [
        "<!-- Generated by ovcaq.cli.render_state_protocol_command_inventory; do not edit. -->",
        "",
        "```text",
        *command_inventory(parser),
        "```",
        "",
    ]
    return "\n".join(lines)


CONTROLLER_CLIENT_NOTES = (
    "## Workflow controller client",
    "",
    "The external workflow controller is opt-in. Without `controller_argv`",
    "there is no controller client, and nothing in OVCAQ invokes it yet: the",
    "state store above remains the only workflow writer.",
    "",
    "```toml",
    "[workflow]",
    'controller_argv = ["autopilot-controller"]  # argv array, never a shell string',
    'contract_bundle = "contracts/controller-v1.json"  # pinned Contract A bundle',
    'actor_file = "secrets/actor.json"  # credential path, needed only for apply',
    "```",
    "",
    "Relative paths resolve from the project root. The client checks the",
    "controller's protocol major, bundle digests, advertised capabilities and",
    "operations, and package version before any other call.",
    "",
    "`python3 tools/autopilot-prerequisites --prd <ID> [--config PATH]` reports",
    "whether a PRD's prerequisites are in place. It runs from the project root,",
    "reads `./ovcaq.toml` unless `--config` is given, and never fetches or",
    'writes. Exit 0 prints `{"ready": true, "prd": "<ID>"}`, exit 1 prints the',
    "same object with `ready: false` and a `missing` list, and exit 2 means an",
    "unknown PRD ID or a config error (stderr only). A predecessor counts only",
    "as a regular `docs/dev/project-management/prds/done/000NN-*.md` file.",
    "PRD 58 also needs `[workflow] controller_artifact` and",
    "`controller_artifact_sha256`, with an `evidence` list holding `core`,",
    "`jobs`, `reviews` and `records`, plus a `contract_bundle` and",
    "`contract_bundle_sha256` precondition: a regular file reachable without a",
    "symlink, whose sha256 matches and whose bytes parse as JSON. PRD 61 also",
    "needs `[autopilot] plugin_artifact` and `plugin_artifact_sha256`;",
    "PRD 65 needs `[operator] client_artifact` and `client_artifact_sha256`. The",
    "PRD 61 and 65 artifacts are each a JSON object of at most 16 MiB with no",
    "symlinked path component, a matching sha256, and an `evidence` list holding",
    "`AP00017` (61) or `Lantern00003` (65).",
    "",
)

PROCESS_IDENTITY_NOTES = (
    "## Process identity and start preflight",
    "",
    "`ovcaq doctor` reports six capability facts: `platform`, `advisory_lock`,",
    "`process_group`, `group_signal`, `directory_fsync` and `process_identity`.",
    "`process_identity` is `supported`, with the start token as detail, when the",
    "libproc probe returns an identity, and `degraded` with the error text",
    "otherwise. `ovcaq doctor --json` lists it under `capabilities` and reports",
    "`ok: false` when it is degraded. OVCAQ reads process identity through",
    "libproc and never spawns `ps`.",
    "",
    'The start token is `"<sec>.<usec>"`, with microseconds zero-padded to six',
    "digits. Tokens persisted in the former `ps lstart` form never match it, so",
    "a supervisor still running across the upgrade reads as dead and its",
    "records are cleaned up once; old tokens are not migrated.",
    "",
    "A probe that cannot run is a `process_probe` error (exit 12): a non-darwin",
    "platform, a libproc load failure, a returned size other than 0 or 136, a",
    "`pbi_pid` that differs from the requested pid, or an errno other than",
    "`ESRCH` on a zero return. The message names the platform and tells the",
    "operator to run `ovcaq doctor`.",
    "",
    "Before any state write, `ovcaq run` validates the process identity probe",
    "and the build, review and done phase routes; a failure leaves `state.json`",
    "at the same revision. An unknown tier is a `usage` error, a raising probe",
    "is `process_probe` (exit 12), and a probe that returns no identity is a",
    "`usage` error. A failure while publishing run metadata or the fleet entry",
    "removes what was written, returns a fresh batch to idle or records an",
    "attention notice on a resumed batch, and exits 1.",
    "",
)


def render_command_reference(parser: argparse.ArgumentParser | None = None) -> str:
    """Generate the operator command reference from the live parser."""
    live_parser = build_parser() if parser is None else parser
    lines = [
        "# Operations",
        "",
        "<!-- Generated by ovcaq.cli.render_command_reference; do not edit. -->",
        "",
        "Command syntax is generated from the installed live parser.",
        "State mutations use the same `StateStore` as `ovcaq state`; requested",
        "compare-and-set revisions fail closed.",
        "",
        "## Commands",
        "",
        "```text",
        *command_inventory(live_parser),
        "```",
        "",
        "`stall` and `park` retain durable recovery intent and can be replayed after",
        "every filesystem boundary. `defer` requires an `op_id` in its JSON record.",
        "Audit and report renders publish deterministic Markdown; metrics renders to",
        "stdout. Add `--json` before `workflow` for machine-readable results.",
        "",
        "## Interactive operation",
        "",
        "On an interactive terminal, `run` launches a supervisor and attaches the",
        "TUI. Non-TTY `run` and `run --no-tui` supervise in the foreground.",
        "Use `q` to detach while leaving the supervisor alive, `p` to pause at a boundary or",
        "resume, `s` to stop the selected run after confirmation, and `?` to toggle",
        "help. `attach` without selectors opens the fleet view; `--root PATH` selects",
        "that project's detail view, and `attach --run-id ID` selects one live run.",
        "",
        "Interactive `resume` attaches to the existing live supervisor, or launches",
        "one when a boundary pause ended it. JSON runs require explicit `--no-tui`.",
        "Noninteractive or JSON `resume` only clears pause; `attach` rejects JSON.",
        "The selected theme is stored at",
        "`$XDG_CONFIG_HOME/ovcaq/theme`, or `~/.config/ovcaq/theme` when unset.",
        "An empty XDG_CONFIG_HOME uses the current directory. If the interactive view is",
        "unavailable, OVCAQ reports the problem and falls back to plain output.",
        "",
        *WORKFLOW_INPUT_NOTES,
        *CONTROLLER_CLIENT_NOTES,
        *PROCESS_IDENTITY_NOTES,
    ]
    return "\n".join(lines)


def _path_operation(operation: Callable[[], JSONValue]) -> JSONValue:
    try:
        return operation()
    except StateMutationConflictError:
        raise
    except SchemaError:
        raise
    except ValueError as error:
        code = (
            ErrorCode.PROTECTED_PATH
            if str(error).startswith("generic mutation path is protected:")
            else ErrorCode.INVALID_PATH
        )
        raise CommandError(code, str(error)) from error


_DispatchResult = tuple[JSONValue, int | None, bool]


def _dispatch_init_or_read(
    args: argparse.Namespace,
    root: Path,
    store: StateStore,
) -> _DispatchResult | None:
    if args.command == "init":
        ensure_runtime_directory(root)
        ensure_project_config(root)
        initialized = store.initialize(new_state(repo_root=root))
        return None, initialized["revision"], True

    service = StateService(store)
    command = args.state_command
    if command == "show":
        shown = service.show()
        return cast(JSONValue, shown), shown["revision"], False
    if command == "validate":
        validated = service.validate()
        return cast(JSONValue, validated), validated["revision"], False
    if command == "get":
        value = _path_operation(lambda: service.get(args.path))
        return value, None, False
    return None


def _dispatch_generic_mutation(
    args: argparse.Namespace,
    service: StateService,
) -> _DispatchResult | None:
    command = args.state_command

    if command in {"set", "append"}:
        value = _decode_json(args.value, source="inline JSON")
        generic_method = service.set if command == "set" else service.append
        committed = _path_operation(
            lambda: cast(
                JSONValue,
                generic_method(
                    args.path,
                    value,
                    unsafe=args.unsafe,
                    expected_revision=args.expected_revision,
                ),
            )
        )
        return None, cast(dict[str, Any], committed)["revision"], True

    if command == "delete":
        committed = _path_operation(
            lambda: cast(
                JSONValue,
                service.delete(
                    args.path,
                    unsafe=args.unsafe,
                    expected_revision=args.expected_revision,
                ),
            )
        )
        return None, cast(dict[str, Any], committed)["revision"], True

    if command == "restore":
        result = service.restore(expected_revision=args.expected_revision)
        return None, result["revision"], True
    return None


def _dispatch_attempt_command(
    args: argparse.Namespace,
    service: StateService,
) -> _DispatchResult:
    attempt = cast(AttemptEntry, _json_file(args.file))
    attempt_method = (
        service.append_attempt
        if args.task_command == "attempt"
        else service.complete_task
    )
    result = attempt_method(
        args.task_id,
        attempt,
        expected_revision=args.expected_revision,
    )
    return cast(JSONValue, result["task_id"]), result["revision"], True


def _dispatch_task_or_contract(
    args: argparse.Namespace,
    service: StateService,
) -> _DispatchResult:
    command = args.state_command

    if command == "contract":
        text = _decode_text(_read_payload(args.file), source=str(args.file))
        result = service.set_contract_card(
            text,
            expected_revision=args.expected_revision,
        )
        return None, result["revision"], True

    task_command = args.task_command
    if task_command == "add":
        result = service.add_task(
            cast(TaskCreate, _json_file(args.file)),
            expected_revision=args.expected_revision,
        )
    elif task_command == "start":
        result = service.start_task(
            args.task_id,
            expected_revision=args.expected_revision,
        )
    elif task_command in {"attempt", "complete"}:
        return _dispatch_attempt_command(args, service)
    elif task_command == "set-body":
        body = _decode_text(_read_payload(args.file), source=str(args.file))
        result = service.set_task_body(
            args.task_id,
            body,
            expected_revision=args.expected_revision,
        )
    elif task_command == "set-meta":
        result = service.set_task_meta(
            args.task_id,
            cast(TaskMetaPatch, _json_file(args.file)),
            expected_revision=args.expected_revision,
        )
    elif task_command == "set-status":
        result = service.set_task_status(
            args.task_id,
            cast(TaskStatus, args.status),
            expected_revision=args.expected_revision,
        )
    else:
        result = service.clear_tasks(expected_revision=args.expected_revision)
    return cast(JSONValue, result["task_id"]), result["revision"], True


def _dispatch(
    args: argparse.Namespace,
    root: Path,
) -> _DispatchResult | _WorkflowResult:
    if args.command == "workflow":
        return _dispatch_workflow(args, root)
    if args.command in {"status", "doctor", "logs"}:
        return _dispatch_runtime(args, root, probe=probe_platform), None, False
    if args.command in {"run", "pause", "resume", "stop", "capability"}:
        value, revision, mutation, code = dispatch_supervisor(args, root)
        return _WorkflowResult(value, revision, mutation, exit_code=code)
    store = StateStore(state_path(root))
    result = _dispatch_init_or_read(args, root, store)
    if result is not None:
        return result

    service = StateService(store)
    result = _dispatch_generic_mutation(args, service)
    if result is not None:
        return result
    return _dispatch_task_or_contract(args, service)


def _attach_view(root: Path, view_root: Path | None, run_id: str | None) -> int:
    from ovcaq.tui.app import RunControlService, attach

    registry = FleetRegistry(supervisor_settings(root).runtime.paths.fleet_root)
    result = attach(
        registry=registry,
        root=view_root,
        run_id=run_id,
        controls=RunControlService(registry),
    )
    return result.exit_code


def _launch_and_attach(root: Path, agent: str | None) -> int:
    from ovcaq.tui.discovery import MissingRunError

    try:
        run = launch_supervisor(root, agent=agent).run
    except LaunchError as error:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT, str(error), path=str(error.evidence.path)
        ) from error
    if run is None:
        return 0
    try:
        return _attach_view(root, run.root, run.run_id)
    except MissingRunError:
        if completed_run(supervisor_settings(root).runtime.paths, run):
            return 0
        raise


def _resume_and_attach(root: Path) -> int:
    from ovcaq.tui.app import RunControlService

    paths = supervisor_settings(root).runtime.paths
    registry = FleetRegistry(paths.fleet_root)
    live = [entry for entry in registry.snapshot().live if entry.root == root]
    status = observe_run(paths).status
    service = StateService(StateStore(paths.state_file))
    if not live and status == "idle":
        service.resume()
        return _launch_and_attach(root, None)
    if len(live) != 1 or status != "active":
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT,
            f"cannot select a unique live run for {root} ({len(live)} live, {status})",
        )
    entry = live[0]
    run = FleetRun.from_entry(entry)
    revision = service.show()["revision"]
    try:
        RunControlService(registry).resume(run, revision)
    except (OSError, ValueError, RuntimeError) as error:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT, f"selected run is stale: {error}"
        ) from error
    return _attach_view(root, run.root, run.run_id)


def _dispatch_interactive(args: argparse.Namespace, root: Path) -> int | None:
    """Handle viewer commands; None means use the plain dispatch path."""
    if args.command == "run" and args.json and not args.no_tui:
        raise CommandError(ErrorCode.USAGE, "JSON run requires --no-tui")
    if args.command == "attach":
        if args.json:
            raise CommandError(ErrorCode.USAGE, "attach does not support --json")
        return _attach_view(root, root if args.root is not None else None, args.run_id)
    interactive = not args.json and sys.stdin.isatty() and sys.stdout.isatty()
    if args.command == "run" and interactive and not args.no_tui:
        return _launch_and_attach(root, args.agent)
    if args.command == "resume" and interactive:
        return _resume_and_attach(root)
    return None


def _normalize_error(error: Exception) -> CommandError:
    if isinstance(error, CommandError):
        return error
    if isinstance(error, DurabilityUnsupportedError):
        code = ErrorCode.DURABILITY_UNSUPPORTED
    elif isinstance(error, FutureSchemaError):
        code = ErrorCode.FUTURE_SCHEMA
    elif isinstance(error, StateExistsError):
        code = ErrorCode.STATE_EXISTS
    elif isinstance(error, BackupError):
        code = ErrorCode.INVALID_BACKUP
    elif isinstance(error, RevisionConflictError):
        code = ErrorCode.REVISION_CONFLICT
    elif isinstance(error, (ResourceLimitError, StateResourceLimitError)):
        code = ErrorCode.RESOURCE_LIMIT
    elif isinstance(error, StateIOError):
        code = ErrorCode.STATE_IO
    elif isinstance(error, (SchemaError, StateError)):
        code = ErrorCode.INVALID_STATE
    elif isinstance(error, OSError):
        code = ErrorCode.STATE_IO
    elif isinstance(error, ValueError):
        code = ErrorCode.USAGE
    else:
        raise error
    return CommandError(code, str(error))


def _write_json(value: object, *, stream: Any) -> None:
    stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def _emit_failure(error: CommandError, *, json_output: bool) -> int:
    if json_output:
        _write_json(
            {
                "ok": False,
                "error": {
                    "code": error.code.value,
                    "message": str(error),
                    "path": error.path,
                },
            },
            stream=sys.stderr,
        )
    else:
        print(str(error), file=sys.stderr)
    return error.exit_code


def _emit_workflow(result: _WorkflowResult, *, json_output: bool) -> int:
    if json_output and result.mutation:
        payload = {
            "ok": result.exit_code == 0,
            "revision": result.revision,
            "result": result.value,
        }
        if result.status is not None:
            payload["status"] = result.status
        _write_json(payload, stream=sys.stdout)
    elif json_output:
        _write_json(result.value, stream=sys.stdout)
    else:
        if result.mutation:
            print(f"state revision {result.revision}", file=sys.stderr)
        if result.text is not None:
            print(
                result.text.rstrip("\n"),
                file=sys.stderr if result.mutation else sys.stdout,
            )
        elif not result.mutation:
            _write_json(result.value, stream=sys.stdout)
    return result.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Run the OVCAQ command-line interface."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_output = "--json" in arguments
    try:
        args = build_parser().parse_args(arguments)
    except CommandError as error:
        return _emit_failure(error, json_output=json_output)
    except SystemExit as error:
        return cast(int, error.code)

    try:
        root = discover_project_root(args.root)
        interactive_code = _dispatch_interactive(args, root)
        if interactive_code is not None:
            return interactive_code
        dispatched = _dispatch(args, root)
    except KeyboardInterrupt:
        return 130
    except (
        CommandError,
        StateError,
        SchemaError,
        OSError,
        ValueError,
    ) as error:
        return _emit_failure(_normalize_error(error), json_output=args.json)

    if isinstance(dispatched, _WorkflowResult):
        return _emit_workflow(dispatched, json_output=args.json)
    result, revision, mutation = dispatched
    return _emit_result(args, result, revision, mutation)


def _emit_result(
    args: argparse.Namespace, result: JSONValue, revision: int | None, mutation: bool
) -> int:
    if args.command == "logs" and not args.json:
        payload = cast(dict[str, Any], result)
        if args.logs_command == "purge":
            for path in payload["selected"]:
                print(path)
            print(f"{payload['total_bytes']} bytes")
            print(shlex.join(payload["command"]))
            if payload["applied"]:
                print("purged selected session evidence", file=sys.stderr)
        else:
            print(payload["path"])
    elif args.json and mutation:
        _write_json(
            {"ok": True, "revision": revision, "result": result},
            stream=sys.stdout,
        )
    elif mutation:
        print(f"state revision {revision}", file=sys.stderr)
    else:
        _write_json(result, stream=sys.stdout)
    return 0
