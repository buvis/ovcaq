# PRD 00008 recovery task 14

Final metric validation preserves unknown numeric usage without inventing zero. Exact seven fields, boolean estimated, and strict known-number validation remain. The real-adapter regression no longer rewrites tool_uses; its real summary reaches the supervisor unchanged. No state fields or provider parsing changed.

Base cf9bd33306d54fb501b6eaeffe1baf8bdbd2d3ef; initial tests6358ab81540a8b2b3c968613c84b819ef92883dd; strengthened tests668cdf0c2cbf54f68a48cf622a8f76bcb9dd582d; implementationcce42f8159797c60527bcfcbae3f30d6fe76dfc6. Micro eligible1finding/1findingpath but actual3files overran; original slices restored, patch retained. Full pipeline followed.

Native logicalopus/actualgpt-6-astra: Tess5b819df9(16992bytes), Devon531f7160(44958bytes), strengthen5856057c(39076bytes), Ivan0f4c097a(47332bytes). Initial Ivan render28f03d8f measured51735bytes and was NOT dispatched; one allowed trim removed unrelated architecture context, preserving full persona and both canonical test files. Backendopus row2/Qwen tier exclusion means no external Codex rung interception. Tess2/max4, no quality retry. Devon8 independently proven wrong implementations each passed125cases; all original bytes restored independently, tests unchanged. Tess strengthened all8 once; no second Devon round. Main additionally required independent copied usage oracle before publication. Computed shape/manual behavior/effect/edge/tautology and style gates passed. Main red15failed116passed, final green131passed2pytest cleanupwarnings1.53s exit0. Tests remained immutable during implementation.

Production repair2lines plus1CHANGELOGline; latestcommit3net/2files, self-deslop skipped:trivial under the mandated threshold. Final style and split hygiene clean; no reflow threshold. Pat21ac9f79(20755bytes), guarded tool-free external Claude with approved network, session38fe80e5-e4a7-4478-adba-17cf6c21b224, actualclaude-sonnet-5-5; parser accepted reply. C14 resolved. Both LOW notes concern scope of extra regression assertions; retained because source-required Devon strengthening addressed proven mutations, and they already live in separate test commit668cdf0. No production scope expansion. No assumptions. Earlier task1 summary-publication limitation is now closed by the unchanged real summary regression. Fresh completion review remains mandatory and has not run in this build session.


## Raw Pat review

CLOSURE | resolved | "Final metric validation rejects None numeric fields from a valid normalized adapter summary; the real-adapter regression failed with invalid metric usage tool_uses until its fixture replaced unknown with zero" | `src/ovcaq/runtime/session.py:124` adds `elif value is None: valid = True` after the `estimated` bool check, so `estimated=None` is still rejected. The `replace(... tool_uses or 0)` workaround is gone from the integration test, and the recorded run shows 131 passed.

LOW | tests/runtime/test_session_metrics.py:176-574 | The diff adds tests unrelated to unknown usage: capability-kind final-row rejection, initial pending identity match, `observe_metrics` batch filtering, `max_records=4097` expansion, and a 16 MiB explicit byte-budget read. Task scope is None-preservation only (surgical-changes rule). The 16 MiB test also writes a file of more than 16 MiB. | Drop these from this commit or move them to a separate test commit or PRD. Keep the unknown-usage, exact-keys and invalid-value tests.

LOW | tests/integration/test_native_telemetry_identity.py:341-345 | The new `model == "fixture-model"` assertions on the captured and final metric are unrelated to usage preservation. The task said to keep existing assertions and remove only the workaround. | Move them to a separate change, or note why they belong here.


## Tess report

# Task 14 Tess report

Tests authored from the supplied requirements/public declarations and the two permitted test files. No production source, architecture, history, workflow state, git metadata, or changelog inspected or edited.

Changes:
- Removed only the real-summary `tool_uses=0` replacement and its unused `replace` import. Kept `super().summarize`, the usage assertion, state-advance transaction, lifecycle hooks, and every existing behavioral assertion.
- Added round trips for each nullable numeric field and all numeric fields unknown, with both boolean `estimated` values. Checks cover serialized canonical rows, direct reading, reconciliation, aggregate rows, and observation, preserving known values exactly.
- Added exact usage-key rejection, including every missing nullable key, missing `estimated`, and an extra key.
- Extended existing malformed-value cases with publication rejection and canonical/aggregate byte preservation; added non-finite counters, boolean cost, and null `estimated` cases.

