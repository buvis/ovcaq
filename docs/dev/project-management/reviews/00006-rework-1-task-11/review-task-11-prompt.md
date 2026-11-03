
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D1] Repair configuration and redaction contracts (M)

Description:
What: Repair configuration and redaction contracts (M)

Source review: dev/local/reviews/00006-events-claude-adapter-v1-review-1.md (HEAD 24fcec3bed6a41044c3d149d1f42bd678864e7e0)

Location:
- src/ovcaq/config.py
- src/ovcaq/events/model.py
- tests/workflow/test_configuration.py
- tests/events/test_model.py
- tests/drivers/test_claude.py

Details:
Restore the accepted configuration contract: an omitted command defaults to (selected_name,), while explicitly invalid arrays still fail. Reuse one agent-table/tier reader from workflow_settings without forcing unrelated workflow-only commands to configure a launcher. Reject all credential-shaped environment/options keys including authorization, cookie, credential and pinned credential values. Extend normalized free-text sanitization for bare Bearer credentials and recognizable likely-secret token forms, using synthetic samples only and provider-neutral patterns; preserve harmless prose and typed numeric usage fields. Ensure direct AgentSettings construction cannot bypass credential safeguards consumed by the driver. Keep ordinary environment control values allowed. Add behavioral tests that fail before these fixes.

### Findings (verbatim)
- 🟠 High Credential rejection omits `authorization`, `cookie`, and `credential`, so secret-bearing environment/options keys and values can enter agent settings and the launch overlay despite the PRD’s closed sensitive-key contract | File: src/ovcaq/config.py:43 | Consensus: 1/3 | Found by: ALICE
- 🟡 Medium `agent_settings()` rejects configurations without an explicit command instead of applying the required `(name,)` default | File: src/ovcaq/config.py:156 | Consensus: 1/3 | Found by: ALICE
- 🟡 Medium `workflow_settings()` duplicates agent-tier merging instead of delegating to `agent_settings()`, allowing workflow callers to accept agent configurations that the launch configuration rejects | File: src/ovcaq/config.py:221 | Consensus: 1/3 | Found by: ALICE
- 🟠 Normalized-event redaction only catches credential-shaped keys and assignment syntax; bare likely secrets such as provider API tokens embedded in activity or tool text are persisted unchanged, violating the requirement to redact likely secrets from normalized evidence | File: src/ovcaq/events/model.py:22 | Consensus: 1/3 | Found by: BLAKE

Acceptance criteria:
- Every quoted finding no longer reproduces.
- Preserve raw evidence, provider-neutral shared models, state authority and shell-free command construction.
- Run focused regression tests and the work skill's mandatory final verification; do not perform completion review in the implementation session.


Acceptance criteria:
- Every quoted finding no longer reproduces.
- Preserve raw evidence, provider-neutral shared models, state authority and shell-free command construction.
- Run focused regression tests and the work skill's mandatory final verification; do not perform completion review in the implementation session.


## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index c9ccb1d..f25d94d 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -33,6 +33,7 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 
 ### Fixed
 
+- Agent configuration applies command defaults and shared validation; normalized text redacts bare credential tokens while preserving usage counters.
 - Deferred directory setup diagnostics report the full configured path while preserving the originating OS error.
 - Deferred publication revalidates the complete confirmed runtime ancestry before returning success.
 - Deferred ancestry confirmation detects replaced ancestors on reopen, supports search-only access, and avoids redundant ancestor creation and root confirmation.
diff --git a/src/ovcaq/config.py b/src/ovcaq/config.py
index c4644b9..4851a6f 100644
--- a/src/ovcaq/config.py
+++ b/src/ovcaq/config.py
@@ -43,17 +43,22 @@ class WorkflowSettings:
 
 
 _CREDENTIAL_KEY = re.compile(
-    r"(?:^|[\W_])(?:api[_-]?key|token|secret|password)(?:$|[\W_])", re.IGNORECASE
+    r"api[_-]?key|token|secret|password|authorization|cookie|credential",
+    re.IGNORECASE,
 )
 _CREDENTIAL_VALUE = re.compile(
-    r"\bbearer\s+\S+|\b(?:api[_-]?key|token|password|secret)\s*=\s*\S+",
+    r"\bbearer\s+\S+|\bsk-[A-Za-z0-9_-]{20,}\b"
+    r"|\b(?:api[_-]?key|token|secret|password|authorization|cookie|credential)\s*[:=]\s*\S+",
     re.IGNORECASE,
 )
 
 
 def _check_credentials(value: str, *, key: bool = False) -> None:
