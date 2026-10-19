"""Deterministic workflow audit, report, and metrics projections."""

from __future__ import annotations

import json
import os
import stat
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import cast

from ovcaq.state.schema import State, decode_json, validate_json_value
from ovcaq.workflow._files import (
    _serialize_deferred_publication,
    _verify_lifecycle_directory_identity,
)
from ovcaq.workflow.paths import WorkflowIdentifierError, require_safe_identifier
from ovcaq.workflow.records import decision_has_content


class ReportError(ValueError):
    """Raised when deterministic report input or structure is invalid."""


@dataclass(frozen=True)
class MetricsSummary:
    """Provider-neutral reduction of normalized session metric rows."""

    sessions: int
    wall_secs: Decimal | None
    cost_usd: Decimal | None
    tokens_out: int | None
    review_convergences: int
    cycles_to_converge: int | None


def _cell(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).replace("|", r"\|")


def _table(headers: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> str:
    materialized = tuple(rows)
    if not materialized:
        return ""
    heading = "| " + " | ".join(headers) + " |"
    separator = (
        "| "
        + " | ".join("---:" if index == 2 else "---" for index in range(len(headers)))
        + " |"
    )
    body = [
        "| " + " | ".join(_cell(cell) for cell in row) + " |" for row in materialized
    ]
    return "\n".join((heading, separator, *body))


def _audit_tables(state: State) -> tuple[str, str]:
    decisions = sorted(
        (item for item in state["review"]["decisions"] if decision_has_content(item)),
        key=lambda item: (item["created_at"], item["id"]),
    )
    decision_table = _table(
        ("ID", "Status", "Cycle", "Kind", "Summary", "Rationale"),
        (
            (
                item["id"],
                item["status"],
                item["cycle"],
                item["kind"],
                item["summary"],
                item["rationale"],
            )
            for item in decisions
        ),
    )
    doubts = sorted(state["review"]["doubts"], key=lambda item: item["id"])
    doubt_table = _table(
        ("ID", "Status", "Category", "Description", "Justification", "Source"),
        (
            (
                item["id"],
                item["status"],
                item["category"],
                item["description"],
                item["justification"],
                item["source"],
            )
            for item in doubts
        ),
    )
    return decision_table, doubt_table


def render_audit(state: State) -> str:
    """Render the active PRD's decision and doubt audit."""
    configured_prd = state["work"]["prd"]
    prd = (
        "unselected"
        if configured_prd is None
        else _require_component(configured_prd, "work.prd")
    )
    batch_id = state["batch"]["id"]
    batch = "unstarted" if not batch_id else _require_component(batch_id, "batch.id")
    decision_table, doubt_table = _audit_tables(state)
    sections = [
        f"# Workflow audit: {prd}",
        "",
        f"- Batch: {batch}",
        f"- Revision: {state['revision']}",
        f"- Review cycle: {state['review']['cycle']}",
        "",
        "## Decisions",
        "",
        decision_table or "_No decisions recorded._",
        "",
        "## Doubts",
        "",
        doubt_table or "_No doubts recorded._",
    ]
    return "\n".join(sections) + "\n"


def _deferred_rows(
    records: Iterable[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    unique: dict[str, Mapping[str, object]] = {}
    for record in records:
        operation_id = record.get("op_id")
        if isinstance(operation_id, str) and operation_id:
            unique.setdefault(operation_id, record)
    return tuple(unique[key] for key in sorted(unique))


def load_metric_rows(path: Path) -> tuple[Mapping[str, object], ...]:
    """Load provider-neutral normalized metric rows from a JSONL ledger."""
    try:
        payload = _read_file(None, str(path))
        if payload is None:
            return ()
        text = payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ReportError(f"cannot read metrics ledger {path}: {error}") from error

    rows: list[Mapping[str, object]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        source = f"{path}:{line_number}"
        try:
            value = decode_json(line, source=source)
            validate_json_value(value, source)
        except ValueError as error:
            raise ReportError(f"invalid metrics row at {source}: {error}") from error
        if not isinstance(value, dict):
            raise ReportError(f"invalid metrics row at {source}: expected object")
        rows.append(cast(Mapping[str, object], value))
    return tuple(rows)


def _metric_decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _metric_integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _sum_decimal(rows: tuple[Mapping[str, object], ...], field: str) -> Decimal | None:
    total = Decimal(0)
    for row in rows:
        value = _metric_decimal(row.get(field))
        if value is None:
            return None
        total += value
    return total


def _sum_integer(rows: tuple[Mapping[str, object], ...], field: str) -> int | None:
    total = 0
    for row in rows:
        value = _metric_integer(row.get(field))
        if value is None:
            return None
        total += value
    return total


def _metric_partitions(
    metric_rows: Iterable[Mapping[str, object]],
) -> tuple[tuple[Mapping[str, object], ...], tuple[Mapping[str, object], ...]]:
    rows: list[Mapping[str, object]] = []
    for row in metric_rows:
        if "schema_version" not in row:
            rows.append(row)
            continue
        usage = row.get("usage")
        usage = usage if isinstance(usage, Mapping) else {}
        rows.append(
            {
                **row,
                "batch": row.get("batch_id"),
                "ts_start": row.get("started_at"),
                "wall_secs": row.get("wall_seconds"),
                "cost_usd": usage.get("cost_usd"),
                "tokens_out": usage.get("output_tokens"),
            }
        )
    sessions = tuple(
        sorted(
            (
                row
                for row in rows
                if row.get("kind") == "phase"
                or ("schema_version" not in row and "phase_launched" in row)
            ),
            key=lambda row: (
                str(row.get("batch", "")),
                str(row.get("prd", "")),
                str(row.get("ts_start", "")),
                str(row.get("phase_launched", "")),
                json.dumps(dict(row), sort_keys=True, ensure_ascii=False),
            ),
        )
    )
    convergences = tuple(
        sorted(
            (row for row in rows if row.get("event") == "review_converged"),
            key=lambda row: (
                str(row.get("batch", "")),
                str(row.get("prd", "")),
                str(row.get("ts", "")),
                json.dumps(dict(row), sort_keys=True, ensure_ascii=False),
            ),
        )
    )
    return sessions, convergences


def _reduce_metric_partitions(
    sessions: tuple[Mapping[str, object], ...],
    convergences: tuple[Mapping[str, object], ...],
) -> MetricsSummary:
    return MetricsSummary(
        sessions=len(sessions),
        wall_secs=_sum_decimal(sessions, "wall_secs"),
        cost_usd=_sum_decimal(sessions, "cost_usd"),
        tokens_out=_sum_integer(sessions, "tokens_out"),
        review_convergences=len(convergences),
        cycles_to_converge=_sum_integer(convergences, "cycles_to_converge"),
    )


def reduce_metrics(
    metric_rows: Iterable[Mapping[str, object]],
) -> MetricsSummary:
    """Reduce normalized metrics; missing mixed-row totals remain unknown."""
    return _reduce_metric_partitions(*_metric_partitions(metric_rows))


def _metrics_for_batch(
    metric_rows: Iterable[Mapping[str, object]], batch_id: str
) -> tuple[Mapping[str, object], ...]:
    return tuple(
        row for row in metric_rows if row.get("batch_id", row.get("batch")) == batch_id
    )


def _format_decimal(value: Decimal | None, *, zero: str = "0") -> str:
    if value is None:
        return "unknown"
    if value == 0:
        return zero
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _format_integer(value: int | None) -> str:
    return "unknown" if value is None else str(value)


def _metric_summary_lines(summary: MetricsSummary) -> tuple[str, ...]:
    return (
        f"- Sessions: {summary.sessions}",
        f"- Wall seconds: {_format_decimal(summary.wall_secs)}",
        f"- Cost USD: {_format_decimal(summary.cost_usd, zero='0.00')}",
        f"- Output tokens: {_format_integer(summary.tokens_out)}",
        f"- Review convergences: {summary.review_convergences}",
        f"- Cycles to converge: {_format_integer(summary.cycles_to_converge)}",
    )


def _completed_table(completed: tuple[Mapping[str, object], ...]) -> str:
    return _table(
        ("PRD", "Cycles", "Tasks", "Applied decisions", "Escalated decisions"),
        (
            (
                item.get("filename", "unknown"),
                _format_integer(_metric_integer(item.get("cycles"))),
                (
                    f"{_format_integer(_metric_integer(item.get('tasks_completed')))}/"
                    f"{_format_integer(_metric_integer(item.get('tasks_total')))}"
                ),
                _format_integer(_metric_integer(item.get("autonomous_decisions"))),
                _format_integer(_metric_integer(item.get("escalated_decisions"))),
            )
            for item in completed
        ),
    )


def _batch_deferred_table(records: tuple[Mapping[str, object], ...]) -> str:
    return _table(
        ("PRD", "Operation", "Type", "Site", "Detail"),
        (
            (
                item.get("prd"),
                item.get("op_id"),
                item.get("type"),
                item.get("site"),
                item.get("detail"),
            )
            for item in records
        ),
    )


def _prd_report_section(state: State, prd: str) -> list[str]:
    return [
        f"## {prd}",
        "",
        f"- Phase: {state['work']['phase']}",
        f"- Next phase: {state['work']['next_phase'] or 'drained'}",
        f"- Tasks: {state['work']['tasks_completed']}/{state['work']['tasks_total']}",
        "",
    ]


def _batch_report_section(
    state: State, records: tuple[Mapping[str, object], ...], metrics: MetricsSummary
) -> list[str]:
    completed: tuple[Mapping[str, object], ...] = tuple(
        item if isinstance(item, Mapping) else {"filename": item}
        for item in state["batch"]["completed_prds"]
    )
    total_cycles = _format_integer(_sum_integer(completed, "cycles"))
    applied_decisions = _format_integer(_sum_integer(completed, "autonomous_decisions"))
    escalated_decisions = _format_integer(
        _sum_integer(completed, "escalated_decisions")
    )
    completed_table = _completed_table(completed)
    return [
        "## Batch Summary",
        "",
        f"- PRDs completed: {len(completed)}",
        f"- Total cycles: {total_cycles}",
        f"- Applied decisions: {applied_decisions}",
        f"- Escalated decisions: {escalated_decisions}",
        f"- Deferred records: {len(records)}",
        *_metric_summary_lines(metrics),
        "",
        "### Completed PRDs",
        "",
        completed_table or "_No completed PRDs._",
        "",
        "### Deferred records",
        "",
        _batch_deferred_table(records) or "_No deferred records._",
    ]


def render_report(
    state: State,
    deferred_records: Iterable[Mapping[str, object]],
    metric_rows: Iterable[Mapping[str, object]] = (),
) -> str:
    """Render a new batch report with one current-PRD section and summary."""
    configured_prd = state["work"]["prd"]
    prd = (
        "unselected"
        if configured_prd is None
        else _require_component(configured_prd, "work.prd")
    )
    configured_batch = state["batch"]["id"]
    batch = (
        "unstarted"
        if not configured_batch
        else _require_component(configured_batch, "batch.id")
    )
    records = _deferred_rows(deferred_records)
    metrics = reduce_metrics(_metrics_for_batch(metric_rows, configured_batch))
    sections = [
        f"# Workflow report: {batch}",
        "",
        *_prd_report_section(state, prd),
        *_batch_report_section(state, records, metrics),
    ]
    return "\n".join(sections) + "\n"


def _session_table(sessions: Iterable[Mapping[str, object]]) -> str:
    return _table(
        (
            "PRD",
            "Launched phase",
            "End phase",
            "Signal",
            "Model",
            "Wall seconds",
            "Cost USD",
            "Output tokens",
        ),
        (
            (
                item.get("prd"),
                item.get("phase_launched"),
                item.get("phase_end"),
                item.get("signal"),
                item.get("model"),
                _format_decimal(_metric_decimal(item.get("wall_secs"))),
                _format_decimal(_metric_decimal(item.get("cost_usd"))),
                _format_integer(_metric_integer(item.get("tokens_out"))),
            )
            for item in sessions
        ),
    )


def render_metrics(
    metric_rows: Iterable[Mapping[str, object]],
    *,
    batch_id: str | None = None,
) -> str:
    """Render a deterministic summary of normalized session metric rows."""
    if batch_id is not None:
        batch_id = _require_component(batch_id, "batch.id")
        metric_rows = _metrics_for_batch(metric_rows, batch_id)
    sessions, convergences = _metric_partitions(metric_rows)
    summary = _reduce_metric_partitions(sessions, convergences)
    session_table = _session_table(sessions)
    convergence_table = _table(
        ("PRD", "Cycles", "Outcome"),
        (
            (
                item.get("prd"),
                item.get("cycles_to_converge"),
                item.get("outcome"),
            )
            for item in convergences
        ),
    )
    sections = [
        "# Workflow metrics",
        "",
        *_metric_summary_lines(summary),
        "",
        "## Sessions",
        "",
        session_table or "_No sessions recorded._",
        "",
        "## Review convergence",
        "",
        convergence_table or "_No review convergences recorded._",
    ]
    return "\n".join(sections) + "\n"


def _require_component(value: object, label: str) -> str:
    try:
        return require_safe_identifier(value, label)
    except WorkflowIdentifierError as error:
        raise ReportError(str(error)) from error


_DIRECTORY_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)


def _open_real_directory(path: Path) -> int:
    descriptor = os.open(path, _DIRECTORY_FLAGS)
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise OSError(f"output root is not a directory: {path}")
    return descriptor


def _open_child_directory(parent: int, name: str) -> int:
    try:
        os.mkdir(name, mode=0o700, dir_fd=parent)
    except FileExistsError:
        pass
    descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent)
    try:
        opened = os.fstat(descriptor)
        linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if not stat.S_ISDIR(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            linked.st_dev,
            linked.st_ino,
        ):
            raise OSError(f"output component is not a real directory: {name}")
        os.fsync(parent)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


@contextmanager
def _output_directory(
    root: Path, components: tuple[str, ...]
) -> Iterator[tuple[int, Callable[[], None]]]:
    paths = [root]
    descriptors = [_open_real_directory(root)]

    def verify() -> None:
        for path, descriptor in zip(paths, descriptors, strict=True):
            _verify_lifecycle_directory_identity(path, descriptor, label="output")

    try:
        verify()
        for component in components:
            descriptors.append(_open_child_directory(descriptors[-1], component))
            paths.append(paths[-1] / component)
            verify()
        yield descriptors[-1], verify
        verify()
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _read_file(directory: int | None, filename: str) -> bytes | None:
    flags = (
        os.O_RDONLY
        | os.O_NONBLOCK
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(filename, flags, dir_fd=directory)
    except FileNotFoundError:
        return None
    opened = os.fstat(descriptor)
    if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
        os.close(descriptor)
        raise OSError(f"not a single-linked regular file: {filename}")
    with os.fdopen(descriptor, "rb", closefd=True) as stream:
        return stream.read()


def _publish_file(
    directory: int, filename: str, payload: bytes, verify: Callable[[], None]
) -> None:
    verify()
    if _read_file(directory, filename) == payload:
        os.fsync(directory)
        verify()
        return
    descriptor = -1
    temporary: str | None = None
    try:
        temporary = f".{filename}.ovcaq-{uuid.uuid4().hex}.tmp"
        descriptor = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
            dir_fd=directory,
        )
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        verify()
        os.replace(
            temporary,
            filename,
            src_dir_fd=directory,
            dst_dir_fd=directory,
        )
        temporary = None
        os.fsync(directory)
        verify()
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass


def _section_span(lines: list[str], heading: str) -> tuple[int, int] | None:
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.removesuffix("\n") == heading
        ),
        None,
    )
    if start is None:
        return None
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return start, end


