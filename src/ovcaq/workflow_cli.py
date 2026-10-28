"""Workflow parser registration and configured command dispatch."""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, cast

from ovcaq.cli_io import _decode_text, _json_file, _read_payload, _WorkflowResult
from ovcaq.config import WorkflowSettings, workflow_settings
from ovcaq.errors import CommandError, ErrorCode
from ovcaq.state.schema import JSONValue
from ovcaq.state.store import StateStore
from ovcaq.workflow import frontmatter, policy, reports, resume, selection, transitions
from ovcaq.workflow.paths import resolve_lifecycle_paths
from ovcaq.workflow.records import (
    complete_prd_in_store,
    defer_record,
    load_deferred_records,
    park,
    stall,
)

WORKFLOW_INPUT_NOTES = (
    "Workflow inputs use CLI flags, project `ovcaq.toml`, user",
    "`${XDG_CONFIG_HOME:-~/.config}/ovcaq/config.toml`, then package defaults.",
    "`[workflow] prd_root` and `runtime_root` default to `docs/dev/project-management/prds` and",
    "`docs/dev/project-management/ovcaq`; relative paths resolve from the discovered project root.",
    "Runtime roots remain inside the project and reject symlink components.",
    "`--prd-root` and `--runtime-root` override those inputs; `--state` overrides",
    "the workflow state file independently of the runtime root.",
    "Frontmatter receives the neutral tier keys `standard` and `deep` unioned with",
    "the keys from `[agents.<agent>.tiers]` for the configured top-level `agent`.",
    "An `[agents.<agent>.tiers]` table must now define `standard` and `deep`, because",
    "the phase routes ask for those keys; a table that defines neither neutral key",
    "silently falls through to the driver's own models instead of failing.",
    "Codex reserves the tier value `default`, which keeps the Codex CLI on its own",
    "configured model. Model values stay opaque. Repeated `--available-tier KEY`",
    "flags supply the available keys explicitly; an unavailable hint warns and",
    "applies no floor. This input reader does not launch or route agents.",
    "",
    "Phase transitions require a running batch and an active PRD; only an empty",
    "build-phase drain may omit the PRD. Batch finalization remains supervisor-owned.",
    "Stall/park reject missing sources and conflicting destinations before committing",
    "recovery intent. Source identity remains checked through intent publication.",
    "An older unbound intent (step `intent`, artifact `null`) cannot move a PRD;",
    "use `state restore` to recover its pre-intent backup. Bound recovery must",
    "reconcile before restoration. Restoration does not move PRD files.",
    "",
    "After a second consecutive park, the durable pause returns exit 4.",
    "JSON output includes `ok: false`, `status: systemic_park`, and the committed",
    "revision/result; human output asks the operator to inspect held PRDs and",
    "the pause reason. Exact replay returns the same halt without another park.",
    "",
)


def _add_workflow_commands(commands: Any) -> None:
    workflow = commands.add_parser(
        "workflow",
        help="apply deterministic workflow operations",
    )
    workflow_commands = workflow.add_subparsers(
        dest="workflow_command",
        required=True,
    )
    _add_workflow_lifecycle_commands(workflow_commands)
    _add_workflow_record_commands(workflow_commands)
    for child in workflow_commands.choices.values():
        child.add_argument("--prd-root", type=Path, metavar="PATH")
        child.add_argument("--runtime-root", type=Path, metavar="PATH")
        child.add_argument("--state", type=Path, metavar="PATH")