-    pattern = _CREDENTIAL_KEY if key else _CREDENTIAL_VALUE
-    if pattern.search(value):
+    if key:
+        sensitive = bool(_CREDENTIAL_KEY.search(value))
+    else:
+        sensitive = bool(_CREDENTIAL_VALUE.search(value))
+    if sensitive:
         raise ConfigurationError("agent settings must not contain credentials")
 
 
@@ -87,11 +92,31 @@ class AgentSettings:
     options: Mapping[str, object]
 
     def __post_init__(self) -> None:
+        if not isinstance(self.name, str) or not self.name:
+            raise ConfigurationError("agent name must be nonempty text")
+        if not self.command or any(
+            not isinstance(part, str) or not part for part in self.command
+        ):
+            raise ConfigurationError("agent command must be nonempty strings")
+        tiers = dict(self.tiers)
+        environment = dict(self.environment)
+        for field, values in (("tiers", tiers), ("environment", environment)):
+            for key, value in values.items():
+                if (
+                    not isinstance(key, str)
+                    or not key
+                    or not isinstance(value, str)
+                    or not value
+                ):
+                    raise ConfigurationError(
+                        f"agent {field} must contain nonempty string keys and values"
+                    )
+                if field == "environment":
+                    _check_credentials(key, key=True)
+                    _check_credentials(value)
         object.__setattr__(self, "command", tuple(self.command))
-        object.__setattr__(self, "tiers", MappingProxyType(dict(self.tiers)))
-        object.__setattr__(
-            self, "environment", MappingProxyType(dict(self.environment))
-        )
+        object.__setattr__(self, "tiers", MappingProxyType(tiers))
+        object.__setattr__(self, "environment", MappingProxyType(environment))
         object.__setattr__(self, "options", _freeze_options(self.options))
 
 
@@ -151,9 +176,11 @@ def agent_settings(root: Path, *, name: str | None = None) -> AgentSettings:
     active = name if name is not None else project.get("agent", user.get("agent"))
     if not isinstance(active, str) or not active:
         raise ConfigurationError("configuration agent must be a nonempty name")
