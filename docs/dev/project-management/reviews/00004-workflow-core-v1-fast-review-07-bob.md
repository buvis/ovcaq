---
session: FT-04R7
review: 7
reviewer: bob
head_sha: 47a8764760e1fedb82eb1514a344584fb7ad2f3e
runner: native-isolated-codex-subagent
---

# Bob — cycle-07 lens report

The following is the reviewer's final text, preserved without coordinator revisions.

[BOB] 🟡 F1: A FIFO at runtime metrics.jsonl blocks both report and metrics commands indefinitely: load_metric_rows opens it with blocking Path.read_text before checking its file type; use a nonblocking descriptor and reject nonregular inputs before reading | File: src/ovcaq/workflow/reports.py:133 | Task: P02-T08
[BOB] 🟡 F2: Newly added orchestration exceeds the required function/file limits: _execute_operation is 169 lines, _dispatch_workflow 109, and _add_workflow_commands 76; records.py is 955 lines and cli.py 838; separate the existing stages and command groups while preserving transaction, descriptor, lock, and failpoint boundaries | File: N/A | Task: general
[BOB] 🟡 F3: _verify_move introduces redundant existence booleans and an impossible source_stat-is-None branch inside if source_exists; test the stat results directly and retain the regular-file rejection | File: src/ovcaq/workflow/records.py:538 | Task: P02-T07
[BOB] 🟡 F4: _more_prds is a forwarding wrapper referenced only by TRANSITIONS; reference reset_prd_fields directly in that row and remove the wrapper | File: src/ovcaq/workflow/transitions.py:61 | Task: P02-T03
[BOB] ⚪ V1: Cannot statically verify: required tests, lint, formatting, typing, and package build pass | File: N/A | Task: general

Static review only; no project code, tests, or linters executed, and no files modified. Scope included P02-T01–P02-T10, mandatory source-contract material, implementation, and relevant unit/application/installed-command tests.

**Correctness doubts and resolutions**

| Doubt | Static evidence | Resolution |
|---|---|---|
| Can a drained workflow reopen through another transition or saga? | `transitions.apply` rejects `done` with empty `next_phase` before table lookup. `_execute_operation` rejects that state before opening lifecycle directories. Unit and installed tests enumerate transition outcomes, park, and stall. | Dismissed for the supported workflow commands. |
| Can stall silently consume a different pending intent? | `_execute_operation` compares PRD, kind, site, and detail for stall. Park deliberately reconciles the recorded operation; commit uses its explicit kind. Tests cover conflicts and kind collisions. | Dismissed. |
| Can a replaced deferred directory allow recovery intent to clear without durable evidence? | Publication uses directory-relative operations and identity checks. `verify_recorded` checks both the move and matching record, including inside state mutation callbacks. Recorded-step retries require ledger evidence and synchronize the directory. Tests cover replacement and restoration across relevant boundaries. | Dismissed for the inspected boundaries. |
| Do legacy completed rows become misleading zeros, or equal-key metrics depend on input order? | Completed fields reduce independently to `unknown` when absent/invalid; empty collections retain zero. Both metric partitions include canonical whole-row JSON as a tie-breaker. Tests cover TEST-062 shapes and colliding primary keys. | Dismissed. |
| Does nonregular-file refusal protect the complete report command? | `_read_file` protects output targets with `O_NONBLOCK` and `fstat`; `load_metric_rows` instead calls blocking `Path.read_text`. CLI report and metrics dispatch both reach this loader first. Existing nonregular tests exercise output targets. | Confirmed F1. |

F1 reproduction: initialize a temporary project, create `dev/local/ovcaq/metrics.jsonl` as a FIFO without a writer, and run each of `workflow render metrics` and `workflow render report` in a subprocess with a two-second timeout. The blocking open prevents the CLI from producing an error. The coordinator can verify the repair by requiring a prompt structured failure and unchanged FIFO/state bytes.

Other inspected obligations are present: configured path arguments at service boundaries; WIP precedence and hold exclusion; frontmatter defaults, abstract-tier validation, and overwrite ownership; plan validation and resume mapping; reset preservation and idempotent completion; atomic recovery fencing for state mutations; provider-neutral workflow imports/strings; and parser-generated documentation.

**Slop candidates and resolutions**

- **Oversized coordination — confirmed F2.** Separate intent acquisition, move advancement, and ledger/commit stages while keeping resource lifetimes explicit. The supplied mechanical inventory also identifies overlong report renderers: audit 59 lines, report 85, metrics 61. Split render sections and oversized test modules along existing responsibilities; retain all acceptance coverage.
- **Impossible defensive branch — confirmed F3.** `source_exists` was assigned `source_stat is not None`, with no intervening assignment. Replace both existence booleans with direct `is not None` conditions, allowing normal type narrowing.
- **Single-caller wrapper — confirmed F4.** The transition table can hold the imported reset function directly; the wrapper adds no validation, adaptation, or test seam.
- **State transaction wrapper — dismissed.** `StateService._transaction` centralizes the recovery guard inside the state lock across multiple mutations. Its boundary has a current correctness purpose.

**De-slop R1–R5**

| Rule | Inspected evidence | Verdict |
|---|---|---|
| R1 — bloat ratio | Full diff adds 7,593 net lines; source Phase 2 task/exit text plus PRD acceptance excerpt totals 221 words, roughly 34:1. That ratio includes substantial required characterization coverage and is only a screening signal. Concrete concentration appears in the supplied 169/109/85-line function counts and oversized files. | fail |
| R2 — defensive impossibility | `records.py:543` checks `source_stat is None` inside a branch whose condition already proves the opposite. | fail |
| R3 — single-caller abstraction | `_more_prds` only forwards to `reset_prd_fields`, and its sole reference is the transition row. The state transaction wrapper has a justified purpose. | fail |
| R4 — paraphrasing comments | Inspected comments explain durability boundaries, schema/projection distinctions, or public function intent. No material comment-removal repair identified. | pass |
| R5 — framework-verification tests | Parser/docs equality tests enforce an explicit product contract. Saga tests assert retained tasks, recovery steps, directory identity, publication bytes, and replay behavior. No framework-only test identified. | pass |

FIX:

- F1 — `src/ovcaq/workflow/reports.py:133` — Open metric inputs nonblockingly, require a regular file before reading, and add subprocess tests covering FIFO input for both render commands.
- F2 — `src/ovcaq/workflow/records.py:728`, `src/ovcaq/cli.py:145`, `src/ovcaq/cli.py:605`, and the supplied oversized-function inventory — Separate existing stages/command groups/render sections to meet the 50-line function and 800-line file limits without changing public behavior or durable ordering.
- F3 — `src/ovcaq/workflow/records.py:538` — Branch directly on the two stat results and remove the impossible `None` alternative.
- F4 — `src/ovcaq/workflow/transitions.py:61` — Reference `reset_prd_fields` directly in `TRANSITIONS` and remove `_more_prds`.

VERIFY:

- V1 — Inspect retained results for `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src/ovcaq`, and `uv build`; static inspection cannot establish their runtime outcomes.

KNOWN:

- (none)

Residual count: **5 = 4 FIX + 1 VERIFY + 0 KNOWN**. Dismissed doubts are observations, not residual findings. FIX entries are recommended repairs only.

R1: fail
R2: pass
R3: pass
R4: pass
R6: pass
R7: fail
R8: pass
R9: fail
R10: fail
R11: pass
R12: fail
R13: fail

D1: pass
D2: pass
D3: pass
D4: pass
D5: pass
