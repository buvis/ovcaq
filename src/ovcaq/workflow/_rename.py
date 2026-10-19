"""Atomic, non-overwriting lifecycle moves on the supported macOS platform."""

from __future__ import annotations

import ctypes
import errno
import os


def rename_exclusive(
    source: str, destination: str, *, src_dir_fd: int, dst_dir_fd: int
) -> None:
    """Publish a move only if the destination is absent at the rename syscall."""
    library = ctypes.CDLL(None, use_errno=True)
    try:
        rename = library.renameatx_np
    except AttributeError as error:
        raise OSError(
            errno.ENOTSUP, "exclusive lifecycle rename is unavailable"
        ) from error
    rename.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    rename.restype = ctypes.c_int
    # Darwin sys/stdio.h: RENAME_EXCL fails atomically if the destination exists.
    if rename(
        src_dir_fd, os.fsencode(source), dst_dir_fd, os.fsencode(destination), 0x4
    ):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), destination)
