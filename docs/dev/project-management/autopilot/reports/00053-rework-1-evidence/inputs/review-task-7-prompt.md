
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D1] src/ovcaq/drivers/

Description:
### Findings (verbatim)
- 🟠 src/ovcaq/drivers/codex_events.py:301: Numeric diagnostics now need "HTTP", "HTTP status", "status code" or "error code" (src/ovcaq/drivers/codex_events.py:301), so Codex's own status wording falls to UNKNOWN. I ran `classify_failure` on "unexpected status 503 Service Unavailable", "unexpected status 502 Bad Gateway", "unexpected status 403 Forbidden" and "exceeded retry limit, last status: 429 Too Many Requests", and all four return `unknown`. The old code returned connectivity, permission and rate_limit for these. Both prefixes are confirmed as strings in the installed codex 0.162.1 binary; the "503 Service Unavailable" suffix is my guess at how Codex renders the code. Effect: 502/503 skip the bounded connectivity WAIT and get an immediate died-retry and then PARK, and 403 retries instead of halting for the operator. The PRD allows "HTTP/status/error-code" context, and "status 503" is a status context. Fix: accept a bare `status` (e.g. `(?:http(?: status)? | status(?: code)? | error code)`) and add both Codex spellings as literal positives in tests/drivers/test_adapter_failure_classes.py:55 (found by: ALICE, BLAKE, BOB)
- 🟡 src/ovcaq/drivers/codex.py:372: Only the `continue` at src/ovcaq/drivers/codex.py:383 is pinned by tests. The unfinished-only `started_lanes` filter at src/ovcaq/drivers/codex.py:372 is not: dropping it still suppresses LANE_FAILED through the `continue`, and no test asserts the RAW_UNKNOWN that the design requires for a close status on a completed lane (I ran it: completed then shutdown gives `raw.unknown`; that the tests miss its removal comes from reading them, not a run). Add a RAW_UNKNOWN assertion on `closed` in `test_completed_lane_remains_completed_after_close_status` (tests/drivers/test_adapter_outcomes.py:89) (found by: ALICE)
- 🟡 src/ovcaq/drivers/edge.py: `_ResolvedModelCodexDriver.build_launch` copies `_ResolvedModelClaudeDriver.build_launch` line for line. A module helper `_tier_request(settings, request)` would leave each override as one line: `return super().build_launch(_tier_request(self._settings, request))` (found by: BOB)
- ⚪ src/ovcaq/drivers/codex.py:383: The `continue` at codex.py:383 freezes failed lanes as well as completed ones, and silently drops late `errored`/`running`/`completed` updates with no raw-unknown evidence (I ran it: completed then errored gives only `tool.completed`, while completed then shutdown gives `raw.unknown`). docs/driver-protocol.md:242 describes only completed lanes. Document that failed lanes also stay terminal, or emit raw evidence consistently (found by: ALICE)
- ⚪ src/ovcaq/drivers/codex_events.py:307: The new `authentication failed` pattern goes beyond "retain existing word diagnostics". The authentication fixture already classifies through "invalid credentials", and the new pattern widens the authentication HALT to messages like "MCP server authentication failed" (found by: ALICE)
- ⚪ src/ovcaq/drivers/codex_events.py:233: A normal Codex sub-agent run (spawn running, then wait completed, then close_agent shutdown) now emits `raw.unknown` on every close of a completed lane. I confirmed this with a real decode run. It sets the TUI's raw-evidence flag (src/ovcaq/tui/model.py:548). The doc at docs/driver-protocol.md:244 says only unstarted receivers and missing attribution produce raw unknown evidence. (found by: BLAKE)


Acceptance criteria:
Close every quoted finding while retaining public contracts.

## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 9df5784..8fbdcfb 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -42,8 +42,8 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 
 - **drivers**: check both native adapters' executables against the effective host-plus-configured PATH, preserving standard missing/empty host PATH lookup; empty configured PATH remains invalid.
 - **drivers**: preserve once-resolved supervised Codex models when their names also match tier keys, retaining direct tier-key precedence and explicit-model validation.
