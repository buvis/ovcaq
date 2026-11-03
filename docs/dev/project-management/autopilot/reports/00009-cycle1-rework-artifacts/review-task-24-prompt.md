
You are Pat, the per-task code reviewer. Review the single task's committed
diff below. This review is READ-ONLY: report findings, change nothing.

## Task

Subject: [D1] Task 19 split: probe

Description:
Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Resolve the provider-edge and shared launch/presentation findings. Preserve driver API 2, observation protocol 1, state schema 1, strict argv and provider neutrality. Verify native failure examples against pinned upstream source before choosing classifications; distinguish quota, capacity, sandbox, network and explicit agent failure without broad prose scanning. Do not change deferred reset grammar or configured options. Test public behavior independently, including exact fixture expectations and direct decode totality. R14 uses generic adapter health checks, never Codex-specific runtime policy. R16 renders normalized activity for both adapters.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.


Failure-driven split of task 19 (Tess context_overrun, no edits). Scope only findings below; other task-19 findings belong to sequential siblings. Preserve exact findings and all assertions.

### Findings (verbatim)
- 🟡 src/ovcaq/drivers/codex.py:117: Probe capture misses the bounded 16 KiB stdout/stderr contract. `--version` stdout streams into an unbounded `TemporaryFile`; only the 4096-byte read is capped. Auth stdout and all stderr go to DEVNULL, so an auth failure reports only "authentication check failed", with no exit code and no `codex login` hint. The contract asks for "sanitized actionable detail". This is a carried Pat MEDIUM/LOW that is still open. Capture through a pipe with a hard 16 KiB cap, and add the exit code and a login hint to the sanitized detail (found by: ALICE, BOB)
- 🟡 src/ovcaq/drivers/codex.py:115: Simplify `probe`: on each iteration the loop recomputes `label` by comparing `operation == ("--version",)`, then branches on `label` twice more, and the `"0.160.0"` literal appears twice. Iterate `(("version", ("--version",)), ("authentication", ("login", "status")))` and hoist `_PINNED_VERSION = "0.160.0"`. Same behavior, fewer branches (found by: ALICE, BOB)
- 🟡 src/ovcaq/drivers/codex.py:139: The version pin can be bypassed. `\bcodex-cli (\d+\.\d+\.\d+)\b` matches anywhere in the first 4096 bytes and accepts `codex-cli 0.160.0-beta.1` and `codex-cli 0.160.0.7` as `0.160.0` (confirmed). So probe reports an unreviewed CLI as healthy, which defeats the "fail health on an unreviewed version" drift guard. This is a carried Pat MEDIUM that is still open (00009-task-3-pat-02-corrected.md). Anchor to the first line, e.g. `^codex-cli (\d+\.\d+\.\d+)\s*$`, and test prerelease and extra-component outputs (found by: ALICE)
- 🟡 src/ovcaq/drivers/codex.py:58: Simplify: the check uses `isinstance(..., bool)` and then needs a justification comment plus a `# noqa: TRY004` suppression in order to raise ValueError. Claude makes the same check as `type(options.get("allow_explicit_model", False)) is not bool` (src/ovcaq/drivers/claude.py:49) with no suppression. Use that idiom and drop the comment and the noqa. Behavior is identical, since bool cannot be subclassed (found by: ALICE)


Acceptance criteria:
Every quoted finding closed. Preserve strict argv, 5second deadline and existing version diagnostic fragments; no spool or unbounded captured output.

## Diff under review

