"""Persistent advisory ownership of a runtime."""

from __future__ import annotations

import ctypes
import ctypes.util
import errno
import fcntl
import json
import os
import secrets
import stat
import struct
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Self

from ovcaq.errors import CommandError, ErrorCode
from ovcaq.state.schema import MAX_STATE_BYTES, decode_json, validate_timestamp


class DuplicateRunError(RuntimeError):
    """Another owner already holds the run lock."""


@contextmanager
def observe_unowned_run(path: Path) -> Iterator[None]:
    """Check an idle lock before and after reads without competing for ownership."""
    descriptor = os.open(
        path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    )
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError(f"Run lock is not a regular file: {path}")
        if run_lock_held(path):
            raise OSError(f"Run lock is held during observation: {path}")
        if not os.path.samestat(opened, path.lstat()):
            raise OSError(f"Run lock changed during observation: {path}")
        yield
        if run_lock_held(path) or not os.path.samestat(opened, path.lstat()):
            raise OSError(f"Run lock changed during observation: {path}")
    finally:
        os.close(descriptor)


def run_lock_held(path: Path, *, directory: int | None = None) -> bool:
    """Query the persistent macOS flock without becoming a competing owner."""
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            dir_fd=directory,
        )
    except FileNotFoundError:
        return False
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError(f"Run lock is not a regular file: {path}")
        if sys.platform != "darwin":
            raise OSError("Run lock observation requires macOS")
        # Darwin reports flock locks through F_GETLK (with owner pid -1).
        query = struct.pack("qqihh", 0, 0, 0, fcntl.F_WRLCK, os.SEEK_SET)
        result = fcntl.fcntl(descriptor, fcntl.F_GETLK, query)
        observed = os.stat(path, dir_fd=directory, follow_symlinks=False)
        if not os.path.samestat(opened, observed):
            raise OSError(f"Run lock changed during observation: {path}")
        return bool(struct.unpack("qqihh", result)[3] != fcntl.F_UNLCK)
    finally:
        os.close(descriptor)


class RunLock:
    """Hold one persistent lock inode until explicitly closed."""

    def __init__(self, descriptor: int) -> None:
        self._descriptor: int | None = descriptor

    @classmethod
    def acquire(cls, path: Path) -> Self:
        descriptor = os.open(
            path,
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            0o600,
        )
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise OSError(f"Run lock is not a regular file: {path}")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise DuplicateRunError(f"Run lock is already held: {path}") from error
            observed = path.lstat()
            if (opened.st_dev, opened.st_ino) != (observed.st_dev, observed.st_ino):
                raise OSError(f"Run lock changed during acquisition: {path}")
            os.fchmod(descriptor, 0o600)
            return cls(descriptor)
        except BaseException:
            os.close(descriptor)
            raise

    def close(self) -> None:
        """Release ownership without removing the persistent lock file."""
        if self._descriptor is not None:
            descriptor, self._descriptor = self._descriptor, None
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    started: str


# Darwin <sys/proc_info.h>: struct proc_bsdinfo, naturally aligned fields.
PROC_PIDTBSDINFO = 3
PROC_BSDINFO_SIZE = 136
PBI_STATUS_OFFSET = 4
PBI_PID_OFFSET = 12
PBI_START_TVSEC_OFFSET = 120
PBI_START_TVUSEC_OFFSET = 128
SZOMB = 5


def _libproc() -> ctypes.CDLL:
    """Load libproc, or raise the typed probe failure."""
    platform = sys.platform
    if platform != "darwin":
        raise CommandError(
            ErrorCode.PROCESS_PROBE,
            f"Process probe requires macOS, not {platform}; run ovcaq doctor",
        )
    path = ctypes.util.find_library("proc")
    if path is None:
        raise CommandError(
            ErrorCode.PROCESS_PROBE,
            f"Process probe library libproc is missing on {platform}; run ovcaq doctor",
        )
    try:
        library = ctypes.CDLL(path, use_errno=True)
        probe = library.proc_pidinfo
    except (OSError, AttributeError) as error:
        raise CommandError(
            ErrorCode.PROCESS_PROBE,
            f"Process probe library {path} is unusable on {platform}: {error}; "
            "run ovcaq doctor",
        ) from error
    probe.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    probe.restype = ctypes.c_int
    return library


