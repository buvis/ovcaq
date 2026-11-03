
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D2] Tail sweep: tests/runtime/test_supervisor_adapters.py


Description:
### Findings (verbatim)
- ⚪ tests/runtime/test_supervisor_adapters.py:40: Carried Pat18 LOW: `workflow_fixture` writes the Claude wrapper file and returns its path, but its name is a noun. Action functions should start with a verb, e.g. `write_workflow_fixture` (call sites tests/runtime/test_supervisor_adapters.py:56 and tests/runtime/test_adapter_launch_routing.py:33). The new helpers `configured_workflow` (tests/runtime/test_adapter_launch_routing.py:24) and `configured_driver` (tests/drivers/test_codex_launch.py:30) have the same shape. Against renaming: the older helpers in the same file (`adapter_harness`, `workflow_agent`) also use nouns, so a rename would break from the file's current style (found by: ALICE, BOB)



Acceptance criteria:
Rename workflow_fixture to write_workflow_fixture, configured_workflow to configure_workflow, configured_driver to configure_driver; update references. Preserve behavior, signatures, assertions. No unrelated helper renames.


## Diff under review

```diff
diff --git a/tests/drivers/test_codex_launch.py b/tests/drivers/test_codex_launch.py
index 4d537c1..82da4d4 100644
--- a/tests/drivers/test_codex_launch.py
+++ b/tests/drivers/test_codex_launch.py
@@ -27,7 +27,7 @@ def toml_value(value: object) -> str:
     return json.dumps(value)
 
 
-def configured_driver(
+def configure_driver(
     settings: AgentSettings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
 ) -> AgentDriver:
     root = tmp_path / "configured-project"
@@ -86,7 +86,7 @@ def test_launch_has_exact_order_and_omits_unconfigured_flags(
     monkeypatch: pytest.MonkeyPatch,
 ) -> None:
     driver = (
-        configured_driver(settings, tmp_path, monkeypatch)
+        configure_driver(settings, tmp_path, monkeypatch)
         if use_factory
         else CodexDriver(settings, run_id="launch-contract")
     )
@@ -209,7 +209,7 @@ def test_arbitrary_explicit_models_require_the_opt_in(
     options = {} if allow is None else {"allow_explicit_model": allow}
     selected = replace(settings, options=options)
     driver = (
-        configured_driver(selected, tmp_path, monkeypatch)
+        configure_driver(selected, tmp_path, monkeypatch)
         if use_factory
         else CodexDriver(selected, run_id="explicit-model")
     )
diff --git a/tests/runtime/test_adapter_launch_routing.py b/tests/runtime/test_adapter_launch_routing.py
index 5a23e5f..52ec8d6 100644
--- a/tests/runtime/test_adapter_launch_routing.py
+++ b/tests/runtime/test_adapter_launch_routing.py
@@ -11,7 +11,7 @@ from tests.runtime.test_supervisor import Harness, rows
 from tests.runtime.test_supervisor_adapters import (
     adapter_harness,
     prepare_workflow,
-    workflow_fixture,
+    write_workflow_fixture,
 )
 
 from ovcaq.config import supervisor_settings
@@ -21,7 +21,7 @@ from ovcaq.runtime.session import reconcile_metrics
 from ovcaq.runtime.supervisor import Supervisor
 
 
-def configured_workflow(
+def configure_workflow(
     tmp_path: Path,
     monkeypatch: pytest.MonkeyPatch,
     tiers: dict[str, str],
@@ -30,7 +30,7 @@ def configured_workflow(
 ) -> Harness:
     h = adapter_harness(tmp_path, monkeypatch)
     monkeypatch.setenv("CODEX_HOME", str(tmp_path / "provider-home"))
-    fake = workflow_fixture(tmp_path, provider)
+    fake = write_workflow_fixture(tmp_path, provider)
     command = [sys.executable, "-u", str(fake)]
     cli = str(Path(sys.executable).with_name("ovcaq"))
     (h.root / "ovcaq.toml").write_text(
@@ -104,7 +104,7 @@ def test_configured_supervisor_launches_each_selected_literal_model_and_effort(
     routes: tuple[tuple[str, str, str], ...],
     provider: str,
 ) -> None:
-    h = configured_workflow(tmp_path, monkeypatch, tiers, routes, provider)
+    h = configure_workflow(tmp_path, monkeypatch, tiers, routes, provider)
     settings = supervisor_settings(
         h.root, runtime=h.settings.runtime, policy=h.settings.policy
     )
diff --git a/tests/runtime/test_supervisor_adapters.py b/tests/runtime/test_supervisor_adapters.py
index 1305449..12673c6 100644
--- a/tests/runtime/test_supervisor_adapters.py
+++ b/tests/runtime/test_supervisor_adapters.py
@@ -37,7 +37,7 @@ def adapter_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
     return h
 
 
-def workflow_fixture(tmp_path: Path, provider: str) -> Path:
+def write_workflow_fixture(tmp_path: Path, provider: str) -> Path:
     fixtures = Path(__file__).parents[1] / "fixtures"
     fake = fixtures / "codex/v1/fake_codex.py"
     if provider == "claude":
@@ -53,7 +53,7 @@ def workflow_fixture(tmp_path: Path, provider: str) -> Path:
 
 
 def workflow_agent(h: Harness, tmp_path: Path, provider: str) -> AgentSettings:
-    fake = workflow_fixture(tmp_path, provider)
+    fake = write_workflow_fixture(tmp_path, provider)
     command = [sys.executable, str(fake)]
     environment = {
         "OVCAQ_FAKE_SCENARIO": "workflow",

```

## Recorded verification

The task's tests were run before this review. This is what they reported:

mise exec -- uv run pytest -q --tb=line tests/runtime/test_supervisor_adapters.py tests/runtime/test_adapter_launch_routing.py tests/drivers/test_codex_launch.py
Exit 1. 8 failed, 73 passed, 2 warnings in 0.22s. All eight failures are PermissionError: Operation not permitted: ps. Worker initial and escalated runs and coordinator escalated retry confirm host restriction. Test counts and failures are retained, not green.
Style limits and split hygiene exit 0.


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


