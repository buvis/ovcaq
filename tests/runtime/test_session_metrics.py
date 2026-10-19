from __future__ import annotations

import json
import os
import stat
import tracemalloc
from dataclasses import FrozenInstanceError, asdict, replace
from pathlib import Path

import pytest

from ovcaq.paths import resolve_runtime_paths
from ovcaq.runtime.session import (
    SessionMetadata,
    SessionMetric,
    create_session,
    metric_from_record,
    observe_emergency_failure,
    observe_metrics,
    observe_session_evidence,
    publish_session_metric,
    reconcile_metrics,
)


def _metric(session_id: str = "session-1") -> SessionMetric:
    return SessionMetric(
        schema_version=1,
        kind="phase",
        run_id="run-1",
        session_id=session_id,
        batch_id="batch-1",
        prd="00004-workflow-core-v1.md",
        phase_launched="build",
        capability=None,
        phase_end=None,
        decision=None,
        started_at="2026-09-14T10:00:00Z",
        finished_at=None,
        wall_seconds=None,
        model="test-model",
        usage=None,
    )


def _metadata(metric: SessionMetric) -> SessionMetadata:
    return SessionMetadata(
        schema_version=1,
        run_id=metric.run_id,
        session_id=metric.session_id,
        agent="generic",
        pid=os.getpid(),
        process_start="process-start-token",
        started_at=metric.started_at,
    )


def _final(metric: SessionMetric) -> SessionMetric:
    return replace(
        metric,
        phase_end="review",
        decision="continue",
        finished_at="2026-09-14T10:01:00Z",
        wall_seconds=60.0,
    )


def _rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _usage() -> dict[str, int | float | bool | None]:
    return {
        "input_tokens": 10,
        "output_tokens": 2,
        "cache_creation_input_tokens": 3,
        "cache_read_input_tokens": 4,
        "tool_uses": 1,
        "cost_usd": 0.1,
        "estimated": False,
    }


@pytest.mark.parametrize("unknown", (*tuple(_usage())[:-1], "all"))
@pytest.mark.parametrize("estimated", (False, True))
def test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries(
    tmp_path: Path, unknown: str, estimated: bool
) -> None:
    usage = _usage()
    for key in usage:
        if key != "estimated" and unknown in (key, "all"):
            usage[key] = None
    usage["estimated"] = estimated
    paths = resolve_runtime_paths(tmp_path)
    pending = replace(_metric(), model="alternate-model")
    final = replace(_final(pending), usage=usage)
    expected = replace(final, usage=usage.copy())
    expected_record = asdict(expected)
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    publish_session_metric(paths, session, final)
    (record,) = _rows(session.metrics)
    assert record == expected_record
    assert metric_from_record(record) == expected
    assert reconcile_metrics(paths) == (expected,)
    assert _rows(paths.metrics) == [expected_record]
    snapshot = observe_metrics(paths, batch_id=pending.batch_id)
    assert snapshot.rows == (expected,)
    assert snapshot.complete and snapshot.gaps == ()


@pytest.mark.parametrize("field", (*_usage(), "extra"))
def test_usage_requires_exact_keys_including_nullable_fields(
    tmp_path: Path, field: str
) -> None:
    usage = dict.fromkeys(_usage())
    usage["estimated"] = False
    if field == "extra":
        usage[field] = None
    else:
        del usage[field]
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    before = session.metrics.read_bytes()
    invalid = replace(_final(pending), usage=usage)
    with pytest.raises((ValueError, TypeError, KeyError)):
        metric_from_record(asdict(invalid))
    with pytest.raises((ValueError, TypeError, KeyError)):
        publish_session_metric(paths, session, invalid)
    assert session.metrics.read_bytes() == before


