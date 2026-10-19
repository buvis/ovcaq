"""A selected owner's exit during a poll must not freeze an uncertain frame."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from tests.integration.test_observer_terminal_cleanup import (
    assert_committed,
    assert_final_telemetry,
    selected_run,
)
from tests.integration.test_observer_terminal_cleanup import (
    isolated_config as isolated_config,  # noqa: PLC0414 - pytest fixture re-export
)

from ovcaq.runtime import _run_observation
from ovcaq.state.store import StateStore
from ovcaq.tui import model


@pytest.mark.parametrize(
    "boundary,immediate_terminal",
    [("identity", True), ("run", False), ("state", False), ("evidence", False)],
)
def test_exit_during_poll_preserves_validated_terminal_frame(
    isolated_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    boundary: str,
    immediate_terminal: bool,
) -> None:
    with selected_run(isolated_config, "completed", telemetry=True) as selected:
        targets = {
            "identity": (_run_observation, "process_matches"),
            "run": (_run_observation, "observe_run"),
            "state": (StateStore, "read"),
            "evidence": (model, "observe_metrics"),
        }
        target, name = targets[boundary]
        original: Callable[..., object] = getattr(target, name)
        final_state = None

        def exit_after_read(*args: object, **kwargs: object) -> object:
            nonlocal final_state
            result = original(*args, **kwargs)
            if final_state is None:
                final_state = selected.finish()
            return result

        with monkeypatch.context() as edge:
            edge.setattr(target, name, exit_after_read)
            interrupted = selected.observer.poll()
        assert final_state is not None
        # Identity-before-cleanup can collect a coherent terminal sample;
        # an invalidated evidence read must leave final delivery to the next poll.
        assert interrupted.ended is immediate_terminal
        final = selected.observer.poll()
        assert final.status == "completed"
        assert_committed(final, final_state, selected)
        assert_final_telemetry(final, selected, final_state)
        assert selected.observer.poll() == final


@pytest.mark.parametrize("damage", ["missing", "digest"])
def test_exit_during_poll_with_invalid_attestation_still_ends_uncertain(
    isolated_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    with selected_run(isolated_config, "completed", telemetry=True) as selected:
        original = model.observe_metrics

        def exit_without_attestation(*args: object, **kwargs: object) -> object:
            result = original(*args, **kwargs)
            selected.finish()
            path = selected.settings.runtime.paths.runtime_root / "run-terminal.json"
            if damage == "missing":
                path.unlink()
            else:
                record = json.loads(path.read_text())
                record["state_digest"] = "invalid"
                path.write_text(json.dumps(record))
            return result

        monkeypatch.setattr(model, "observe_metrics", exit_without_attestation)
        final = selected.observer.poll()
        assert final.ended and final.status == "unknown"
        assert final.gaps and final.run == selected.first.run
        assert selected.observer.poll() == final
