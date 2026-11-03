
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D4] src/ovcaq/drivers/codex_events.py


Description:
### Findings (verbatim)
- 🟡 src/ovcaq/drivers/codex_events.py:301: The ` error` branch inside the `http(...)` group of the `status` prefix can never change a result, so it is dead code. The new bare `error(?: code)?` branch already matches every string it catches, because a word boundary always sits between "http " and "error". I checked this by running both regexes on 4,288,305 generated token strings: 0 differences. Simpler version with the same behavior: `r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?)?"`, keeping line 302 as it is. "HTTP error 503" still returns connectivity through the bare `error` branch, so the `hTtP ErRoR {code}` tests keep passing (found by: ALICE, BOB)


Acceptance criteria:
- Remove both redundant ` error` and plain ` status` alternatives inside the HTTP prefix group. Keep the reqwest parenthetical branch and HTTP version branch.
- Preserve all classification behavior, including precedence, status/error label spellings, complete-code boundaries, ordinary-number negatives and possessive whitespace behavior.
- Change only src/ovcaq/drivers/codex_events.py; no new tests or broader grammar.
- This is the approved behavior-preserving micro repair for review-4 R2. Bob's complete merged detail is retained in the canonical review; the task description preserves the consolidated Alice row verbatim.


## Diff under review

```diff
diff --git a/src/ovcaq/drivers/codex_events.py b/src/ovcaq/drivers/codex_events.py
index 7dcbd90..a4247fe 100644
--- a/src/ovcaq/drivers/codex_events.py
+++ b/src/ovcaq/drivers/codex_events.py
@@ -298,7 +298,7 @@ def item_tool(
 def classify_failure(detail: str) -> FailureClass:
     """Match native diagnostics in authentication-to-agent precedence order."""
     status = (
-        r"(?:http(?:/\d+(?:\.\d+)?| status(?: (?:client|server) error \()?| error)?"
+        r"(?:http(?:/\d+(?:\.\d+)?| status (?:client|server) error \()?"
         r"|status(?: code)?|error(?: code)?)\s*+[:=]?\s*+"
     )
     for failure, pattern in (

```

## Recorded verification

The task's tests were run before this review. This is what they reported:

Command: mise exec -- uv run pytest tests/drivers/test_adapter_failure_classes.py -q --tb=line
Exit: 0
Runner summary: 140 passed in 0.22s
Source: native worker /root/ivan27, dispatch 9e1a37c7; raw worker evidence copied beside this record.
git diff --check: exit 0
check_reflow.py src/ovcaq/drivers/codex_events.py: exit 0
check_style_limits.py over task base c621a2c..ca59071: exit 0
The diff is one replacement line and preserves the second regex string and all other patterns.


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