Final verification commands and results:

```text
python3 docs/dev/tmp/run_bounded.py 300 /tmp/r14-tess-tests.log uv run pytest -q --tb=line tests/integration/test_native_telemetry_identity.py tests/runtime/test_session_metrics.py
exit 2: sandbox denied uv cache access; no tests ran.

python3 docs/dev/tmp/run_bounded.py 300 /tmp/r14-tess-tests-approved.log uv run pytest -q --tb=line tests/integration/test_native_telemetry_identity.py tests/runtime/test_session_metrics.py
exit 1: 15 failed, 110 passed, 2 warnings in 1.33s.
```

The second command received exact-command elevated approval for cache/process access. Its process was awaited to completion. All 15 failures reproduce the required defect: the real adapter's unknown `tool_uses` plus 14 nullable usage cases fail publication with `ValueError: invalid metric usage <field>`. The remaining 110 cases, including malformed-value rejection, pass. The two warnings concern pytest cleanup of temporary garbage directories. Full evidence remains in the named logs. No test rerun was used to recover counts, and no test edits followed this run.

Final size inspection (exit 0; `/tmp/r14-tess-final-counts.log`):

```bash
python3 docs/dev/tmp/run_bounded.py 60 /tmp/r14-tess-final-counts.log python3 -c 'import ast; from pathlib import Path
for name in ("tests/runtime/test_session_metrics.py", "tests/integration/test_native_telemetry_identity.py"):
    text = Path(name).read_text()
    tree = ast.parse(text)
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    largest = max(functions, key=lambda node: node.end_lineno - node.lineno + 1)
    print(f"{name}: {len(text.splitlines())} lines; max function {largest.name}: {largest.end_lineno - largest.lineno + 1} physical lines")
    print("Functions >=50:", [(node.name, node.end_lineno - node.lineno + 1) for node in functions if node.end_lineno - node.lineno + 1 >= 50])'
```

Final file counts: metrics 717 lines; integration 391 lines. Largest function spans are respectively 36 and 47 physical lines; none reaches 50. No formatting/lint/full-suite command was run.

ASSUMPTIONS: none


## Devon full evidence

# Devon isolated mutation report

Dispatch: 531f7160. Logical opus / actual gpt-6-astra. Eight independent candidates; all passed both complete supplied test files (125 tests each). No rejected candidates.

Only production file inspected/mutated: src/ovcaq/runtime/session.py, original lines 1–288. All candidates preserve the suffix byte-for-byte. No PRD, acceptance, sibling tests, unrelated production, network, git, state, or CHANGELOG reads/edits. The first prompt read used cat before the prompt-specific command prohibition was known; the entire prompt was then read using bounded sed sections.

Every candidate includes two necessary baseline additions: permit null normalized usage values except estimated, and require schema_version to be integer 1. These are included in each complete diff; candidate patches are independent, not cumulative.

Weak points:

1. test_pending_row_cannot_be_finalized_under_another_identity - initial publication can carry run/session IDs inconsistent with session metadata - publish the first pending row with each mismatched ID and assert ValueError and no metrics file.

2. test_final_canonical_row_rejects_all_later_publications - finalized capability rows can be replaced by pending, identical, or changed rows - parameterize the existing immutability test over phase and capability.

3. test_pending_publication_and_finalization_keep_one_private_canonical_row - later pending usage updates can be silently discarded - publish two pending snapshots with different cumulative usage and assert the canonical row contains the second snapshot.

4. test_metrics_choose_last_valid_session_rows_in_file_order_and_filter_batch - batch_id is ignored and batch-1 is always selected - query another-batch and a nonexistent batch and assert their exact rows.

5. test_metrics_default_record_budget_keeps_only_the_first_4096_rows - explicitly larger record budgets are silently capped at 4096 - query 4097 valid rows with max_records=4097 and assert all rows and a complete snapshot.

