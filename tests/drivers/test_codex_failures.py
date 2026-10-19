"""Codex health and native failure helpers obey their read-only contract."""

import json
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from ovcaq.drivers.base import DriverHealth
from ovcaq.drivers.codex import CodexDriver
from ovcaq.drivers.codex_events import classify_failure, failure_reset
from ovcaq.drivers.edge import build_driver
from ovcaq.events.model import FailureClass
from ovcaq.paths import CONFIG_NAME

NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
SECRET = "sk-" + "proj-fixturecredential12345678901234567890"
PREFIX = "literal prefix ; $(touch must-not-exist)"

FAKE_PROBE = r"""
import json
import os
import sys
import time

args = sys.argv[1:]
record = {
    "args": args,
    "stdin": sys.stdin.read(),
    "overlay": os.environ.get("PROBE_OVERLAY"),
    "home": os.environ.get("HOME"),
    "codex_home": os.environ.get("CODEX_HOME"),
}
with open(os.environ["PROBE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(record) + "\n")
if args[0:1] != [os.environ["PROBE_PREFIX"]]:
    sys.exit(80)
operation = args[1:]
mode = os.environ["PROBE_MODE"]
secret = "sk-" + "proj-fixturecredential12345678901234567890"
if operation == ["--version"]:
    if mode == "version-timeout":
        time.sleep(30)
    if mode == "empty-version":
        sys.exit(0)
    if mode == "bad-version-status":
        print("version command failed", file=sys.stderr)
        sys.exit(7)
    if mode == "unsupported-version":
        print("codex-cli 0.159.0")
        sys.exit(0)
    if mode == "version-credential-first-line":
        print("codex-cli 0.160.0 Authorization: Bearer " + secret)
        sys.exit(0)
    print("codex-cli 0.160.0", flush=True)
    if mode == "version-credential-later-line":
        print("Authorization: Bearer " + secret)
    if mode == "oversized":
        sys.stdout.write("v" * 131072)
        sys.stderr.write("e" * 131072 + "\nAuthorization: Bearer " + secret)
    sys.exit(0)
if operation == ["login", "status"]:
    if mode == "auth-timeout":
        time.sleep(30)
    if mode == "auth-failure":
        print("Not logged in: invalid credential", file=sys.stderr)
        sys.exit(1)
    if mode == "credential-failure":
        print("401 unauthorized: Authorization: Bearer " + secret, file=sys.stderr)
        sys.exit(1)
    if mode == "oversized":
        sys.stdout.write("a" * 131072)
        sys.stderr.write("b" * 131072)
    print("Logged in using ChatGPT", file=sys.stderr)
    print("raw-auth-diagnostic-must-not-be-in-health")
    sys.exit(0)
sys.exit(81)
"""


@pytest.fixture
def probe_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "isolated-config"))
    project = tmp_path / "project"
    project.mkdir()
    script = tmp_path / "probe.py"
    script.write_text(FAKE_PROBE, encoding="utf-8")
    (tmp_path / "home").mkdir()
    (tmp_path / "provider-home").mkdir()
    return project


def probe_driver(
    root: Path, mode: str, command: tuple[str, ...] | None = None
) -> CodexDriver:
    temporary = root.parent
    argv = command or (sys.executable, str(temporary / "probe.py"), PREFIX)
    environment = {
        "PROBE_MODE": mode,
        "PROBE_LOG": str(temporary / "probe-log.jsonl"),
        "PROBE_PREFIX": PREFIX,
        "PROBE_OVERLAY": "configured-value",
        "HOME": str(temporary / "home"),
        "CODEX_HOME": str(temporary / "provider-home"),
    }
    configuration = (
        'agent = "codex"\n[agents.codex]\n'
        f"command = {json.dumps(argv)}\n"
        'tiers = { standard = "fixture-model" }\n'
        "environment = { "
        + ", ".join(
            f"{key} = {json.dumps(value)}" for key, value in environment.items()
        )
        + ' }\n[agents.codex.options]\nsandbox = "workspace-write"\n'
        'approval = "never"\n'
    )
    (root / CONFIG_NAME).write_text(configuration, encoding="utf-8")
    driver = build_driver(root, "codex")
    assert isinstance(driver, CodexDriver)
    return driver