def _add_workflow_lifecycle_commands(workflow_commands: Any) -> None:
    workflow_commands.add_parser("select", help="select the next PRD")

    frontmatter_parser = workflow_commands.add_parser(
        "frontmatter",
        help="parse and apply PRD frontmatter",
    )
    frontmatter_parser.add_argument("--available-tier", action="append", metavar="KEY")
    frontmatter_parser.add_argument("--prd", metavar="PATH", type=Path, required=True)
    frontmatter_parser.add_argument("--expected-revision", metavar="N", type=int)

    phase_complete_parser = workflow_commands.add_parser(
        "phase-complete",
        help="commit one workflow transition",
    )
    phase_complete_parser.add_argument(
        "--outcome",
        required=True,
        choices=transitions.OUTCOMES,
    )
    phase_complete_parser.add_argument("--expected-revision", metavar="N", type=int)

    workflow_commands.add_parser(
        "resume-target",
        help="derive the next action from state",
    )

    check_plan = workflow_commands.add_parser(
        "check-plan",
        help="validate the task plan and size policy",
    )
    check_plan.add_argument(
        "--ceiling",
        type=int,
        default=policy.LOOP_TASK_CEILING,
    )


def _add_workflow_record_commands(workflow_commands: Any) -> None:
    stall_parser = workflow_commands.add_parser(
        "stall",
        help="move a PRD to hold through a recovery saga",
    )
    stall_parser.add_argument("--prd", metavar="NAME", required=True)
    stall_parser.add_argument("--site", metavar="SITE", required=True)
    stall_parser.add_argument("--detail", metavar="TEXT", required=True)

    workflow_commands.add_parser(
        "park",
        help="park the active PRD or reconcile recovery",
    )

    defer_parser = workflow_commands.add_parser(
        "defer",
        help="append an operation-ID-deduplicated record",
    )
    defer_parser.add_argument("--prd", metavar="NAME", required=True)
    defer_parser.add_argument("--record", metavar="FILE", type=Path, required=True)

    complete = workflow_commands.add_parser(
        "complete-prd",
        help="record an idempotent completed-PRD summary",
    )
    complete.add_argument("--prd", metavar="NAME", required=True)
    complete.add_argument("--expected-revision", metavar="N", type=int)

    render = workflow_commands.add_parser(
        "render",
        help="render a deterministic workflow projection",
    )
    render.add_argument("surface", choices=("audit", "report", "metrics"))


