
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D3] src/ovcaq/drivers/codex_events.py

Description:
### Contract
Production: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex_events.py
Tests: /Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_adapter_failure_classes.py
Changelog: /Users/bob/git/src/github.com/buvis/ovcaq/CHANGELOG.md
Public API: classify_failure(detail: str) -> FailureClass.

### Operator scope resolution
Only explicit diagnostic prefixes are in scope: status=<code>, Error <code>:, and HTTP error <code>, for existing codes 401, 403, 429, 502, 503. Preserve case-insensitivity, existing diagnostic precedence, existing supported forms, ordinary-number negatives, complete-code boundaries, and bounded whitespace behavior. Bare numbers/reason phrases acquire no new contract. Update the existing numeric-classification changelog entry, not a new intra-PRD fix entry. Prior mixed diagnostic-prefix/count grammar, lifecycle and PATH/cwd deferrals remain settled.

Verify: mise exec -- uv run pytest tests/drivers/test_adapter_failure_classes.py -q --tb=line
Acceptance criteria:
- Each explicit spelling maps 401 to authentication, 403 to permission, 429 to rate_limit, and 502/503 to connectivity.
- Existing negative controls, precedence and long-whitespace behavior remain intact.
- No reset grammar, provider-independent runtime, schema or API changes.

### Findings (verbatim)
- 🟡 src/ovcaq/drivers/codex_events.py:300: Some explicit status-code messages now classify as `unknown`. Before this change they classified correctly. Probed: `status=429`, `Error 429: Too Many Requests`, `HTTP error 503`, and bare reason-phrase forms like `429 Too Many Requests` and `503 Service Unavailable`. The spec allows numbers only in explicit HTTP/status/error-code context, and `status=429` and `Error 429:` are exactly that. Worse, tests/drivers/test_adapter_failure_classes.py:115 locks `status=429` and `Error 429:` in as `unknown`, so the wrong answer is now enforced as the expected class. Impact: a real 429 or 503 in these forms goes to the generic retry-then-PARK path instead of the bounded WAIT or rate-limit path. The native Codex forms ("unexpected status N", reqwest, HTTP/x) are covered. (found by: BLAKE)


Acceptance criteria:
status=<code>, Error <code>:, HTTP error <code> classify: 401 -> AUTHENTICATION; 403 -> PERMISSION; 429 -> RATE_LIMIT; 502/503 -> CONNECTIVITY. Matching remains case-insensitive and requires a complete numeric code. Existing ordinary-number negative controls remain unknown. Existing long whitespace inputs must remain bounded; ensure the newly accepted prefix forms do not introduce hangs, using the current child-process timeout pattern if expanding coverage. Keep this narrowly scoped: no broader diagnostic prose or reset grammar.

The operator explicitly scoped out bare number/reason phrases; the verbatim historical finding mentions these but this repair does not promise them. Existing mixed-prefix/count ambiguity remains deferred.


## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 1a5b447..632e431 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -43,7 +43,7 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 - **drivers**: avoid quadratic backtracking when Codex failure diagnostics contain long whitespace runs after a status prefix.
 - **drivers**: check Claude's executable against the effective host-plus-configured PATH, matching subprocess lookup with `os.defpath` when host PATH is absent and treating an empty host PATH as unhealthy. Codex already uses the merged environment and searches the current directory with an empty host PATH; empty configured PATH remains invalid.
 - **drivers**: preserve once-resolved supervised Codex models when their names also match tier keys, retaining direct tier-key precedence and explicit-model validation.
-- **drivers**: require HTTP/status/error-code context, including native bare-status and HTTP-version forms, for Codex numeric failures; retain existing authentication word diagnostics and genuine rate/quota limits.
+- **drivers**: require HTTP/status/error context, including equals-delimited status, bare error, HTTP error, native bare-status and HTTP-version forms, for Codex numeric failures; retain existing authentication word diagnostics and genuine rate/quota limits.
 - **drivers**: classify 'Selected model is at capacity' as connectivity so it gets bounded WAIT retries instead of rate-limit handling.
 - **drivers**: keep remembered completed and failed Codex receiver lanes terminal under late updates; synthetic close failures apply only to remembered unfinished lanes, while closes of terminal lanes retain raw unknown evidence.
 - **drivers**: redact diagnostic credentials both before and after terminal control removal, preserving original token boundaries and hiding reconstructed tokens before truncation.
