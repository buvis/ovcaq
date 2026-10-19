from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from tests.state.test_supervisor_commands import NOTICE, _service, _state


@pytest.mark.parametrize("field", ["phase", "next_phase"])
@pytest.mark.parametrize("site", ["review_cap", "systemic", "operator-check"])
def test_resume_preserves_phase_pause_routing_and_drained_results(
    tmp_path: Path, field: str, site: str
) -> None:
    initial = _state(tmp_path)
    initial["work"][field] = "paused"
    reason = {**NOTICE, "site": site}
    initial["control"].update(
        pause_requested=True, pause_reason=reason, attention=deepcopy(NOTICE)
    )
    initial["recovery"].update(phase_fingerprint="saved", phase_repeats=3)
    service, store = _service(tmp_path, initial)
    result = service.resume(expected_revision=0)
    assert result == store.read()
    assert result["control"]["pause_reason"] == reason
    assert result["control"]["attention"] == initial["control"]["attention"]
    for key in ("work", "tasks", "review", "recovery", "batch"):
        assert result[key] == initial[key]