def process_identity(pid: int) -> ProcessIdentity | None:
    """Observe a live process and its start token without signalling it."""
    if pid <= 0:
        return None
    library = _libproc()
    buffer = ctypes.create_string_buffer(PROC_BSDINFO_SIZE)
    ctypes.set_errno(0)
    written = library.proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, buffer, PROC_BSDINFO_SIZE)
    if written == 0:
        denied = ctypes.get_errno()
        if denied in (errno.EPERM, errno.EACCES):
            raise CommandError(
                ErrorCode.PROCESS_PROBE,
                f"Process probe for pid {pid} on {sys.platform} was denied "
                f"({errno.errorcode.get(denied, denied)}); run ovcaq doctor",
            )
        return None
    if written != PROC_BSDINFO_SIZE:
        raise CommandError(
            ErrorCode.PROCESS_PROBE,
            f"Process probe for pid {pid} on {sys.platform} returned {written} bytes "
            f"instead of {PROC_BSDINFO_SIZE}; run ovcaq doctor",
        )
    record = buffer.raw
    (status,) = struct.unpack_from("=I", record, PBI_STATUS_OFFSET)
    (reported,) = struct.unpack_from("=I", record, PBI_PID_OFFSET)
    if reported != pid:
        raise CommandError(
            ErrorCode.PROCESS_PROBE,
            f"Process probe for pid {pid} on {sys.platform} described pid {reported}; "
            "run ovcaq doctor",
        )
    if status == SZOMB:
        return None
    (tvsec,) = struct.unpack_from("=Q", record, PBI_START_TVSEC_OFFSET)
    (tvusec,) = struct.unpack_from("=Q", record, PBI_START_TVUSEC_OFFSET)
    return ProcessIdentity(pid=pid, started=f"{tvsec}.{tvusec:06d}")


def process_matches(identity: ProcessIdentity) -> bool:
    return process_identity(identity.pid) == identity


@dataclass(frozen=True)
class FleetEntry:
    schema_version: int
    root: Path
    pid: int
    process_start: str
    run_id: str
    agent: str
    started_at: str


@dataclass(frozen=True, slots=True)
class FleetRun:
    run_id: str
    root: Path
    agent: str
    started_at: str
    pid: int
    process_start: str

    @classmethod
    def from_entry(cls, entry: FleetEntry) -> FleetRun:
        return cls(
            entry.run_id,
            entry.root,
            entry.agent,
            entry.started_at,
            entry.pid,
            entry.process_start,
        )


@dataclass(frozen=True)
class RegistrySnapshot:
    live: tuple[FleetEntry, ...]
    malformed: tuple[Path, ...]
    stale: tuple[Path, ...]


def _validate_run_id(run_id: str) -> None:
    if not run_id or run_id in {".", ".."} or "/" in run_id or "\x00" in run_id:
        raise ValueError("run_id must be a single nonempty filename component")


def _decode_entry(value: object) -> FleetEntry:
    if not isinstance(value, dict) or set(value) != {
        field.name for field in fields(FleetEntry)
    }:
        raise ValueError("Invalid fleet entry fields")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ValueError("Unsupported fleet schema version")
    if type(value["pid"]) is not int or value["pid"] <= 0:
        raise ValueError("Fleet pid must be a positive integer")
    for name in ("root", "process_start", "run_id", "agent", "started_at"):
        if not isinstance(value[name], str) or not value[name]:
            raise ValueError(f"Fleet {name} must be a nonempty string")
    _validate_run_id(value["run_id"])
    validate_timestamp(value["started_at"], "started_at")
    return FleetEntry(
        schema_version=value["schema_version"],
        root=Path(value["root"]),
        pid=value["pid"],
        process_start=value["process_start"],
        run_id=value["run_id"],
        agent=value["agent"],
        started_at=value["started_at"],
    )


def _read_entry(path: Path, directory: int) -> FleetEntry:
    descriptor = os.open(
        path.name,
        os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
        dir_fd=directory,
    )
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Fleet entry is not a regular file")
        encoded = stream.read(MAX_STATE_BYTES + 1)
    if len(encoded) > MAX_STATE_BYTES:
        raise ValueError("Fleet entry exceeds size limit")
    entry = _decode_entry(decode_json(encoded.decode("utf-8"), source=str(path)))
    if path.name != f"{entry.run_id}.json":
        raise ValueError("Fleet filename does not match run_id")
    return entry


