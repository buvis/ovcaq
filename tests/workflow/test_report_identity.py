from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest

from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.workflow.reports import archive_final_state, publish_audit, publish_report


@pytest.fixture(
    params=(
        ("report", ""),
        ("report", "reports"),
        ("audit", ""),
        ("audit", "docs"),
        ("audit", "docs/dev/project-management"),
        ("audit", "docs/dev/project-management/reviews"),
        ("archive", ""),
        ("archive", "reports"),
    ),
    ids=lambda case: "-".join(case),
)
def publication(
    request: pytest.FixtureRequest, tmp_path: Path, workflow_state: State
) -> tuple[Callable[[], Path], Path, Path]:
    surface, component = request.param
    root = tmp_path / "output"
    root.mkdir()
    workflow_state["work"].update(phase="done", next_phase="")
    store = StateStore(tmp_path / "state.json")
    store.initialize(workflow_state)
    state = store.read()
    publish = {
        "report": lambda: publish_report(root, state, ()),
        "audit": lambda: publish_audit(root, state),
        "archive": lambda: archive_final_state(root, state),
    }[surface]
    return publish, root / component, store.path


@pytest.mark.parametrize("boundary", ("replace", "replay-sync"))
def test_displaced_publication_chain_refuses_then_retries_at_configured_path(
    publication: tuple[Callable[[], Path], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
) -> None:
    publish, component, state_path = publication
    path = publish()
    payload, state_before = path.read_bytes(), state_path.read_bytes()
    output_inode = path.parent.stat().st_ino
    retained = component.with_name(component.name + "-retained")
    native_replace, native_sync = os.replace, os.fsync
    if boundary == "replace":
        path.unlink()

    def displace() -> None:
        component.rename(retained)
        component.mkdir()

    def replace(source: str, destination: str, **kwargs: int) -> None:
        displace()
        native_replace(source, destination, **kwargs)

    def sync(descriptor: int) -> None:
        if os.fstat(descriptor).st_ino == output_inode:
            displace()
        native_sync(descriptor)

    with monkeypatch.context() as patches:
        patches.setattr(
            os,
            "replace" if boundary == "replace" else "fsync",
            replace if boundary == "replace" else sync,
        )
        with pytest.raises(OSError, match="output directory identity changed"):
            publish()

    assert not path.exists()
    assert (retained / path.relative_to(component)).read_bytes() == payload
    assert state_path.read_bytes() == state_before
    assert list(retained.rglob("*.tmp")) == []
    assert publish() == path
    assert path.read_bytes() == payload
    assert publish() == path
    assert path.read_bytes() == payload
    assert state_path.read_bytes() == state_before