-- **drivers**: require HTTP/status/error-code context for Codex numeric diagnostics and retry model capacity as connectivity through bounded WAIT/retry exhaustion; genuine rate/quota limits and reset parsing remain unchanged.
-- **drivers**: keep completed Codex receiver lanes terminal under late running, interrupted, shutdown and not-found updates; synthetic close failures apply only to remembered unfinished lanes.
+- **drivers**: require HTTP/status/error-code context, including native bare status diagnostics, for Codex numeric failures and retry model capacity as connectivity through bounded WAIT/retry exhaustion; retain existing authentication word diagnostics and genuine rate/quota limits.
+- **drivers**: keep completed and failed Codex receiver lanes terminal under late updates; synthetic close failures apply only to remembered unfinished lanes, while closes of terminal lanes retain raw unknown evidence.
 - **drivers**: redact diagnostic credentials both before and after terminal control removal, preserving original token boundaries and hiding reconstructed tokens before truncation.
 - **events**: speed up surrogate detection while preserving original-container validation and tolerant native preflight handling.
 - **drivers**: remove terminal controls before redacting and bounding Codex diagnostic details so split credentials cannot survive normalization.
diff --git a/docs/driver-protocol.md b/docs/driver-protocol.md
index 5725833..b1ef602 100644
--- a/docs/driver-protocol.md
+++ b/docs/driver-protocol.md
@@ -239,11 +239,12 @@ removal is outside this diagnostic-helper contract.
 
 Collaboration requires `agents_states` keys matching native receiver thread
 IDs. Pending/running receivers start or progress a lane, completed receivers
-complete it, and errored receivers fail it. Completed lanes remain terminal
-under late pending/running, interrupted, shutdown and not-found updates.
+complete it, and errored receivers fail it. Completed and failed lanes remain
+terminal under all late receiver updates. Late pending/running, completed and
+errored updates for terminal lanes do not emit lane observations.
 Interrupted, shutdown and not-found receivers emit `lane.failed` only for
-remembered unfinished lanes; unstarted receivers and missing attribution remain
-raw unknown evidence.
+remembered unfinished lanes; these close statuses for terminal or unstarted
+receivers, and missing attribution, remain raw unknown evidence.
 Lane payloads supply `label` and bounded `detail`; a completed collaboration
 tool does not prove receiver completion.
 The checked-in `lanes.jsonl` deliberately mismatches these identities and