def _root_relative(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def _dispatch_workflow_render(
    args: argparse.Namespace,
    root: Path,
    store: StateStore,
    runtime_root: Path,
) -> _WorkflowResult:
    state = store.read()
    surface = args.surface
    path: Path | None = None
    metric_rows = (
        reports.load_metric_rows(runtime_root / "metrics.jsonl")
        if surface in {"report", "metrics"}
        else ()
    )
    if surface == "audit":
        text = reports.render_audit(state)
        path = reports.publish_audit(root, state)
    elif surface == "report":
        batch_id = state["batch"]["id"]
        records = load_deferred_records(runtime_root, batch_id) if batch_id else ()
        path, text = reports._publish_report(runtime_root, state, records, metric_rows)
        if state["work"]["phase"] == "done" and not state["work"]["next_phase"]:
            reports.archive_final_state(runtime_root, state)
    else:
        text = reports.render_metrics(
            metric_rows,
            batch_id=state["batch"]["id"] or None,
        )
    value: dict[str, JSONValue] = {
        "surface": surface,
        "path": None if path is None else str(path),
        "text": text,
    }
    human_text = text if path is None else str(path)
    return _WorkflowResult(value=cast(JSONValue, value), text=human_text)


def _frontmatter(
    args: argparse.Namespace, root: Path, store: StateStore, settings: WorkflowSettings
) -> _WorkflowResult:
    prd_path = _root_relative(root, args.prd)
    text = _decode_text(_read_payload(prd_path), source=str(prd_path))
    frontmatter_result = frontmatter.apply_to_store(
        store,
        text,
        prd=prd_path.name,
        available_tiers=settings.available_tiers,
        expected_revision=args.expected_revision,
    )
    for warning in frontmatter_result.warnings:
        print(warning, file=sys.stderr)
    value: dict[str, JSONValue] = {
        "fields": cast(JSONValue, frontmatter_result.fields),
        "warnings": list(frontmatter_result.warnings),
    }
    return _WorkflowResult(
        value=cast(JSONValue, value),
        revision=frontmatter_result.state["revision"],
        mutation=True,
    )


def _phase_complete(args: argparse.Namespace, store: StateStore) -> _WorkflowResult:
    committed = transitions.phase_complete(
        store,
        args.outcome,
        expected_revision=args.expected_revision,
    )
    value = {
        "phase": committed["work"]["phase"],
        "next_phase": committed["work"]["next_phase"],
    }
    return _WorkflowResult(
        value=cast(JSONValue, value),
        revision=committed["revision"],
        mutation=True,
    )


def _check_plan(args: argparse.Namespace, store: StateStore) -> _WorkflowResult:
    state = store.read()
    count = policy.validate_plan_shape(state)
    over, _count = policy.plan_over_ceiling(state, args.ceiling)
    if over:
        raise CommandError(
            ErrorCode.OVERSIZED_PLAN,
            f"plan has {count} tasks, over the {args.ceiling}-task ceiling; "
            'stall this PRD at site "oversized_plan"',
        )
    value = {"over_ceiling": over, "task_count": count}
    return _WorkflowResult(value=cast(JSONValue, value))


def _complete_prd(args: argparse.Namespace, store: StateStore) -> _WorkflowResult:
    committed = complete_prd_in_store(
        store,
        args.prd,
        expected_revision=args.expected_revision,
    )
    summary = next(
        item
        for item in committed["batch"]["completed_prds"]
        if item["filename"] == args.prd
    )
    return _WorkflowResult(
        value=cast(JSONValue, summary),
        revision=committed["revision"],
        mutation=True,
    )


def _saga(
    args: argparse.Namespace, root: Path, store: StateStore, settings: WorkflowSettings
) -> _WorkflowResult:
    paths = resolve_lifecycle_paths(root, settings.prd_root)
    if args.workflow_command == "stall":
        result = stall(
            store,
            paths=paths,
            runtime_root=settings.runtime_root,
            prd=args.prd,
            site=args.site,
            detail=args.detail,
        )
    else:
        result = park(store, paths=paths, runtime_root=settings.runtime_root)
    return _WorkflowResult(
        value=cast(JSONValue, asdict(result)),
        revision=store.read()["revision"],
        mutation=True,
        status="systemic_park" if result.systemic_halt else None,
        exit_code=4 if result.systemic_halt else 0,
        text=(
            "batch halted after consecutive parks. Inspect held PRDs and the pause reason before resuming."
            if result.systemic_halt
            else None
        ),
    )


def _dispatch_workflow(args: argparse.Namespace, root: Path) -> _WorkflowResult:
    settings = workflow_settings(
        root,
        prd_root=args.prd_root,
        runtime_root=args.runtime_root,
        state_file=args.state,
        available_tiers=getattr(args, "available_tier", None),
    )
    command = args.workflow_command
    if command == "select":
        prd, source = selection.select_from_paths(
            resolve_lifecycle_paths(root, settings.prd_root)
        )
        return _WorkflowResult(value={"prd": prd, "source": source})
    store = StateStore(settings.state_file)
    if command == "frontmatter":
        return _frontmatter(args, root, store, settings)
    if command == "phase-complete":
        return _phase_complete(args, store)
    if command == "resume-target":
        target = resume.resume_target(store.read())
        return _WorkflowResult(value=target, text=target)
    if command == "check-plan":
        return _check_plan(args, store)
    if command in {"stall", "park"}:
        return _saga(args, root, store, settings)
    if command == "defer":
        record = cast(dict[str, object], _json_file(_root_relative(root, args.record)))
        path = defer_record(store, settings.runtime_root, args.prd, record)
        return _WorkflowResult(value={"path": str(path)})
    if command == "complete-prd":
        return _complete_prd(args, store)
    return _dispatch_workflow_render(args, root, store, settings.runtime_root)
