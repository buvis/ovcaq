from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    USAGE = "usage"
    INVALID_STATE = "invalid_state"
    STATE_IO = "state_io"
    FUTURE_SCHEMA = "future_schema"
    STATE_EXISTS = "state_exists"
    INVALID_BACKUP = "invalid_backup"
    REVISION_CONFLICT = "revision_conflict"
    INVALID_PATH = "invalid_path"
    PROTECTED_PATH = "protected_path"
    DURABILITY_UNSUPPORTED = "durability_unsupported"
    RESOURCE_LIMIT = "resource_limit"
    OVERSIZED_PLAN = "oversized_plan"
    RUNTIME_FORMAT = "runtime_format"
    PROCESS_PROBE = "process_probe"


EXIT_CODES: dict[ErrorCode, int] = {
    ErrorCode.USAGE: 1,
    ErrorCode.INVALID_STATE: 1,
    ErrorCode.STATE_IO: 2,
    ErrorCode.FUTURE_SCHEMA: 6,
    ErrorCode.STATE_EXISTS: 7,
    ErrorCode.INVALID_BACKUP: 8,
    ErrorCode.REVISION_CONFLICT: 9,
    ErrorCode.INVALID_PATH: 1,
    ErrorCode.PROTECTED_PATH: 1,
    ErrorCode.DURABILITY_UNSUPPORTED: 10,
    ErrorCode.RESOURCE_LIMIT: 11,
    ErrorCode.OVERSIZED_PLAN: 3,
    ErrorCode.RUNTIME_FORMAT: 1,
    ErrorCode.PROCESS_PROBE: 12,
}


class CommandError(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        path: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.path = path

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.code]
