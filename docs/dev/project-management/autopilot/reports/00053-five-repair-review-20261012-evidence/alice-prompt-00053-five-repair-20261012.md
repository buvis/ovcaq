You are Alice, a code reviewer.

Never call bash `head`, `tail`, `cat`, `grep`, or `find` - a hook blocks them. Use the Read tool (offset/limit), `rg`, or `rg --files` instead. Never pipe between heterogeneous commands and never combine an inspection (read, list, search, diff) with a test, lint or build invocation in one Bash call - run them as separate calls. Pass an explicit `timeout` on every Bash call: 60000 ms for an inspection, 300000 ms for a lint run or a narrow test run, 600000 ms for a full suite or a full build.

Read /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/review-context-00053-five-repair-20261012.md for review context, and /Users/bob/git/src/github.com/buvis/ovcaq/docs/dev/tmp/review-diff-00053-five-repair-20261012.diff for the full diff.

Read (no pack available this cycle) and treat its full content as prepended context: similar code, reuse precedent, findings precedent, and task prose for this diff's changed symbols.

Use this review checklist:
# Review Dimensions

Detailed checklist for reviewing completed work.

## Plan Compliance

- [ ] Implementation matches task description
- [ ] All acceptance criteria met
- [ ] No scope creep (extra features not requested)
- [ ] No missing pieces from original task

## PRD Coverage

- [ ] All "must have" requirements addressed
- [ ] Success metrics achievable with implementation
- [ ] No PRD sections left unimplemented
- [ ] Dependencies correctly handled

## Simplification

Hunt actively for simplification — do not just tick boxes. The diff under
review is fresh; this is the cheapest moment to cut complexity before it sets.
For every added or changed file, ask "what would make this simpler to read
without changing what it does?" and flag concrete opportunities.

- [ ] **Reduce complexity** — no needless indirection, dead branches, or
      abstractions built for a single caller; nesting <= 4 levels; functions
      under 50 lines
- [ ] **Eliminate redundancy** — no logic duplicated within the diff or against
      existing code; no helper that reimplements a stdlib or existing utility
- [ ] **Improve naming** — names state intent; no opaque abbreviations;
      action-named functions start with a verb
- [ ] **Follow project standards** — conventions from CLAUDE.md / AGENTS.md and
      the surrounding code; no style drift
- [ ] **No dead code** — no commented-out blocks, unused imports, variables, or
      speculatively-added parameters
- [ ] **Appropriate error handling** — explicit, never silently swallowed

**How to flag a simplification:** give the file:line, the current shape, and
the simpler replacement. Flag concrete behavior-preserving simplifications at
🟡 Medium so the decision gate routes them into the rework loop. Do not inflate
them to 🟠 High; that floods the rework loop and can trip the scope alarm.

**Balance — do not over-simplify:** never propose a change that trades clarity
for brevity, drops error handling, collapses a deliberate boundary, or removes
a documented invariant. Simpler means easier to read and maintain, not shorter
at any cost. If a "simplification" would change behavior, it is out of scope —
do not flag it.

## Testing

- [ ] Unit tests for new logic
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] Integration tests if crossing boundaries
- [ ] Tests actually run and pass
- [ ] No tautological test — every new or changed test fails against the
      pre-change code (the context's fail-first replay block), and no assert
      is constant, self-comparing, or an either-or hedge (the shapes block)

## Security

- [ ] No hardcoded secrets
- [ ] Input validation at boundaries
- [ ] No SQL/command injection risks
- [ ] Auth/authz correctly applied
- [ ] Sensitive data not logged

## Documentation

- [ ] Public APIs documented
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] Breaking changes noted

In addition, work through the numbered rubric:
# Review-Work-Completion Rubric

This rubric defines binary pass/fail criteria for consensus review of completed work. Each rule is numbered and stable for tracking coverage. Reviewers must answer "R{n}: pass|fail" for every rule in their prompt.

## Rules

### Tests

