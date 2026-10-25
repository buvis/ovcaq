"""Contract A types for the external workflow controller boundary."""

from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ovcaq.paths import ProjectPathError, _checked_path

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
        try:
            bundle = _checked_path(self.contract_bundle)
        except ProjectPathError as error:
            raise ValueError(
                f"contract_bundle must not traverse a symlink: {error}"
            ) from error
        if not bundle.is_file():
            raise ValueError(
                f"contract_bundle must be an existing file: {self.contract_bundle}"
            )
        object.__setattr__(self, "contract_bundle", bundle)
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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IncompatibleContractError(f"bundle has duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise IncompatibleContractError(f"bundle has non-finite number: {name}")


def controller_bundle_digest(path: Path, expected_digest: str | None = None) -> str:
    """Return the sha256 of the bundle's sorted-key canonical JSON form.

    Raise IncompatibleContractError when the bundle is unreadable or not a
    strict JSON object, or when expected_digest is given and does not match.
    """
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise IncompatibleContractError(
            f"cannot read contract bundle {path}: {error}"
        ) from error
    if not isinstance(data, dict):
        raise IncompatibleContractError(
            f"contract bundle must be a JSON object: {path}"
        )
    canonical = json.dumps(data, sort_keys=True).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    if expected_digest is not None and expected_digest != digest:
        raise IncompatibleContractError(
            f"contract bundle digest mismatch for {path}: "
            f"expected {expected_digest}, computed {digest}"
        )
    return digest


def _string_set(data: Mapping[str, Any], field: str) -> frozenset[str]:
    value = data.get(field)
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ControllerOutputError(f"contract {field} must be a list of strings")
    return frozenset(value)


class ControllerClient:
    """Run the external workflow controller through explicit argv only."""

    def __init__(self, config: ControllerConfig) -> None:
        self._config = config
        self._contract: ControllerContract | None = None

    def _run(self, *arguments: str) -> dict[str, Any]:
        config = self._config
        process = subprocess.Popen(
            [*config.argv, "--json", *arguments],
            cwd=config.project_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=config.timeout_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise ControllerTimeoutError(
                f"controller did not answer within {config.timeout_seconds}s"
            ) from None
        if process.returncode != 0:
            detail = stderr.decode("utf-8", errors="replace").strip()
            raise ControllerError(
                f"controller exited with status {process.returncode}: {detail}"
            )
        if len(stdout) > config.max_output_bytes:
            raise ControllerOutputError(
                f"controller output exceeds {config.max_output_bytes} bytes"
            )
        try:
            data = json.loads(stdout)
        except ValueError as error:
            raise ControllerOutputError(
                f"controller output is not valid JSON: {error}"
            ) from None
        if not isinstance(data, dict):
            raise ControllerOutputError("controller output must be a JSON object")
        return data

    def contract(self) -> ControllerContract:
        """Return the live contract once it matches the pinned bundle."""
        if self._contract is not None:
            return self._contract
        pinned_path = self._config.contract_bundle
        controller_bundle_digest(pinned_path)
        pinned = json.loads(pinned_path.read_text(encoding="utf-8"))
        live = self._run("contract")
        major = live.get("protocol_major")
        if type(major) is not int or major != PROTOCOL_MAJOR:
            raise IncompatibleContractError(
                f"controller protocol_major {major!r} is not {PROTOCOL_MAJOR}"
            )
        for field in ("schema_digest", "fixture_digest"):
            if live.get(field) != pinned.get(field):
                raise IncompatibleContractError(
                    f"controller {field} {live.get(field)!r} does not match "
                    f"pinned {pinned.get(field)!r}"
                )
        version = live.get("package_version")
        if not isinstance(version, str):
            raise ControllerOutputError("contract package_version must be a string")
        self._contract = ControllerContract(
            protocol_major=major,
            package_version=version,
            schema_digest=live["schema_digest"],
            fixture_digest=live["fixture_digest"],
            operations=_string_set(live, "operations"),
            capabilities=_string_set(live, "capabilities"),
        )
        return self._contract

    def snapshot(self, *, workflow_id: str) -> dict[str, Any]:
        """Return the controller's snapshot payload unmodified."""
        _require_string(workflow_id, "workflow_id")
        return self._run("snapshot", "--project-root", str(self._config.project_root))

    def apply(self, envelope: MutationEnvelope) -> ApplyResult:
        """Hand one mutation envelope to the controller in a private file."""
        actor_file = self._config.actor_file
        if actor_file is None:
            raise ControllerError("apply requires a configured actor_file")
        request = {
            "protocol_major": envelope.protocol_major,
            "operation": envelope.operation,
            "request_id": envelope.request_id,
            "expected_revision": envelope.expected_revision,
            "project_id": envelope.project_id,
            "workflow_id": envelope.workflow_id,
            "actor_id": envelope.actor_id,
            "lease_epoch": envelope.lease_epoch,
            "payload": dict(envelope.payload),
        }
        descriptor, name = tempfile.mkstemp(prefix="ovcaq-request-", suffix=".json")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(request, stream)
            response = self._run(
                "apply",
                "--project-root",
                str(self._config.project_root),
                "--actor-file",
                str(actor_file),
                "--request",
                name,
            )
        finally:
            os.unlink(name)
        ok = response.get("ok")
        revision = response.get("revision")
        result = response.get("result")
        error_code = response.get("error_code")
        retryable = response.get("retryable")
        if (
            not isinstance(ok, bool)
            or not (revision is None or type(revision) is int)
            or not (result is None or isinstance(result, dict))
            or not (error_code is None or isinstance(error_code, str))
            or not isinstance(retryable, bool)
        ):
            raise ControllerOutputError("controller apply response is malformed")
        return ApplyResult(ok, revision, result, error_code, retryable)
