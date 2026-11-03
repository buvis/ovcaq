# PRD 00006 build dispatch evidence

Host adaptation: native Claude Agent/Task roles were dispatched as isolated native Codex subagents. Logical `opus` used `gpt-6-astra`; the fixed Pat lane used external Claude Sonnet through `use-sonnet`.

## Task 1 — Define the normalized event protocol

| Role | Dispatch ID | Logical tier | Provider/model | Outcome |
|---|---|---|---|---|
| Tess initial | `520e5d7e` | opus | Codex / `gpt-6-astra` | requirements blocker surfaced |
| Tess corrected | `05fa789d` | opus | Codex / `gpt-6-astra` | tests authored |
| Devon round 1 | `655997f0` | opus | Codex / `gpt-6-astra` | exploit found |
| Tess strengthen | `eacbdb65` | opus | Codex / `gpt-6-astra` | tests strengthened |
| Devon round 2 | `783ba776` | opus | Codex / `gpt-6-astra` | round exhausted; success-field gap retained |
| Ivan | `944f6076` | opus | Codex / `gpt-6-astra` | implementation completed; 218 focused tests passed |
| Self-deslop | `e22c16d3` | opus | Codex / `gpt-6-astra` | no slop found |
| Pat initial | `228521ab` | fixed sonnet | Claude / `sonnet` alias | invalid output contract |
| Pat correction | `d1c249f1` | fixed sonnet | Claude / `sonnet` alias | invalid output contract; LOW-only findings |

The prior attempt already recorded in state (`attempt: 1`) ended as `subagent_infra_failure`; this session was the task's single permitted infrastructure re-dispatch.

## Task 2 — Implement deterministic session reduction

| Role | Dispatch ID | Logical tier | Provider/model | Outcome |
|---|---|---|---|---|
| Tess initial | `6b318879` | opus | Codex / `gpt-6-astra` | tests authored after monotonic-terminal clarification |
| Devon round 1 | `2436021e` | opus | Codex / `gpt-6-astra` | public-model prerequisite and invalid cost fixtures surfaced |
| Tess strengthen | `e3c1a6a8` | opus | Codex / `gpt-6-astra` | fixtures corrected; reset regression added |
| Devon round 2 | `7bb51712` | opus | Codex / `gpt-6-astra` | provider-hardcode exploit found; round exhausted |
| Ivan initial | `52439cf5` | opus | Codex / `gpt-6-astra` | implementation completed; 309 focused tests passed |
| Self-deslop | `30fd38fd` | opus | Codex / `gpt-6-astra` | no slop found |
| Ivan style fix | `db0a8dfb` | opus | Codex / `gpt-6-astra` | oversized functions split; gate clean |
| Pat initial | `29983dd0` | fixed sonnet | Claude / `sonnet` alias | one MEDIUM and one LOW |
| Ivan review fix | `8621027c` | opus | Codex / `gpt-6-astra` | MEDIUM stale-reset finding fixed |
| Pat delta rerun | `5b98d436` | fixed sonnet | Claude / `sonnet` alias | `NO FINDINGS`; medium retry fixed |

Pat's initial LOW about importing the private `_parse_utc` helper was retained for the mandatory PRD-level review; the in-task retry was intentionally scoped to the confirmed MEDIUM finding.
