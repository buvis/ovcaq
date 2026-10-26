from __future__ import annotations

import errno
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

_REAL_POPEN_INIT = subprocess.Popen.__init__


def _is_ps(argv: object) -> bool:
    program = argv[0] if isinstance(argv, (list, tuple)) and argv else argv
    if not isinstance(program, (str, bytes, os.PathLike)):
        return False
    return Path(os.fsdecode(program)).name == "ps"


@pytest.fixture(autouse=True)
def forbid_ps(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Deny every `ps` spawn, as the macOS sandbox this product runs in does."""

    def deny_ps(self: subprocess.Popen, *args: object, **kwargs: object) -> None:
        argv = args[0] if args else kwargs.get("args")
        if _is_ps(argv):
            # Popen.__del__ reads this flag the real __init__ never got to set.
            self._child_created = False
            raise PermissionError(errno.EPERM, "ps is denied")
        _REAL_POPEN_INIT(self, *args, **kwargs)

    monkeypatch.setattr(subprocess.Popen, "__init__", deny_ps)
    yield