R1: Tests cover every new behavior introduced by the diff.
R2: Tests bind to intent, not just observable behavior; no new or changed test is tautological (passes against the pre-change code, or cannot fail as written).
R3: No skipped or xfail tests mask failures.

### Integration

R4: Changed components integrate with existing callers.

### Security

R6: No hardcoded secrets in the codebase.
R7: All user input is validated and sanitized.
R8: No injection-unsafe queries or commands.

### Domain

R9: Implementation matches PRD feature behavior exactly.
R10: Error handling is explicit and not swallowed.
R11: No debug statements, TODOs, or placeholder markers remain.

### Code Quality

R12: Function sizes respect the 50-line limit.
R13: File sizes respect the 800-line limit.

Review the completed work against PRD requirements. Explore the codebase as needed.

OUTPUT FORMAT IS MANDATORY. Follow exactly:
## Agent Output Format (Single Source of Truth)

Each agent outputs issues in this exact format:

```
[{AGENT_NAME}] {emoji} {description} | File: {path or "N/A"} | Task: {id or "general"}
```

**Severity emojis:** 🔴 Critical, 🟠 High, 🟡 Medium, ⚪ Low

**Rules:**
- One issue per line
- Use "N/A" for file if issue is architectural/cross-cutting
- Use "general" for task if issue spans multiple tasks or is a PRD gap
- If zero issues found: `[{AGENT_NAME}] ✅ No issues found`

**Examples:**
```
[ALICE] 🔴 SQL injection in query builder | File: src/db/query.ts | Task: 3
[BOB] 🟠 Missing error handling strategy | File: N/A | Task: general
[CARL] 🟡 PRD section 2.3 not implemented | File: N/A | Task: 5
```

Your agent name is ALICE.

Cite files repo-relative as path:line (for example skills/work/SKILL.md:166), never absolute and never with a "(lines a-b)" suffix.

PER-RULE VERDICTS ARE MANDATORY. For every rule in the numbered rubric, emit one line:
R{n}: pass   or   R{n}: fail
(one rule per line, no other text on the line, no rationale).

## Settled decisions — do not re-raise

> These calls were already made in an earlier cycle of this same review, with
> the reasons given. Do not re-raise them. Raise a NEW finding only if you can
> show the settled reason no longer holds.

