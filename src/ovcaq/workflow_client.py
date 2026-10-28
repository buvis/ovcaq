"""Contract A types for the external workflow controller boundary."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from ovcaq.paths import ProjectPathError, _checked_path

PROTOCOL_MAJOR = 1
INITIAL_OPEN_OPERATION = "workflow.open"
MAX_TIMEOUT_SECONDS = 300
MAX_STDERR_TAIL_CHARS = 512
TRUNCATION_MARKER = "...(truncated) "
REDACTED_MARKER = "<redacted>"
MIN_SECRET_CHARS = 8
_LONG_TOKEN = re.compile(rf"\S{{{MIN_SECRET_CHARS},}}")
READ_CHUNK_BYTES = 65_536
POLL_SECONDS = 0.05
JOIN_SECONDS = 1.0
REQUIRED_CONTRACT_STRINGS = ("package_version", "schema_digest", "fixture_digest")
ADVERTISED_CONTRACT_FIELDS = ("operations", "capabilities")
# The fields a file must carry before it is a contract bundle at all. Presence
# only: contract() negotiates their shapes and the protocol major.
REQUIRED_BUNDLE_FIELDS = ("protocol_major", *ADVERTISED_CONTRACT_FIELDS)


class ControllerError(RuntimeError):
    """The workflow controller could not serve a request."""


class IncompatibleContractError(ControllerError):
    """The controller contract does not match the pinned bundle."""


class ControllerTimeoutError(ControllerError):
    """The controller did not answer within the configured timeout."""


class ControllerOutputError(ControllerError):
    """The controller produced malformed or oversized output."""


class ControllerLaunchError(ControllerError):
    """The controller program could not be launched, so it never ran."""


class ApplyOutcomeUnknownError(ControllerError):
    """An apply may have committed without acking, so it must be retried.

    Raised for every post-spawn failure of an apply: the controller timed
    out, tripped the output bound (an overrun), answered with a non-JSON or
    non-dict body, broke the ApplyResult contract, or exited non-zero after
    the spawn. Deliberately not a ControllerTimeoutError: a caller that
    swallows timeouts must not swallow an unknown outcome.
    """

    def __init__(self, request_id: str, detail: str) -> None:
        super().__init__(
            f"outcome unknown for apply request {request_id}: {detail}; "
            "retry the same envelope"
        )
        self.request_id = request_id


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
    bundle_digest: str | None = None

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
        if self.bundle_digest is not None:
            _require_string(self.bundle_digest, "bundle_digest")


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


def _apply_request(envelope: MutationEnvelope) -> dict[str, Any]:
    """The wire request body for one mutation envelope."""
    return {
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


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IncompatibleContractError(f"bundle has duplicate key: {key!r}")
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise IncompatibleContractError(f"bundle has non-finite number: {name}")


def _read_bundle(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise IncompatibleContractError(
            f"cannot read contract bundle {path}: {error}"
        ) from error


def _parse_bundle(data: bytes, path: Path) -> dict[str, Any]:
    try:
        parsed = json.loads(
            data,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise IncompatibleContractError(
            f"cannot read contract bundle {path}: {error}"
        ) from error
    if not isinstance(parsed, dict):
        raise IncompatibleContractError(
            f"contract bundle must be a JSON object: {path}"
        )
    return parsed


def _validated_bundle(
    path: Path, expected_digest: str | None
) -> tuple[dict[str, Any], str]:
    """The bundle's body and digest, hashed and parsed from one read.

    The digest is the sha256 of the file's raw bytes, so it is what
    `sha256sum <file>` and tools/autopilot-prerequisites both compute. The
    whole digest is compared, with hex letter case normalised as the tool
    normalises it: a prefix of it pins nothing.
    """
    data = _read_bundle(path)
    digest = hashlib.sha256(data).hexdigest()
    parsed = _parse_bundle(data, path)
    for field in REQUIRED_BUNDLE_FIELDS:
        if field not in parsed:
            raise IncompatibleContractError(f"contract bundle {path} has no {field}")
    if expected_digest is not None and expected_digest.lower() != digest:
        raise IncompatibleContractError(
            f"contract bundle digest mismatch for {path}: "
            f"expected {expected_digest}, computed {digest}"
        )
    return parsed, digest


def controller_bundle_digest(path: Path, expected_digest: str | None = None) -> str:
    """Return the sha256 of the contract bundle file's raw bytes.

    Raise IncompatibleContractError when the bundle is unreadable, is not a
    strict JSON object, lacks a required contract field, or when
    expected_digest is given and is not that whole digest.
    """
    return _validated_bundle(path, expected_digest)[1]


def _string_set(data: Mapping[str, Any], field: str) -> frozenset[str]:
    value = data.get(field)
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ControllerOutputError(f"contract {field} must be a list of strings")
    return frozenset(value)


def _pinned_string(pinned: Mapping[str, Any], field: str) -> str:
    value = pinned.get(field)
    if not isinstance(value, str) or not value:
        raise IncompatibleContractError(
            f"pinned contract {field} must be a nonempty string, got {value!r}"
        )
    return value


def _pinned_names(pinned: Mapping[str, Any], field: str) -> list[str]:
    value = pinned.get(field)
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise IncompatibleContractError(
            f"pinned contract {field} must be a list of strings"
        )
    return value


def _live_string(live: Mapping[str, Any], field: str, *, allow_empty: bool) -> str:
    value = live.get(field)
    if not isinstance(value, str) or (not value and not allow_empty):
        raise ControllerOutputError(f"contract {field} must be a nonempty string")
    return value


def _check_advertised(field: str, pinned: list[str], live: frozenset[str]) -> None:
    missing = sorted(set(pinned) - live)
    if missing:
        raise IncompatibleContractError(
            f"controller does not advertise pinned {field}: {', '.join(missing)}"
        )


def _read_capped(stream: IO[bytes], cap: int, sink: list[bytes]) -> None:
    """Read at most cap bytes from the stream into the sink, then stop.

    The reader closes its own stream: closing it from another thread while
    this read is blocked waits out that read, so a detached descendant
    holding the pipe open would stall the caller past its deadline.
    """
    size = 0
    try:
        while size < cap:
            chunk = stream.read(min(READ_CHUNK_BYTES, cap - size))
            if not chunk:
                return
            sink.append(chunk)
            size += len(chunk)
    finally:
        stream.close()


def _kill_group(process: subprocess.Popen[bytes]) -> None:
    """Kill the controller's whole process group, so grandchildren die too."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass  # the controller exited before the signal reached its group
    try:
        process.wait(timeout=JOIN_SECONDS)
    except subprocess.TimeoutExpired:
        # SIGKILL did not reap the group within the bound; it may still be
        # a zombie. Nothing further to wait for here without risking the
        # same indefinite block this bound exists to prevent.
        pass