```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 0ca1b4c..73a050c 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -50,6 +50,8 @@ The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
 
 ### Fixed
 
+- **drivers**: require exact reviewed Codex version evidence and retain sanitized authentication diagnostics with exit codes and login guidance; drain probe output with 16 KiB memory limits per stream.
+
 - **drivers**: classify native Codex failures before bounding sanitized details, tolerate unsafe tool JSON, close interrupted receiver lanes, accept punctuated reset deadlines, and preserve simultaneous usage and thread gaps.
 
 - **drivers**: emit one startup observation per Codex thread header and defer conflicting-thread gaps to the next usage completion; include decoder helpers in the package inventory and sanitize generic launcher-home help references with recorded provenance.
diff --git a/src/ovcaq/drivers/codex.py b/src/ovcaq/drivers/codex.py
index 27b0c32..bc882aa 100644
--- a/src/ovcaq/drivers/codex.py
+++ b/src/ovcaq/drivers/codex.py
@@ -4,12 +4,12 @@ import hashlib
 import json
 import logging
 import os
-import re
+import selectors
 import subprocess
-import tempfile
 from collections.abc import Iterable
 from dataclasses import asdict, replace
 from datetime import UTC, datetime
+from time import monotonic
 
 from ovcaq.config import AgentSettings
 from ovcaq.drivers.base import DriverHealth, LaunchRequest, LaunchSpec
@@ -35,6 +35,72 @@ from ovcaq.events.reducer import reduce_session
 
 logger = logging.getLogger(__name__)
 
+_PINNED_VERSION = "0.160.0"
+_PROBE_OUTPUT_LIMIT = 16 * 1024
+
+
+def _run_probe_command(
+    command: tuple[str, ...], environment: dict[str, str]
+) -> tuple[int, bytearray, bytearray]:
+    deadline = monotonic() + 5
+    with (
+        subprocess.Popen(
+            command,
+            env=environment,
+            stdin=subprocess.DEVNULL,
+            stdout=subprocess.PIPE,
+            stderr=subprocess.PIPE,
+            bufsize=0,
+        ) as process,
+        selectors.DefaultSelector() as selector,
+    ):
+        assert process.stdout is not None and process.stderr is not None
+        stdout, stderr = bytearray(), bytearray()
+        buffers = {
+            process.stdout.fileno(): stdout,
+            process.stderr.fileno(): stderr,
+        }
+        for stream in (process.stdout, process.stderr):
+            selector.register(stream, selectors.EVENT_READ)
+        try:
+            while selector.get_map():
+                remaining = deadline - monotonic()
+                if remaining <= 0:
+                    raise subprocess.TimeoutExpired(process.args, 5)
+                for key, _ in selector.select(remaining):
+                    chunk = os.read(key.fd, 4096)
+                    if not chunk:
+                        selector.unregister(key.fileobj)
+                        continue
+                    buffer = buffers[key.fd]
+                    buffer.extend(chunk[: _PROBE_OUTPUT_LIMIT - len(buffer)])
+            exit_code = process.wait(timeout=max(0, deadline - monotonic()))
+        except subprocess.TimeoutExpired:
+            process.kill()
+            process.wait()
+            raise
+    return exit_code, stdout, stderr
+
+
+def _probe_failure(
+    executable: str, label: str, exit_code: int, stdout: bytearray, stderr: bytearray
+) -> DriverHealth:
+    diagnostics = sanitize_text(
+        stdout.decode("utf-8", errors="replace")
+        + "\n"
+        + stderr.decode("utf-8", errors="replace")
+    ).strip()
+    hint = "; run codex login" if label == "authentication" else ""
+    detail = (
+        f"{executable}: {label} check failed (exit code {exit_code})"
+        f"{hint}: {diagnostics}"
+    )
+    return DriverHealth(
+        False,
+        detail.encode("utf-8")[:_PROBE_OUTPUT_LIMIT].decode("utf-8", errors="ignore"),
+    )
+
+
 _DEFAULT_PROMPT = """Read the committed OVCAQ state to determine the current phase. Use `ovcaq state`
 and `ovcaq workflow` commands for all durable mutations. Perform only the
 current phase, commit exactly one successful phase handoff through the OVCAQ
@@ -56,9 +122,8 @@ class CodexDriver:
             raise ValueError("Codex sandbox must be workspace-write")
         if options.get("approval", "never") != "never":
             raise ValueError("Codex approval must be never")
-        if not isinstance(options.get("allow_explicit_model", False), bool):
-            # Invalid configuration values use ValueError in the adapter contract.
-            raise ValueError("Codex allow_explicit_model must be a boolean")  # noqa: TRY004
+        if type(options.get("allow_explicit_model", False)) is not bool:
+            raise ValueError("Codex allow_explicit_model must be a boolean")
         self._settings = settings
         self._run_id = run_id
         self._session_id: str | None = None
@@ -113,44 +178,38 @@ class CodexDriver:
     def probe(self) -> DriverHealth:
         executable = sanitize_text(self._settings.command[0])[:1024]
         environment = dict(os.environ) | dict(self._settings.environment)
-        for operation in (("--version",), ("login", "status")):
-            label = "version" if operation == ("--version",) else "authentication"
-            with tempfile.TemporaryFile() as output:
-                try:
-                    result = subprocess.run(
-                        (*self._settings.command, *operation),
-                        env=environment,
-                        stdin=subprocess.DEVNULL,
-                        stdout=output if label == "version" else subprocess.DEVNULL,
-                        stderr=subprocess.DEVNULL,
-                        timeout=5,
-                        check=False,
+        for label, operation in (
+            ("version", ("--version",)),
+            ("authentication", ("login", "status")),
+        ):
+            try:
+                exit_code, stdout, stderr = _run_probe_command(
+                    (*self._settings.command, *operation), environment
+                )
+            except subprocess.TimeoutExpired:
+                return DriverHealth(
+                    False, f"{executable}: {label} check timed out after 5 seconds"
+                )
+            except OSError:
+                return DriverHealth(False, f"{executable}: executable unavailable")
+            if exit_code != 0:
+                return _probe_failure(executable, label, exit_code, stdout, stderr)
+            if label == "version":
+                text = stdout.decode("utf-8", errors="replace")
+                version = text.splitlines()[0] if text else ""
+                if version != f"codex-cli {_PINNED_VERSION}":
+                    detail = (
+                        f"observed {sanitize_text(version)[:1024]}"
+                        if version.startswith("codex-cli ")
+                        else "missing Codex version"
                     )
-                except subprocess.TimeoutExpired:
                     return DriverHealth(
-                        False, f"{executable}: {label} check timed out after 5 seconds"
+                        False,
+                        f"{executable}: {detail}; pinned {_PINNED_VERSION}; "
+                        "refresh the Codex fixture contract",
                     )
-                except OSError:
-                    return DriverHealth(False, f"{executable}: executable unavailable")
-                if result.returncode != 0:
-                    return DriverHealth(False, f"{executable}: {label} check failed")
-                if label == "version":
-                    output.seek(0)
-                    text = output.read(4096).decode("utf-8", errors="replace")
-                    match = re.search(r"\bcodex-cli (\d+\.\d+\.\d+)\b", text)
-                    if match is None:
-                        return DriverHealth(
-                            False, f"{executable}: missing Codex version"
-                        )
-                    version = match[1]
-                    if version != "0.160.0":
-                        return DriverHealth(
-                            False,
-                            f"{executable}: observed {version}; pinned 0.160.0; "
-                            "refresh the Codex fixture contract",
-                        )
         return DriverHealth(
-            True, f"{executable}: Codex {version}; authentication verified"
+            True, f"{executable}: Codex {_PINNED_VERSION}; authentication verified"
         )
 
     def decode(self, raw_line: str) -> tuple[Observation, ...]:
diff --git a/tests/drivers/test_codex_rework_probe.py b/tests/drivers/test_codex_rework_probe.py
new file mode 100644
index 0000000..1bec7bc
--- /dev/null
+++ b/tests/drivers/test_codex_rework_probe.py
@@ -0,0 +1,154 @@
+"""Probe version evidence and failure diagnostics obey the public contract."""
+
+import json
+import re
+import sys
+from pathlib import Path
+
+import pytest
+
+from ovcaq.drivers.base import DriverHealth
+from ovcaq.drivers.codex import CodexDriver
+from ovcaq.drivers.edge import build_driver
+from ovcaq.paths import CONFIG_NAME
+
+SECRET = "sk-" + "proj-fixturecredential12345678901234567890"
+PREFIX = "literal prefix ; $(touch must-not-exist)"
+LIMIT = 16 * 1024
+PROBE_SCRIPT = r"""
+import json
+import os
+import sys
+
+args = sys.argv[1:]
+with open(os.environ["PROBE_LOG"], "a", encoding="utf-8") as log:
+    log.write(json.dumps({"args": args, "stdin": sys.stdin.read()}) + "\n")
+if args[0:1] != [os.environ["PROBE_PREFIX"]]:
+    sys.exit(80)
+operation = args[1:]
+if operation == ["--version"]:
+    print(os.environ["PROBE_VERSION"], flush=True)
+    sys.exit(0)
+if operation != ["login", "status"]:
+    sys.exit(81)
+stream = sys.stdout if os.environ["PROBE_STREAM"] == "stdout" else sys.stderr
+secret = "sk-" + "proj-fixturecredential12345678901234567890"
+print("Not logged in: expired credential; account needs reauthentication", file=stream)
+print("Authorization: Bearer " + secret, file=stream, flush=True)
+stream.write("é" * int(os.environ["PROBE_PADDING"]))
+stream.flush()
+sys.exit(int(os.environ["PROBE_EXIT"]))
+"""
+
+
+@pytest.fixture
+def probe_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
+    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "isolated-config"))
+    project = tmp_path / "project"
+    project.mkdir()
+    (tmp_path / "probe.py").write_text(PROBE_SCRIPT, encoding="utf-8")
+    return project
+
+
+def configured_probe(
+    project: Path,
+    version: str = "codex-cli 0.160.0",
+    stream: str = "stderr",
+    padding: int = 0,
+    exit_code: int = 23,
+) -> CodexDriver:
+    argv = (sys.executable, str(project.parent / "probe.py"), PREFIX)
+    environment = {
+        "PROBE_LOG": str(project.parent / "probe.jsonl"),
+        "PROBE_PREFIX": PREFIX,
+        "PROBE_VERSION": version,
+        "PROBE_STREAM": stream,
+        "PROBE_PADDING": str(padding),
+        "PROBE_EXIT": str(exit_code),
+    }
+    configuration = (
+        'agent = "codex"\n[agents.codex]\n'
+        f"command = {json.dumps(argv)}\n"
+        'tiers = { standard = "fixture-model" }\n'
+        "environment = { "
+        + ", ".join(
+            f"{key} = {json.dumps(value)}" for key, value in environment.items()
+        )
+        + ' }\n[agents.codex.options]\nsandbox = "workspace-write"\n'
+        'approval = "never"\n'
+    )
+    (project / CONFIG_NAME).write_text(configuration, encoding="utf-8")
+    driver = build_driver(project, "codex")
+    assert isinstance(driver, CodexDriver)
+    return driver
+
+
+@pytest.mark.parametrize(
+    "version",
+    (
+        "prefixnoise codex-cli 0.160.0",
+        "codex-cli 0.160.0-rc.1",
+        "codex-cli 0.160.0.1",
+        "codex-cli 0.160.00",
+        "codex-cli 0.160.0+unreviewed",
+        "codex-cli 0.160.0 trailing-noise",
+        "codex-cli 0.160.01",
+        "unreviewed first line\ncodex-cli 0.160.0",
+    ),
+)
+def test_probe_rejects_version_aliases_that_are_not_exact_reviewed_evidence(
+    probe_project: Path, version: str
+) -> None:
+    health = configured_probe(probe_project, version=version, exit_code=0).probe()
+    assert isinstance(health, DriverHealth)
+    assert health.healthy is False
+    assert "0.160.0" in health.detail
+    assert health.detail.strip()
+    records = (probe_project.parent / "probe.jsonl").read_text().splitlines()
+    assert [json.loads(record) for record in records] == [
+        {"args": [PREFIX, "--version"], "stdin": ""}
+    ]
+
+
+@pytest.mark.parametrize("stream", ("stdout", "stderr"))
+@pytest.mark.parametrize("exit_code", (1, 23))
+def test_probe_preserves_actionable_sanitized_authentication_failures(
+    probe_project: Path,
+    capfd: pytest.CaptureFixture[str],
+    stream: str,
+    exit_code: int,
+) -> None:
+    health = configured_probe(
+        probe_project, stream=stream, exit_code=exit_code
+    ).probe()
+    captured = capfd.readouterr()
+    assert health.healthy is False
+    assert "expired credential" in health.detail.lower()
+    assert "codex login" in health.detail.lower()
+    assert re.search(rf"(?<!\d){exit_code}(?!\d)", health.detail)
+    assert len(health.detail.encode("utf-8")) <= LIMIT
+    disclosed = health.detail + captured.out + captured.err
+    assert SECRET not in disclosed
+    assert "fixturecredential12345678901234567890" not in disclosed
+    records = (probe_project.parent / "probe.jsonl").read_text().splitlines()
+    assert [json.loads(record) for record in records] == [
+        {"args": [PREFIX, "--version"], "stdin": ""},
+        {"args": [PREFIX, "login", "status"], "stdin": ""},
+    ]
+    assert not (probe_project / "must-not-exist").exists()
+
+
+@pytest.mark.parametrize("stream", ("stdout", "stderr"))
+def test_probe_bounds_authentication_details_and_retains_useful_diagnostics(
+    probe_project: Path, capfd: pytest.CaptureFixture[str], stream: str
+) -> None:
+    health = configured_probe(probe_project, stream=stream, padding=131072).probe()
+    captured = capfd.readouterr()
+    assert isinstance(health, DriverHealth)
+    assert health.healthy is False
+    assert "expired credential" in health.detail.lower()
+    assert "codex login" in health.detail.lower()
+    assert len(health.detail.encode("utf-8")) <= LIMIT
+    disclosed = health.detail + captured.out + captured.err
+    assert SECRET not in disclosed
+    assert "fixturecredential12345678901234567890" not in disclosed
```

## Recorded verification

The task's tests were run before this review. This is what they reported:

uv --cache-dir /private/tmp/ovcaq-rework-uv run pytest tests/drivers/test_codex_rework_probe.py -q --tb=line -> exit0,14passed,2pytesttemporarycleanupwarnings. Repeated after style extraction14passed. Style gate and split hygiene exit0. Public tests cannot fully observe retained outputbuffer: review code for eachstream16KiBhardcap. Full suite not run until all queuedreworkcomplete.

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


