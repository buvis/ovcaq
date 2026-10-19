"""Configuration-driven Codex launch adapter."""

import hashlib
import json
import logging
import os
import selectors
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from time import monotonic

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import DriverHealth, LaunchRequest, LaunchSpec
from ovcaq.drivers.codex_events import (
    bounded_detail,
    classify_failure,
    failure_reset,
    item_activity,
    item_lanes,
    item_tool,
    turn_usage,
)
from ovcaq.events import Observation, SessionSummary
from ovcaq.events.model import (
    PROTOCOL_VERSION,
    FailureClass,
    JSONValue,
    ObservationType,
    Usage,
    sanitize_text,
)
from ovcaq.events.reducer import reduce_session

logger = logging.getLogger(__name__)

_PINNED_VERSION = "0.160.0"
_PROBE_OUTPUT_LIMIT = 16 * 1024


def _run_probe_command(
    command: tuple[str, ...], environment: dict[str, str]
) -> tuple[int, bytearray, bytearray]:
    deadline = monotonic() + 5
    with (
        subprocess.Popen(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        ) as process,
        selectors.DefaultSelector() as selector,
    ):
        assert process.stdout is not None and process.stderr is not None
        stdout, stderr = bytearray(), bytearray()
        buffers = {
            process.stdout.fileno(): stdout,
            process.stderr.fileno(): stderr,
        }
        for stream in (process.stdout, process.stderr):
            selector.register(stream, selectors.EVENT_READ)
        try:
            while selector.get_map():
                remaining = deadline - monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(process.args, 5)
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fd, 4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    buffer = buffers[key.fd]
                    buffer.extend(chunk[: _PROBE_OUTPUT_LIMIT - len(buffer)])
            exit_code = process.wait(timeout=max(0, deadline - monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
    return exit_code, stdout, stderr


def _probe_failure(
    executable: str, label: str, exit_code: int, stdout: bytearray, stderr: bytearray
) -> DriverHealth:
    diagnostics = sanitize_text(
        stdout.decode("utf-8", errors="replace")
        + "\n"
        + stderr.decode("utf-8", errors="replace")
    ).strip()
    hint = "; run codex login" if label == "authentication" else ""
    detail = (
        f"{executable}: {label} check failed (exit code {exit_code})"
        f"{hint}: {diagnostics}"
    )
    return DriverHealth(
        False,
        detail.encode("utf-8")[:_PROBE_OUTPUT_LIMIT].decode("utf-8", errors="ignore"),
    )


_DEFAULT_PROMPT = """Read the committed OVCAQ state to determine the current phase. Use `ovcaq state`
and `ovcaq workflow` commands for all durable mutations. Perform only the
current phase, commit exactly one successful phase handoff through the OVCAQ
workflow command, then exit the session. Never edit state.json directly. Do not
start a second phase in this session. Completion is determined by committed
state, not your final message. Do not install, upgrade, or modify launcher
plugins or marketplace content."""


class CodexDriver:
    name = "codex"

    def __init__(self, settings: AgentSettings, *, run_id: str) -> None:
        options = settings.options
        unknown = options.keys() - {"sandbox", "approval", "allow_explicit_model"}
        if unknown:
            raise ValueError(f"Unknown Codex options: {sorted(unknown)}")
        if options.get("sandbox", "workspace-write") != "workspace-write":
            raise ValueError("Codex sandbox must be workspace-write")
        if options.get("approval", "never") != "never":
            raise ValueError("Codex approval must be never")
        if type(options.get("allow_explicit_model", False)) is not bool:
            raise ValueError("Codex allow_explicit_model must be a boolean")
        self._settings = settings
        self._run_id = run_id
        self._session_id: str | None = None
        self._usage = Usage()
        self._thread_conflict = False
        self._identities: dict[tuple[str, str], bool] = {}

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        settings = self._settings
        model = request.model
        if model is not None:
            if model in settings.tiers:
                model = settings.tiers[model]
            elif model not in settings.tiers.values() and not settings.options.get(
                "allow_explicit_model", False
            ):
                raise ValueError(f"Unknown Codex model: {model}")
        effort_arguments: tuple[str, ...] = ()
        effort = request.effort
        if effort is not None:
            if not effort.strip():
                raise ValueError("Codex effort must be nonblank")
            if effort in {"low", "medium", "high", "xhigh"}:
                effort_arguments = ("-c", f'model_reasoning_effort="{effort}"')
            else:
                logger.warning("Unmapped Codex effort: %s", effort)
        self._session_id = None
        self._usage = Usage()
        self._thread_conflict = False
        self._identities.clear()
        return LaunchSpec(
            argv=(
                *settings.command,
                "--ask-for-approval",
                "never",
                "exec",
                "--json",
                "--sandbox",
                "workspace-write",
                "-C",
                str(request.root),
                *(("-m", model) if model is not None else ()),
                *effort_arguments,
                "--",
                request.prompt,
            ),
            env=dict(settings.environment),
            cwd=request.root,
            raw_format="codex-exec-json-v1",
        )

    def probe(self) -> DriverHealth:
        executable = sanitize_text(self._settings.command[0])[:1024]
        environment = dict(os.environ) | dict(self._settings.environment)
        for label, operation in (
            ("version", ("--version",)),
            ("authentication", ("login", "status")),
        ):
            try:
                exit_code, stdout, stderr = _run_probe_command(
                    (*self._settings.command, *operation), environment
                )
            except subprocess.TimeoutExpired:
                return DriverHealth(
                    False, f"{executable}: {label} check timed out after 5 seconds"
                )
            except OSError:
                return DriverHealth(False, f"{executable}: executable unavailable")
            if exit_code != 0:
                return _probe_failure(executable, label, exit_code, stdout, stderr)
            if label == "version":
                text = stdout.decode("utf-8", errors="replace")
                version = text.splitlines()[0] if text else ""
                if version != f"codex-cli {_PINNED_VERSION}":
                    detail = (
                        f"observed {sanitize_text(version[10:])[:1024]}"
                        if version.startswith("codex-cli ")
                        else "missing Codex version"
                    )
                    return DriverHealth(
                        False,
                        f"{executable}: {detail}; pinned {_PINNED_VERSION}; "
                        "refresh the Codex fixture contract",
                    )
        return DriverHealth(
            True, f"{executable}: Codex {_PINNED_VERSION}; authentication verified"
        )

    def decode(self, raw_line: str) -> tuple[Observation, ...]:
        timestamp = datetime.now(UTC)
        kind = ObservationType.RAW_UNKNOWN
        payload: dict[str, JSONValue] = {
            "reason": "Malformed or unsupported Codex record",
            "raw_sha256": hashlib.sha256(raw_line.encode()).hexdigest(),
            "preview": sanitize_text(raw_line)[:512],
        }
        try:
            record = json.loads(raw_line)
        except (ValueError, RecursionError):
            record = None
        if isinstance(record, dict):
            event = record.get("type")
            if event == "thread.started":
                thread_id = record.get("thread_id")
                if isinstance(thread_id, str) and thread_id:
                    kind = ObservationType.SESSION_STARTED
                    started = replace(
                        self._observation(kind, {}, timestamp),
                        session_id=thread_id,
                    )
                    conflict = self._session_id not in (None, thread_id)
                    self._thread_conflict = self._thread_conflict or conflict
                    usage = Usage() if conflict else self._usage
                    self._session_id = thread_id
                    self._usage = usage
                    return (started,)
            elif event == "turn.started":
                kind = ObservationType.ACTIVITY_MESSAGE
                payload = {"kind": "turn"}
            elif event in ("item.started", "item.updated", "item.completed"):
                try:
                    return self._item_observations(
                        record.get("item"), event, timestamp, payload
                    )
                except (ValueError, RecursionError):
                    payload["reason"] = "Malformed or invalid JSON in Codex item"
            elif event == "turn.completed":
                return self._usage_observations(record.get("usage"), timestamp, payload)
            elif event in ("error", "turn.failed"):
                failure = self._failure_observations(record, event, timestamp)
                if failure is not None:
                    return failure
        return (self._observation(kind, payload, timestamp),)

    def _failure_observations(
        self,
        record: dict[str, JSONValue],
        event: str,
        timestamp: datetime,
    ) -> tuple[Observation, ...] | None:
        source = record if event == "error" else record.get("error")
        detail = source.get("message") if isinstance(source, dict) else None
        if isinstance(detail, str):
            failure_class = classify_failure(detail)
            reset = failure_reset(detail, timestamp)
            detail = bounded_detail(detail)
            reset_at = reset.isoformat() if reset is not None else None
            if event == "error":
                return (
                    self._observation(
                        ObservationType.ACTIVITY_MESSAGE,
                        {
                            "kind": "error",
                            "detail": detail,
                            "failure_class": failure_class.value,
                            "reset_at": reset_at,
                        },
                        timestamp,
                    ),
                )
            terminal = self._observation(
                ObservationType.SESSION_FAILED,
                {"failure_class": failure_class.value, "detail": detail},
                timestamp,
            )
            if failure_class == FailureClass.RATE_LIMIT:
                return (
                    terminal,
                    self._observation(
                        ObservationType.RATE_LIMIT_STARTED,
                        {"reset_at": reset_at, "window": None, "detail": detail},
                        timestamp,
                    ),
                )
            return (terminal,)
        return None

    def _usage_observations(
        self,
        native: object,
        timestamp: datetime,
        raw_payload: dict[str, JSONValue],
    ) -> tuple[Observation, ...]:
        snapshot, gap = turn_usage(native)
        if self._thread_conflict:
            gap = "; ".join(
                reason for reason in (gap, "Conflicting thread identity") if reason
            )
        values = asdict(self._usage)
        for name, value in asdict(snapshot).items():
            if name == "estimated":
                values[name] = values[name] or value
            elif value is not None:
                previous = values[name]
                values[name] = value if previous is None else max(previous, value)
        cumulative = Usage(**values)
        serialized = asdict(cumulative)
        observations = [
            self._observation(
                ObservationType.USAGE_UPDATED,
                {
                    "usage": serialized,
                    "identity": f"thread:{self._session_id or 'unknown'}",
                },
                timestamp,
            ),
            self._observation(
                ObservationType.SESSION_COMPLETED, {"usage": serialized}, timestamp
            ),
        ]
        if gap is not None:
            observations.append(
                self._observation(
                    ObservationType.RAW_UNKNOWN,
                    raw_payload | {"reason": gap},
                    timestamp,
                )
            )
        self._usage = cumulative
        self._thread_conflict = False
        return tuple(observations)

    def _item_observations(
        self,
        item: object,
        event: str,
        timestamp: datetime,
        raw_payload: dict[str, JSONValue],
    ) -> tuple[Observation, ...]:
        activity = item_activity(item)
        if activity is not None:
            return (
                self._observation(
                    ObservationType.ACTIVITY_MESSAGE, activity, timestamp
                ),
            )
        tool = item_tool(item, event)
        if tool is None:
            return (
                self._observation(ObservationType.RAW_UNKNOWN, raw_payload, timestamp),
            )
        kind, payload = tool
        observations = [self._observation(kind, payload, timestamp)]
        projected, has_unknown = item_lanes(
            item,
            {
                lane_id
                for (category, lane_id), done in self._identities.items()
                if category == "lane" and not done
            },
        )
        if has_unknown:
            observations.append(
                self._observation(ObservationType.RAW_UNKNOWN, raw_payload, timestamp)
            )
        for lane_id, lane_kind, lane_payload in projected:
            if self._identities.get(("lane", lane_id)):
                continue
            if (
                lane_kind == ObservationType.LANE_PROGRESS
                and ("lane", lane_id) not in self._identities
            ):
                lane_kind = ObservationType.LANE_STARTED
            observations.append(
                self._observation(lane_kind, lane_payload, timestamp, lane_id)
            )
        gaps = self._remember(observations, raw_payload, timestamp)
        return (*gaps, *observations)

    def _remember(
        self,
        observations: list[Observation],
        raw_payload: dict[str, JSONValue],
        timestamp: datetime,
    ) -> list[Observation]:
        gaps: list[Observation] = []
        identities = self._identities.copy()
        for observation in observations:
            if observation.lane_id is not None:
                identity = ("lane", observation.lane_id)
            elif observation.type.startswith("tool."):
                tool_id = observation.payload["tool_id"]
                assert isinstance(tool_id, str)
                identity = ("item", tool_id)
            else:
                continue
            if identity not in identities and len(identities) == 4096:
                evicted = next(
                    (key for key, done in identities.items() if done),
                    next(iter(identities)),
                )
                gap_payload = raw_payload | {
                    "reason": "Identity capacity gap; evicted "
                    + evicted[0]
                    + " "
                    + sanitize_text(evicted[1])[:512]
                }
                gaps.append(
                    self._observation(
                        ObservationType.RAW_UNKNOWN, gap_payload, timestamp
                    )
                )
                del identities[evicted]
            identities[identity] = observation.type in (
                ObservationType.TOOL_COMPLETED,
                ObservationType.TOOL_FAILED,
                ObservationType.LANE_COMPLETED,
                ObservationType.LANE_FAILED,
            )
        self._identities = identities
        return gaps

    def _observation(
        self,
        kind: ObservationType,
        payload: dict[str, JSONValue],
        timestamp: datetime,
        lane_id: str | None = None,
    ) -> Observation:
        return Observation(
            protocol_version=PROTOCOL_VERSION,
            timestamp=timestamp,
            provider=self.name,
            run_id=self._run_id,
            session_id=self._session_id,
            lane_id=lane_id,
            type=kind,
            payload=payload,
        )

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        reduction = reduce_session(observations, exit_code)
        if any(
            observation.type
            in (
                ObservationType.SESSION_COMPLETED,
                ObservationType.SESSION_FAILED,
            )
            for observation in reduction.observations
        ):
            return reduction.summary
        for observation in reversed(reduction.observations):
            payload = observation.payload
            if (
                observation.type == ObservationType.ACTIVITY_MESSAGE
                and payload.get("kind") == "error"
                and "failure_class" in payload
            ):
                failure_class = FailureClass(str(payload["failure_class"]))
                fallback = [
                    replace(
                        observation,
                        type=ObservationType.SESSION_FAILED,
                        payload={
                            "failure_class": failure_class.value,
                            "detail": payload["detail"],
                        },
                    )
                ]
                if failure_class == FailureClass.RATE_LIMIT:
                    fallback.append(
                        replace(
                            observation,
                            type=ObservationType.RATE_LIMIT_STARTED,
                            payload={
                                "reset_at": payload.get("reset_at"),
                                "window": None,
                                "detail": payload["detail"],
                            },
                        )
                    )
                return reduce_session(
                    (*reduction.observations, *fallback), exit_code
                ).summary
        return reduction.summary

    def default_prompt(self, phase: str) -> str:
        if phase not in {"build", "review", "done"}:
            raise ValueError(f"Unknown Codex prompt phase: {phase}")
        return f"$run-autopilot\n{_DEFAULT_PROMPT}"