diff --git a/src/ovcaq/drivers/codex_events.py b/src/ovcaq/drivers/codex_events.py
index b1a7411..7dcbd90 100644
--- a/src/ovcaq/drivers/codex_events.py
+++ b/src/ovcaq/drivers/codex_events.py
@@ -298,8 +298,8 @@ def item_tool(
 def classify_failure(detail: str) -> FailureClass:
     """Match native diagnostics in authentication-to-agent precedence order."""
     status = (
-        r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?)?"
-        r"|status(?: code)?|error code)\s*+:?\s*+"
+        r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?| error)?"
+        r"|status(?: code)?|error(?: code)?)\s*+[:=]?\s*+"
     )
     for failure, pattern in (
         (
diff --git a/tests/drivers/test_adapter_failure_classes.py b/tests/drivers/test_adapter_failure_classes.py
index b8dfbdd..93fca03 100644
--- a/tests/drivers/test_adapter_failure_classes.py
+++ b/tests/drivers/test_adapter_failure_classes.py
@@ -54,7 +54,15 @@ def running_snapshot() -> ProgressSnapshot:
 )
 @pytest.mark.parametrize(
     "template",
-    ["HTTP {code}", "HTTP status: {code}", "status code: {code}", "error code: {code}"],
+    [
+        "HTTP {code}",
+        "HTTP status: {code}",
+        "status code: {code}",
+        "error code: {code}",
+        "StAtUs={code}",
+        "eRrOr {code}:",
+        "hTtP ErRoR {code}",
+    ],
 )
 def test_numeric_diagnostics_require_an_explicit_status_or_error_context(
     code: str, expected: FailureClass, template: str
@@ -112,15 +120,13 @@ def test_reqwest_and_http_version_status_diagnostics_are_classified(
     assert classify_failure(detail) is expected
 
 
-@pytest.mark.parametrize("detail", ["status=429", "Error 429:"])
-def test_unsupported_numeric_status_forms_remain_unknown(detail: str) -> None:
-    assert classify_failure(detail) is FailureClass.UNKNOWN
-
-
-def test_long_whitespace_status_diagnostic_returns_unknown_without_hanging() -> None:
+@pytest.mark.parametrize("prefix", ["status", "status=", "Error", "HTTP error"])
+def test_long_whitespace_status_diagnostic_returns_unknown_without_hanging(
+    prefix: str,
+) -> None:
     script = (
         "from ovcaq.drivers.codex_events import classify_failure\n"
-        'print(classify_failure("status" + " " * 200_000 + "x").value)\n'
+        f'print(classify_failure({prefix!r} + " " * 200_000 + "x").value)\n'
     )
     try:
         result = subprocess.run(
@@ -166,8 +172,15 @@ def test_ordinary_resource_capacity_is_unknown(detail: str) -> None:
 
 
 @pytest.mark.parametrize("code", ["401", "403", "429", "502", "503"])
-def test_numeric_diagnostics_require_a_complete_status_number(code: str) -> None:
-    assert classify_failure(f"HTTP {code}0") is FailureClass.UNKNOWN
+@pytest.mark.parametrize(
+    "template", ["HTTP {code}", "status={code}", "Error {code}:", "HTTP error {code}"]
+)
+@pytest.mark.parametrize("extra_digit", ["{code}0", "0{code}"])
+def test_numeric_diagnostics_require_a_complete_status_number(
+    code: str, template: str, extra_digit: str
+) -> None:
+    detail = template.format(code=extra_digit.format(code=code))
+    assert classify_failure(detail) is FailureClass.UNKNOWN
 
 
 @pytest.mark.parametrize(

```

## Recorded verification

The task's tests were run before this review. This is what they reported:

uv run pytest tests/drivers/test_adapter_failure_classes.py -q --tb=line
exit 0
140 passed in 0.21s
Style and split-hygiene checks exit 0.


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