class FleetRegistry:
    """Publish durable fleet records; snapshots never take mutation locks."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._root_identity: os.stat_result | None = None
        self._lock_identity: os.stat_result | None = None

    def _verify_root(self, directory: int) -> None:
        try:
            observed = self.root.lstat()
        except OSError as error:
            raise ValueError("Fleet root is no longer accessible") from error
        opened = os.fstat(directory)
        if (
            not stat.S_ISDIR(observed.st_mode)
            or not os.path.samestat(opened, observed)
            or (
                self._root_identity is not None
                and not os.path.samestat(opened, self._root_identity)
            )
        ):
            raise ValueError("Fleet root changed")
        self._root_identity = opened

    @contextmanager
    def _directory(self, *, create: bool = False) -> Iterator[int | None]:
        if create and self._root_identity is None:
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            directory = os.open(
                self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            )
        except FileNotFoundError as error:
            if self._root_identity is not None or create:
                raise ValueError("Fleet root disappeared") from error
            yield None
            return
        except OSError as error:
            raise ValueError("Fleet root is not a real directory") from error
        try:
            self._verify_root(directory)
            yield directory
        finally:
            os.close(directory)

    @contextmanager
    def _mutation(self, directory: int, *, private: bool = True) -> Iterator[None]:
        descriptor = os.open(
            "fleet.lock",
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            0o600,
            dir_fd=directory,
        )
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError("Fleet lock is not a regular file")
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            self._verify_root(directory)
            observed = os.stat("fleet.lock", dir_fd=directory, follow_symlinks=False)
            if not os.path.samestat(opened, observed) or (
                self._lock_identity is not None
                and not os.path.samestat(opened, self._lock_identity)
            ):
                raise ValueError("Fleet lock changed during acquisition")
            self._lock_identity = opened
            os.fchmod(descriptor, 0o600)
            if private:
                os.fchmod(directory, 0o700)
            yield
        finally:
            os.close(descriptor)

    @contextmanager
    def guard_mutation(
        self, validate: Callable[[], object]
    ) -> Iterator[Callable[[], None]]:
        """Exclude ownership changes while validating a state publication.

        Acquire this context before the state transaction. The validator must
        not acquire or read the state store; the yielded guard runs under its
        lock and keeps this registry exclusion held through rollback.
        """
        with self._directory(create=True) as directory:
            assert directory is not None
            with self._mutation(directory, private=False):
                identity = self._lock_identity
                assert identity is not None

                def guard() -> None:
                    self._verify_root(directory)
                    observed = os.stat(
                        "fleet.lock", dir_fd=directory, follow_symlinks=False
                    )
                    if not os.path.samestat(identity, observed):
                        raise ValueError("Fleet lock changed during guarded mutation")
                    validate()

                guard()
                yield guard

    def publish(self, entry: FleetEntry) -> Path:
        document = asdict(entry)
        document["root"] = str(entry.root)
        _decode_entry(document)
        encoded = json.dumps(document).encode("utf-8")
        if len(encoded) > MAX_STATE_BYTES:
            raise ValueError("Fleet entry exceeds size limit")
        destination = self.root / f"{entry.run_id}.json"
        with self._directory(create=True) as directory:
            assert directory is not None
            with self._mutation(directory):
                temporary = f"{secrets.token_hex(16)}.tmp"
                descriptor = os.open(
                    temporary,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                    0o600,
                    dir_fd=directory,
                )
                try:
                    with os.fdopen(descriptor, "wb") as stream:
                        stream.write(encoded)
                        stream.flush()
                        os.fsync(stream.fileno())
                    self._verify_root(directory)
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
        return destination

    def _scan(
        self, directory: int
    ) -> tuple[RegistrySnapshot, dict[Path, os.stat_result]]:
        live: list[FleetEntry] = []
        malformed: list[Path] = []
        stale: list[Path] = []
        identities: dict[Path, os.stat_result] = {}
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = self.root / name
            try:
                identities[path] = os.stat(
                    name, dir_fd=directory, follow_symlinks=False
                )
                entry = _read_entry(path, directory)
            except FileNotFoundError:
                continue
            except (OSError, ValueError):
                malformed.append(path)
                continue
            if process_matches(ProcessIdentity(entry.pid, entry.process_start)):
                live.append(entry)
            else:
                stale.append(path)
        self._verify_root(directory)
        return RegistrySnapshot(tuple(live), tuple(malformed), tuple(stale)), identities

    def snapshot(self) -> RegistrySnapshot:
        with self._directory() as directory:
            if directory is None:
                return RegistrySnapshot((), (), ())
            return self._scan(directory)[0]

    def remove(self, run_id: str, *, expected: FleetEntry | None = None) -> bool:
        _validate_run_id(run_id)
        path = self.root / f"{run_id}.json"
        with self._directory() as directory:
            if directory is None:
                return False
            with self._mutation(directory, private=False):
                try:
                    if (
                        expected is not None
                        and _read_entry(path, directory) != expected
                    ):
                        return False
                    os.unlink(path.name, dir_fd=directory)
                except (OSError, ValueError):
                    return False
                os.fsync(directory)
        return True

    def prune(self) -> RegistrySnapshot:
        with self._directory(create=True) as directory:
            assert directory is not None
            snapshot, identities = self._scan(directory)
            with self._mutation(directory):
                current, current_identities = self._scan(directory)
                discarded = set(current.malformed + current.stale)
                removed = False
                for path in snapshot.malformed + snapshot.stale:
                    if (
                        path not in discarded
                        or path not in identities
                        or path not in current_identities
                        or not os.path.samestat(
                            identities[path], current_identities[path]
                        )
                    ):
                        continue
                    try:
                        observed = os.stat(
                            path.name, dir_fd=directory, follow_symlinks=False
                        )
                        if not os.path.samestat(current_identities[path], observed):
                            continue
                        os.unlink(path.name, dir_fd=directory)
                    except FileNotFoundError:
                        continue
                    removed = True
                if removed:
                    os.fsync(directory)
                return self._scan(directory)[0]