def probe_records(root: Path) -> list[dict[str, object]]:
    log = root.parent / "probe-log.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def test_healthy_probe_checks_only_version_and_auth_with_closed_stdin(
    probe_root: Path,
) -> None:
    health = probe_driver(probe_root, "healthy").probe()
    assert isinstance(health, DriverHealth)
    assert health.healthy is True
    assert sys.executable in health.detail
    assert "0.160.0" in health.detail
    assert "auth" in health.detail.lower()
    assert "raw-auth-diagnostic" not in health.detail
    assert probe_records(probe_root) == [
        {
            "args": [PREFIX, "--version"],
            "stdin": "",
            "overlay": "configured-value",
            "home": str(probe_root.parent / "home"),
            "codex_home": str(probe_root.parent / "provider-home"),
        },
        {
            "args": [PREFIX, "login", "status"],
            "stdin": "",
            "overlay": "configured-value",
            "home": str(probe_root.parent / "home"),
            "codex_home": str(probe_root.parent / "provider-home"),
        },
    ]
    assert list((probe_root.parent / "home").iterdir()) == []
    assert list((probe_root.parent / "provider-home").iterdir()) == []
    assert not (probe_root / "must-not-exist").exists()


@pytest.mark.parametrize("executable", (False, True), ids=("missing", "nonexecutable"))
def test_probe_rejects_missing_or_nonexecutable_binary(
    probe_root: Path, executable: bool
) -> None:
    binary = probe_root.parent / "unavailable-codex"
    if executable:
        binary.write_text("fixture is not executable\n", encoding="utf-8")
        binary.chmod(0o600)
    health = probe_driver(probe_root, "healthy", (str(binary),)).probe()
    assert health.healthy is False
    assert health.detail.strip()
    assert binary.name in health.detail
    assert not (probe_root.parent / "probe-log.jsonl").exists()


@pytest.mark.parametrize(
    "mode",
    ("empty-version", "bad-version-status", "unsupported-version", "auth-failure"),
)
def test_probe_reports_unhealthy_version_or_auth_status(
    probe_root: Path, mode: str
) -> None:
    health = probe_driver(probe_root, mode).probe()
    assert health.healthy is False
    assert health.detail.strip()
    records = probe_records(probe_root)
    assert records[0]["args"] == [PREFIX, "--version"]
    assert all(
        record["args"] in ([PREFIX, "--version"], [PREFIX, "login", "status"])
        for record in records
    )
    if mode == "auth-failure":
        assert len(records) == 2
        assert any(
            word in health.detail.lower() for word in ("auth", "login", "logged")
        )
    if mode == "unsupported-version":
        assert "0.159.0" in health.detail
        assert "0.160.0" in health.detail
        assert "refresh" in health.detail.lower()


