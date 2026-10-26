from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from tests.runtime.test_supervisor_cli import _failure, _invoke, _state, _success

from ovcaq.cli import build_parser
from ovcaq.config import supervisor_settings
from ovcaq.runtime.capability import CapabilityExecution, CapabilityRequest
from ovcaq.state.schema import State
from ovcaq.state.store import StateStore
from ovcaq.supervisor_cli import dispatch_supervisor

DECLARED = ("archive", "agoge")


@pytest.fixture(autouse=True)
def isolated_homes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "xdg-state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))


@dataclass
class Runner:
    names: list[str] = field(default_factory=list)

    def run(self, request: CapabilityRequest) -> CapabilityExecution:
        self.names.append(request.name)
        return CapabilityExecution(True, request.session.root.name, None)


def _declare_failed(root: Path, capsys: pytest.CaptureFixture[str]) -> State:
    _success(_invoke(root, capsys, "init"))

    def seed(state: State) -> None:
        state["batch"].update(id="cli-batch", status="running")
        for name in DECLARED:
            state["batch"]["capabilities"][name] = {
                "required": True,
                "launcher": "fake",
                "plugin": f"fake/{name}",
                "version": "1",
                "failure": "attention",
                "status": "failed",
                "attempts": [
                    {
                        "id": f"attempt-{name}",
                        "status": "failed",
                        "started_at": "2026-10-02T10:00:00Z",
                        "finished_at": "2026-10-02T10:01:00Z",
                        "session_id": None,
                        "detail": f"{name} failed",
                    }
                ],
            }

    store = StateStore(supervisor_settings(root).runtime.paths.state_file)
    return store.transaction(seed)


@pytest.mark.parametrize("name", DECLARED)
def test_retry_accepts_a_declared_capability_and_runs_only_that_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    before = _declare_failed(tmp_path, capsys)
    runner = Runner()
    arguments = ["--root", str(tmp_path), "--json", "capability", "retry", name]
    value, revision, mutation, code = dispatch_supervisor(
        build_parser().parse_args(arguments), tmp_path, capability_runner=runner
    )
    after = _state(tmp_path)
    assert runner.names == [name]
    assert code == 0 and mutation is True
    assert value == after and revision == after["revision"] > before["revision"]
    capability = after["batch"]["capabilities"][name]
    previous = before["batch"]["capabilities"][name]["attempts"]
    assert capability["status"] == "succeeded"
    assert len(capability["attempts"]) == 2 and capability["attempts"][0] == previous[0]
    (other,) = set(DECLARED) - {name}
    assert (
        after["batch"]["capabilities"][other] == before["batch"]["capabilities"][other]
    )


@pytest.mark.parametrize("name", DECLARED)
def test_cli_retry_of_a_declared_capability_is_not_a_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], name: str
) -> None:
    before = _declare_failed(tmp_path, capsys)
    failure = _failure(_invoke(tmp_path, capsys, "capability", "retry", name))
    assert failure["error"]["code"] != "usage"
    assert "unknown capability" not in failure["error"]["message"]
    (other,) = set(DECLARED) - {name}
    after = _state(tmp_path)
    assert (
        after["batch"]["capabilities"][other] == before["batch"]["capabilities"][other]
    )
