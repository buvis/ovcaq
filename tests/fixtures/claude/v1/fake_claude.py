#!/usr/bin/env python3
"""Deterministic executable fixture for the Claude subprocess contract."""

import json
import os
import sys


def emit(record: object) -> None:
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)


emit(
    {
        "type": "fake_invocation",
        "argv": sys.argv[1:],
        "cwd": os.getcwd(),
        "environment": {
            key: os.environ.get(key)
            for key in (
                "CLAUDE_UNATTENDED",
                "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS",
                "WARDEN_UNATTENDED",
                "HOST_ONLY_MARKER",
            )
        },
        "password": "raw-fixture-secret",
    }
)
emit(
    {
        "type": "system",
        "subtype": "init",
        "session_id": "fake-session",
        "model": "fixture-model",
        "claude_code_version": "fixture-version",
        "permissionMode": "auto",
    }
)
emit(
    {
        "type": "assistant",
        "session_id": "fake-session",
        "message": {
            "id": "fake-message",
            "content": [
                {"type": "text", "text": "Running fake Claude."},
                {"type": "tool_use", "id": "fake-tool", "name": "Read"},
            ],
            "usage": {"input_tokens": 5, "output_tokens": 2},
        },
    }
)
emit(
    {
        "type": "user",
        "session_id": "fake-session",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "fake-tool",
                    "is_error": False,
                    "content": "done password=normalized-value",
                }
            ]
        },
    }
)
emit(
    {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "session_id": "fake-session",
        "result": "Fake Claude complete.",
        "total_cost_usd": 0.125,
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }
)