def _replace_section(existing: str, heading: str) -> str:
    """Remove every exact level-two section matching ``heading``."""
    lines = existing.splitlines(keepends=True)
    while (span := _section_span(lines, heading)) is not None:
        start, end = span
        del lines[start:end]
    return "".join(lines)


def _report_section(text: str, heading: str) -> str:
    lines = text.splitlines(keepends=True)
    span = _section_span(lines, heading)
    if span is None:
        raise ReportError(f"rendered report is missing section {heading!r}")
    start, end = span
    return "".join(lines[start:end]).rstrip("\n")


def _updated_report(
    existing: str | None,
    state: State,
    deferred_records: Iterable[Mapping[str, object]],
    metric_rows: Iterable[Mapping[str, object]],
) -> str:
    rendered = render_report(state, deferred_records, metric_rows)
    header = rendered.partition("\n")[0]
    prd_heading = f"## {state['work']['prd'] or 'unselected'}"
    summary_heading = "## Batch Summary"
    if existing is None:
        base = f"{header}\n"
    else:
        if existing.partition("\n")[0] != header:
            raise ValueError("existing workflow report belongs to a different batch")
        base = existing
    base = _replace_section(base, prd_heading)
    base = _replace_section(base, summary_heading)
    prd_section = _report_section(rendered, prd_heading)
    summary = _report_section(rendered, summary_heading)
    return f"{base.rstrip()}\n\n{prd_section}\n\n{summary}\n"


