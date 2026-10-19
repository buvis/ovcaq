#!/usr/bin/env python3
"""Deterministic executable fixture for the pinned Codex subprocess contract."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def emit(record: object, *, stderr: bool = False) -> None:
    print(
        json.dumps(record, sort_keys=True, separators=(",", ":")),
        file=sys.stderr if stderr else sys.stdout,
        flush=True,
    )


def valid_exec_argv(argv: list[str]) -> bool:
    prefix = [
        "--ask-for-approval",
        "never",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "-C",
        os.getcwd(),
    ]
    if argv[:8] != prefix:
        return False
    remaining = argv[8:]
    if remaining[:1] == ["-m"] and len(remaining) >= 2:
        remaining = remaining[2:]
    if remaining[:1] == ["-c"] and len(remaining) >= 2:
        if remaining[1] not in {
            f'model_reasoning_effort="{level}"'
            for level in ("low", "medium", "high", "xhigh")
        }:
            return False
        remaining = remaining[2:]
    return len(remaining) == 2 and remaining[0] == "--"


def descendant(scenario: str) -> int:
    handler = signal.SIG_IGN if scenario == "descendant-kill" else signal.SIG_DFL
    child_code = (
        "import signal,time; "
        f"signal.signal(signal.SIGTERM, {int(handler)}); "
        "print('ready', flush=True); time.sleep(60)"
    )
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    child = subprocess.Popen(
        [sys.executable, "-c", child_code],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "ready"
        emit(
            {
                "type": "fake_descendant",
                "pid": child.pid,
                "parent_pid": os.getpid(),
                "pgid": os.getpgrp(),
            }
        )
        returncode = child.wait(timeout=60)
        emit({"type": "fake_descendant_reaped", "returncode": returncode})
        if scenario == "descendant-kill":
            time.sleep(60)
        return 0
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        if child.stdout is not None:
            child.stdout.close()


def workflow_command(*arguments: str) -> object:
    argv = [os.environ["OVCAQ_FAKE_CLI"], "--root", os.getcwd(), "--json", *arguments]
    result = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    value = json.loads(result.stdout)
    emit({"type": "fake_workflow_command", "argv": argv, "result": value})
    return value


def workflow() -> int:
    state = workflow_command("state", "show")
    phase = state["work"]["phase"]
    if phase == "build":
        workflow_command("workflow", "select")
        state = workflow_command("state", "show")
    if phase == "done":
        workflow_command(
            "workflow",
            "complete-prd",
            "--prd",
            state["work"]["prd"],
            "--expected-revision",
            str(state["revision"]),
        )
        state = workflow_command("state", "show")
    outcome = {"build": "tasks_done", "review": "converged", "done": "drained"}[phase]
    committed = workflow_command(
        "workflow",
        "phase-complete",
        "--outcome",
        outcome,
        "--expected-revision",
        str(state["revision"]),
    )
    emit(
        {
            "type": "fake_workflow_handoff",
            "phase": phase,
            "outcome": outcome,
            "revision": committed["revision"],
            "result": committed["result"],
        }
    )
    sys.stdout.write(Path(__file__).with_name("healthy.jsonl").read_text())
    sys.stdout.flush()
    return 0


def version(scenario: str) -> int:
    if scenario == "version-timeout":
        time.sleep(6)
    if scenario == "version-failed":
        return 1
    if scenario != "version-empty":
        print(
            "codex-cli 0.159.0"
            if scenario == "version-unsupported"
            else "codex-cli 0.160.0",
            flush=True,
        )
    return 0


def authentication(scenario: str) -> int:
    if scenario == "auth-timeout":
        time.sleep(6)
    if scenario == "auth-failed":
        return 1
    print("Logged in with fixture authentication", flush=True)
    return 0


def native_rate_limit(scenario: str) -> int:
    emit({"type": "thread.started", "thread_id": "fake-native"})
    detail = (
        "Rate limit reached; retry after 60 seconds."
        if scenario == "native-reset"
        else "Rate limit reached."
    )
    emit({"type": "error", "message": detail})
    if scenario == "noisy-success":
        emit(
            {
                "type": "item.completed",
                "item": {
                    "id": "warning",
                    "type": "error",
                    "message": detail,
                },
            }
        )
        emit(
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 100,
                    "cached_input_tokens": 20,
                    "cache_write_input_tokens": 0,
                    "output_tokens": 25,
                    "reasoning_output_tokens": 10,
                },
            }
        )
        return 0
    emit({"type": "turn.failed", "error": {"message": detail}})
    return 1


def emit_invocation(argv: list[str]) -> None:
    emit(
        {
            "type": "fake_invocation",
            "argv": argv,
            "cwd": os.getcwd(),
            "stdin_closed": sys.stdin.read() == "",
            "environment": {
                key: os.environ.get(key)
                for key in (
                    "HOME",
                    "XDG_CONFIG_HOME",
                    "XDG_STATE_HOME",
                    "OVCAQ_FAKE_SCENARIO",
                    "OVCAQ_FAKE_MARKER",
                )
            },
        },
        stderr=argv in (["--version"], ["login", "status"]),
    )


def main() -> int:
    argv = sys.argv[1:]
    scenario = os.environ.get("OVCAQ_FAKE_SCENARIO", "healthy")
    emit_invocation(argv)
    if argv == ["--version"]:
        return version(scenario)
    if argv == ["login", "status"]:
        return authentication(scenario)

    if not valid_exec_argv(argv):
        return 2

    if scenario in {"descendant-term", "descendant-kill"}:
        return descendant(scenario)
    if scenario == "workflow":
        return workflow()

    replay = {
        "healthy",
        "lanes",
        "lanes-matched",
        "malformed",
        "tool-active",
        "rate-limited",
        "authentication-failed",
        "connectivity-failed",
        "permission-failed",
    }
    if scenario in replay:
        sys.stdout.write(Path(__file__).with_name(f"{scenario}.jsonl").read_text())
        sys.stdout.flush()
        return 1 if scenario.endswith("-failed") or scenario == "rate-limited" else 0
    if scenario in {"native-reset", "native-no-reset", "noisy-success"}:
        return native_rate_limit(scenario)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