6. test_metrics_default_byte_budget_bounds_memory_and_leaves_later_rows_unread - explicitly larger byte budgets are silently capped at 16 MiB - query valid bounded-size records spanning over 16 MiB with a larger max_bytes and max_records budget and assert the later records and complete snapshot.

7. test_real_claude_telemetry_binds_native_ids_to_owning_supervisor_sessions - every phase metric serializes the hardcoded model test-model - assert the published metric model equals the requested/resolved fixture model, and round-trip another model value.

8. test_reconciliation_projects_interrupted_pending_without_rewriting_evidence - interrupted projection erases already-known pending usage - give the pending row non-null cumulative usage and assert the interrupted aggregate preserves it exactly.



Evidence follows. Every runner invocation completed with exit 0; warnings concern pytest temporary-directory cleanup, not assertion failures.



## Candidate 1

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c1.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c1.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c1.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -209,8 +213,6 @@
     metadata = parse_session_metadata(
         decode_json(session.metadata.read_text(), source=str(session.metadata))
     )
-    if (metric.run_id, metric.session_id) != (metadata.run_id, metadata.session_id):
-        raise ValueError("metric does not match session metadata")
     if session.metrics.exists():
         previous = _read_metric(session.metrics)
         if previous.decision is not None:
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-d478860b-091b-410f-8bec-3229b6e99b7c
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-d478860b-091b-410f-8bec-3229b6e99b7c'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a1649f1f-eb3c-4f8c-b616-c4525eeaf314
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a1649f1f-eb3c-4f8c-b616-c4525eeaf314'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.79s

```



## Candidate 2

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c2.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c2.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c2.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -213,7 +217,7 @@
         raise ValueError("metric does not match session metadata")
     if session.metrics.exists():
         previous = _read_metric(session.metrics)
-        if previous.decision is not None:
+        if previous.decision is not None and previous.kind != "capability":
             raise ValueError("session metric is already final")
         if (previous.run_id, previous.session_id) != (metric.run_id, metric.session_id):
             raise ValueError("metric does not match pending identity")
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-51b83dad-bb86-4ffe-8fd4-4a5b352581b8
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-51b83dad-bb86-4ffe-8fd4-4a5b352581b8'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c57f076b-4fd9-40bd-bd45-933dfa4230c0
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c57f076b-4fd9-40bd-bd45-933dfa4230c0'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.62s

```



## Candidate 3

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c3.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c3.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c3.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -213,6 +217,8 @@
         raise ValueError("metric does not match session metadata")
     if session.metrics.exists():
         previous = _read_metric(session.metrics)
+        if previous.decision is None and metric.decision is None:
+            return
         if previous.decision is not None:
             raise ValueError("session metric is already final")
         if (previous.run_id, previous.session_id) != (metric.run_id, metric.session_id):
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4af9ab3a-9eb2-4cce-880d-31e7b392f5a0
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4af9ab3a-9eb2-4cce-880d-31e7b392f5a0'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-31b2c7ff-1c6e-4d65-84c1-a7266a4e4c76
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-31b2c7ff-1c6e-4d65-84c1-a7266a4e4c76'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.65s

```



## Candidate 4

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c4.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c4.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c4.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -274,7 +278,7 @@
         follower.close()
     latest: dict[str, SessionMetric] = {}
     for row in batch.records:
-        if row.batch_id == batch_id:
+        if row.batch_id == "batch-1":
             # Rows are cumulative updates; the last one in file order wins.
             latest.pop(row.session_id, None)
             latest[row.session_id] = row
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-085b938c-d3ce-48b2-9342-745121733003
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-085b938c-d3ce-48b2-9342-745121733003'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b61fbcb6-cbac-42f6-9a8c-64979eeb5c94
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-b61fbcb6-cbac-42f6-9a8c-64979eeb5c94'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.66s

```



## Candidate 5

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c5.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c5.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c5.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -264,7 +268,7 @@
         metric_from_record,
         # Always start at byte zero; max_read_bytes caps the work instead.
         replay_bytes=sys.maxsize,