def _enforce_bound(
    process: subprocess.Popen[bytes],
    buffers: list[list[bytes]],
    config: ControllerConfig,
) -> None:
    """Kill the group and raise when either stream passed the output bound."""
    for name, sink in zip(("output", "stderr"), buffers, strict=True):
        if sum(map(len, sink)) > config.max_output_bytes:
            _kill_group(process)
            raise ControllerOutputError(
                f"controller {name} exceeds {config.max_output_bytes} bytes"
            )


def _timed_out(config: ControllerConfig) -> ControllerTimeoutError:
    return ControllerTimeoutError(
        f"controller did not answer within {config.timeout_seconds}s"
    )


def _truncated(text: str) -> str:
    """Text bounded to its tail, marked when anything was dropped."""
    if len(text) > MAX_STDERR_TAIL_CHARS:
        return TRUNCATION_MARKER + text[-MAX_STDERR_TAIL_CHARS:]
    return text


class ControllerClient:
    """Run the external workflow controller through explicit argv only."""

    def __init__(self, config: ControllerConfig) -> None:
        self._config = config
        self._contract: ControllerContract | None = None

    def _redact(self, text: str) -> str:
        """Mask every whitespace-delimited token long enough to be a secret.

        The actor file is never read: only its path is ever passed to the
        controller, so the credential's value is unknown here by design.
        Tokens shorter than MIN_SECRET_CHARS stay legible: they are prose,
        and masking them would cost the diagnostic its meaning.
        """
        return _LONG_TOKEN.sub(REDACTED_MARKER, text)

    def _can_mask_credential(self) -> bool:
        """Whether token-length masking can reach the actor file's credential.

        Settled from a stat alone, never a read: the actor file's contents
        stay unknown here by design, so the only evidence available is its
        size. A file of at least MIN_SECRET_CHARS bytes may hold a token
        long enough for _redact to mask; a smaller file, or one that cannot
        be stat'ed at all, is unsafe.

        Known residual: size bounds the credential only from above, so a
        short credential wrapped in a larger file (a JSON actor document, or
        a trailing newline) still reads as safe and survives masking in a
        diagnostic. That is a known miss against PRD 00057's task-3
        criterion for short secrets, deferred at the review gate of cycle 1:
        closing it needs the credential's length, or a redaction token,
        declared in configuration, since reading the actor file here is
        forbidden.
        """
        actor_file = self._config.actor_file
        if actor_file is None:
            return True
        try:
            return actor_file.stat().st_size >= MIN_SECRET_CHARS
        except OSError:
            return False

    def _bounded(self, text: str) -> str:
        """Controller text, redacted and then bounded to a tail.

        Dropped wholesale, down to the marker alone, when masking cannot
        reach the credential: the controller's own bytes may then be the
        credential itself, and no inspection here can tell.
        """
        if not self._can_mask_credential():
            return REDACTED_MARKER
        return _truncated(self._redact(text))

    def _detail(self, stderr: bytes) -> str:
        """The controller's stderr, redacted and then bounded to a tail."""
        return self._bounded(stderr.decode("utf-8", errors="replace").strip())

    def _await_output(
        self,
        process: subprocess.Popen[bytes],
        readers: list[threading.Thread],
        buffers: list[list[bytes]],
    ) -> None:
        """Poll until both readers finish, the bound trips or the time runs out."""
        config = self._config
        deadline = time.monotonic() + config.timeout_seconds
        while True:
            _enforce_bound(process, buffers, config)
            if not any(reader.is_alive() for reader in readers):
                break
            if time.monotonic() >= deadline:
                _kill_group(process)
                raise _timed_out(config)
            time.sleep(POLL_SECONDS)
        _enforce_bound(process, buffers, config)
        try:
            process.wait(timeout=max(deadline - time.monotonic(), 0.0))
        except subprocess.TimeoutExpired:
            _kill_group(process)
            raise _timed_out(config) from None

    def _capture(self, process: subprocess.Popen[bytes]) -> tuple[bytes, bytes]:
        """Both streams, read incrementally and capped one byte over the bound."""
        cap = self._config.max_output_bytes + 1
        buffers: list[list[bytes]] = [[], []]
        pipes = [pipe for pipe in (process.stdout, process.stderr) if pipe is not None]
        readers = [
            threading.Thread(target=_read_capped, args=(pipe, cap, sink), daemon=True)
            for pipe, sink in zip(pipes, buffers, strict=True)
        ]
        for reader in readers:
            reader.start()
        # The readers are never joined: _await_output returns only once every
        # reader has finished, so a join can only ever wait on a reader still
        # blocked on a pipe a detached descendant holds open. Such a reader is
        # a daemon thread that closes its own stream and is abandoned here,
        # because waiting for it would breach the configured bound.
        self._await_output(process, readers, buffers)
        return b"".join(buffers[0]), b"".join(buffers[1])

    def _run(self, *arguments: str) -> dict[str, Any]:
        config = self._config
        try:
            process = subprocess.Popen(
                [*config.argv, "--json", *arguments],
                cwd=config.project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
        except OSError as error:
            raise ControllerLaunchError(
                f"cannot run controller program {config.argv[0]}: {error}"
            ) from error
        # Not `with process:`: Popen.__exit__ closes the pipes, and closing a
        # pipe a reader thread is still blocked on waits out that read. The
        # readers close their own streams instead, and _capture always reaps
        # the controller, on its own wait or through _kill_group.
        stdout, stderr = self._capture(process)
        if process.returncode != 0:
            raise ControllerError(
                f"controller exited with status {process.returncode}: "
                f"{self._detail(stderr)}"
            )
        try:
            data = json.loads(stdout)
        except ValueError as error:
            raise ControllerOutputError(
                f"controller output is not valid JSON: {self._redact(str(error))}"
            ) from None
        if not isinstance(data, dict):
            raise ControllerOutputError("controller output must be a JSON object")
        return data

    def _check_package_version(self, pinned: str, live: str) -> None:
        """Accept the pinned version itself or the pinned version plus a build tag."""
        prefix = f"{pinned}+"
        if live == pinned or (live.startswith(prefix) and len(live) > len(prefix)):
            return
        raise IncompatibleContractError(
            f"controller package_version {self._bounded(live)!r} "
            f"does not match pinned {pinned!r}"
        )

    def _pinned_contract(self) -> dict[str, Any]:
        """The pinned bundle, digest-checked and validated before any spawn."""
        pinned_path = self._config.contract_bundle
        pinned, _ = _validated_bundle(pinned_path, self._config.bundle_digest)
        for field in REQUIRED_CONTRACT_STRINGS:
            _pinned_string(pinned, field)
        for field in ADVERTISED_CONTRACT_FIELDS:
            _pinned_names(pinned, field)
        return pinned

    def contract(self) -> ControllerContract:
        """Return the live contract once it matches the pinned bundle."""
        if self._contract is not None:
            return self._contract
        pinned = self._pinned_contract()
        live = self._run("contract")
        _live_string(live, "package_version", allow_empty=True)
        for field in ("schema_digest", "fixture_digest"):
            _live_string(live, field, allow_empty=False)
        operations = _string_set(live, "operations")
        capabilities = _string_set(live, "capabilities")
        major = live.get("protocol_major")
        if type(major) is not int or major != PROTOCOL_MAJOR:
            raise IncompatibleContractError(
                f"controller protocol_major {major!r} is not {PROTOCOL_MAJOR}"
            )
        for field in ("schema_digest", "fixture_digest"):
            if live.get(field) != pinned.get(field):
                raise IncompatibleContractError(
                    f"controller {field} {self._bounded(live[field])!r} does not match "
                    f"pinned {pinned.get(field)!r}"
                )
        version = live["package_version"]
        self._check_package_version(pinned["package_version"], version)
        _check_advertised("operations", pinned["operations"], operations)
        _check_advertised("capabilities", pinned["capabilities"], capabilities)
        self._contract = ControllerContract(
            protocol_major=major,
            package_version=version,
            schema_digest=live["schema_digest"],
            fixture_digest=live["fixture_digest"],
            operations=operations,
            capabilities=capabilities,
        )
        return self._contract

    def snapshot(self, *, workflow_id: str) -> dict[str, Any]:
        """Return the controller's snapshot payload unmodified."""
        _require_string(workflow_id, "workflow_id")
        self.contract()
        return self._run("snapshot", "--project-root", str(self._config.project_root))

    def apply(self, envelope: MutationEnvelope) -> ApplyResult:
        """Hand one mutation envelope to the controller in a private file."""
        actor_file = self._config.actor_file
        if actor_file is None:
            raise ControllerError("apply requires a configured actor_file")
        self.contract()
        request = _apply_request(envelope)
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
        except ControllerLaunchError:
            raise  # the controller never ran, so the mutation did not happen
        except ControllerError as error:
            raise ApplyOutcomeUnknownError(envelope.request_id, str(error)) from error
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
            raise ApplyOutcomeUnknownError(
                envelope.request_id, "controller apply response is malformed"
            )
        return ApplyResult(ok, revision, result, error_code, retryable)