def test_pending_publication_and_finalization_keep_one_private_canonical_row(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = replace(_metric(), usage=_usage())
    previous_umask = os.umask(0)
    try:
        session = create_session(paths, _metadata(pending))
        publish_session_metric(paths, session, pending)
        assert _rows(session.metrics) == [asdict(pending)]
        pending = replace(pending, usage={**_usage(), "input_tokens": 25})
        publish_session_metric(paths, session, pending)
        assert _rows(session.metrics) == [asdict(pending)]
        with session.metrics.open() as original:
            final = replace(
                _final(pending),
                usage={
                    "input_tokens": 101,
                    "output_tokens": 19,
                    "cache_creation_input_tokens": 13,
                    "cache_read_input_tokens": 7,
                    "tool_uses": 3,
                    "cost_usd": 0.125,
                    "estimated": False,
                },
            )
            publish_session_metric(paths, session, final)
            assert json.loads(original.read()) == asdict(pending)
        assert _rows(session.metrics) == [asdict(final)]
        assert reconcile_metrics(paths) == (final,)
    finally:
        os.umask(previous_umask)
    assert _rows(paths.metrics) == [asdict(final)]
    for directory in (paths.runtime_root, paths.sessions, session.root):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    for artifact in (session.metrics, paths.metrics):
        assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
    with pytest.raises(FrozenInstanceError):
        pending.decision = "changed"


@pytest.mark.parametrize("replacement", ("pending", "identical", "different"))
@pytest.mark.parametrize("kind", ("phase", "capability"))
def test_final_canonical_row_rejects_all_later_publications(
    tmp_path: Path, replacement: str, kind: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    if kind == "capability":
        pending = replace(
            pending,
            kind="capability",
            capability="test-capability",
            phase_launched=None,
            model=None,
        )
    final = _final(pending)
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    publish_session_metric(paths, session, final)
    before = session.metrics.read_bytes()
    candidate = {
        "pending": pending,
        "identical": final,
        "different": replace(final, wall_seconds=59.0),
    }[replacement]
    with pytest.raises(ValueError):
        publish_session_metric(paths, session, candidate)
    assert session.metrics.read_bytes() == before


@pytest.mark.parametrize("field", ("run_id", "session_id"))
def test_initial_pending_publication_must_match_session_metadata(
    tmp_path: Path, field: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    session = create_session(paths, _metadata(pending))
    with pytest.raises(ValueError):
        publish_session_metric(paths, session, replace(pending, **{field: "other"}))
    assert not session.metrics.exists()
    assert not paths.metrics.exists()


@pytest.mark.parametrize("field", ("run_id", "session_id"))
def test_pending_row_cannot_be_finalized_under_another_identity(
    tmp_path: Path, field: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    before = session.metrics.read_bytes()
    with pytest.raises(ValueError):
        publish_session_metric(
            paths, session, replace(_final(pending), **{field: "other"})
        )
    assert session.metrics.read_bytes() == before


@pytest.mark.parametrize("kind", ["phase", "capability"])
def test_reconciliation_projects_interrupted_pending_without_rewriting_evidence(
    tmp_path: Path,
    kind: str,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = replace(_metric(), usage=_usage())
    expected_usage = _usage()
    if kind == "capability":
        pending = replace(
            pending,
            kind="capability",
            capability="test-capability",
            phase_launched=None,
            model=None,
        )
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    before = session.metrics.read_bytes()
    rows = reconcile_metrics(paths)
    assert len(rows) == 1
    assert rows == (replace(pending, decision="interrupted"),)
    assert rows[0].usage == expected_usage
    assert rows[0].session_id == pending.session_id
    assert rows[0].decision == "interrupted"
    assert rows[0].run_id == pending.run_id
    assert rows[0].batch_id == pending.batch_id
    assert rows[0].prd == pending.prd
    assert rows[0].started_at == pending.started_at
    assert _rows(paths.metrics) == [asdict(rows[0])]
    assert session.metrics.read_bytes() == before
    assert reconcile_metrics(paths) == rows
    assert _rows(paths.metrics) == [asdict(rows[0])]
    assert session.metrics.read_bytes() == before


def test_reconciliation_orders_by_start_then_session_and_does_not_accumulate_rows(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metrics = (
        _final(_metric("session-z")),
        _final(replace(_metric("session-c"), started_at="2026-09-14T09:59:00Z")),
        _final(_metric("session-a")),
    )
    for metric in metrics:
        session = create_session(paths, _metadata(metric))
        pending = replace(
            metric, phase_end=None, decision=None, finished_at=None, wall_seconds=None
        )
        publish_session_metric(paths, session, pending)
        publish_session_metric(paths, session, metric)
    duplicate_root = paths.sessions / "retained-copy"
    duplicate_root.mkdir(mode=0o700)
    (duplicate_root / "metrics.jsonl").write_bytes(session.metrics.read_bytes())
    paths.metrics.write_text(
        "".join(json.dumps(asdict(metrics[0])) + "\n" for _ in range(2))
    )
    expected = (metrics[1], metrics[2], metrics[0])
    assert reconcile_metrics(paths) == expected
    first = paths.metrics.read_bytes()
    assert _rows(paths.metrics) == [asdict(row) for row in expected]
    assert reconcile_metrics(paths) == expected
    assert paths.metrics.read_bytes() == first


def test_capability_metrics_round_trip_without_phase_or_model(tmp_path: Path) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metric = replace(
        _metric(),
        kind="capability",
        capability="test-capability",
        phase_launched=None,
        model=None,
    )
    session = create_session(paths, _metadata(metric))
    publish_session_metric(paths, session, metric)
    final = _final(metric)
    publish_session_metric(paths, session, final)
    assert _rows(session.metrics) == [asdict(final)]
    assert reconcile_metrics(paths) == (final,)


@pytest.mark.parametrize(
    "changes",
    (
        {"schema_version": 2},
        {"schema_version": True},
        {"kind": "unknown"},
        {"run_id": ""},
        {"session_id": "../escape"},
        {"batch_id": ""},
        {"phase_launched": None},
        {"model": None},
        {"capability": "unexpected"},
        {"kind": "capability"},
        {"started_at": "not-a-timestamp"},
        {"finished_at": "not-a-timestamp"},
        {"wall_seconds": -1},
        {"wall_seconds": float("nan")},
        {"wall_seconds": float("inf")},
        {"wall_seconds": True},
        {"finished_at": "2026-09-14T09:00:00Z"},
    ),
)
def test_invalid_metric_values_are_rejected_without_replacing_pending(
    tmp_path: Path, changes: dict[str, object]
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    before = session.metrics.read_bytes()
    with pytest.raises(ValueError):
        invalid = replace(_final(pending), **changes)
        publish_session_metric(paths, session, invalid)
    assert session.metrics.read_bytes() == before


@pytest.mark.parametrize("malformed", ("json", "multiple", "schema", "empty"))
def test_malformed_retained_rows_fail_visibly_and_preserve_previous_aggregate(
    tmp_path: Path, malformed: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    metric = _final(_metric())
    session = create_session(paths, _metadata(metric))
    publish_session_metric(paths, session, _metric())
    publish_session_metric(paths, session, metric)
    reconcile_metrics(paths)
    before = paths.metrics.read_bytes()
    valid = json.dumps(asdict(metric)) + "\n"
    payload = {
        "json": "{not-json}\n",
        "multiple": valid + valid,
        "schema": json.dumps({**asdict(metric), "schema_version": 9}) + "\n",
        "empty": "",
    }[malformed]
    session.metrics.write_text(payload)
    with pytest.raises(ValueError):
        reconcile_metrics(paths)
    assert paths.metrics.read_bytes() == before
    assert session.metrics.read_text() == payload


@pytest.mark.parametrize("final", (False, True))
def test_metric_reader_round_trips_the_published_schema(final: bool) -> None:
    metric = _final(_metric()) if final else _metric()
    record = asdict(metric)
    assert metric_from_record(record) == metric
    assert record == asdict(metric)


@pytest.mark.parametrize(
    "changes",
    (
        {"schema_version": True},
        {"kind": "unknown"},
        {"session_id": "../escape"},
        {"run_id": ""},
        {"run_id": 42},
        {"batch_id": ""},
        {"batch_id": None},
        {"phase_launched": None},
        {"phase_launched": "unknown-phase"},
        {"phase_end": "unknown-phase"},
        {"model": None},
        {"capability": "unexpected"},
        {"finished_at": None},
        {"phase_end": None},
        {"wall_seconds": float("nan")},
        {"wall_seconds": -1.0},
        {"wall_seconds": True},
        {"started_at": "not-a-timestamp"},
        {"finished_at": "2026-09-14T09:00:00Z"},
        {"usage": {"input_tokens": 5}},
        {"extra": "unexpected"},
    ),
)
def test_metric_reader_rejects_invalid_schema_and_publication_invariants(
    changes: dict[str, object],
) -> None:
    record = {**asdict(_final(_metric())), **changes}
    with pytest.raises((ValueError, TypeError)):
        metric_from_record(record)


def test_metric_reader_rejects_missing_nullable_fields() -> None:
    record = asdict(_metric())
    del record["usage"]
    with pytest.raises((ValueError, TypeError, KeyError)):
        metric_from_record(record)


@pytest.mark.parametrize(
    "field,value",
    (
        ("input_tokens", -1),
        ("output_tokens", "12"),
        ("cache_creation_input_tokens", True),
        ("cache_read_input_tokens", -1),
        ("tool_uses", 1.5),
        ("input_tokens", float("inf")),
        ("output_tokens", float("nan")),
        ("cost_usd", -0.1),
        ("cost_usd", float("inf")),
        ("cost_usd", float("nan")),
        ("cost_usd", "0.25"),
        ("cost_usd", True),
        ("estimated", 1),
        ("estimated", "false"),
        ("estimated", None),
    ),
)
def test_metric_reader_rejects_invalid_values_in_complete_usage(
    tmp_path: Path, field: str, value: object
) -> None:
    usage = {
        "input_tokens": 10,
        "output_tokens": 2,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "tool_uses": 1,
        "cost_usd": 0.1,
        "estimated": False,
    }
    record = {**asdict(_final(_metric())), "usage": usage}
    assert metric_from_record(record).usage == usage
    record["usage"] = {**usage, field: value}
    with pytest.raises((ValueError, TypeError)):
        metric_from_record(record)
    paths = resolve_runtime_paths(tmp_path)
    pending = _metric()
    session = create_session(paths, _metadata(pending))
    publish_session_metric(paths, session, pending)
    reconcile_metrics(paths)
    before = session.metrics.read_bytes(), paths.metrics.read_bytes()
    with pytest.raises((ValueError, TypeError)):
        publish_session_metric(
            paths, session, replace(_final(pending), usage=record["usage"])
        )
    assert (session.metrics.read_bytes(), paths.metrics.read_bytes()) == before


def test_metrics_choose_last_valid_session_rows_in_file_order_and_filter_batch(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    first = _final(_metric("session-z"))
    second = _final(_metric("session-a"))
    latest = replace(first, wall_seconds=59.0)
    foreign = replace(first, batch_id="another-batch", wall_seconds=58.0)
    create_session(paths, _metadata(first))
    content = "".join(
        json.dumps(asdict(row)) + "\n" for row in (first, second, latest, foreign)
    )
    paths.metrics.write_text(content)
    before = paths.metrics.stat()
    snapshot = observe_metrics(paths, batch_id="batch-1")
    assert snapshot.rows == (second, latest)
    assert snapshot.complete and snapshot.gaps == ()
    other = observe_metrics(paths, batch_id="another-batch")
    assert other.rows == (foreign,)
    assert other.complete and other.gaps == ()
    missing = observe_metrics(paths, batch_id="nonexistent-batch")
    assert missing.rows == ()
    assert missing.complete and missing.gaps == ()
    assert paths.metrics.read_text() == content
    assert os.path.samestat(before, paths.metrics.stat())


@pytest.mark.parametrize("limiting", ("bytes", "records", "malformed"))
def test_metrics_report_incomplete_aggregation_when_evidence_is_limited(
    tmp_path: Path, limiting: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    first = _final(_metric("session-1"))
    second = _final(_metric("session-2"))
    create_session(paths, _metadata(first))
    line = json.dumps(asdict(first)) + "\n"
    content = line + ("{broken}\n" if limiting == "malformed" else "")
    content += json.dumps(asdict(second)) + "\n"
    paths.metrics.write_text(content)
    limits = {
        "bytes": {"max_bytes": len(line.encode())},
        "records": {"max_records": 1},
        "malformed": {},
    }[limiting]
    snapshot = observe_metrics(paths, batch_id="batch-1", **limits)
    assert not snapshot.complete and snapshot.gaps
    assert all(isinstance(gap, str) and gap for gap in snapshot.gaps)
    if limiting == "malformed":
        assert snapshot.rows == (first, second)
    else:
        assert snapshot.rows == (first,)
    assert paths.metrics.read_text() == content


def test_metrics_default_record_budget_keeps_only_the_first_4096_rows(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    rows = tuple(_final(_metric(f"session-{index}")) for index in range(4097))
    create_session(paths, _metadata(rows[0]))
    with paths.metrics.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(asdict(row)) + "\n")
    snapshot = observe_metrics(paths, batch_id="batch-1")
    assert snapshot.rows == rows[:4096]
    assert not snapshot.complete and snapshot.gaps
    expanded = observe_metrics(paths, batch_id="batch-1", max_records=4097)
    assert expanded.rows == rows
    assert expanded.complete and expanded.gaps == ()


def test_metrics_default_byte_budget_bounds_memory_and_leaves_later_rows_unread(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    first = _final(_metric("session-1"))
    last = _final(_metric("session-2"))
    create_session(paths, _metadata(first))
    chunk = b"x" * (1024 * 1024)
    with paths.metrics.open("wb") as stream:
        stream.write((json.dumps(asdict(first)) + "\n").encode())
        for _ in range(64):
            stream.write(chunk)
        stream.write(("\n" + json.dumps(asdict(last)) + "\n").encode())
    before = paths.metrics.stat()
    tracemalloc.start()
    try:
        snapshot = observe_metrics(paths, batch_id="batch-1")
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 48 * 1024 * 1024
    assert snapshot.rows == (first,)
    assert not snapshot.complete and snapshot.gaps
    assert paths.metrics.stat().st_size == before.st_size
    assert paths.metrics.stat().st_mtime_ns == before.st_mtime_ns


def test_explicit_byte_budget_reads_valid_rows_beyond_sixteen_mib(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    first = _final(_metric("session-1"))
    last = _final(_metric("session-2"))
    create_session(paths, _metadata(first))
    line = (json.dumps(asdict(first)) + "\n").encode()
    repeats = (16 * 1024 * 1024) // len(line) + 1
    with paths.metrics.open("wb") as stream:
        for _ in range(repeats):
            stream.write(line)
        stream.write((json.dumps(asdict(last)) + "\n").encode())
    size = paths.metrics.stat().st_size
    assert size > 16 * 1024 * 1024
    snapshot = observe_metrics(
        paths, batch_id="batch-1", max_bytes=size + 1, max_records=repeats + 2
    )
    assert snapshot.rows == (first, last)
    assert snapshot.complete and snapshot.gaps == ()


def test_metrics_deduplicate_cumulative_usage_without_summing_session_updates(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    usage = {
        "input_tokens": 10,
        "output_tokens": 2,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "tool_uses": 1,
        "cost_usd": 0.1,
        "estimated": False,
    }
    pending = replace(_metric(), usage=usage)
    final = replace(_final(pending), usage={**usage, "input_tokens": 15})
    second = replace(_final(_metric("session-2")), usage=usage)
    create_session(paths, _metadata(pending))
    paths.metrics.write_text(
        "".join(json.dumps(asdict(row)) + "\n" for row in (pending, final, second))
    )
    snapshot = observe_metrics(paths, batch_id="batch-1")
    assert snapshot.complete and not snapshot.gaps
    assert snapshot.rows == (final, second)
    assert sum(row.usage["input_tokens"] for row in snapshot.rows) == 25


def test_missing_evidence_observers_do_not_create_runtime_artifacts(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    before = set(tmp_path.rglob("*"))
    evidence = observe_session_evidence(paths, "session-1")
    assert not evidence.raw and not evidence.normalized and not evidence.summary
    emergency = observe_emergency_failure(paths)
    assert not emergency.present and emergency.detail is None
    assert not emergency.malformed
    assert set(tmp_path.rglob("*")) == before


@pytest.mark.parametrize("artifact", ("raw", "normalized", "summary"))
def test_session_evidence_does_not_follow_artifact_symlinks(
    tmp_path: Path, artifact: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    session = create_session(paths, _metadata(_metric()))
    target = tmp_path / "target"
    target.write_text('{"private":"evidence"}\n')
    path = getattr(session, artifact)
    path.symlink_to(target)
    status = observe_session_evidence(paths, "session-1")
    assert getattr(status, artifact) is False
    assert path.is_symlink()
    assert target.read_text() == '{"private":"evidence"}\n'


def test_session_evidence_reports_regular_raw_normalized_and_summary_artifacts(
    tmp_path: Path,
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    session = create_session(paths, _metadata(_metric()))
    session.raw.write_bytes(b"raw session output\n")
    session.normalized.write_bytes(b"")
    summary = json.dumps(
        {
            "success": True,
            "session_id": "session-1",
            "failure_class": None,
            "failure_detail": None,
            "rate_limit_reset_at": None,
            "usage": None,
        }
    )
    session.summary.write_text(summary)
    status = observe_session_evidence(paths, "session-1")
    assert status.raw and status.normalized and status.summary
    assert session.raw.read_bytes() == b"raw session output\n"
    assert session.normalized.read_bytes() == b""
    assert session.summary.read_text() == summary


@pytest.mark.parametrize("malformed", (False, True))
@pytest.mark.parametrize("detail", ("disk full during commit", "lock disappeared"))
def test_emergency_observation_preserves_marker_and_sanitizes_detail(
    tmp_path: Path, malformed: bool, detail: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    create_session(paths, _metadata(_metric()))
    marker = paths.runtime_root / "state-write-failed.json"
    content = (
        b"{broken}"
        if malformed
        else json.dumps(
            {
                "schema_version": 1,
                "site": "session-end",
                "detail": f"{detail} password=hidden-value",
                "created_at": "2026-09-14T10:00:00Z",
            }
        ).encode()
    )
    marker.write_bytes(content)
    marker.chmod(0o600)
    before = marker.stat()
    observed = observe_emergency_failure(paths)
    assert observed.present and observed.malformed is malformed
    assert isinstance(observed.detail, str) and observed.detail
    assert "hidden-value" not in observed.detail
    if not malformed:
        assert detail in observed.detail
    assert marker.read_bytes() == content
    assert os.path.samestat(before, marker.stat())
    assert observe_emergency_failure(paths) == observed


@pytest.mark.parametrize(
    "record",
    (
        [],
        None,
        "failure",
        {},
        {"schema_version": 1, "site": "session-end", "detail": "missing time"},
        {
            "schema_version": 2,
            "site": "session-end",
            "detail": "bad schema",
            "created_at": "2026-09-14T10:00:00Z",
        },
        {
            "schema_version": 1,
            "site": "session-end",
            "detail": "bad time",
            "created_at": "not-a-timestamp",
        },
        {
            "schema_version": 1,
            "site": "session-end",
            "detail": 42,
            "created_at": "2026-09-14T10:00:00Z",
        },
    ),
)
def test_emergency_observation_preserves_invalid_schema_as_malformed(
    tmp_path: Path, record: object
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    create_session(paths, _metadata(_metric()))
    marker = paths.runtime_root / "state-write-failed.json"
    content = json.dumps(record).encode()
    marker.write_bytes(content)
    marker.chmod(0o600)
    before = marker.stat()
    observed = observe_emergency_failure(paths)
    assert observed.present and observed.malformed
    assert isinstance(observed.detail, str) and observed.detail
    assert marker.read_bytes() == content
    assert os.path.samestat(before, marker.stat())


@pytest.mark.parametrize("obstacle", ("symlink", "directory", "fifo"))
def test_emergency_observation_keeps_unsafe_marker_present_and_malformed(
    tmp_path: Path, obstacle: str
) -> None:
    paths = resolve_runtime_paths(tmp_path)
    create_session(paths, _metadata(_metric()))
    marker = paths.runtime_root / "state-write-failed.json"
    target = tmp_path / "target"
    target.write_text("preserve target")
    if obstacle == "symlink":
        marker.symlink_to(target)
    elif obstacle == "directory":
        marker.mkdir()
    else:
        os.mkfifo(marker)
    before = marker.lstat()
    observed = observe_emergency_failure(paths)
    assert observed.present and observed.malformed
    assert isinstance(observed.detail, str) and observed.detail
    assert os.path.samestat(before, marker.lstat())
    assert target.read_text() == "preserve target"
