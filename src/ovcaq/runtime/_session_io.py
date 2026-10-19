"""Private record encoding and atomic publication for session evidence."""

from __future__ import annotations

import json
import os
import stat
from contextlib import ExitStack
from pathlib import Path
from uuid import uuid4

from ovcaq.state.schema import MAX_STATE_BYTES, validate_json_value


def _encode_record(record: dict[str, object]) -> bytes:
    validate_json_value(record, "record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ValueError("record schema_version must be integer 1")
    payload = (json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n").encode(
        "utf-8"
    )
    if len(payload) > MAX_STATE_BYTES:
        raise ValueError("record exceeds the maximum document size")
    return payload


def _private_directory(
    path: Path,
    stack: ExitStack,
    *,
    identities: tuple[tuple[Path, int, int], ...] = (),
    private: tuple[Path, ...] = (),
    create: bool = True,
) -> int:
    expected = {item: (device, inode) for item, device, inode in identities}
    descriptor: int | None = None
    for directory in (*reversed(path.parents), path):
        name = directory.name if descriptor is not None else str(directory)
        try:
            information = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            if directory in expected:
                raise ValueError(f"directory changed since resolution: {directory}")
            if not create:
                raise
            os.mkdir(name, mode=0o700, dir_fd=descriptor)
            information = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
        if not stat.S_ISDIR(information.st_mode) or (
            directory in expected
            and (information.st_dev, information.st_ino) != expected[directory]
        ):
            raise ValueError(f"not a regular directory: {directory}")
        descriptor = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=descriptor,
        )
        stack.callback(os.close, descriptor)
        if not os.path.samestat(information, os.fstat(descriptor)):
            raise ValueError(f"directory changed while opening: {directory}")
        if create and (directory == path or directory in private):
            os.fchmod(descriptor, 0o700)
    assert descriptor is not None
    return descriptor


def _publish(
    destination: Path,
    payload: bytes,
    *,
    directory: int | None = None,
    identities: tuple[tuple[Path, int, int], ...] = (),
) -> None:
    with ExitStack() as stack:
        if directory is None:
            directory = _private_directory(
                destination.parent, stack, identities=identities
            )
        try:
            information = os.stat(
                destination.name, dir_fd=directory, follow_symlinks=False
            )
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISREG(information.st_mode):
                raise ValueError(f"not a regular record file: {destination}")
        temporary = f".{destination.name}.{uuid4().hex}"
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory,
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(
                temporary,
                destination.name,
                src_dir_fd=directory,
                dst_dir_fd=directory,
            )
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
