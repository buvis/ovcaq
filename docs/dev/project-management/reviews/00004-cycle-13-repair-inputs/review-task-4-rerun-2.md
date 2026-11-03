Same task, next review cycle. You already reviewed this task's diff earlier in
this conversation; below is only what changed since.

You already reviewed be5e385bd9714952b4803ee30f7c72e661c278f2..6d5a306a22f2522e541ddb666608580ebd810331 earlier in this conversation. That range is unchanged and is not repeated here.

The delta implements your fail-loud option for the confirmed permissions diagnostic: fallback O_RDONLY ancestry opens that fail with PermissionError now explain the read access needed for durable ancestry confirmation. Readable fallback paths continue working. Required directory fsyncs are preserved. Native O_SEARCH behavior is unchanged. O_PATH is unsuitable because it does not open a descriptor for filesystem I/O; Linux open(2) documents its restrictions (https://man7.org/linux/man-pages/man2/open.2.html). Native Linux was not run; platforms without a fsync-capable search descriptor still require read access for durable ancestry confirmation. The unsupported capability is now explicit in the error, with the affected path.

Recorded verification after this commit: mise exec -- uv run --offline --no-sync pytest tests/packaging/test_rework_13.py -q --basetemp /private/tmp/ovcaq-r13-task4-retry-green -> exit 0, 7 passed in 1.20s. Style-limit check passed. Disposable probe on macOS uid501 forced the actual O_RDONLY fallback against a real 0111 ancestor: PermissionError errno13, original cause retained, exact explanatory message and path, no deferred directory created. After read permission was restored, the same fallback successfully published. This is fallback-branch verification, not claimed native Linux execution. The LOW naming suggestion is retained for fresh PRD review under the no-LOW-retry policy.


## Findings you raised, sent to the implementor

MEDIUM | src/ovcaq/workflow/_files.py:404-406 | `search_only` falls back to `os.O_RDONLY` on any non-Darwin platform lacking `os.O_SEARCH`, reproducing the exact EACCES-on-search-only-ancestor defect from finding 2 on Linux; the diff's own test self-skips there (`search_capability()` returns `{"skip": ...}` when `search is None` and platform isn't darwin), so the gap is untested | Fail loud (raise, don't silently downgrade to O_RDONLY) or use `os.O_PATH` for traversal-only opens on platforms without O_SEARCH, so the finding is closed everywhere OVCAQ runs, not just Darwin.


## What changed since your last review

```diff
diff --git a/src/ovcaq/workflow/_files.py b/src/ovcaq/workflow/_files.py
index d016231..3e50fd4 100644
--- a/src/ovcaq/workflow/_files.py
+++ b/src/ovcaq/workflow/_files.py
@@ -412,6 +412,17 @@ def _open_lifecycle_directory(
     try:
         descriptor = os.open(directory, flags)
     except OSError as error:
+        if (
+            search_only
+            and access == os.O_RDONLY
+            and isinstance(error, PermissionError)
+        ):
+            raise PermissionError(
+                error.errno,
+                f"{label} directory requires read access for durable ancestry "
+                "confirmation on this platform",
+                directory,
+            ) from error
         raise OSError(
             f"{label} directory is not a real directory: {directory}"
         ) from error
```

Judge two things, in this order:

1. For each finding above, is it resolved by this delta? Ground the verdict in a
   line of the delta, not in how clean the code now reads. A change that
   improves the file while leaving the defect reachable is not resolved.
   **Re-emit every finding you judge unresolved as a contract line of its own**,
   carrying the severity and `file:line` it had before. That line is the only
   thing that carries an unresolved finding out of this cycle: silence reads as
   fixed, and the defect ships.
2. Report new findings from THIS delta only. Do not re-report anything else from
   the earlier range — you already reviewed it — and do not re-raise a finding
   you are calling resolved.

Judge from this prompt and what you already read in this conversation.

Your reporting contract is unchanged: the one you were given at the top of this
conversation (`agents/pat.md`). Same line shape, same severities, and CLOSURE
verdicts still apply wherever they applied on the first dispatch. Emit
`NO FINDINGS` only when the delta is clean AND every finding above is resolved.
