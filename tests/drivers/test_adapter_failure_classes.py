import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.config import AgentSettings
from ovcaq.drivers.claude_events import failure_payload
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.codex_events import classify_failure
from ovcaq.events.model import FailureClass
from ovcaq.runtime.decision import (
    AttemptResult,
    DecisionKind,
    ProgressSnapshot,
    RetryState,
    SupervisorPolicy,
    decide,
    snapshot,
)
from ovcaq.state.schema import new_state


@pytest.fixture
def driver() -> CodexDriver:
    settings = AgentSettings(
        name="codex",
        command=("fixture-wrapper",),
        tiers={"standard": "fixture-model"},
        environment={},
        options={},
    )
    return CodexDriver(settings, run_id="capacity-run")


def running_snapshot() -> ProgressSnapshot:
    state = new_state(repo_root=Path("/tmp/decision-contract"))
    state["batch"]["id"] = "batch-1"
    state["batch"]["status"] = "running"
    state["work"]["prd"] = "00001-feature.md"
    return snapshot(state)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("401", FailureClass.AUTHENTICATION),
        ("403", FailureClass.PERMISSION),
        ("429", FailureClass.RATE_LIMIT),
        ("502", FailureClass.CONNECTIVITY),
        ("503", FailureClass.CONNECTIVITY),
    ],
)
@pytest.mark.parametrize(
    "template",
    [
        "HTTP {code}",
        "HTTP status: {code}",
        "status code: {code}",
        "error code: {code}",
        "StAtUs={code}",
        "eRrOr {code}:",
        "hTtP ErRoR {code}",
    ],
)
def test_numeric_codes_classify_with_explicit_status_or_error_context(
    code: str, expected: FailureClass, template: str
) -> None:
    assert classify_failure(template.format(code=code)) is expected


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("unexpected status 503 Service Unavailable", FailureClass.CONNECTIVITY),
        ("unexpected status 502 Bad Gateway", FailureClass.CONNECTIVITY),
        ("unexpected status 403 Forbidden", FailureClass.PERMISSION),
        (
            "exceeded retry limit, last status: 429 Too Many Requests",
            FailureClass.RATE_LIMIT,
        ),
    ],
)
def test_explicit_bare_status_diagnostics_are_classified(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        (
            "HTTP status client error (429 Too Many Requests) for url (https://example.test)",
            FailureClass.RATE_LIMIT,
        ),
        (
            "HTTP status client error (403 Forbidden) for url (https://example.test)",
            FailureClass.PERMISSION,
        ),
        (
            "HTTP status server error (503 Service Unavailable) for url (https://example.test)",
            FailureClass.CONNECTIVITY,
        ),
        ("HTTP/1.1 401 Unauthorized", FailureClass.AUTHENTICATION),
        ("HTTP/1.1 403 Forbidden", FailureClass.PERMISSION),
        ("HTTP/1.1 429 Too Many Requests", FailureClass.RATE_LIMIT),
        ("HTTP/1.1 502 Bad Gateway", FailureClass.CONNECTIVITY),
        ("HTTP/1.1 503 Service Unavailable", FailureClass.CONNECTIVITY),
        ("HTTP/2 503 Service Unavailable", FailureClass.CONNECTIVITY),
        ("HTTP/2 429 Too Many Requests", FailureClass.RATE_LIMIT),
        ("HTTP/3 503 Service Unavailable", FailureClass.CONNECTIVITY),
        ("HTTP/3 429 Too Many Requests", FailureClass.RATE_LIMIT),
    ],
)
def test_reqwest_and_http_version_status_diagnostics_are_classified(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize("prefix", ["status", "status=", "Error", "HTTP error"])
def test_long_whitespace_status_diagnostic_returns_unknown_without_hanging(
    prefix: str,
) -> None:
    script = (
        "from ovcaq.drivers.codex_events import classify_failure\n"
        f'print(classify_failure({prefix!r} + " " * 200_000 + "x").value)\n'
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Failure classification exceeded the 5-second child timeout")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == FailureClass.UNKNOWN.value


@pytest.mark.parametrize("code", ["401", "403", "429", "502", "503"])
@pytest.mark.parametrize(
    "template",
    [
        "processed {code} files",
        "inspected {code} records",
        "port {code}",
        "{code}",
        "completed {code} tasks",
    ],
)
def test_unrelated_numbers_are_not_failure_diagnostics(
    code: str, template: str
) -> None:
    assert classify_failure(template.format(code=code)) is FailureClass.UNKNOWN


@pytest.mark.parametrize(
    "detail",
    [
        "disk at capacity",
        "context capacity reached",
        "Disk at capacity while model runs normally",
    ],
)
def test_ordinary_resource_capacity_is_unknown(detail: str) -> None:
    assert classify_failure(detail) is FailureClass.UNKNOWN


@pytest.mark.parametrize("code", ["401", "403", "429", "502", "503"])
@pytest.mark.parametrize(
    "template", ["HTTP {code}", "status={code}", "Error {code}:", "HTTP error {code}"]
)
@pytest.mark.parametrize("extra_digit", ["{code}0", "0{code}"])
def test_numeric_diagnostics_require_a_complete_status_number(
    code: str, template: str, extra_digit: str
) -> None:
    detail = template.format(code=extra_digit.format(code=code))
    assert classify_failure(detail) is FailureClass.UNKNOWN


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("UnAuThOrIzEd", FailureClass.AUTHENTICATION),
        ("Rate limit reached", FailureClass.RATE_LIMIT),
        ("Rate\tlimit reached", FailureClass.UNKNOWN),
        ("invalid credentials", FailureClass.AUTHENTICATION),
    ],
)
def test_native_word_diagnostics_retain_case_without_widening_whitespace(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize(
    "detail", ["Authentication failed", "MCP server authentication failed"]
)
def test_generic_authentication_failure_messages_remain_unknown(detail: str) -> None:
    assert classify_failure(detail) is FailureClass.UNKNOWN


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("timeout; connection refused", FailureClass.CONNECTIVITY),
        ("permission denied; not logged in", FailureClass.AUTHENTICATION),
        ("not logged in; permission denied", FailureClass.AUTHENTICATION),
        (
            "unexpected status 403 Forbidden; not logged in",
            FailureClass.AUTHENTICATION,
        ),
        (
            "not logged in; unexpected status 403 Forbidden",
            FailureClass.AUTHENTICATION,
        ),
    ],
)
def test_failure_precedence_is_independent_of_diagnostic_order(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize(
    ("connectivity_retries", "expected_kind"),
    [
        (2, DecisionKind.WAIT),
        (3, DecisionKind.HALT),
    ],
)
def test_model_capacity_uses_connectivity_wait_until_exact_retry_bound(
    driver: CodexDriver, connectivity_retries: int, expected_kind: DecisionKind
) -> None:
    observations = driver.decode(
        json.dumps(
            {
                "type": "turn.failed",
                "error": {"message": "Selected model is at capacity"},
            }
        )
    )
    summary = driver.summarize(observations, 1)
    assert not summary.success
    assert summary.failure_class is FailureClass.CONNECTIVITY
    assert summary.rate_limit_reset_at is None
    assert not any(o.type == "rate_limit.started" for o in observations)
    before = running_snapshot()
    now = datetime(2026, 10, 2, 12, tzinfo=UTC)
    result = AttemptResult(
        summary=summary,
        started_at=now - timedelta(seconds=10),
        finished_at=now,
        state_after=before,
        state_error=None,
    )
    policy = SupervisorPolicy(
        died_retries=2,
        connectivity_retries=3,
        rate_limit_retries=2,
        connectivity_wait_seconds=7.5,
        rate_limit_wait_seconds=120.0,
        phase_repeat_limit=3,
    )
    retries = RetryState(connectivity=connectivity_retries, rate_limit=0)
    decision = decide(before, result, retries, policy, now=now)
    assert decision.kind is expected_kind
    assert decision.wait_seconds == (
        7.5 if expected_kind is DecisionKind.WAIT else None
    )


_CLAUDE_DIAGNOSTIC_ROWS: list[tuple[object, FailureClass]] = [
    # One row per authentication marker.
    ("Claude could not complete the OAuth login flow", FailureClass.AUTHENTICATION),
    ("The refresh token has expired; run /login again", FailureClass.AUTHENTICATION),
    ("Session rejected because the stored token expired", FailureClass.AUTHENTICATION),
    ("The CLI sent an expired token to the API", FailureClass.AUTHENTICATION),
    ("You are not logged in to Claude Code", FailureClass.AUTHENTICATION),
    ("The API answered HTTP 401 for this account", FailureClass.AUTHENTICATION),
    ("The terminal exited after status 401 from the API", FailureClass.AUTHENTICATION),
    # One row per rate-limit marker.
    ("The API answered HTTP 429 for this account", FailureClass.RATE_LIMIT),
    ("The terminal exited after status 429 from the API", FailureClass.RATE_LIMIT),
    ("The gateway replied Too Many Requests for this turn", FailureClass.RATE_LIMIT),
    ("Anthropic reported a rate limit on this organization", FailureClass.RATE_LIMIT),
    ("The request hit the rate-limit policy of the gateway", FailureClass.RATE_LIMIT),
    (
        "Upstream returned the error kind rate_limit for the turn",
        FailureClass.RATE_LIMIT,
    ),
    # One row per connectivity marker.
    ("read ECONNRESET", FailureClass.CONNECTIVITY),
    ("connect ECONNREFUSED 127.0.0.1:443", FailureClass.CONNECTIVITY),
    ("The host lookup returned EAI_AGAIN for the API", FailureClass.CONNECTIVITY),
    ("getaddrinfo failed for the API host", FailureClass.CONNECTIVITY),
    # Real-world diagnostics quoted verbatim.
    ("OAuth token has expired", FailureClass.AUTHENTICATION),
    ("HTTP 429 Too Many Requests", FailureClass.RATE_LIMIT),
    ("rate limit exceeded", FailureClass.RATE_LIMIT),
    ("connect ETIMEDOUT", FailureClass.CONNECTIVITY),
    # The remaining classes stay reachable, and a near-miss of a connectivity
    # marker ("connection") still lands in timeout.
    ("Claude CLI exited: operation not permitted", FailureClass.PERMISSION),
    ("The connection timeout stopped the stream read", FailureClass.TIMEOUT),
    # Earlier classes win over later ones when both markers are present.
    ("connect ETIMEDOUT after the request timed out", FailureClass.CONNECTIVITY),
    (
        "OAuth token has expired after HTTP 429 Too Many Requests",
        FailureClass.AUTHENTICATION,
    ),
    ("permission denied and you are not logged in", FailureClass.PERMISSION),
    # Unmatched text, including bare numbers and no text at all.
    ("exit code 401", FailureClass.AGENT),
    ("processed 429 rows", FailureClass.AGENT),
    ("provider execution failed", FailureClass.AGENT),
    ("", FailureClass.AGENT),
    # Accepted asymmetry: plain containment makes "HTTP 4290" a rate limit.
    ("HTTP 4290", FailureClass.RATE_LIMIT),
    # Evidence that is not text at all.
    (42, FailureClass.UNKNOWN),
    (None, FailureClass.UNKNOWN),
]


@pytest.mark.parametrize(("detail", "expected"), _CLAUDE_DIAGNOSTIC_ROWS)
def test_claude_diagnostics_classify_by_table(
    detail: object, expected: FailureClass
) -> None:
    payload = failure_payload(detail)
    assert set(payload) == {"failure_class", "detail"}
    assert payload["failure_class"] == expected
    if not isinstance(detail, str):
        assert payload["detail"] == "Malformed terminal error evidence"
