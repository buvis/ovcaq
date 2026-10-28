"""Claude command construction and normalized session summaries."""

import hashlib
import json
import math
import os
import shutil
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, replace
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any

from ovcaq.config import AgentSettings
from ovcaq.drivers.base import DriverHealth, LaunchRequest, LaunchSpec
from ovcaq.drivers.claude_events import (
    banner_reset,
    block_payload,
    failure_payload,
    init_payload,
    rate_limit_payload,
    record_timestamp,
    task_payload,
)
from ovcaq.events import (
    PROTOCOL_VERSION,
    Observation,
    ObservationType,
    SessionSummary,
    Usage,
    reduce_session,
    sanitize_text,
)
from ovcaq.events.model import JSONValue


class ClaudeDriver:
    name = "claude"
    default_tiers: Mapping[str, str] = MappingProxyType(
        {"standard": "sonnet", "deep": "opus"}
    )

    def __init__(self, settings: AgentSettings, *, run_id: str) -> None:
        options = settings.options
        if options.keys() - {
            "permission_mode",
            "allow_explicit_model",
            "fallback_model",
        }:
            raise ValueError("Unknown Claude driver option")
        if options.get("permission_mode") != "auto":
            raise ValueError("Claude permission_mode must be auto")
        if type(options.get("allow_explicit_model", False)) is not bool:
            raise ValueError("allow_explicit_model must be a boolean")
        if "fallback_model" in options and (
            not isinstance(options["fallback_model"], str)
            or not options["fallback_model"].strip()
        ):
            raise ValueError("fallback_model must be a nonblank string")
        defaults = {
            "CLAUDE_UNATTENDED": "1",
            "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS": "0",
        }
        for key, value in settings.environment.items():
            if key in defaults and value != defaults[key]:
                raise ValueError(f"Cannot override fixed Claude environment key: {key}")
        self._settings = replace(
            settings, tiers={**self.default_tiers, **settings.tiers}
        )
        self._run_id = run_id
        self._environment = defaults | dict(settings.environment)
        self._session_id: str | None = None
        self._limit_live = False
        self._messages: OrderedDict[str, dict[str, int]] = OrderedDict()
        self._message_totals: dict[str, int] = {}
        # Evicted IDs remain in a fixed Bloom filter. False positives can
        # conservatively undercount new messages, but never inflate replays.
        self._evicted = bytearray(1024 * 1024)

    def default_prompt(self, phase: str) -> str:
        if phase not in {"build", "review", "done"}:
            raise ValueError(f"Unknown phase: {phase}")
        return "/autopilot:run-autopilot"

    def probe(self) -> DriverHealth:
        command = self._settings.command[0]
        path = self._environment.get("PATH", os.environ.get("PATH", os.defpath))
        resolved = shutil.which(command, path=path)
        if resolved is None:
            return DriverHealth(
                False, f"Command is missing or not executable: {command}"
            )
        return DriverHealth(
            True, f"Executable command: {resolved}; permission_mode=auto"
        )

    def build_launch(self, request: LaunchRequest) -> LaunchSpec:
        settings = self._settings
        model = request.model
        if model is None:
            raise ValueError("Claude requires a model tier")
        if model in settings.tiers:
            model = settings.tiers[model]
        elif not settings.options.get("allow_explicit_model", False):
            raise ValueError(f"Unknown Claude model tier: {model}")
        if request.effort is None or not request.effort.strip():
            raise ValueError("Claude requires a nonblank effort")
        fallback_arguments: tuple[str, ...] = ()
        fallback_tier = settings.options.get("fallback_model")
        if isinstance(fallback_tier, str):
            if fallback_tier not in settings.tiers:
                raise ValueError(f"Unknown Claude fallback tier: {fallback_tier}")
            fallback_model = settings.tiers[fallback_tier]
            if fallback_model != model:
                fallback_arguments = ("--fallback-model", fallback_model)
        return LaunchSpec(
            argv=(
                *settings.command,
                "-p",
                "--permission-mode",
                "auto",
                "--model",
                model,
                "--effort",
                request.effort,
                *fallback_arguments,
                "--output-format",
                "stream-json",
                "--verbose",
                request.prompt,
            ),
            env=dict(self._environment),
            cwd=request.root,
            raw_format="claude-stream-json-v1",
        )

    def decode(self, raw_line: str) -> tuple[Observation, ...]:
        now = datetime.now(UTC)
        timestamp = now
        observations: list[Observation] = []
        try:
            record = json.loads(raw_line)
        except (ValueError, RecursionError):
            record = None
        if isinstance(record, dict):
            session_id = record.get("session_id")
            if isinstance(session_id, str) and session_id:
                self._session_id = session_id
            lane_id = record.get("parent_tool_use_id")
            if not isinstance(lane_id, str) or not lane_id:
                lane_id = None
            timestamp = record_timestamp(record, now)
            observations = self._decode_record(record, timestamp, now, lane_id)
        if not observations:
            observations.append(
                self._observation(
                    ObservationType.RAW_UNKNOWN,
                    {
                        "reason": "unrecognized Claude stream record",
                        "raw_sha256": hashlib.sha256(
                            raw_line.encode("utf-8", errors="replace")
                        ).hexdigest(),
                        "preview": sanitize_text(raw_line)[:512],
                    },
                    timestamp,
                )
            )
        return tuple(observations)

    def _decode_record(
        self,
        record: dict[str, Any],
        timestamp: datetime,
        now: datetime,
        lane_id: str | None,
    ) -> list[Observation]:
        kind, subtype = record.get("type"), record.get("subtype")
        if kind == "system" and subtype == "init":
            return [
                self._observation(
                    ObservationType.SESSION_STARTED, init_payload(record), timestamp
                )
            ]
        if kind in ("assistant", "user"):
            return self._decode_message(record, timestamp, lane_id)
        if kind == "system" and subtype in (
            "task_started",
            "task_progress",
            "task_notification",
            "task_updated",
            "background_tasks_changed",
        ):
            return self._decode_tasks(record, timestamp)
        if kind == "rate_limit_event":
            info = record.get("rate_limit_info")
            projected = (
                rate_limit_payload(info, now) if isinstance(info, dict) else None
            )
            if projected is not None:
                event, payload = projected
                if event == ObservationType.RATE_LIMIT_STARTED:
                    self._limit_live = payload["reset_at"] is not None
                elif event == ObservationType.RATE_LIMIT_CLEARED:
                    self._limit_live = False
                return [self._observation(event, payload, timestamp)]
        if kind == "result":
            return self._decode_result(record, timestamp)
        return []

    def _decode_message(
        self,
        record: dict[str, Any],
        timestamp: datetime,
        lane_id: str | None,
    ) -> list[Observation]:
        observations: list[Observation] = []
        message = record.get("message")
        if not isinstance(message, dict):
            return observations
        message_id = message.get("id")
        metadata: dict[str, JSONValue] = {}
        if isinstance(message_id, str) and message_id:
            metadata["message_id"] = message_id
        blocks = message.get("content")
        for block in blocks if isinstance(blocks, list) else ():
            if not isinstance(block, dict):
                continue
            projected = block_payload(block, metadata)
            if projected is not None:
                event, payload = projected
                observations.append(
                    self._observation(event, payload, timestamp, lane_id)
                )
        usage = message.get("usage")
        if isinstance(usage, dict) and metadata:
            identity = f"message:{message_id}"
            snapshot = self._update_usage(usage, identity)
            observations.append(
                self._observation(
                    ObservationType.USAGE_UPDATED,
                    {"identity": identity, "usage": snapshot},
                    timestamp,
                    lane_id,
                )
            )
        return observations

    def _decode_tasks(
        self,
        record: dict[str, Any],
        timestamp: datetime,
    ) -> list[Observation]:
        observations: list[Observation] = []
        subtype = record.get("subtype")
        tasks = (
            record.get("tasks") if subtype == "background_tasks_changed" else [record]
        )
        for task in tasks if isinstance(tasks, list) else ():
            if not isinstance(task, dict):
                continue
            projected = task_payload(task, subtype)
            if projected is not None:
                event, payload, task_id = projected
                observations.append(
                    self._observation(event, payload, timestamp, task_id)
                )
        return observations

    def _decode_result(
        self,
        record: dict[str, Any],
        timestamp: datetime,
    ) -> list[Observation]:
        observations: list[Observation] = []
        usage = record.get("usage")
        snapshot = None
        if isinstance(usage, dict):
            identity = f"result:{self._session_id}"
            snapshot = self._update_usage(
                usage, identity, cumulative=True, cost=record.get("total_cost_usd")
            )
            observations.append(
                self._observation(
                    ObservationType.USAGE_UPDATED,
                    {"identity": identity, "usage": snapshot},
                    timestamp,
                )
            )
        if record.get("is_error") is True or record.get("subtype") != "success":
            event = ObservationType.SESSION_FAILED
            payload = failure_payload(record.get("result"))
            reset_at = None
            if payload["failure_class"] == "rate_limit" and not self._limit_live:
                reset_at = banner_reset(
                    str(record.get("result")), timestamp, datetime.now(UTC)
                )
            if reset_at is not None:
                observations.append(
                    self._observation(
                        ObservationType.RATE_LIMIT_STARTED,
                        {
                            "reset_at": reset_at,
                            "window": None,
                            "detail": payload["detail"],
                        },
                        timestamp,
                    )
                )
        else:
            event = ObservationType.SESSION_COMPLETED
            payload = {"usage": snapshot} if snapshot is not None else {}
        observations.append(self._observation(event, payload, timestamp))
        return observations

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

    def _update_usage(
        self,
        values: dict[str, object],
        identity: str,
        *,
        cumulative: bool = False,
        cost: object = None,
    ) -> dict[str, JSONValue]:
        counters = {
            name: value
            for name, value in values.items()
            if name
            in (
                "input_tokens",
                "output_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
                "tool_uses",
            )
            and type(value) is int
            and value >= 0
        }
        if not cumulative:
            self._remember_usage(identity, counters)
            counters = self._message_totals
        snapshot = asdict(Usage(estimated=not cumulative))
        snapshot.update(counters)
        if (
            isinstance(cost, (int, float))
            and not isinstance(cost, bool)
            and math.isfinite(cost)
            and cost >= 0
        ):
            snapshot["cost_usd"] = float(cost)
        return snapshot

    def _remember_usage(self, identity: str, counters: dict[str, int]) -> None:
        previous = self._messages.get(identity)
        digest = hashlib.sha256(identity.encode()).digest()
        indices = [
            int.from_bytes(digest[index : index + 4]) % (len(self._evicted) * 8)
            for index in range(0, 16, 4)
        ]
        seen = all(self._evicted[index // 8] & (1 << (index % 8)) for index in indices)
        if previous is not None or not seen:
            contribution = dict(previous or {})
            for name, value in counters.items():
                old = contribution.get(name, 0)
                contribution[name] = max(old, value)
                self._message_totals[name] = self._message_totals.get(name, 0) + max(
                    0, value - old
                )
            self._messages[identity] = contribution
            self._messages.move_to_end(identity)
            if len(self._messages) > 4096:
                evicted, _ = self._messages.popitem(last=False)
                digest = hashlib.sha256(evicted.encode()).digest()
                for offset in range(0, 16, 4):
                    index = int.from_bytes(digest[offset : offset + 4]) % (
                        len(self._evicted) * 8
                    )
                    self._evicted[index // 8] |= 1 << (index % 8)

    def summarize(
        self, observations: Iterable[Observation], exit_code: int
    ) -> SessionSummary:
        return reduce_session(observations, exit_code).summary