def test_probe_sanitizes_auth_credentials_on_stderr(
    probe_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    health = probe_driver(probe_root, "credential-failure").probe()
    captured = capsys.readouterr()
    assert health.healthy is False
    assert health.detail.strip()
    assert SECRET not in health.detail + captured.out + captured.err
    assert "fixturecredential12345678901234567890" not in health.detail


@pytest.mark.parametrize(
    "mode", ("version-credential-first-line", "version-credential-later-line")
)
def test_probe_does_not_disclose_credentials_from_version_stdout(
    probe_root: Path, capsys: pytest.CaptureFixture[str], mode: str
) -> None:
    health = probe_driver(probe_root, mode).probe()
    captured = capsys.readouterr()
    assert isinstance(health, DriverHealth)
    assert health.detail.strip()
    disclosed = health.detail + captured.out + captured.err
    assert SECRET not in disclosed
    assert "fixturecredential12345678901234567890" not in disclosed


def test_probe_bounds_oversized_output_without_disclosing_raw_credentials(
    probe_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    started = time.monotonic()
    health = probe_driver(probe_root, "oversized").probe()
    elapsed = time.monotonic() - started
    captured = capsys.readouterr()
    assert isinstance(health, DriverHealth)
    assert health.detail.strip()
    assert len(health.detail.encode("utf-8")) <= 16 * 1024
    assert SECRET not in health.detail + captured.out + captured.err
    assert elapsed < 12
    assert all(
        record["args"] in ([PREFIX, "--version"], [PREFIX, "login", "status"])
        for record in probe_records(probe_root)
    )


@pytest.mark.parametrize("mode", ("version-timeout", "auth-timeout"))
def test_probe_times_out_each_read_only_command_after_five_seconds(
    probe_root: Path, mode: str
) -> None:
    started = time.monotonic()
    health = probe_driver(probe_root, mode).probe()
    elapsed = time.monotonic() - started
    assert health.healthy is False
    assert "tim" in health.detail.lower()
    assert 4.5 <= elapsed < 8
    records = probe_records(probe_root)
    assert records[0]["args"] == [PREFIX, "--version"]
    if mode == "auth-timeout":
        assert len(records) == 2
        assert records[1]["args"] == [PREFIX, "login", "status"]


@pytest.mark.parametrize(
    ("detail", "expected"),
    (
        ("HTTP 401", FailureClass.AUTHENTICATION),
        ("UNAUTHORIZED", FailureClass.AUTHENTICATION),
        ("Not logged in", FailureClass.AUTHENTICATION),
        ("invalid credential", FailureClass.AUTHENTICATION),
        ("expired credential", FailureClass.AUTHENTICATION),
        ("HTTP 403", FailureClass.PERMISSION),
        ("Permission denied", FailureClass.PERMISSION),
        ("SANDBOX DENIED", FailureClass.PERMISSION),
        ("approval denied", FailureClass.PERMISSION),
        ("HTTP 429", FailureClass.RATE_LIMIT),
        ("Rate limit exceeded", FailureClass.RATE_LIMIT),
        ("Quota limit reached", FailureClass.RATE_LIMIT),
        ("Usage limit reached", FailureClass.RATE_LIMIT),
        ("Connection reset", FailureClass.CONNECTIVITY),
        ("connection refused", FailureClass.CONNECTIVITY),
        ("DNS lookup failed", FailureClass.CONNECTIVITY),
        ("NETWORK UNREACHABLE", FailureClass.CONNECTIVITY),
        ("server unavailable", FailureClass.CONNECTIVITY),
        ("HTTP 502", FailureClass.CONNECTIVITY),
        ("HTTP 503", FailureClass.CONNECTIVITY),
        ("request timed out", FailureClass.TIMEOUT),
        ("TIMEOUT", FailureClass.TIMEOUT),
        ("agent failed", FailureClass.AGENT),
        ("agent failure", FailureClass.AGENT),
        ("Error: HTTP 401.", FailureClass.AUTHENTICATION),
        ("Request rejected: EXPIRED CREDENTIAL.", FailureClass.AUTHENTICATION),
        ("Error: HTTP 403.", FailureClass.PERMISSION),
        ("Action refused: SANDBOX DENIED.", FailureClass.PERMISSION),
        ("Error: HTTP 429.", FailureClass.RATE_LIMIT),
        ("Request rejected: QUOTA LIMIT reached.", FailureClass.RATE_LIMIT),
        ("Error: HTTP 503.", FailureClass.CONNECTIVITY),
        ("Transport error: CONNECTION REFUSED.", FailureClass.CONNECTIVITY),
        ("Request failed: TIMEOUT.", FailureClass.TIMEOUT),
        ("Request failed: TIMED OUT while waiting.", FailureClass.TIMEOUT),
        ("Turn ended: AGENT FAILED.", FailureClass.AGENT),
        ("Turn ended: AGENT FAILURE during execution.", FailureClass.AGENT),
        ("", FailureClass.UNKNOWN),
        ("unrecognized native failure", FailureClass.UNKNOWN),
    ),
)
def test_classifies_native_failure_detail_case_insensitively(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize(
    ("detail", "expected"),
    (
        (
            "HTTP 401; HTTP 403; HTTP 429; HTTP 502; timeout agent failed",
            FailureClass.AUTHENTICATION,
        ),
        ("HTTP 403; HTTP 429; HTTP 503; timeout agent failed", FailureClass.PERMISSION),
        ("HTTP 429; HTTP 502; timeout agent failed", FailureClass.RATE_LIMIT),
        ("HTTP 503; timeout agent failed", FailureClass.CONNECTIVITY),
        ("timeout agent failed", FailureClass.TIMEOUT),
        ("permission denied; expired credential", FailureClass.AUTHENTICATION),
        ("rate limit; sandbox denied", FailureClass.PERMISSION),
    ),
)
def test_failure_classification_uses_documented_precedence(
    detail: str, expected: FailureClass
) -> None:
    assert classify_failure(detail) is expected


@pytest.mark.parametrize("code", ("401", "403", "429", "502", "503"))
@pytest.mark.parametrize("template", ("item_{code}_abc", "item{code}abc", "9{code}7"))
def test_numeric_status_substrings_in_identifiers_are_unknown(
    code: str, template: str
) -> None:
    assert classify_failure(template.format(code=code)) is FailureClass.UNKNOWN


@pytest.mark.parametrize(
    ("detail", "expected"),
    (
        ("rate limit; reset at 2026-10-04T12:00:01Z", NOW + timedelta(seconds=1)),
        ("rate limit; reset at 2026-10-04T14:01:00+02:00", NOW + timedelta(seconds=60)),
        ("rate limit; reset at 2026-10-04T18:00:00+00:00", NOW + timedelta(hours=6)),
        ("rate limit; retry after 1 seconds", NOW + timedelta(seconds=1)),
        ("rate limit; retry after 0.5 seconds", NOW + timedelta(seconds=0.5)),
        ("rate limit; retry after 21600 seconds", NOW + timedelta(hours=6)),
    ),
)
def test_failure_reset_accepts_explicit_future_aware_resets(
    detail: str, expected: datetime
) -> None:
    reset = failure_reset(detail, NOW)
    assert reset == expected
    assert reset is not None and reset.tzinfo is not None


@pytest.mark.parametrize(
    "detail",
    (
        "",
        "rate limit exceeded",
        "rate limit resets at 3pm",
        "rate limit; reset at 2026-10-04T12:01:00",
        "rate limit; reset at 2026-10-04T11:59:59Z",
        "rate limit; reset at 2026-10-04T12:00:00Z",
        "rate limit; reset at 2026-10-04T18:00:01Z",
        "rate limit; reset at 2026-13-04T12:01:00Z",
        "rate limit; reset at 9999-12-31T23:59:59Z",
        "rate limit; retry after -1 seconds",
        "rate limit; retry after 0 seconds",
        "rate limit; retry after 21601 seconds",
        "rate limit; retry after NaN seconds",
        "rate limit; retry after inf seconds",
        "rate limit; retry after Infinity seconds",
        "rate limit; retry after 1e309 seconds",
        "rate limit; retry after " + "9" * 400 + " seconds",
        "rate limit; retry after many seconds",
    ),
)
def test_failure_reset_rejects_missing_ambiguous_invalid_or_unbounded_resets(
    detail: str,
) -> None:
    assert failure_reset(detail, NOW) is None


def test_failure_reset_compares_aware_now_using_its_actual_instant() -> None:
    now = datetime.fromisoformat("2026-10-04T14:00:00+02:00")
    assert failure_reset("rate limit; reset at 2026-10-04T12:01:00Z", now) == (
        NOW + timedelta(seconds=60)
    )


@pytest.mark.parametrize(
    "now",
    (
        datetime.fromisoformat("2026-10-05T12:00:00Z"),
        datetime.fromisoformat("2027-01-01T00:00:00+02:00"),
    ),
)
@pytest.mark.parametrize("seconds", (0.5, 1, 21600))
def test_failure_reset_anchors_relative_delay_to_supplied_now(
    now: datetime, seconds: float
) -> None:
    reset = failure_reset(f"rate limit; retry after {seconds} seconds", now)
    assert reset == now + timedelta(seconds=seconds)
    assert reset is not None and reset.tzinfo is not None
