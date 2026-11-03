Abort above100K input; no state writes or commits. Only named tests; real process tests require approved escalation.

A diff has been written to satisfy this task. The implementation passed its
tests. Your job: prune slop from the diff while keeping every test green.
This is best-effort cleanup, not a correctness rework — do not change
behavior, do not modify tests, do not refactor.

Task: [D1] Task 19 split: shared health and activity

Description:
Review: docs/dev/project-management/reviews/00009-codex-adapter-v1-review-1.md
Design context: docs/dev/project-management/designs/00009-codex-adapter-v1-design.md

Resolve the provider-edge and shared launch/presentation findings. Preserve driver API 2, observation protocol 1, state schema 1, strict argv and provider neutrality. Verify native failure examples against pinned upstream source before choosing classifications; distinguish quota, capacity, sandbox, network and explicit agent failure without broad prose scanning. Do not change deferred reset grammar or configured options. Test public behavior independently, including exact fixture expectations and direct decode totality. R14 uses generic adapter health checks, never Codex-specific runtime policy. R16 renders normalized activity for both adapters.

Acceptance: every quoted finding no longer reproduces; preserve all existing assertions and full shared conformance. Run source work pipeline, independent behavioral regressions where needed, and its mandatory final verification.


Failure-driven split of task 19 (Tess context_overrun, no edits). Scope only findings below; other task-19 findings belong to sequential siblings. Preserve exact findings and all assertions.

### Findings (verbatim)
- 🟡 src/ovcaq/drivers/edge.py:26: `CodexDriver.probe()` (binary check, exact 0.160.0 version pin, `login status` auth check) never runs in production. `build_driver` and `supervisor_cli` build the driver without probing it. Only `discover_drivers` calls `probe()` (src/ovcaq/drivers/base.py:155), and no code under src calls `discover_drivers`. So the CLI-drift guard and the auth check do nothing in real runs, and a newer CLI would launch unchecked. (found by: BLAKE)
- 🟡 src/ovcaq/tui/panels.py:86: The TUI Activity panel shows only lanes. Codex command, file-change, MCP, web, plan and message activity is decoded but never displayed, so a Codex session without collaboration lanes shows "no lanes observed". The PRD requires that the "TUI shows Codex identity/activity/usage". docs/driver-protocol.md:273 admits that panels render lanes only. (found by: BLAKE)


Acceptance criteria:
All quoted findings resolved; preserve passing assertions.

Tests that the diff made pass (do NOT modify):
/Users/bob/git/src/github.com/buvis/ovcaq/tests/runtime/test_rework_health.py, /Users/bob/git/src/github.com/buvis/ovcaq/tests/tui/test_rework_activity.py

Files in the diff:
/Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/supervisor_cli.py, /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/model.py, /Users/bob/git/src/github.com/buvis/ovcaq/src/ovcaq/tui/panels.py, /Users/bob/git/src/github.com/buvis/ovcaq/docs/driver-protocol.md, /Users/bob/git/src/github.com/buvis/ovcaq/CHANGELOG.md

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
     chore: prune slop from [D1] Task 19 split: shared health and activity
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
