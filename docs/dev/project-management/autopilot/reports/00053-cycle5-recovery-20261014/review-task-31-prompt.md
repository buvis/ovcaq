
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D5] tests/runtime/test_adapter_health.py


Description:
### Findings (verbatim)
- ⚪ tests/runtime/test_adapter_health.py:229: docs/driver-protocol.md:36 says both native adapters fall back to the standard default search path when the host PATH is missing. Only Claude has a test for this (`test_claude_probe_uses_default_search_path_when_host_path_is_absent`). The design says to "reproduce and regress" the existing Codex probe behavior. Parametrize the test over ("claude", "codex") and drop "claude" from its name. As I read `os.get_exec_path`, the patched `os.defpath` also steers the Codex subprocess lookup (not run) (found by: BOB)



Acceptance criteria:
Every quoted finding no longer reproduces; no unrelated change.


## Diff under review

```diff
diff --git a/tests/runtime/test_adapter_health.py b/tests/runtime/test_adapter_health.py
index 58bd563..448a026 100644
--- a/tests/runtime/test_adapter_health.py
+++ b/tests/runtime/test_adapter_health.py
@@ -226,9 +226,11 @@ def test_probe_preserves_absolute_executable_with_unrelated_overlay_path(
     assert_probe_evidence(provider, log, marker, healthy=True)
 
 
-def test_claude_probe_uses_default_search_path_when_host_path_is_absent(
+@pytest.mark.parametrize("provider", ("claude", "codex"))
+def test_probe_uses_default_search_path_when_host_path_is_absent(
     tmp_path: Path,
     monkeypatch: pytest.MonkeyPatch,
+    provider: str,
 ) -> None:
     log, marker = tmp_path / "probe.jsonl", tmp_path / "phase-exec"
     executable = fake_executable(tmp_path / "default-bin", log, marker)
@@ -236,11 +238,11 @@ def test_claude_probe_uses_default_search_path_when_host_path_is_absent(
     monkeypatch.delenv("PATH", raising=False)
     assert shutil.which(executable.name) is None
 
-    health = driver_for("claude", executable.name, {}).probe()
+    health = driver_for(provider, executable.name, {}).probe()
 
     assert health.healthy is True
     assert health.detail.strip()
-    assert_probe_evidence("claude", log, marker, healthy=True)
+    assert_probe_evidence(provider, log, marker, healthy=True)
 
 
 @pytest.mark.parametrize("command_kind", ("fixture", "default-path"))
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Command: mise exec -- uv run pytest tests/runtime/test_adapter_health.py -k uses_default_search_path_when_host_path_is_absent -q --tb=line
Exit: 0
Runner summary: 2 passed, 22 deselected, 2 warnings in 1.06s
Warnings concern pytest temporary-directory cleanup. Executed once by the isolated worker; raw output retained in its rollout.


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


