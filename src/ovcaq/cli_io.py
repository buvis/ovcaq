"""Shared CLI payload and workflow result types."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ovcaq.errors import CommandError, ErrorCode
from ovcaq.runtime.session import SessionMetadata, parse_session_metadata
from ovcaq.state.schema import (
    MAX_COMMAND_PAYLOAD_BYTES,
    JSONValue,
    ResourceLimitError,
    decode_json,
    validate_timestamp,
)


def _read_payload(path: Path) -> bytes:
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY
            | os.O_NONBLOCK
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError(f"not a regular file: {path}")
            payload = stream.read(MAX_COMMAND_PAYLOAD_BYTES + 1)
    except OSError as error:
        raise CommandError(
            ErrorCode.USAGE,
            f"cannot read payload {path}: {error}",
        ) from error
    if len(payload) > MAX_COMMAND_PAYLOAD_BYTES:
        raise CommandError(
            ErrorCode.RESOURCE_LIMIT,
            f"payload exceeds {MAX_COMMAND_PAYLOAD_BYTES} bytes: {path}",
        )
    return payload


def _decode_text(payload: bytes, *, source: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CommandError(
            ErrorCode.USAGE,
            f"{source} is not UTF-8: {error}",
        ) from error


def _decode_json(text: str, *, source: str) -> JSONValue:
    if len(text.encode("utf-8")) > MAX_COMMAND_PAYLOAD_BYTES:
        raise CommandError(
            ErrorCode.RESOURCE_LIMIT,
            f"{source} exceeds {MAX_COMMAND_PAYLOAD_BYTES} bytes",
        )
    try:
        return decode_json(text, source=source)
    except ResourceLimitError:
        raise
    except ValueError as error:
        raise CommandError(
            ErrorCode.USAGE,
            f"invalid JSON in {source}: {error}",
        ) from error


def _json_file(path: Path) -> dict[str, JSONValue]:
    payload = _read_payload(path)
    value = _decode_json(_decode_text(payload, source=str(path)), source=str(path))
    if not isinstance(value, dict):
        raise CommandError(ErrorCode.USAGE, f"{path} must contain a JSON object")
    return value


def _runtime_timestamp(value: str) -> datetime:
    validate_timestamp(value, "metadata.started_at")
    return datetime.fromisoformat(value)


def _runtime_metadata(path: Path) -> SessionMetadata:
    try:
        return parse_session_metadata(_json_file(path))
    except (CommandError, ValueError, TypeError) as error:
        raise CommandError(
            ErrorCode.RUNTIME_FORMAT, str(error), path=str(path)
        ) from error


@dataclass(frozen=True)
class _WorkflowResult:
    value: JSONValue
    revision: int | None = None
    mutation: bool = False
    text: str | None = None
    status: str | None = None
    exit_code: int = 0
