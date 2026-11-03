Abort and report if you read more than 100K of total input. Return the partial result and an abort_reason: context_overrun field.

A diff has been written to satisfy this task. The implementation passed its
tests. Your job: prune slop from the diff while keeping every test green.
This is best-effort cleanup, not a correctness rework — do not change
behavior, do not modify tests, do not refactor.

Task: [D1] Task 19 split: decoder

Description:
Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Resolve the provider-edge and shared launch/presentation findings. Preserve driver API 2, observation protocol 1, state schema 1, strict argv and provider neutrality. Verify native failure examples against pinned upstream source before choosing classifications; distinguish quota, capacity, sandbox, network and explicit agent failure without broad prose scanning. Do not change deferred reset grammar or configured options. Test public behavior independently, including exact fixture expectations and direct decode totality. R14 uses generic adapter health checks, never Codex-specific runtime policy. R16 renders normalized activity for both adapters.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.


Failure-driven split of task 19 (Tess context_overrun, no edits). Scope only findings below; other task-19 findings belong to sequential siblings. Preserve exact findings and all assertions.

### Findings (verbatim)
- 🟡 src/ovcaq/drivers/codex.py:212: Native failure `detail` is never bounded. `_failure_observations` passes the raw message straight into the `activity.message`, `session.failed` and `rate_limit.started` payloads, and `Observation` only sanitizes, it does not truncate. Confirmed: a 20000-char `turn.failed` message yields two observations with 20015-char details, and a top-level `error` keeps all 20000 chars. Frames up to 1 MiB pass through, and the rate-limit record duplicates them. The contract caps text/detail at 4096, and Claude's `failure_payload` bounds at source (src/ovcaq/drivers/claude_events.py:261). Fix: `detail = sanitize_text(detail)[:4096]` after classification, plus a regression test (found by: ALICE, BOB)
- 🟡 src/ovcaq/drivers/codex_events.py:99: `CodexDriver.decode` raises on valid-JSON records that carry `NaN` or `Infinity` (which `json.loads` accepts) inside an MCP `result` or web `results`. `sanitize_json` raises `ValueError("JSON numbers must be finite")` out of `mcp_detail`/`web_detail`, confirmed with a one-line mcp_tool_call record. The shared `RawFirstDecoder` catch keeps the supervisor alive. But the driver's own contract ("never raise, return raw.unknown with a specific reason") fails, and the evidence reason drops to the generic "driver failed to decode frame". Deep nesting near the recursion limit takes the same path. Fix at the boundary: either `json.loads(raw_line, parse_constant=<raise ValueError>)`, which codex.py:165 already catches, or catch `(ValueError, TypeError, RecursionError)` in the two detail helpers. Add a malformed-record test (found by: ALICE, BOB)
- ⚪ src/ovcaq/drivers/codex_events.py:262: `failure_reset` captures `reset at (\S+)`, so a trailing `.`, `,` or `)` makes `fromisoformat` fail and silently drops a valid deadline. `classify_failure` misses "usage limits", "quota limits" and "rate limiting" because of the trailing `\b`. Both fall back safely to None/unknown (carried Pat LOWs) (found by: ALICE, BOB)
- 🟠 src/ovcaq/drivers/codex_events.py:245: Checked-in `connectivity-failed.jsonl` fixture does not classify as connectivity. Its message "Connection failed: unable to reach example endpoint." matches none of the connectivity patterns, so the classifier returns `unknown` (confirmed by running it). The fixture test can't catch this because it builds its expected value by calling `classify_failure` itself (tests/drivers/test_codex_decode_terminals.py:120). The decision matrix skips the fixture and uses a made-up "connection refused" string instead (tests/runtime/test_codex_decisions.py:138). Phase B exit ("fixture matrix produces expected summaries") fails for this family. (found by: BLAKE)
- 🟠 src/ovcaq/drivers/codex_events.py:230: Failure classifier is not based on real Codex 0.160.0 error text (checked against upstream `codex-rs/protocol/src/error.rs` at tag rust-v0.160.0). These real messages all come back `unknown`: "stream disconnected before completion: …" (Codex's main network failure), "Quota exceeded. Check your plan and billing details.", "internal error; agent loop died unexpectedly", "sandbox error: …", "Selected model is at capacity". Impact: a real network drop uses the died-retry budget (default 1) and then parks or halts, instead of the connectivity wait (3 retries, 1800 s). (found by: BLAKE)
- 🟡 src/ovcaq/drivers/codex.py:205: Simplification: chained ternary for `detail`. Replace with `source = record if event == "error" else record.get("error")` and `detail = source.get("message") if isinstance(source, dict) else None`. (found by: BOB)
- ⚪ src/ovcaq/drivers/codex_events.py:44: `turn_usage` keeps a single `gap` string, and later branches overwrite it. A malformed-counter reason gets replaced by the partition or reads-exceed-input reason, so the raw.unknown still appears but names only the last cause. Keep the first reason or join them (found by: ALICE)
- ⚪ src/ovcaq/drivers/codex_events.py:154: The Codex lane statuses `interrupted`, `shutdown` and `not_found` are mapped to raw.unknown with no lane end event. A lane that was started earlier then shows as "running" in the TUI forever. (found by: BLAKE)
- ⚪ src/ovcaq/drivers/codex.py:254: `gap = gap or "Conflicting thread identity"` drops the conflict reason when the usage itself also has a gap (malformed or all-zero). `_thread_conflict` is then cleared, so the conflict is never reported. (found by: BOB)


Acceptance criteria:
(none recorded)

Tests that the diff made pass (do NOT modify):
/Users/bob/git/src/github.com/buvis/ovcaq/tests/drivers/test_codex_rework_decode.py

Files in the diff:
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex.py, /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/drivers/codex_events.py, /Users/bob/git/src/github.com/buvis/ovcaq/CHANGELOG.md

Procedure:

1. Read the diff for each file in scope (`git diff HEAD~1..HEAD <file>` or
   equivalent in your environment).
2. For each line, block, helper, comment or docstring added in the
   diff, ask:
     "Does this trace to a failing test, an acceptance criterion, or
     existing-behavior preservation?"
   If the answer is no, mark the construct for removal.
3. Apply removals one at a time. After each individual removal, re-run the
   tests listed above (the narrow set Tess wrote). If any test fails,
   restore that single removal and move on to the next candidate. Never
   delete the test that fails — the test is authoritative.
4. If no removal survived its test re-run, exit WITHOUT committing. Return
   the literal string "no slop found" so the caller can record a noop.
5. If at least one removal survived, commit with message:
     chore: prune slop from [D1] Task 19 split: decoder
   No CHANGELOG entry. No HEREDOC. No Co-Authored-By trailer. One commit
   only — do not split into multiple cleanup commits.

Rules:

- **Do not modify tests.** If a test reads as weak, that is the per-task
  reviewer's call (step 5.7), not yours. Leave it. Dead bindings a split left
  behind in a test file are not yours either: `check_split_hygiene.py` answers
  that mechanically at the task boundary (step 5.65), with `ast` rather than
  judgment, so you never have to guess which test binding is safe to drop.
- **Do not change behavior.** Tests prove behavior; if you cannot satisfy
  the tests, the deletion is wrong. Restore.
- **Do not refactor.** This pass deletes; it does not move code around,
  rename symbols, or extract helpers. If a slop pattern would only resolve
  through restructuring, note it in the return message instead of acting.
- **Do not touch files outside the diff.** The cleanup is scoped to what
  the implementor just produced. Adjacent slop in untouched files is out
  of scope here — the post-session codex pass catches it separately.

Slop patterns to look for (catalog inlined from `prompts/de-sloppify.md`):

## What to remove

### 1. Language/framework verification tests

Tests that only prove the runtime or framework works, not the project's behavior.

### 2. Weak or tautological tests

Replace existence checks, mock-confirming tests, self-referential assertions, and unexplained magic assertions with behavior-focused assertions. If an important boundary or failure case is missing, add the smallest useful test.

### 3. Redundant type checks

Remove runtime checks that duplicate compile-time guarantees, except at system boundaries.

### 4. Impossible-state error handling

Remove defensive handling for states that cannot occur from the current control flow. Keep validation and error handling at boundaries.

### 5. Swallowed errors and empty catch blocks

Do not hide failures. Re-throw, surface, or handle them meaningfully.

### 6. Debug statements

Remove development-only prints and logs.

### 7. Commented-out code

Delete dead code kept in comments.

### 8. Obvious comments

Remove comments that restate the code. Keep comments that explain intent, constraints, workarounds, or why.

### 9. Over-abstraction and unnecessary indirection

Inline abstractions that have only one consumer and no current testability or architectural value.

### 10. Duplicate code

Reuse existing code or standard library helpers instead of introducing parallel logic.

### 11. Suspicious dependencies

Verify any newly added dependency exists, is used, and is justified. Remove hallucinated, unused, or speculative dependencies.

### 12. Hardcoded secrets and placeholder credentials

Replace with environment variables, secret storage, or project-approved configuration.

### 13. Deprecated APIs and outdated patterns

Modernize only when the newer approach is already supported by the project and the change stays in scope.

### 14. Naive performance patterns

Fix only if the code is on a hot path or clearly scales poorly with input size.

### 15. Leftover artifacts

Remove temp files, scratch scripts, backup files, unrelated lockfile churn, and agent-generated planning docs.

### 16. AI-style docstrings

Remove multi-paragraph docstrings on trivial functions. Remove docstrings that paraphrase the function name or restate its arguments — when the function is well-named, the docstring is noise. Remove "this function does X by calling Y" preambles that describe implementation rather than contract. Keep docstrings that capture non-obvious intent, invariants, or constraints.

### 17. Trivial-type validation

Remove runtime type guards, JSON schemas, or pydantic models that duplicate compile-time guarantees in a fully-typed file. Examples: `isinstance(x, int)` inside a function whose signature is `x: int`; a pydantic model declared for a function-internal dict whose shape is already pinned by the caller's types. Keep validation at real system boundaries (request bodies, file inputs, external API responses).

### 18. Single-instantiation factories

Inline factory functions, builders, or wrapper classes called from exactly one place where direct construction reads more clearly. A factory pattern only earns its complexity when multiple call sites benefit; before there are multiple call sites, the abstraction is speculative.

### 19. Speculative configuration

Remove config flags, env vars, options parameters that have exactly one used value across the codebase. Configuration is a contract with future readers — exposing one without a current consumer adds maintenance burden for no benefit.

### 20. Restating comments

Remove comments that say what the next line of code already says. Examples: `// increment counter` above `counter += 1`; `# parse the response` above `data = json.loads(raw)`. Keep comments that explain non-obvious why (invariants, workarounds, constraints).

### 21. Framework-verification tests

A more explicit subsection of #2. Remove tests asserting only "import works", "function exists", "method returns truthy" without exercising business logic. Remove mock-confirming tests (the only assertion is `mock.assert_called_with(...)`). Remove snapshot tests where the shape itself is not the contract — they catch any change, including correct ones. Keep behavior assertions that fail when business logic changes.


Return one of:
  - "no slop found" — exited without commit, nothing to clean.
  - "committed {sha}" — committed `chore: prune slop from ...` at {sha},
    test suite green.
  - "errored: {short reason}" — dispatch problem; do not commit, just
    explain so the caller can record the failure.
