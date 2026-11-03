
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D1] tests/drivers/

Description:
### Findings (verbatim)
- 🟡 tests/drivers/test_adapter_outcomes.py:1: The Phase 0 acceptance command (`tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_decode_terminals.py`) does not test the capacity WAIT and retry exhaustion, the unrelated-number negatives, or HTTP positives that rely on the number alone. Those tests live in tests/drivers/test_adapter_failure_classes.py, a file the PRD does not list, so the stated acceptance run passes without proving them. (found by: BLAKE)
- 🟡 tests/drivers/test_adapter_outcomes.py: The normal sequence spawn → wait(completed) → close_agent(shutdown) now emits raw.unknown for every completed lane, which sets the TUI raw-evidence flag (tui/model.py:548). Late running/errored/completed updates for a finished lane are dropped with no trace (codex.py:383). No test asserts either outcome, so the design's "raw-unknown evidence" rule is unpinned (found by: BOB)
- 🟡 tests/drivers/test_adapter_outcomes.py: 40 of the 49 new outcome test cases pass on the pre-change code and repeat existing tests: test_codex_rework_decode.py:201 already covers an unfinished lane failing on close, and test_codex_decode_lanes.py:257 covers an unstarted receiver staying raw. The 3-way receiver-name parametrization exercises no extra code path, and `test_non_json_output_retains_raw_unknown` has nothing to do with lanes (found by: BOB)
- ⚪ tests/drivers/test_codex_launch.py: `test_configured_factory_rejects_unknown_or_invalid_options` re-tests `CodexDriver.__init__`, which the new subclass does not override, and passes on the pre-change code. Its `pytest.raises(ValueError)` also accepts `ConfigurationError` (a ValueError subclass) raised by config parsing, so it can pass for the wrong reason (found by: BOB)


Acceptance criteria:
Close every quoted finding; preserve existing behavior.

## Diff under review

```diff
diff --git a/docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md b/docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
index 04e4da1..2f839ae 100644
--- a/docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
+++ b/docs/dev/project-management/prds/wip/00053-adapter-operational-corrections-v1.md
@@ -82,6 +82,7 @@ Keep driver API 2, observation protocol 1 and state schema 1 unchanged.
 src/ovcaq/drivers/{codex.py,codex_events.py,claude.py}
 src/ovcaq/drivers/edge.py                 # existing edge factories
 tests/drivers/test_adapter_outcomes.py   # new behavioral regressions
+tests/drivers/test_adapter_failure_classes.py
 tests/drivers/test_codex_decode_terminals.py
 tests/runtime/test_adapter_launch_routing.py # new real-fake launch checks
 tests/runtime/test_adapter_health.py     # new no-spawn/overlay checks
@@ -122,6 +123,7 @@ CHANGELOG.md
 **Tasks**:
 - [ ] Repair native outcomes and independent fixture expectations (no deps).
   Acceptance: `uv run pytest tests/drivers/test_adapter_outcomes.py
