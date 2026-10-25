"""Contract A types for the external workflow controller boundary."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROTOCOL_MAJOR = 1
INITIAL_OPEN_OPERATION = "workflow.open"
MAX_TIMEOUT_SECONDS = 300


class ControllerError(RuntimeError):
    """The workflow controller could not serve a request."""


class IncompatibleContractError(ControllerError):
    """The controller contract does not match the pinned bundle."""


class ControllerTimeoutError(ControllerError):
    """The controller did not answer within the configured timeout."""


class ControllerOutputError(ControllerError):
    """The controller produced malformed or oversized output."""


class RevisionConflictError(ControllerError):
    """The expected revision no longer matches the controller state."""


class RejectedRequestError(ControllerError):
    """The controller rejected a request with a structured error."""

    def __init__(self, error_code: str, retryable: bool, detail: str) -> None:
        super().__init__(f"{error_code}: {detail}")
        self.error_code = error_code
        self.retryable = retryable
        self.detail = detail


def _require_string(value: object, field: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    if not value:
        raise ValueError(f"{field} must not be empty")


def _require_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{field} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class ControllerConfig:
    argv: tuple[str, ...]
    contract_bundle: Path
    actor_file: Path | None
    project_root: Path
    timeout_seconds: int = 30
    max_output_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple):
            raise TypeError("argv must be a tuple")
        if not self.argv:
            raise ValueError("argv must not be empty")
        for argument in self.argv:
            _require_string(argument, "argv argument")
        if not isinstance(self.contract_bundle, Path):
            raise TypeError("contract_bundle must be a Path")
        if not self.contract_bundle.is_file():
            raise ValueError(
                f"contract_bundle must be an existing file: {self.contract_bundle}"
            )
        if self.actor_file is not None and not isinstance(self.actor_file, Path):
            raise TypeError("actor_file must be a Path or None")
        if not isinstance(self.project_root, Path):
            raise TypeError("project_root must be a Path")
        timeout = _require_int(self.timeout_seconds, "timeout_seconds")
        if not 1 <= timeout <= MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}"
            )
        if _require_int(self.max_output_bytes, "max_output_bytes") <= 0:
            raise ValueError("max_output_bytes must be positive")


@dataclass(frozen=True, slots=True)
class ControllerContract:
    protocol_major: int
    package_version: str
    schema_digest: str
    fixture_digest: str
    operations: frozenset[str]
    capabilities: frozenset[str]


@dataclass(frozen=True, slots=True)
class ApplyResult:
    ok: bool
    revision: int | None
    result: Mapping[str, Any] | None
    error_code: str | None
    retryable: bool


@dataclass(frozen=True, slots=True)
class MutationEnvelope:
    protocol_major: int
    operation: str
    request_id: str
    expected_revision: int
    project_id: str
    workflow_id: str | None
    actor_id: str | None
    lease_epoch: int | None
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if _require_int(self.protocol_major, "protocol_major") != PROTOCOL_MAJOR:
            raise ValueError(f"protocol_major must be {PROTOCOL_MAJOR}")
        _require_string(self.operation, "operation")
        _require_string(self.request_id, "request_id")
        if _require_int(self.expected_revision, "expected_revision") < 0:
            raise ValueError("expected_revision must not be negative")
        _require_string(self.project_id, "project_id")
        initial_open = (
            self.operation == INITIAL_OPEN_OPERATION and self.expected_revision == 0
        )
        for field in ("workflow_id", "actor_id"):
            value = getattr(self, field)
            if value is None and initial_open:
                continue
            _require_string(value, field)
        if not (self.lease_epoch is None and initial_open):
            _require_int(self.lease_epoch, "lease_epoch")


def controller_bundle_digest(path: Path) -> str:
    """Return the sha256 of the bundle's sorted-key canonical JSON form."""
    data = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(data, sort_keys=True).encode()
    return hashlib.sha256(canonical).hexdigest()