-        max_records=max_records,
+        max_records=min(max_records, 4096),
         max_read_bytes=max_bytes,
         max_record_bytes=MAX_STATE_BYTES,
     )
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-54996a49-4c2a-4297-ae59-1ebce26fc898
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-54996a49-4c2a-4297-ae59-1ebce26fc898'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c72a57f1-e7ec-436b-b370-cc7f7ca75ce4
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c72a57f1-e7ec-436b-b370-cc7f7ca75ce4'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.68s

```



## Candidate 6

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c6.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c6.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c6.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -265,7 +269,7 @@
         # Always start at byte zero; max_read_bytes caps the work instead.
         replay_bytes=sys.maxsize,
         max_records=max_records,
-        max_read_bytes=max_bytes,
+        max_read_bytes=min(max_bytes, 16 * 1024 * 1024),
         max_record_bytes=MAX_STATE_BYTES,
     )
     try:
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bd8f5713-4cd4-4585-b5b7-ed226381d6f0
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-bd8f5713-4cd4-4585-b5b7-ed226381d6f0'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0ca1bf70-4130-4224-aa83-09cae0eab358
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0ca1bf70-4130-4224-aa83-09cae0eab358'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.66s

```



## Candidate 7

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c7.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c7.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c7.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -178,6 +182,8 @@
         or metric.wall_seconds < 0
     ):
         raise ValueError("metric wall_seconds must be finite and nonnegative")
+    if metric.kind == "phase":
+        metric = replace(metric, model="test-model")
     return _encode_record(asdict(metric))
 
 
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-73397309-1a22-47b3-9fbc-26a4a099f85b
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-73397309-1a22-47b3-9fbc-26a4a099f85b'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 1 warning in 1.23s

```



## Candidate 8

Complete diff: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c8.diff

Exact bounded output: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c8.log

Exit: 0. Cases: 125 passed.

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-c8.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

```diff
--- a/src/ovcaq/runtime/session.py
+++ b/src/ovcaq/runtime/session.py
@@ -119,6 +119,8 @@
     ):
         raise ValueError("metric usage must contain exactly the normalized fields")
     for key, value in (metric.usage or {}).items():
+        if value is None and key != "estimated":
+            continue
         if key == "estimated":
             valid = isinstance(value, bool)
         elif key == "cost_usd":
@@ -135,6 +137,8 @@
 
 
 def _metric_payload(metric: SessionMetric) -> bytes:
+    if type(metric.schema_version) is not int or metric.schema_version != 1:
+        raise ValueError("invalid schema version")
     for identifier in (metric.run_id, metric.session_id, metric.batch_id):
         _validate_identifier(identifier)
     if metric.phase_launched is not None and metric.phase_launched not in get_args(
@@ -229,7 +233,7 @@
         if previous is None or previous.decision is None or metric.decision is not None:
             unique[metric.session_id] = metric
     rows = tuple(
-        replace(metric, decision="interrupted") if metric.decision is None else metric
+        replace(metric, decision="interrupted", usage=None) if metric.decision is None else metric
         for metric in sorted(
             unique.values(), key=lambda row: (row.started_at, row.session_id)
         )
```

```text
........................................................................ [ 57%]
.....................................................                    [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2218f6ea-45d5-4926-a155-19017cc407ff
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-2218f6ea-45d5-4926-a155-19017cc407ff'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9453e9f4-5319-4ff4-bef1-e08e178c9a53
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-9453e9f4-5319-4ff4-bef1-e08e178c9a53'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
125 passed, 2 warnings in 0.68s

```



## Restoration

Original production restored byte-for-byte: /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py

SHA-256 before and after: f43dd4d318cfa0d670102d774d373fec9e5c1e502868324362d4d4713e955914

All test processes completed and were awaited. Both supplied test files were never written. Mutation script and original-byte backup were overwritten with the required placeholder. Evidence diffs, logs, report, and manifest are retained as explicitly requested.

Placeholder files: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-original.bin; /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-devon-mutate.py.


## Strengthening report

# Task 14 — Tess single strengthening pass

Dispatch: `5856057c`. Logical opus / actual gpt-6-astra. No second Devon round.

## Eight dispositions

1. strengthened: `test_initial_pending_publication_must_match_session_metadata` parameterizes both run/session mismatches before any canonical publication, requires `ValueError`, and verifies neither canonical nor aggregate metrics exists. The original finalization identity test remains intact.
2. strengthened: `test_final_canonical_row_rejects_all_later_publications` now covers phase and capability rows for pending, identical-final, and changed-final replacement attempts; canonical bytes must survive unchanged.
3. strengthened: `test_pending_publication_and_finalization_keep_one_private_canonical_row` publishes two different cumulative pending usage snapshots and checks the second canonical snapshot before finalization. Existing open-reader, finalization, reconciliation, frozen-value, and permissions assertions remain.
4. strengthened: `test_metrics_choose_last_valid_session_rows_in_file_order_and_filter_batch` additionally queries `another-batch` and `nonexistent-batch`, asserting exact rows and complete/gap-free snapshots.
5. strengthened: `test_metrics_default_record_budget_keeps_only_the_first_4096_rows` retains the default-boundary assertions and additionally reads all 4097 rows with `max_records=4097`, requiring a complete/gap-free snapshot.
6. strengthened: `test_explicit_byte_budget_reads_valid_rows_beyond_sixteen_mib` writes individually bounded valid JSONL rows beyond 16 MiB followed by a distinct final session. Explicitly larger byte and record budgets must return both sessions and a complete/gap-free snapshot. The original default byte-budget/memory test is unchanged.
7. strengthened: `test_real_claude_telemetry_binds_native_ids_to_owning_supervisor_sessions` checks both captured pending and final published metric models against the fixture's resolved `fixture-model`. `test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries` additionally round-trips `alternate-model` through canonical publication, parsing, reconciliation, and observation. No real-adapter or state-advance hooks changed.
8. strengthened: `test_reconciliation_projects_interrupted_pending_without_rewriting_evidence` supplies non-null cumulative usage for both phase and capability pending rows and independently asserts its preservation. All original interruption, identity, ordering, idempotence, aggregate, and unchanged-canonical assertions remain.

Additional quality correction: the nullable roundtrip captures an independent copied usage mapping and serialized expected record before publication. Publication cannot move the expected oracle by mutating the caller's dictionary. Its full-record assertion preserves known values, unknowns, estimated, and the alternate model.

## Final verification evidence

Initial sandbox attempt (no tests collected):

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-tess-strengthen-tests.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

Exit **2**: uv cache initialization denied at `/Users/bob/.cache/uv/sdists-v9/.git`. Preserved in `r14-tess-strengthen-tests.log`.

Approved exact bounded cache/process retry:

```bash
mise exec -- python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-tess-strengthen-tests-approved.log uv run pytest -q --tb=line /Users/bob/git/src/github.com/buvis/ovcaq/tests/integration/test_native_telemetry_identity.py /Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_session_metrics.py
```

Exit **1**; exact summary: **15 failed, 116 passed, 2 warnings in 1.36s**. All 131 cases completed and the process was awaited. Warnings concern pytest temporary-directory cleanup.

All 15 failures expose the original known defect: `ValueError: invalid metric usage <numeric field>` at `src/ovcaq/runtime/session.py:134`. They comprise the real-adapter test (`tool_uses`) and the 14 nullable-usage combinations. Model assertions and the copied nullable oracle remain downstream of that publication failure until production is repaired. This pass does not claim a green suite or empirically rerun Devon's mutations.

The added initial identity, capability immutability, pending-update, alternate-batch, expanded-budget, and interrupted-known-usage checks passed against restored production. No production body was read or edited; only embedded wrong diffs and supplied declarations were used. No full suite or lint ran.

Bounded AST/line inspection exited **0** (`r14-tess-strengthen-size.log`): runtime test file **777** lines, integration test file **396** lines; every function below **50** nonblank/noncomment computed lines. No sibling split required.

## FILES_TOUCHED

- `tests/runtime/test_session_metrics.py`
- `tests/integration/test_native_telemetry_identity.py`
- `docs/dev/tmp/r14-tess-strengthen-report.md`
- `docs/dev/tmp/r14-tess-strengthen-size.log` (inspection evidence)
- `docs/dev/tmp/r14-tess-strengthen-tests.log` (sandbox failure evidence)
- `docs/dev/tmp/r14-tess-strengthen-tests-approved.log` (final test evidence)

ASSUMPTIONS: none


## Implementation report

Ivan task 14 — dispatch 0f4c097a

Changed only metric usage validation: numeric usage fields accept None, preserving unknown values through existing serialization and readers. The estimated field still requires bool; exact keys and existing numeric validation remain enforced.

Command (run once; 300-second bound):
```text
python3 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/run_bounded.py 300 /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-ivan-tests-0f4c097a.log uv run pytest -q --tb=line tests/integration/test_native_telemetry_identity.py tests/runtime/test_session_metrics.py
```

Exact output:
```text
........................................................................ [ 54%]
...........................................................              [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0bd49668-8034-4856-bd36-24aa54fffc3a
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-0bd49668-8034-4856-bd36-24aa54fffc3a'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-15b2772d-3bdf-4718-8286-db68bb3f33c2
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-15b2772d-3bdf-4718-8286-db68bb3f33c2'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
131 passed, 2 warnings in 1.43s

RECORDED EXIT 0: /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/r14-ivan-tests-0f4c097a.log
```

Pytest exit: 0. Wrapper exit: 0. All processes awaited. No tests, state, git, or CHANGELOG edited; no broader source reads needed.

ASSUMPTIONS: none

FILES_TOUCHED:
src/ovcaq/runtime/session.py
docs/dev/tmp/r14-ivan-tests-0f4c097a.log
docs/dev/tmp/r14-ivan-report.md


## Main red

F.....FFFFFFFFFFFFFF.................................................... [ 54%]
...........................................................              [100%]
=================================== FAILURES ===================================
E   ValueError: invalid metric usage tool_uses
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage tool_uses
E   ValueError: invalid metric usage input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage input_tokens
E   ValueError: invalid metric usage output_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage output_tokens
E   ValueError: invalid metric usage cache_creation_input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cache_creation_input_tokens
E   ValueError: invalid metric usage cache_read_input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cache_read_input_tokens
E   ValueError: invalid metric usage tool_uses
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage tool_uses
E   ValueError: invalid metric usage cost_usd
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cost_usd
E   ValueError: invalid metric usage input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage input_tokens
E   ValueError: invalid metric usage input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage input_tokens
E   ValueError: invalid metric usage output_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage output_tokens
E   ValueError: invalid metric usage cache_creation_input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cache_creation_input_tokens
E   ValueError: invalid metric usage cache_read_input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cache_read_input_tokens
E   ValueError: invalid metric usage tool_uses
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage tool_uses
E   ValueError: invalid metric usage cost_usd
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage cost_usd
E   ValueError: invalid metric usage input_tokens
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/runtime/session.py:134: ValueError: invalid metric usage input_tokens
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c426f817-655c-43e2-87dd-3878aae21d93
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-c426f817-655c-43e2-87dd-3878aae21d93'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-1fe9b59f-482c-43e6-b709-e3721ce55220
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-1fe9b59f-482c-43e6-b709-e3721ce55220'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/integration/test_native_telemetry_identity.py::test_real_claude_telemetry_binds_native_ids_to_owning_supervisor_sessions
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-output_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-cache_creation_input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-cache_read_input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-tool_uses]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-cost_usd]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[False-all]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-output_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-cache_creation_input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-cache_read_input_tokens]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-tool_uses]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-cost_usd]
FAILED tests/runtime/test_session_metrics.py::test_final_usage_preserves_unknown_and_known_values_across_metric_boundaries[True-all]
15 failed, 116 passed, 2 warnings in 1.29s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/integration/test_native_telemetry_identity.py",
    "tests/runtime/test_session_metrics.py"
  ],
  "exit": 1,
  "timeout_seconds": 300
}

## Main green

........................................................................ [ 54%]
...........................................................              [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4ae8e283-d207-4dfe-8019-d076f536f404
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-4ae8e283-d207-4dfe-8019-d076f536f404'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a52d6179-7afd-4262-bfc1-fc832260033e
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-a52d6179-7afd-4262-bfc1-fc832260033e'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
131 passed, 2 warnings in 1.53s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/integration/test_native_telemetry_identity.py",
    "tests/runtime/test_session_metrics.py"
  ],
  "exit": 0,
  "timeout_seconds": 300
}