+  tests/drivers/test_adapter_failure_classes.py
   tests/drivers/test_codex_decode_terminals.py` covers each completed/unfinished
   lane status, capacity WAIT and retry exhaustion, genuine HTTP diagnostics,
   unrelated numeric counts, and all failure fixtures with literal expected classes.
diff --git a/tests/drivers/test_adapter_outcomes.py b/tests/drivers/test_adapter_outcomes.py
index d6a1785..4a9d7f4 100644
--- a/tests/drivers/test_adapter_outcomes.py
+++ b/tests/drivers/test_adapter_outcomes.py
@@ -85,7 +85,6 @@ def test_completed_lane_remains_completed_after_close_status(
         observation.type == ObservationType.LANE_FAILED for observation in completed
     )
 
-    decode(driver, collab_record("running", tool="wait"))
     closed = decode(driver, collab_record(child_status, tool=tool))
     assert any(
         observation.type == ObservationType.RAW_UNKNOWN for observation in closed
@@ -99,15 +98,12 @@ def test_completed_lane_remains_completed_after_close_status(
 
 @pytest.mark.parametrize("tool", ["wait", "close_agent"])
 @pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
-@pytest.mark.parametrize("receiver", ["child", "reviewer-17", "thread-blue"])
 def test_unfinished_lane_fails_after_close_status(
-    driver: CodexDriver, tool: str, child_status: str, receiver: str
+    driver: CodexDriver, tool: str, child_status: str
 ) -> None:
-    start_lane(driver, receiver)
+    start_lane(driver)
 
-    observations = decode(
-        driver, collab_record(child_status, tool=tool, receiver=receiver)
-    )
+    observations = decode(driver, collab_record(child_status, tool=tool))
 
     failures = [
         observation
@@ -115,7 +111,7 @@ def test_unfinished_lane_fails_after_close_status(
         if observation.type == ObservationType.LANE_FAILED
     ]
     assert len(failures) == 1
-    assert failures[0].lane_id == receiver
+    assert failures[0].lane_id == "child"
     assert not any(
         observation.type == ObservationType.LANE_COMPLETED
         for observation in observations
@@ -123,17 +119,13 @@ def test_unfinished_lane_fails_after_close_status(
 
 
 @pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
-@pytest.mark.parametrize(
-    ("receiver", "unknown_receiver"),
-    [("child", "unseen"), ("reviewer-17", "missing-23"), ("thread-blue", "other")],
-)
 def test_unknown_receiver_close_retains_raw_unknown(
-    driver: CodexDriver, child_status: str, receiver: str, unknown_receiver: str
+    driver: CodexDriver, child_status: str
 ) -> None:
-    start_lane(driver, receiver)
+    start_lane(driver)
 
     raw_line = json.dumps(
-        collab_record(child_status, tool="close_agent", receiver=unknown_receiver)
+        collab_record(child_status, tool="close_agent", receiver="unseen")
     )
     observations = driver.decode(raw_line)
 
@@ -146,14 +138,12 @@ def test_unknown_receiver_close_retains_raw_unknown(
     assert not any(
         observation.type == ObservationType.LANE_FAILED for observation in observations
     )
-    known_receiver = decode(
-        driver, collab_record(child_status, tool="close_agent", receiver=receiver)
-    )
+    known_receiver = decode(driver, collab_record(child_status, tool="close_agent"))
     assert [
         observation.lane_id
         for observation in known_receiver
         if observation.type == ObservationType.LANE_FAILED
-    ] == [receiver]
+    ] == ["child"]
 
 
 @pytest.mark.parametrize("child_status", ["interrupted", "shutdown", "not_found"])
@@ -172,7 +162,6 @@ def test_repeated_close_does_not_fail_lane_again(
         == 1
     )
 
-    decode(driver, collab_record("running", tool="wait"))
     repeated_close = decode(driver, record)
 
     assert not any(
@@ -265,17 +254,41 @@ def test_unrelated_event_type_does_not_transition_lane(
     ] == ["child"]
 
 
-def test_non_json_output_retains_raw_unknown(driver: CodexDriver) -> None:
-    raw_line = "receiver output: {unfinished JSON"
-    observations = driver.decode(raw_line)
-    assert any(
-        observation.type == ObservationType.RAW_UNKNOWN
-        and observation.payload["raw_sha256"] == sha256(raw_line.encode()).hexdigest()
-        and observation.payload["preview"] == raw_line[:512]
-        for observation in observations
-    )
-    assert not any(
+@pytest.mark.parametrize(
+    ("terminal_status", "terminal_type"),
+    [
+        ("completed", ObservationType.LANE_COMPLETED),
+        ("errored", ObservationType.LANE_FAILED),
+    ],
+    ids=["completed", "failed"],
+)
+@pytest.mark.parametrize("late_status", ["running", "errored", "completed"])
+def test_finished_lane_late_update_retains_only_non_lane_observations(
+    driver: CodexDriver,
+    terminal_status: str,
+    terminal_type: ObservationType,
+    late_status: str,
+) -> None:
+    start_lane(driver)
+    terminal = decode(driver, collab_record(terminal_status, tool="wait"))
+    assert [
+        (observation.type, observation.lane_id)
+        for observation in terminal
+        if observation.type
+        in (ObservationType.LANE_COMPLETED, ObservationType.LANE_FAILED)
+    ] == [(terminal_type, "child")]
+
+    observations = decode(driver, collab_record(late_status, tool="wait"))
+
+    assert observations
+    assert all(
         observation.type
-        in (ObservationType.LANE_FAILED, ObservationType.LANE_COMPLETED)
+        not in (
+            ObservationType.LANE_STARTED,
+            ObservationType.LANE_PROGRESS,
+            ObservationType.LANE_FAILED,
+            ObservationType.LANE_COMPLETED,
+            ObservationType.RAW_UNKNOWN,
+        )
         for observation in observations
     )
diff --git a/tests/drivers/test_codex_launch.py b/tests/drivers/test_codex_launch.py
index df19498..c67744c 100644
--- a/tests/drivers/test_codex_launch.py
+++ b/tests/drivers/test_codex_launch.py
@@ -167,21 +167,9 @@ INVALID_OPTIONS = (
 def test_constructor_rejects_unknown_or_invalid_options(
     settings: AgentSettings, options: dict[str, object]
 ) -> None:
-    with pytest.raises(ValueError):
+    with pytest.raises(ValueError) as raised:
         CodexDriver(replace(settings, options=options), run_id="invalid-options")
-
-
-@pytest.mark.parametrize(
-    "options", [options for options in INVALID_OPTIONS if None not in options.values()]
-)
-def test_configured_factory_rejects_unknown_or_invalid_options(
-    settings: AgentSettings,
-    options: dict[str, object],
-    tmp_path: Path,
-    monkeypatch: pytest.MonkeyPatch,
-) -> None:
-    with pytest.raises(ValueError):
-        configured_driver(replace(settings, options=options), tmp_path, monkeypatch)
+    assert raised.type is ValueError
 
 
 @pytest.mark.parametrize(
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

uv run --cache-dir /private/tmp/ovcaq-uv-cache pytest -q --tb=line tests/drivers/test_adapter_outcomes.py tests/drivers/test_codex_launch.py tests/drivers/test_adapter_failure_classes.py tests/drivers/test_codex_decode_terminals.py
exit 0; 230 passed; two pre-existing cleanup warnings

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


