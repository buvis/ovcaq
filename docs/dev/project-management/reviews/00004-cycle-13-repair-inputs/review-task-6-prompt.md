
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D13] Remove redundant child origin assertions (S)


Description:
Review cycle 13 follow-up. PAUSED: no execution is authorized by the connectivity recovery or this artifact. Operator recovery must authorize repairs; preserve the fresh work/review boundary.

### Findings (verbatim)
- low: B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant | File: tests/packaging/rework_12_scripts.py:84 | Consensus: 1/3

### Acceptance criteria
Every quoted finding no longer reproduces. Keep the parent-side installed-root/site-packages/module-origin verification on every subprocess result and event; remove only proven redundant child assertions.

### Evidence
Review: dev/local/reviews/00004-workflow-core-v1-review-13.md
Probe: dev/local/reviews/00004-cycle-13-approved-installed-probe.json
Original work base, cycle 13 and cap 2 remain unchanged.


Acceptance criteria:
Every quoted finding no longer reproduces. Keep the parent-side installed-root/site-packages/module-origin verification on every subprocess result and event; remove only proven redundant child assertions.


## Diff under review

```diff
diff --git a/tests/packaging/rework_12_scripts.py b/tests/packaging/rework_12_scripts.py
index c6cfb4f..4e22786 100644
--- a/tests/packaging/rework_12_scripts.py
+++ b/tests/packaging/rework_12_scripts.py
@@ -9,14 +9,11 @@ from pathlib import Path
 
 def installed_origins() -> dict[str, str]:
     origins = {}
-    prefix = Path(sys.prefix).resolve()
     for name, module in tuple(sys.modules.items()):
         if name == "ovcaq" or name.startswith("ovcaq."):
             filename = getattr(module, "__file__", None)
             assert filename, f"product module has no origin: {name}"
             path = Path(filename).resolve()
-            assert path.is_relative_to(prefix), (name, filename, str(prefix))
-            assert "site-packages" in path.parts, (name, filename)
             origins[name] = str(path)
     assert "ovcaq" in origins
     return origins
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Operator explicitly authorized repairs of tasks 4–6; the PAUSED statement in the historical task description is superseded by that recorded authorization. Task 6 qualifies for the installed work skill's micro lane: one LOW finding in one clean file. Coordinator removed only the two child location assertions and their now-unused prefix binding, net -3 lines in one file. The filename and package-presence guards remain.

mise exec -- uv run --offline --no-sync pytest tests/packaging/test_rework_12.py tests/packaging/test_rework_13.py -q --basetemp /private/tmp/ovcaq-r13-task6
Exit 0: 11 passed in 1.95s. These tests cover every consumer of this child helper, including crash/peer subprocess events, installed origin collection, replacements, native search-only access, root confirmation and external ancestors. Style-limit and split-hygiene checks passed.

Coordinator inspected the unchanged parent consumers. Both _assert_installed helpers in tests/packaging/test_rework_12.py:19 and tests/packaging/test_rework_13.py:19 loop over each module/filename, resolve Path(filename), and assert path.is_relative_to(installed.root.resolve()) plus "site-packages" in path.parts. The first requires "ovcaq" in origins; the second requires "ovcaq.workflow.records" in origins. Every parsed child result/event passes through these helpers. Child filename and package-presence guards remain because only the two location assertions have been established as redundant across all consumers.


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


