
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D2] Tail sweep: tests/runtime/test_adapter_launch_routing.py

Description:
### Findings (verbatim)
- 🟡 tests/runtime/test_adapter_launch_routing.py: tests/runtime/test_adapter_launch_routing.py:30 re-implements the runpy Claude wrapper from tests/runtime/test_supervisor_adapters.py:44. The wrapper rebinds `fake_codex.workflow.__globals__['__file__']` to the Claude fixture, and the new copy adds only an `edge['emit_invocation'](sys.argv[1:])` call. That leaves two copies of a hack tied to fake_codex.py internals, and they will drift apart. Keep one wrapper builder in test_supervisor_adapters.py that always emits the invocation (Codex `main()` already emits it unconditionally) and call it from both files (found by: BOB)


Acceptance criteria:
One shared wrapper; preserve invocation records and both providers.

## Diff under review

```diff
diff --git a/tests/runtime/test_adapter_launch_routing.py b/tests/runtime/test_adapter_launch_routing.py
index 2b3ecf9..5a23e5f 100644
--- a/tests/runtime/test_adapter_launch_routing.py
+++ b/tests/runtime/test_adapter_launch_routing.py
@@ -8,7 +8,11 @@ from pathlib import Path
 
 import pytest
 from tests.runtime.test_supervisor import Harness, rows
-from tests.runtime.test_supervisor_adapters import adapter_harness, prepare_workflow
+from tests.runtime.test_supervisor_adapters import (
+    adapter_harness,
+    prepare_workflow,
+    workflow_fixture,
+)
 
 from ovcaq.config import supervisor_settings
 from ovcaq.drivers.edge import build_driver
@@ -26,18 +30,7 @@ def configured_workflow(
 ) -> Harness:
     h = adapter_harness(tmp_path, monkeypatch)
     monkeypatch.setenv("CODEX_HOME", str(tmp_path / "provider-home"))
-    fake = Path(__file__).parents[1] / "fixtures/codex/v1/fake_codex.py"
-    if provider == "claude":
-        claude_fixture = fake.parents[2] / "claude/v1/fake_claude.py"
-        wrapper = tmp_path / "fake_claude_workflow.py"
-        wrapper.write_text(
-            "import runpy, sys\n"
-            f"edge = runpy.run_path({str(fake)!r})\n"
-            f"edge['workflow'].__globals__['__file__'] = {str(claude_fixture)!r}\n"
-            "edge['emit_invocation'](sys.argv[1:])\n"
-            "raise SystemExit(edge['workflow']())\n"
-        )
-        fake = wrapper
+    fake = workflow_fixture(tmp_path, provider)
     command = [sys.executable, "-u", str(fake)]
     cli = str(Path(sys.executable).with_name("ovcaq"))
     (h.root / "ovcaq.toml").write_text(
diff --git a/tests/runtime/test_supervisor_adapters.py b/tests/runtime/test_supervisor_adapters.py
index 5d2111c..1305449 100644
--- a/tests/runtime/test_supervisor_adapters.py
+++ b/tests/runtime/test_supervisor_adapters.py
@@ -37,17 +37,23 @@ def adapter_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
     return h
 
 
-def workflow_agent(h: Harness, tmp_path: Path, provider: str) -> AgentSettings:
+def workflow_fixture(tmp_path: Path, provider: str) -> Path:
     fixtures = Path(__file__).parents[1] / "fixtures"
     fake = fixtures / "codex/v1/fake_codex.py"
     if provider == "claude":
         fake = tmp_path / "fake_claude_workflow.py"
         fake.write_text(
-            "import runpy\n"
+            "import runpy, sys\n"
             f"edge = runpy.run_path({str(fixtures / 'codex/v1/fake_codex.py')!r})\n"
             f"edge['workflow'].__globals__['__file__'] = {str(fixtures / 'claude/v1/fake_claude.py')!r}\n"
+            "edge['emit_invocation'](sys.argv[1:])\n"
             "raise SystemExit(edge['workflow']())\n"
         )
+    return fake
+
+
+def workflow_agent(h: Harness, tmp_path: Path, provider: str) -> AgentSettings:
+    fake = workflow_fixture(tmp_path, provider)
     command = [sys.executable, str(fake)]
     environment = {
         "OVCAQ_FAKE_SCENARIO": "workflow",
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

uv --cache-dir /private/tmp/ovcaq-uv-cache run pytest tests/runtime/test_supervisor_adapters.py tests/runtime/test_adapter_launch_routing.py -q
exit 0; 8 passed, 2 warnings in 6.50s; approved ps-access retry after sandbox failure.

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


