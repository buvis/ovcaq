# Discovery: Hold backlog re-triage and remaining hardening

## Classification

Depth: standard | Date: 2026-10-19 | Status: open

## Problem

`prds/hold/` holds 39 triage stubs minted by machine review on 2026-09-06 and
2026-10-09. They look like a large defect backlog, but later repair work fixed
most of them without closing the stubs. All 39 were re-checked against HEAD
`cee9b94` on 2026-10-18 and 2026-10-19: 30 are fixed, 4 are partial, 5 are
live. Until the fixed ones are closed, the folder overstates the risk and
hides the few defects that remain.

## Requirements

### Must have

- Close the 30 fixed stubs, each with the evidence line from the table below.
- Fix the live redaction and telemetry defects:
  - 00035: the reducer binds session identity only on start or terminal events,
    so another session's usage merges in. Repro: B's usage, then A start and
    complete, gives `session_id='A'`, `input_tokens=999`. Bind on the first
    observation; treat a different id as a conflict. (`src/ovcaq/events/reducer.py:50-61`)
  - 00037: values under an `environment` mapping survive when the key name
    looks harmless (`{"MY_VAR": "hunter2plain"}`). Redact every value under
    `environment` or `env`. (`src/ovcaq/events/model.py:112-119`)
  - 00055: Codex `bounded_detail` leaks the tail of a token split by control
    characters (`'Bearer [REDACTED]bbbbbbbb'`). Merge the marker with stuck
    token characters before control removal, then recheck the claim at
    `docs/driver-protocol.md:224`. (`src/ovcaq/drivers/codex_events.py:57-67`)
- Refresh the Codex pin (00052): `drivers/codex.py:38` and the fixture pin
  0.160.0; the installed CLI is 0.163.0. Characterize 0.163.0, update the pin,
  the fake launcher default, and a new fixture directory. Add direct
  `_run_probe_command` tests that bound each stream at 16,384 bytes.
- Fleet registry identity (00019, partial): compare the opened fd identity
  with the pre-open stat in `_scan`, and re-check the inode in `remove` before
  `os.unlink`. (`src/ovcaq/runtime/registry.py:387-390`, `:416-422`)

### Nice to have

- Session evidence paths that still reopen by name (all inside symlink-refusing
  trees, so not exploitable today): `acknowledge_emergency_failure`
  (`session.py:680`), `_publish` without identities (`session.py:605,636,647`),
  and `publish_session_metric` (`session.py:211-217`).

### Out of scope

- Supervisor residuals 00020, 00034, 00041 and classification 00036. They
  live in discovery 00004.
- The state-file resolver 00021. It lives in discovery 00003.

## Codebase Context

Full verdicts. "Read" means code reading; "ran" means a probe or test.

| Stub | Verdict | Evidence | How |
| --- | --- | --- | --- |
| 00015 | fixed | `workflow/_files.py:295-319` fsyncs every parent on every call | read, ran |
| 00016 | fixed | `_files.py:299-306` rejects a replaced parent | read, ran |
| 00017 | fixed | `_files.py:290-293,321`, re-check at `:351-370` | read, ran |
| 00018 | fixed | `_files.py:267-279` lstat-checks every ancestor | read, ran |
| 00019 | partial | see Must have | read |
| 00020 | fixed, residual in 00004 | `supervisor.py:161-182` | read |
| 00021 | live, in 00003 | three resolvers disagree | ran |
| 00022 | fixed | `_retention.py:343-370` locks by dir fd | read |
| 00023 | fixed | `_retention.py:300-308` bounds each row | read |
| 00024 | fixed | `registry.py:218-221`, `:290-301`, `:447-451` | read |
| 00025 | fixed | `registry.py:243-287` | read |
| 00026 | fixed | `process.py:147-159` kills the group before closing | read |
| 00027 | fixed | `config.py:236,243,251` validate paths | ran |
| 00028 | fixed | `config.py:185-188,225-228`, `paths.py:93-95` | ran |
| 00029 | fixed | `_session_io.py:27-112` | read |
| 00030 | fixed | `runtime_cli.py:154-165` | read |
| 00031 | fixed | `_run_observation.py:200-203` | read |
| 00032 | fixed | `runtime_cli.py:193-240` | read |
| 00033 | fixed | `_run_observation.py:167-213` uses F_GETLK | read |
| 00034 | partial, in 00004 | `FleetRegistry.prune` has no caller | read |
| 00035 | live | see Must have | ran |
| 00036 | partial, in 00004 | Claude misses auth, 429, ECONNRESET | ran |
| 00037 | live | see Must have | ran |
| 00038 | fixed | `claude.py:45-56`, `:129` | read |
| 00039 | fixed | `claude_events.py:127-147`, `claude.py:288` | ran, read |
| 00040 | fixed | `commands.py:599-605` sets attention | read |
| 00041 | partial, in 00004 | reset at `supervisor.py:611-612`, bounded by repeat limit | ran |
| 00042 | fixed | `supervisor.py:145-156` starts the batch | ran |
| 00043 | fixed | `tui/model.py:529-540` | read |
| 00044 | fixed | `_run_observation.py:102-133`, `tui/app.py:123-130` | read |
| 00045 | fixed | `tui/app.py:341,367-388` polls off the UI thread | read |
| 00046 | fixed | `tui/model.py:367-388` | read |
| 00047 | fixed | `cli.py:549-550` | ran |
| 00048 | fixed | `session.py:305-321` | read |
| 00049 | fixed | `tui/app.py:98-114` | read |
| 00050 | fixed | `_run_observation.py:156-163` | read |
| 00052 | live | see Must have | ran |
| 00055 | live | see Must have | ran |
| 00056 | fixed | `codex_events.py:300-303` | ran |

Several stubs still name `dev/local/prds/hold/` as their home (for example
00022, 00026). That path is obsolete.

## Success Criteria

- `prds/hold/` contains only the five phase PRDs (00010 to 00014) and stubs
  with a live or partial defect, each linked from a discovery doc.
- Each live defect has a regression test that fails on today's code.

## Risks

- **Closing a stub that is not really fixed**: 18 verdicts rest on code
  reading only. Close them with the cited line, and keep the review ledger
  key, so a later regression can be traced.

## Open Questions

- A symlinked `~/.config/ovcaq` (for example a stow-folded dotfile) is refused
  even when no config file exists (`tests/runtime/test_paths.py:485`). Is that
  intended? Many dotfile setups fold that directory.

## Discovery Log

### Q1: Is the hold folder mostly real defects or mostly stale?

**Answer**: Mostly stale. 30 of 39 are fixed at HEAD; 5 are live, all in
telemetry redaction, session identity, or launcher pinning.