- [discarded] low: `_ResolvedModelCodexDriver.build_launch` is identical to `_ResolvedModelClaudeDriver.build_launch` (inverse tier map plus `replace`). A shared module function such as `_tier_key_request(settings, request)` called by both overrides would remove the copy. The design asked for mirroring, so this is low (src/ovcaq/drivers/edge.py:26) - reason: Duplicate of R7: both cite the identical inverse-tier overrides. R7 is fixed; no second task is needed. Raw findings remain preserved.
- [discarded] low: Cannot statically verify: phase-2 exit gate (pytest, ruff check, ruff format --check, mypy, uv build). The test gate reports exit 0 but gives no counts (N/A) - reason: Resolved by current-HEAD verification: 7165 passed, 0 failed, 0 skipped; sync, Ruff lint/format, mypy and build all exit 0. See 00053-review-1-verification.json. Bob VERIFY command uses &&, so not queued: command shape; each required gate already ran separately.
- [settled-deferral] low: The Codex probe runs in the caller's working directory, while the launch runs in request.root. A relative command or an empty-PATH lookup can therefore succeed in the probe and fail at launch, or the reverse (existing behavior) (src/ovcaq/drivers/codex.py) - reason: Known pre-existing caller/request-root cwd disagreement. PRD explicitly excludes probe descendant/ownership redesign and preserves Codex probe behavior. Defer outside this repair; do not change the current scope.
- [discarded] medium: 33 touched test(s) pass against the pre-change code: test_numeric_diagnostics_require_an_explicit_status_or_error_context +27 more (tests/drivers/test_adapter_failure_classes.py) - reason: Existing valid HTTP/word diagnostics, precedence and reset parsing are compatibility controls the PRD explicitly requires retaining. New false-positive negatives and capacity cases fail at base; literal oracle expectations are independently pinned. Passing preservation cases are not tautologies.
- [discarded] medium: 40 touched test(s) pass against the pre-change code: test_unfinished_lane_fails_after_close_status +34 more (tests/drivers/test_adapter_outcomes.py) - reason: New completed-lane regressions fail at base; running/unstarted/unknown preservation cases deliberately cover unchanged behavior. R8 separately fixes actual redundant test padding; it is not silently dismissed by this characterization decision.
- [discarded] medium: 10 touched test(s) pass against the pre-change code: test_native_failure_emits_classified_terminal_with_receipt_identity +4 more (tests/drivers/test_codex_decode_terminals.py) - reason: Existing terminal fixture outcomes remain unchanged; only the independent literal oracle replaces a production-derived expected class. Such an oracle correction is expected to pass base.
- [discarded] medium: 7 touched test(s) pass against the pre-change code: test_failure_classification_uses_documented_precedence +1 more (tests/drivers/test_codex_failures.py) - reason: Existing failure fixtures and reset behavior are compatibility controls; independent literal oracles replace classifier-derived expectations without requiring changed production outcomes.
- [discarded] medium: 81 touched test(s) pass against the pre-change code: test_launch_has_exact_order_and_omits_unconfigured_flags +75 more (tests/drivers/test_codex_launch.py) - reason: Direct tier precedence, explicit-model validation, safe flags and ordinary config remain unchanged by contract; supervised collision regressions fail at base. R13 separately fixes the broad factory exception check.
- [discarded] medium: 14 touched test(s) pass against the pre-change code: test_native_diagnostics_have_independent_failure_classification +8 more (tests/drivers/test_codex_rework_decode.py) - reason: Existing diagnostic fixture is deliberately unchanged, with expected CONNECTIVITY now a literal independent oracle. Passing at base is required characterization.
- [discarded] medium: 21 touched test(s) pass against the pre-change code: test_probe_finds_executable_available_only_on_overlay_path, test_probe_rejects_absolute_command_that_is_not_an_executable_file +15 more (tests/runtime/test_adapter_health.py) - reason: Codex effective PATH already behaved correctly and PRD requires regression rather than forced production edits; inherited/absolute/default health controls preserve behavior. Claude overlay failures fail at base. R3 separately repairs the empty-PATH test discrimination.
- [discarded] medium: 1 touched test(s) pass against the pre-change code: test_configured_supervisor_launches_each_selected_literal_model_and_effort (tests/runtime/test_adapter_launch_routing.py) - reason: This parametrized test includes unchanged non-colliding routes as compatibility controls; colliding Codex route cases fail at base. A passing invocation of the same test function does not negate its failing cases.
- [settled-deferral] medium: The `continue` at codex.py:383 drops every native update for a lane that has already finished. codex-cli 0.162.1 ships a `resume_agent` tool ("Resume a previously closed agent by id so it can receive send_input"; I confirmed the string in the binary). So a lane can legitimately go completed → close → resume → running → errored. With the `continue`, the resumed run's running and errored updates disappear with no trace, and a later interrupt or shutdown of the resumed run becomes raw unknown instead of `lane.failed`. The pre-change code reported these. The TUI already handles a restart, because the last write wins (src/ovcaq/tui/model.py:607). The PRD only requires that close statuses do not fail a completed lane, and the unfinished-only filter at src/ovcaq/drivers/codex.py:372 already does that on its own. Fix: delete lines 383-384. Then flip `test_finished_lane_late_update_retains_only_non_lane_observations` (tests/drivers/test_adapter_outcomes.py:266) so it expects running → `lane.progress` and errored → `lane.failed`, and reword docs/driver-protocol.md:243. Confidence: the tool is confirmed; the exact `agents_states` sequence after a resume is my guess (src/ovcaq/drivers/codex.py:383) - reason: Requirements ambiguity: resume/restart generation semantics are not specified by this PRD. The existing contract deliberately freezes completed/failed identities and pins late updates. A binary tool name does not prove a native status sequence; changing this would undo reviewed stability without a fixture. Preserve for separately specified adapter lifecycle work.
- [discarded] low: The normal Codex sequence (`wait` reports completed, then `close_agent` reports shutdown) emits `raw.unknown` on every close of a completed lane. The tests pin this at tests/drivers/test_adapter_outcomes.py:89. The lane result is right, but routine flows now show recurring normalization gaps. (src/ovcaq/drivers/codex_events.py:233) - reason: Intentional documented raw-evidence rule: unsupported terminal close statuses on finished lanes retain RAW_UNKNOWN while preserving terminal identity. Exact tests and protocol document it. UI gap-noise redesign is outside this PRD; deleting evidence would contradict the reviewed contract.
- [settled-deferral] low: A status prefix followed by an ordinary count still classifies. `status: 401 tests passed` returns `authentication` and `error code: 503 records` returns `connectivity` (confirmed by probe). The negative tests only cover counts with no status word in front. (src/ovcaq/drivers/codex_events.py:301) - reason: Requirements ambiguity: mixed diagnostic-prefix/ordinary-count messages need an explicit precedence contract. Existing scope requires diagnostic status contexts and ordinary count negatives; do not invent a broader prose grammar or silently change precedence. Keep the confirmed counterexamples for later specified work.
- [discarded] low: Suspected, not confirmed: a Codex `turn.failed` reading "Authentication failed" classifies as `unknown` (pinned at tests/drivers/test_adapter_failure_classes.py:129). That means a retry or park instead of the operator-access halt. The Claude classifier treats "authentication" as authentication, so the two adapters disagree. I could not check whether this was already the behavior before this change. (src/ovcaq/drivers/codex_events.py:306) - reason: The old classifier did not match authentication failed; cycle1 deliberately removed that added pattern to retain existing word diagnostics. This is known original behavior, not a lost required diagnostic. Existing authentication fixtures use literal invalid-credentials/unauthorized oracles.
- [discarded] low: Every routine close of a completed lane (wait completed, then close_agent shutdown) now emits raw.unknown. The TUI then marks ordinary multi-agent sessions as having raw evidence. Late running or completed updates for terminal lanes emit nothing, so the two cases behave differently. This is documented and tested as intended, but it adds noise. (src/ovcaq/drivers/codex_events.py:233) - reason: Previously settled and intentionally pinned raw-evidence behavior; no contract change authorized.
- [settled-deferral] low: Probe and launch can disagree on relative lookups. Both probes resolve relative PATH entries and relative command paths against the supervisor's own working directory, but launch runs with `cwd=request.root`. Absolute paths and normal PATH entries are unaffected. (src/ovcaq/drivers/claude.py:82) - reason: Existing out-of-scope relative-path/cwd limitation; probe ownership redesign excluded by PRD. New Claude citation retained.
- [discarded] low: The CHANGELOG entry about reqwest/HTTP-version forms and literal whitespace describes no change from the pre-PRD base. Bare codes already matched those forms there, and whitespace was already literal. The entry records rework done inside this PRD and overlaps the numeric-context entry three lines below (CHANGELOG.md) - reason: Duplicate of R2 changelog finding; one distinct repair request, both raw outputs preserved.
- [settled-deferral] low: The bare word "status" counts as an HTTP context, so ordinary counts after it still get a failure class. Confirmed: "status 401 files processed" and "exit status 401" both return `authentication`. Inside the PRD's wording, but no negative control is pinned for it (src/ovcaq/drivers/codex_events.py:302) - reason: Existing mixed diagnostic-prefix/count precedence limitation; requires later explicit contract.
- [discarded] low: A late update for a lane that already finished is now dropped with no `raw_unknown` record, while a late close status for the same lane does emit one. So a contradictory late "errored" after "completed" leaves no trace in the normalized stream; only raw.jsonl keeps it. `item_lanes(started_lanes=None)` also keeps its optional default: a caller that leaves it out never fails a lane on close (review R1 asked for it to be required) (src/ovcaq/drivers/codex.py:383) - reason: Existing remembered-terminal identity contract; raw session evidence survives. Production decoder supplies unfinished identities; no new required helper signature.