def _publish(
    root: Path,
    components: tuple[str, ...],
    filename: str,
    payload: bytes,
) -> Path:
    with _output_directory(root, components) as (directory, verify):
        _publish_file(directory, filename, payload, verify)
    return root.joinpath(*components, filename)


def publish_audit(repo_root: Path, state: State) -> Path:
    """Publish the deterministic active-PRD audit."""
    prd = state["work"]["prd"]
    if prd is None:
        raise ValueError("cannot render audit without an active PRD")
    prd = _require_component(prd, "work.prd")
    filename = f"{Path(prd).stem}-audit.md"
    return _publish(
        repo_root,
        ("docs", "dev", "project-management", "reviews"),
        filename,
        render_audit(state).encode("utf-8"),
    )


def publish_report(
    runtime_root: Path,
    state: State,
    deferred_records: Iterable[Mapping[str, object]],
    metric_rows: Iterable[Mapping[str, object]] = (),
) -> Path:
    """Publish the deterministic current-batch report."""
    path, _text = _publish_report(runtime_root, state, deferred_records, metric_rows)
    return path


def _publish_report(
    runtime_root: Path,
    state: State,
    deferred_records: Iterable[Mapping[str, object]],
    metric_rows: Iterable[Mapping[str, object]] = (),
) -> tuple[Path, str]:
    """Return the report path and composed text after verified publication."""
    batch_id = state["batch"]["id"]
    if not batch_id:
        raise ValueError("cannot render report without an active batch")
    batch_id = _require_component(batch_id, "batch.id")
    prd = state["work"]["prd"]
    if prd is not None:
        _require_component(prd, "work.prd")
    filename = f"{batch_id}-report.md"
    records = tuple(deferred_records)
    metrics = tuple(metric_rows)
    report_path = runtime_root / "reports" / filename
    with (
        _output_directory(runtime_root, ("reports",)) as (directory, verify),
        _serialize_deferred_publication(report_path, directory),
    ):
        existing_bytes = _read_file(directory, filename)
        existing = None if existing_bytes is None else existing_bytes.decode("utf-8")
        text = _updated_report(existing, state, records, metrics)
        _publish_file(directory, filename, text.encode("utf-8"), verify)
    return report_path, text


def archive_final_state(runtime_root: Path, state: State) -> Path:
    """Publish a canonical terminal-state snapshot without deleting live state."""
    if state["work"]["phase"] != "done" or state["work"]["next_phase"] != "":
        raise ValueError("cannot archive state before the terminal drained state")
    batch_id = _require_component(state["batch"]["id"], "batch.id")
    payload = (
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    return _publish(
        runtime_root,
        ("reports",),
        f"{batch_id}-state-final.json",
        payload,
    )
