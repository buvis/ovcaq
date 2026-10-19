from __future__ import annotations

import json
import os
from pathlib import Path

from ovcaq.runtime.session import SessionMetadata
from ovcaq.state.schema import MAX_STATE_BYTES


def _metadata(session_id: str = "session-1") -> SessionMetadata:
    return SessionMetadata(
        schema_version=1,
        run_id="run-1",
        session_id=session_id,
        agent="generic",
        pid=os.getpid(),
        process_start="process-start-token",
        started_at="2026-09-14T10:00:00Z",
    )


def _summary(session_id: str = "session-1") -> dict[str, object]:
    return {
        "schema_version": 1,
        "session_id": session_id,
        "finished_at": "2026-09-14T10:01:00Z",
        "returncode": 0,
        "signal": None,
        "timed_out": False,
        "detail": None,
    }


def _decode(path: Path) -> dict[str, object]:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result, f"duplicate owned JSON key: {key}"
            result[key] = value
        return result

    payload = path.read_bytes()
    assert len(payload) <= MAX_STATE_BYTES
    document = json.loads(payload, object_pairs_hook=unique_keys)
    assert isinstance(document, dict)
    return document


def _publication_path(path: str | Path, descriptor: object, parent: Path) -> Path:
    candidate = Path(path)
    if descriptor is not None and not candidate.is_absolute():
        information = os.fstat(descriptor)
        assert os.path.samestat(information, parent.stat())
        return parent / candidate
    return candidate