-    user_agent = _table(_table(user, "agents"), active)
-    project_agent = _table(_table(project, "agents"), active)
-    command = project_agent.get("command", user_agent.get("command"))
+    user_agents = _table(user, "agents")
+    project_agents = _table(project, "agents")
+    user_agent = _table(user_agents, active)
+    project_agent = _table(project_agents, active)
+    command = project_agent.get("command", user_agent.get("command", [active]))
     if (
         not isinstance(command, list)
         or not command
@@ -217,14 +244,13 @@ def workflow_settings(
         "state_file",
     )
     state = runtime_directory(root, state)
-    tiers: dict[str, object] = {}
     active = project.get("agent", user.get("agent"))
     if active is not None:
         if not isinstance(active, str) or not active:
             raise ConfigurationError("configuration agent must be a nonempty name")
-        for config in (user, project):
-            agent = _table(_table(config, "agents"), active)
-            tiers.update(_table(agent, "tiers"))
+        tiers = dict(agent_settings(root, name=active).tiers)
+    else:
+        tiers = {}
     return WorkflowSettings(
         prds,
         runtime,
diff --git a/src/ovcaq/events/model.py b/src/ovcaq/events/model.py
index 062678b..2aef6e4 100644
--- a/src/ovcaq/events/model.py
+++ b/src/ovcaq/events/model.py
@@ -27,6 +27,11 @@ _CREDENTIAL = re.compile(
     r"""(?:"[^"]*"|'[^']*'|[^\s,;]+)""",
     re.IGNORECASE,
 )
+_LIKELY_SECRET = re.compile(
+    r"(?P<bearer>\bBearer\s+)(?=[A-Za-z0-9_.-]{20,}\b)[A-Za-z0-9_.-]+"
+    r"|(?P<sk>\bsk-[A-Za-z0-9_-]{20,}\b)",
+    re.IGNORECASE,
+)
 _UTC_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)")
 
 
@@ -60,7 +65,10 @@ class FailureClass(StrEnum):
 
 def sanitize_text(text: str) -> str:
     """Redact credential assignments while retaining ordinary prose."""
-    return _CREDENTIAL.sub(lambda match: match["prefix"] + "[REDACTED]", text)
+    sanitized = _CREDENTIAL.sub(lambda match: match["prefix"] + "[REDACTED]", text)
+    return _LIKELY_SECRET.sub(
+        lambda match: (match["bearer"] or "") + "[REDACTED]", sanitized
+    )
 
 
 def sanitize_json(value: object) -> JSONValue:
diff --git a/tests/events/test_model_rework.py b/tests/events/test_model_rework.py
new file mode 100644
index 0000000..ce82dcf
--- /dev/null
+++ b/tests/events/test_model_rework.py
@@ -0,0 +1,76 @@
+from __future__ import annotations
+
+from dataclasses import asdict
+from datetime import UTC, datetime
+
+import pytest
+
+from ovcaq.events import (
+    Observation,
+    ObservationType,
+    Usage,
+    observation_record,
+    sanitize_text,
+)
+
+
+@pytest.mark.parametrize(
+    "text,expected",
+    (
+        ("Bearer Q7v-k9_42.mN8p23.R4j62y", "Bearer [REDACTED]"),
+        ("bEaReR Q7v-k9_42mN8p23R4j62y", "bEaReR [REDACTED]"),
+        (
+            "request used sk-synthetic_Q7v-k9_42mN8p23R4j62y",
+            "request used [REDACTED]",
+        ),
+        (
+            "token sk-test-synthetic-Q7v_k9-42mN8p23R4j62y",
+            "token [REDACTED]",
+        ),
+    ),
+)
+def test_text_sanitization_redacts_bare_likely_secret_tokens(
+    text: str, expected: str
+) -> None:
+    assert sanitize_text(text) == expected
+
+
+@pytest.mark.parametrize(
+    "text",
+    (
+        "Bearer harmless",
+        "token budget exhausted after 42 requests",
+        "authorization denied because the credential is unavailable",
+        "cookie jar contains 3 entries",
+    ),
+)
+def test_text_sanitization_preserves_harmless_prose(text: str) -> None:
+    assert sanitize_text(text) == text
+
+
+def test_usage_preserves_typed_numeric_counters_during_sanitization() -> None:
+    usage = Usage(
+        input_tokens=101,
+        output_tokens=23,
+        cache_creation_input_tokens=7,
+        cache_read_input_tokens=11,
+        tool_uses=3,
+        cost_usd=0.125,
+        estimated=False,
+    )
+    observation = Observation(
+        protocol_version=1,
+        timestamp=datetime(2026, 9, 26, tzinfo=UTC),
+        provider="test-driver",
+        run_id="run-1",
+        session_id="session-1",
+        lane_id=None,
+        type=ObservationType("usage.updated"),
+        payload={"usage": asdict(usage), "identity": "request-1"},
+    )
+    serialized = observation_record(observation)["payload"]["usage"]
+
+    assert serialized == asdict(usage)
+    assert type(serialized["input_tokens"]) is int
+    assert type(serialized["cost_usd"]) is float
+    assert type(serialized["estimated"]) is bool
diff --git a/tests/workflow/test_configuration.py b/tests/workflow/test_configuration.py
index 0c628cc..106f9f2 100644
--- a/tests/workflow/test_configuration.py
+++ b/tests/workflow/test_configuration.py
@@ -261,7 +261,6 @@ def test_agent_settings_merge_user_then_project_for_only_the_selected_agent(
         'agent = ""',
         "agent = 12",
         "agent = false",
-        'agent = "missing"',
     ),
 )
 def test_agent_settings_reject_missing_empty_or_non_string_selection(
@@ -272,6 +271,20 @@ def test_agent_settings_reject_missing_empty_or_non_string_selection(
         agent_settings(config_root)
 
 
+def test_selected_agent_without_a_declaration_defaults_command_to_its_name(
+    config_root: Path,
+) -> None:
+    (config_root / "ovcaq.toml").write_text('agent = "missing"\n')
+
+    settings = agent_settings(config_root)
+
+    assert settings.name == "missing"
+    assert settings.command == ("missing",)
+    assert settings.tiers == {}
+    assert settings.environment == {}
+    assert settings.options == {}
+
+
 def test_empty_explicit_agent_name_does_not_fall_back_to_configured_selection(
     config_root: Path,
 ) -> None:
@@ -329,14 +342,15 @@ def test_agent_settings_reject_invalid_argv_tables_and_non_json_options(
     assert list(config_root.iterdir()) == [config]
 
 
-def test_agent_settings_require_a_command_even_when_other_tables_are_valid(
+def test_agent_settings_default_omitted_command_to_selected_name(
     config_root: Path,
 ) -> None:
     (config_root / "ovcaq.toml").write_text(
         'agent = "local"\n[agents.local]\ntiers = {}\nenvironment = {}\noptions = {}\n'
     )
-    with pytest.raises(ConfigurationError):
-        agent_settings(config_root)
+    settings = agent_settings(config_root)
+    assert settings.name == "local"
+    assert settings.command == ("local",)
 
 
 @pytest.mark.parametrize("table", ("environment", "options"))
@@ -389,27 +403,21 @@ def test_agent_settings_reject_credentials_nested_in_option_arrays(
         agent_settings(config_root)
 
 
-def test_agent_settings_accept_ordinary_words_containing_secret_key_fragments(
+@pytest.mark.parametrize(
+    "key",
+    ("TOKENIZER", "PASSWORDLESS", "SECRETARY"),
+)
+def test_agent_settings_reject_credential_substrings_in_keys(
     config_root: Path,
+    key: str,
 ) -> None:
     (config_root / "ovcaq.toml").write_text(
         'agent = "local"\n[agents.local]\ncommand = ["runner"]\ntiers = {}\n'
-        'environment = { MONKEY = "monkey", TOKENIZER = "tokenizer", '
-        'PASSWORDLESS = "passwordless", SECRETARY = "secretary" }\n'
-        'options = { monkey = "monkey", tokenizer = "tokenizer", '
-        'passwordless = "passwordless", secretary = "secretary" }\n'
+        f'environment = {{ {key} = "synthetic" }}\noptions = {{}}\n'
     )
-    settings = agent_settings(config_root)
-    expected = {
-        "monkey": "monkey",
-        "tokenizer": "tokenizer",
-        "passwordless": "passwordless",
-        "secretary": "secretary",
-    }
-    assert settings.options == expected
-    assert settings.environment == {
-        key.upper(): value for key, value in expected.items()
-    }
+
+    with pytest.raises(ConfigurationError):
+        agent_settings(config_root)
 
 
 def test_agent_settings_copy_and_recursively_freeze_constructor_inputs() -> None:
diff --git a/tests/workflow/test_configuration_rework.py b/tests/workflow/test_configuration_rework.py
new file mode 100644
index 0000000..6ea34ff
--- /dev/null
+++ b/tests/workflow/test_configuration_rework.py
@@ -0,0 +1,135 @@
+from __future__ import annotations
+
+from pathlib import Path
+
+import pytest
+
+from ovcaq.config import (
+    AgentSettings,
+    ConfigurationError,
+    agent_settings,
+    workflow_settings,
+)
+
+
+@pytest.fixture
+def config_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
+    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "user-config"))
+    root = tmp_path / "project"
+    root.mkdir()
+    return root
+
+
+def test_workflow_settings_load_without_an_agent_selection(config_root: Path) -> None:
+    config = config_root / "ovcaq.toml"
+    config.write_text('[workflow]\nprd_root = "requirements"\n')
+
+    settings = workflow_settings(config_root)
+
+    assert settings.prd_root == config_root / "requirements"
+    assert settings.available_tiers == set()
+    assert config.read_text() == '[workflow]\nprd_root = "requirements"\n'
+
+
+def test_workflow_settings_validate_the_selected_agent(config_root: Path) -> None:
+    (config_root / "ovcaq.toml").write_text(
+        'agent = "local"\n[agents.local]\ncommand = []\n'
+    )
+
+    with pytest.raises(ConfigurationError):
+        workflow_settings(config_root)
+
+
+@pytest.mark.parametrize("table", ("environment", "options"))
+@pytest.mark.parametrize(
+    "entry",
+    (
+        'AUTHORIZATION = "synthetic"',
+        'Cookie = "synthetic"',
+        'clientCredential = "synthetic"',
+        'clientcredential = "synthetic"',
+        '"service-api-key-file" = "synthetic"',
+        'VALUE = "authorization=synthetic-value"',
+        'VALUE = "cookie: synthetic-value"',
+        'VALUE = "credential=synthetic-value"',
+        'VALUE = "sk-synthetic_Q7v-k9_42mN8p23R4j62y"',
+        'VALUE = "sk-test-synthetic-Q7v_k9-42mN8p23R4j62y"',
+    ),
+)
+def test_agent_settings_reject_additional_credential_keys_and_pinned_values(
+    config_root: Path, table: str, entry: str
+) -> None:
+    other = "options" if table == "environment" else "environment"
+    (config_root / "ovcaq.toml").write_text(
+        'agent = "local"\n[agents.local]\ncommand = ["runner"]\ntiers = {}\n'
+        f"{other} = {{}}\n{table} = {{ {entry} }}\n"
+    )
+
+    with pytest.raises(ConfigurationError):
+        agent_settings(config_root)
+
+
+@pytest.mark.parametrize(
+    "key",
+    (
+        "SERVICE_TOKEN_HEADER",
+        "CLIENT_SECRET_VALUE",
+        "DATABASE_PASSWORD_FILE",
+        "HEADER_AUTHORIZATION_MODE",
+        "PRIMARY_API_KEY_PATH",
+        "SESSION_COOKIE_VALUE",
+        "CLIENT_CREDENTIAL_FILE",
+        "clientcredential",
+        "service-api-key-file",
+    ),
+)
+@pytest.mark.parametrize("table", ("environment", "options"))
+def test_direct_agent_settings_reject_credential_key_substrings(
+    table: str, key: str
+) -> None:
+    environment = {key: "synthetic"} if table == "environment" else {}
+    options = {key: "synthetic"} if table == "options" else {}
+    with pytest.raises(ConfigurationError):
+        AgentSettings(
+            name="local",
+            command=("local",),
+            tiers={},
+            environment=environment,
+            options=options,
+        )
+
+
+@pytest.mark.parametrize(
+    "environment,options",
+    (
+        ({"MODE": "authorization=synthetic-value"}, {}),
+        ({"MODE": "sk-synthetic_Q7v-k9_42mN8p23R4j62y"}, {}),
+        ({}, {"value": "cookie: synthetic-value"}),
+        ({}, {"value": "sk-test-synthetic-Q7v_k9-42mN8p23R4j62y"}),
+        ({}, {"nested": [{"value": "credential=synthetic-value"}]}),
+    ),
+)
+def test_direct_agent_settings_reject_pinned_credential_values(
+    environment: dict[str, str], options: dict[str, object]
+) -> None:
+    with pytest.raises(ConfigurationError):
+        AgentSettings(
+            name="local",
+            command=("local",),
+            tiers={},
+            environment=environment,
+            options=options,
+        )
+
+
+def test_agent_settings_allow_ordinary_environment_controls(config_root: Path) -> None:
+    (config_root / "ovcaq.toml").write_text(
+        'agent = "local"\n[agents.local]\ncommand = ["runner"]\n'
+        "tiers = {}\noptions = {}\n"
+        'environment = { TERM = "dumb", NO_COLOR = "1", CI = "true" }\n'
+    )
+
+    settings = agent_settings(config_root)
+
+    assert settings.command == ("runner",)
+    assert settings.environment == {"TERM": "dumb", "NO_COLOR": "1", "CI": "true"}
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Command: UV_CACHE_DIR=/private/tmp/ovcaq-autocodex-uv-cache mise exec -- uv run pytest -q tests/workflow/test_configuration.py tests/workflow/test_configuration_rework.py tests/events/test_model_rework.py
Exit: 0
........................................................................ [ 53%]
..............................................................           [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cdb49c8a-c459-4905-898a-39f34054ad35
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-cdb49c8a-c459-4905-898a-39f34054ad35'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-425a05fa-e21b-415b-9298-ad34a77783d8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-425a05fa-e21b-415b-9298-ad34a77783d8'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
134 passed, 2 warnings in 0.14s


Judge only from this prompt: the diff above, the task text, and this recorded
result. Do not read other files, run commands, or re-run the tests. What is not
in this prompt is not evidence, and a finding you cannot ground in what is here
is one you should not report.

# Simplification Mandate (step 5.7 reviewer-prompt appendix)

Append this block **verbatim** to every per-task code-reviewer prompt (see
`SKILL.md` step 5.7). It ships inside the prompt, so it must stay
self-contained.

> Beyond bugs, actively hunt for simplification in the diff under review. For
> every added or changed file, ask "what would make this simpler to read
> without changing what it does?" and flag concrete behavior-preserving
> opportunities to: reduce complexity (needless indirection, dead branches,
> single-caller abstractions, nesting deeper than 4 levels, functions over 50
> lines); eliminate redundancy (logic duplicated within the diff or against
> existing code, a helper that reimplements a stdlib or existing utility);
> improve naming (names that state intent, no opaque abbreviations); and
> remove dead code. Follow CLAUDE.md / AGENTS.md conventions and the
> surrounding code's style.
>
> Report each concrete behavior-preserving simplification as a LOW finding,
> with file:line, the current shape, and the simpler replacement. LOW findings
> are carried to the PRD-level review, never retried here.
>
> Do not over-simplify: never propose a change that trades clarity for
> brevity, drops error handling, collapses a deliberate boundary, or removes a
> documented invariant. Simpler means easier to read and maintain, not shorter
> at any cost. If a change would alter behavior, it is out of scope — do not
> flag it.


## Reporting contract

Report one finding per line, in exactly this shape:

SEVERITY | file:line | issue | fix

Severities are CRITICAL, HIGH, MEDIUM, LOW.

Severity has a fixed meaning here, and it decides what happens next. MEDIUM is
reserved for a correctness or security defect this diff introduces that its own
tests do not catch: a wrong result, an unhandled error path, data loss,
injection, secret exposure, or a missing authorization check. Style, naming,
duplication, structure and maintainability are LOW, and so is every
behavior-preserving simplification, whatever its size. A LOW is noted and
carried to the PRD-level review; it is never retried in this loop.

If the diff has no findings, emit the literal line:

NO FINDINGS

## Closure verdicts (only when the description carries a findings block)

When the Description above contains a `### Findings (verbatim)` block, this is
a rework task and each quoted finding is a claim to check. Before your findings
lines, emit one verdict per quoted finding, in this shape:

CLOSURE | resolved|unresolved | <the finding, quoted> | <one line of evidence from the diff>

Judge each finding against the diff, not against the commit message and not
against how clean the code reads. A diff that improves the file while leaving
the quoted defect reachable is `unresolved`. Quote the line that resolves it,
or say what still reaches the defect. Emit a verdict for every quoted finding,
including ones you judge already fixed elsewhere.


