
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D2] Tail sweep: tests/ (post-sweep)

Description:
### Findings (verbatim, post-sweep review 2026-10-12; authorization reports/00053-postsweep-repair-authorization.md)
- ⚪ tests/runtime/test_adapter_launch_routing.py:114-115: Claude routing cases set every phase effort to "high" with no reason; config accepts low/medium/high/xhigh (src/ovcaq/config.py:364) and ClaudeDriver passes effort through, so pass-through is tested with one value only. Cover at least two distinct effort values, or keep the override with a one-line comment giving the reason if removing it fails (found by: BOB)
- ⚪ tests/drivers/test_codex_launch.py:32: `configured_driver` is annotated `-> CodexDriver` but returns `build_driver(...)` typed `AgentDriver`; annotate `-> AgentDriver` imported from `ovcaq.drivers.base` (found by: BOB)


Acceptance criteria:
Claude efforts must vary and configured_driver must return AgentDriver.

## Diff under review

```diff
diff --git a/tests/drivers/test_codex_launch.py b/tests/drivers/test_codex_launch.py
index d9120fa..4d537c1 100644
--- a/tests/drivers/test_codex_launch.py
+++ b/tests/drivers/test_codex_launch.py
@@ -10,7 +10,7 @@ from pathlib import Path
 import pytest
 
 from ovcaq.config import AgentSettings
-from ovcaq.drivers.base import LaunchRequest
+from ovcaq.drivers.base import AgentDriver, LaunchRequest
 from ovcaq.drivers.codex import CodexDriver
 from ovcaq.drivers.edge import build_driver
 
@@ -29,7 +29,7 @@ def toml_value(value: object) -> str:
 
 def configured_driver(
     settings: AgentSettings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
-) -> CodexDriver:
+) -> AgentDriver:
     root = tmp_path / "configured-project"
     root.mkdir()
     monkeypatch.setenv("HOME", str(tmp_path / "home"))
diff --git a/tests/runtime/test_adapter_launch_routing.py b/tests/runtime/test_adapter_launch_routing.py
index 47eeb5c..2b3ecf9 100644
--- a/tests/runtime/test_adapter_launch_routing.py
+++ b/tests/runtime/test_adapter_launch_routing.py
@@ -111,8 +111,6 @@ def test_configured_supervisor_launches_each_selected_literal_model_and_effort(
     routes: tuple[tuple[str, str, str], ...],
     provider: str,
 ) -> None:
-    if provider == "claude":
-        routes = tuple((phase, tier, "high") for phase, tier, _ in routes)
     h = configured_workflow(tmp_path, monkeypatch, tiers, routes, provider)
     settings = supervisor_settings(
         h.root, runtime=h.settings.runtime, policy=h.settings.policy
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

env UV_CACHE_DIR=/tmp/ovcaq-uv-cache uv run --no-sync pytest tests/runtime/test_adapter_launch_routing.py tests/drivers/test_codex_launch.py -q --tb=line
exit 0; 79 passed, 2 pytest temp cleanup warnings in 5.56s. Sandbox initial run had 6 ps PermissionError failures; approved retry passed. Style and split-hygiene checks exit 0.

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