diff --git a/src/ovcaq/drivers/codex_events.py b/src/ovcaq/drivers/codex_events.py
index 00274b8..2170b8d 100644
--- a/src/ovcaq/drivers/codex_events.py
+++ b/src/ovcaq/drivers/codex_events.py
@@ -298,13 +298,13 @@ def item_tool(
 def classify_failure(detail: str) -> FailureClass:
     """Match native diagnostics in authentication-to-agent precedence order."""
     detail = " ".join(detail.split())
-    status = r"(?:http(?: status)?|(?:status|error) code)\s*:?\s*"
+    status = r"(?:http(?: status)?|status(?: code)?|error code)\s*:?\s*"
     for failure, pattern in (
         (
             FailureClass.AUTHENTICATION,
             (
                 rf"{status}401|unauthorized|not logged in|"
-                r"(?:invalid|expired) credentials?|authentication failed"
+                r"(?:invalid|expired) credentials?"
             ),
         ),
         (
diff --git a/src/ovcaq/drivers/edge.py b/src/ovcaq/drivers/edge.py
index 0ae0fb8..6bdf6a2 100644
--- a/src/ovcaq/drivers/edge.py
+++ b/src/ovcaq/drivers/edge.py
@@ -6,31 +6,32 @@ from dataclasses import replace
 from pathlib import Path
 from uuid import uuid4
 
-from ovcaq.config import agent_settings
+from ovcaq.config import AgentSettings, agent_settings
 from ovcaq.drivers.base import AgentDriver, LaunchRequest, LaunchSpec
 from ovcaq.drivers.claude import ClaudeDriver
 from ovcaq.drivers.codex import CodexDriver
 from ovcaq.errors import CommandError, ErrorCode
 
 
+def _tier_request(settings: AgentSettings, request: LaunchRequest) -> LaunchRequest:
+    tiers = {model: tier for tier, model in settings.tiers.items()}
+    if request.model in tiers:
+        return replace(request, model=tiers[request.model])
+    return request
+
+
 class _ResolvedModelClaudeDriver(ClaudeDriver):
     """Map the supervisor's resolved model back to its configured tier key."""
 
     def build_launch(self, request: LaunchRequest) -> LaunchSpec:
-        tiers = {model: tier for tier, model in self._settings.tiers.items()}
-        if request.model in tiers:
-            request = replace(request, model=tiers[request.model])
-        return super().build_launch(request)
+        return super().build_launch(_tier_request(self._settings, request))
 
 
 class _ResolvedModelCodexDriver(CodexDriver):
     """Map the supervisor's resolved model back to its configured tier key."""
 
     def build_launch(self, request: LaunchRequest) -> LaunchSpec:
-        tiers = {model: tier for tier, model in self._settings.tiers.items()}
-        if request.model in tiers:
-            request = replace(request, model=tiers[request.model])
-        return super().build_launch(request)
+        return super().build_launch(_tier_request(self._settings, request))
 
 
 def build_driver(root: Path, name: str | None) -> AgentDriver:
diff --git a/tests/drivers/test_adapter_failure_classes.py b/tests/drivers/test_adapter_failure_classes.py
index 8a863fc..6e2ae5d 100644
--- a/tests/drivers/test_adapter_failure_classes.py
+++ b/tests/drivers/test_adapter_failure_classes.py
@@ -60,6 +60,24 @@ def test_numeric_diagnostics_require_an_explicit_status_or_error_context(
     assert classify_failure(template.format(code=code)) is expected
 
 
+@pytest.mark.parametrize(
+    ("detail", "expected"),
+    [
+        ("unexpected status 503 Service Unavailable", FailureClass.CONNECTIVITY),
+        ("unexpected status 502 Bad Gateway", FailureClass.CONNECTIVITY),
+        ("unexpected status 403 Forbidden", FailureClass.PERMISSION),
+        (
+            "exceeded retry limit, last status: 429 Too Many Requests",
+            FailureClass.RATE_LIMIT,
+        ),
+    ],
+)
+def test_explicit_bare_status_diagnostics_are_classified(
+    detail: str, expected: FailureClass
+) -> None:
+    assert classify_failure(detail) is expected
+
+
 @pytest.mark.parametrize("code", ["401", "403", "429", "502", "503"])
 @pytest.mark.parametrize(
     "template",
@@ -99,7 +117,7 @@ def test_numeric_diagnostics_require_a_complete_status_number(code: str) -> None
     [
         ("UnAuThOrIzEd", FailureClass.AUTHENTICATION),
         ("Rate\tlimit reached", FailureClass.RATE_LIMIT),
-        ("Authentication failed", FailureClass.AUTHENTICATION),
+        ("invalid credentials", FailureClass.AUTHENTICATION),
     ],
 )
 def test_native_word_diagnostics_retain_case_and_whitespace_variants(
@@ -108,11 +126,27 @@ def test_native_word_diagnostics_retain_case_and_whitespace_variants(
     assert classify_failure(detail) is expected
 
 
+@pytest.mark.parametrize(
+    "detail", ["Authentication failed", "MCP server authentication failed"]
+)
+def test_generic_authentication_failure_messages_remain_unknown(detail: str) -> None:
+    assert classify_failure(detail) is FailureClass.UNKNOWN
+
+
 @pytest.mark.parametrize(
     ("detail", "expected"),
     [
         ("timeout; connection refused", FailureClass.CONNECTIVITY),
         ("permission denied; not logged in", FailureClass.AUTHENTICATION),
+        ("not logged in; permission denied", FailureClass.AUTHENTICATION),
+        (
+            "unexpected status 403 Forbidden; not logged in",
+            FailureClass.AUTHENTICATION,
+        ),
+        (
+            "not logged in; unexpected status 403 Forbidden",
+            FailureClass.AUTHENTICATION,
+        ),
     ],
 )
 def test_failure_precedence_is_independent_of_diagnostic_order(
diff --git a/tests/drivers/test_adapter_outcomes.py b/tests/drivers/test_adapter_outcomes.py
index 71ded39..d6a1785 100644
--- a/tests/drivers/test_adapter_outcomes.py
+++ b/tests/drivers/test_adapter_outcomes.py
@@ -87,6 +87,9 @@ def test_completed_lane_remains_completed_after_close_status(
 
     decode(driver, collab_record("running", tool="wait"))
     closed = decode(driver, collab_record(child_status, tool=tool))
+    assert any(
+        observation.type == ObservationType.RAW_UNKNOWN for observation in closed
+    )
     assert not any(
         observation.type
         in (ObservationType.LANE_FAILED, ObservationType.LANE_COMPLETED)
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

uv run --cache-dir /private/tmp/ovcaq-uv-cache pytest -q --tb=line tests/drivers/test_adapter_failure_classes.py tests/drivers/test_adapter_outcomes.py
exit 0; 122 passed in 0.08s
Worker broader named run: 218 passed, exit 0; two cleanup warnings.

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


