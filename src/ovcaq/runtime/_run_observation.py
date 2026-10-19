"""Read-only run identity and selected-run evidence guards."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ovcaq.paths import RuntimePaths
from ovcaq.runtime._session_io import _encode_record, _private_directory, _publish
from ovcaq.runtime.registry import (
    FleetRun,
    ProcessIdentity,
    observe_unowned_run,
    process_matches,
    run_lock_held,
)
from ovcaq.state.schema import MAX_STATE_BYTES, State, decode_json
from ovcaq.state.store import StateError, StateStore


@dataclass(frozen=True)
class RunObservation:
    status: Literal["idle", "active", "inconsistent"]
    detail: str = "available"
    active_session_id: str | None = None
    run_id: str | None = None
    process: ProcessIdentity | None = None


@dataclass
class SelectedRunObservation:
    state: State | None
    observation: RunObservation
    ended: bool
    gaps: tuple[str, ...] = ()


def _state_digest(state: State) -> str:
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def publish_terminal_evidence(
    paths: RuntimePaths,
    *,
    run_id: str | None = None,
    process: ProcessIdentity | None = None,
    state: State | None = None,
) -> None:
    """Invalidate on acquisition; attest the owner's final state before cleanup."""
    _publish(
        paths.runtime_root / "run-terminal.json",
        _encode_record(
            {
                "schema_version": 1,
                "run_id": run_id,
                "pid": process.pid if process else None,
                "process_start": process.started if process else None,
                "state_digest": _state_digest(state) if state is not None else None,
            }
        ),
        identities=paths._identities,
    )


def _verify_terminal_state(
    paths: RuntimePaths, selected: FleetRun, state: State
) -> None:
    with ExitStack() as stack:
        directory = _private_directory(
            paths.runtime_root, stack, identities=paths._identities, create=False
        )
        descriptor = os.open(
            "run-terminal.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=directory,
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("final evidence must be a regular file")
            payload = stream.read(MAX_STATE_BYTES + 1)
        if len(payload) > MAX_STATE_BYTES:
            raise ValueError("final evidence exceeds size limit")
    record = decode_json(payload.decode("utf-8"), source="run-terminal.json")
    if record != {
        "schema_version": 1,
        "run_id": selected.run_id,
        "pid": selected.pid,
        "process_start": selected.process_start,
        "state_digest": _state_digest(state),
    }:
        raise ValueError("final state does not belong to the selected run")


def _selected_state(paths: RuntimePaths, selected: FleetRun) -> SelectedRunObservation:
    identity = ProcessIdentity(selected.pid, selected.process_start)
    # Once death is observed, sample metadata after cleanup rather than combining
    # an earlier active observation with the owner's later absence.
    ended = not process_matches(identity)
    observation = observe_run(paths)
    if not ended and observation.status != "active":
        # Cleanup may have overtaken the initial identity read. Confirm death
        # once, then require fresh metadata and the normal terminal attestation.
        ended = not process_matches(identity)
        if ended:
            observation = observe_run(paths)
    try:
        if selected.root != paths.project_root:
            raise ValueError("selected run root changed")
        if ended:
            with observe_unowned_run(paths.run_lock):
                if observation.status != "idle":
                    raise ValueError("selected run was replaced or has stale metadata")
                state = StateStore(paths.state_file).read()
                _verify_terminal_state(paths, selected, state)
        else:
            if (observation.run_id, observation.process) != (selected.run_id, identity):
                raise ValueError("selected run identity is unavailable")
            state = StateStore(paths.state_file).read()
            if observe_run(paths) != observation:
                raise ValueError("selected run changed during state observation")
        return SelectedRunObservation(state, observation, ended)
    except (OSError, ValueError, StateError) as error:
        return SelectedRunObservation(
            None, observation, ended, (f"selected state unavailable: {error}",)
        )


@contextmanager
def observe_selected_run(
    paths: RuntimePaths, selected: FleetRun, *, batch_id: str | None
) -> Iterator[SelectedRunObservation]:
    """Invalidate the observation on exit if ownership changed during evidence reads."""
    result = _selected_state(paths, selected)
    yield result
    if result.state is None:
        return
    after = _selected_state(paths, selected)
    if (
        after.state is None
        or (result.ended and after.state != result.state)
        or after.ended != result.ended
        or after.observation != result.observation
        or (batch_id is not None and result.state["batch"]["id"] != batch_id)
    ):
        # An attested live-to-terminal transition crossed this evidence read.
        # Leave this invalidated frame nonterminal; the next poll must collect
        # its own coherent final evidence before the viewer stops observing.
        terminal_transition = (
            not result.ended
            and after.ended
            and after.state is not None
            and (batch_id is None or after.state["batch"]["id"] == batch_id)
        )
        result.state = None
        result.ended = after.ended and not terminal_transition
        result.gaps = after.gaps or ("selected state changed during evidence reads",)


def observe_run(paths: RuntimePaths) -> RunObservation:
    """Observe authority and validated process identity once without taking locks."""
    from ovcaq.runtime.session import parse_session_metadata

    try:
        directory = os.open(
            paths.runtime_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
    except FileNotFoundError:
        return RunObservation("idle")
    except OSError as error:
        return RunObservation("inconsistent", str(error))
    try:
        locked = run_lock_held(Path("run.lock"), directory=directory)
        try:
            record_fd = os.open(
                "run.json",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
        except FileNotFoundError:
            if locked:
                return RunObservation("inconsistent", "held run lock has no metadata")
            return RunObservation("idle")
        with os.fdopen(record_fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("run metadata must be regular")
            payload = stream.read(MAX_STATE_BYTES + 1)
        if len(payload) > MAX_STATE_BYTES:
            raise ValueError("run metadata exceeds size limit")
        metadata = parse_session_metadata(
            decode_json(payload.decode("utf-8"), source="run.json")
        )
        if not locked:
            return RunObservation("inconsistent", "run metadata has no held run lock")
        if not process_matches(ProcessIdentity(metadata.pid, metadata.process_start)):
            return RunObservation("inconsistent", "run process identity is stale")
        return RunObservation(
            "active",
            active_session_id=metadata.session_id,
            run_id=metadata.run_id,
            process=ProcessIdentity(metadata.pid, metadata.process_start),
        )
    except (OSError, ValueError, TypeError) as error:
        return RunObservation("inconsistent", str(error))
    finally:
        os.close(directory)
