# PRD 00008 recovery task 12

Live resume help names clear-pause and interactive launch/attach. Generator-owned operator guidance describes TTY and foreground behavior, exact selector options, live/ended resume, JSON constraints, q/p/s/? controls, boundary pause, confirmed selected-run stop, detach survival, theme storage including unset/empty XDG semantics, and plain fallback. CHANGELOG now has the missing Added entry. The tracked reference equals the live parser renderer; no second handwritten verb inventory was introduced. Lifecycle logic is unchanged.

Basea30ae6b42b6b89653ef047354e58682467ef4a37; commitcf9bd33306d54fb501b6eaeffe1baf8bdbd2d3ef. Micro helper eligible for2findings/2findingpaths, but actual edit49net/3files; preserved scratch diff and restored only task-owned clean-at-claim slices before normal pipeline. Documentation/help-only task skipped new Tess tests and red-check; existing parser/reference checks passed independently2cases2pre-existing pytest cleanup warnings,exit0,0.14s. Main live-help command exit0 verified final description. Per-task review retained for rework closure.

Routing: backendsonnet, effective3writablefiles excludedQwen. Same-batch cached source codex_probe202609062243 unhealthy(hook_doctor empty analyze-instincts.py) reused as required; no external Codex or Claude implementor probe was claimed. Native logicalsonnet actualgpt-5.6-sol Ivanc4beec2d16,050bytes. Coordinator corrected selector, conditional resume, and empty-XDG prose before commit. Fresh self-deslopd495adee13,412bytes returned no slop found/no edits. Mechanical style clean, split hygiene skipped:no-tests, reflow no threshold. The implementor miscalled bounded runner with -- as log path; confirmed task-owned --/--.json were relocated into ignored docs/dev/tmp after their exact metadata matched the reported size check. Main verification used the correct bounded runner with distinct logs, so no ambiguous overwritten agent result was used for acceptance.

Pat51c85db214,870bytes, guarded tool-free external Claude, approved network, sessionbff057cd-4941-49e3-9a8e-7c813372fefa, actualclaude-sonnet-5-5. F27/F33 resolved. LOW empty-XDG concern is rejected as a code change: accepted task9 explicitly shares the existing resolver's unset/empty/relative semantics, and current _config_root uses os.environ.get without treating empty as unset. The new sentence correctly documents delivered behavior; older shell-like shorthand elsewhere does not override that verified contract. LOW paragraph wrapping retained. Raw parsed verdict retained below. No completion review invoked.

## Raw Pat review

CLOSURE | resolved | F27 "CHANGELOG has no Added entry for `ovcaq attach`, TTY-default `ovcaq run`, the TUI with plain fallback, or interactive `resume` that launches or attaches" | CHANGELOG.md adds a `**tui**` Added bullet covering attach, TTY-default run, detach/plain fallback and interactive resume that attaches or launches once.

CLOSURE | resolved | F33 "`resume` help still says 'clear a pause request'... operator docs don't mention the q/p/s/? keys, the theme path, or the plain fallback" | cli.py:202 help is now "clear pause; interactively launch or attach", and the new "Interactive operation" section in docs/operations.md and `render_command_reference` covers q/p/s/?, the theme path and the plain fallback. The two parser-inventory tests pass (2 passed).

LOW | docs/operations.md:70 (mirrored in src/ovcaq/cli.py `render_command_reference`) | "An empty XDG_CONFIG_HOME uses the current directory" contradicts the contract `${XDG_CONFIG_HOME:-~/.config}/ovcaq/theme`, where `:-` treats an empty value as unset. It also contradicts the "when unset" sentence just before it and the config.toml line below, which uses the `:-` form. I can't see the implementation, so the doc may describe the code and the code may be the defect. | Confirm the theme path code treats empty as unset, then delete the sentence, or fix the code to match the contract.

LOW | docs/operations.md:58 | The `q`/`p` line is noticeably longer than the surrounding wrapped lines. | Rewrap the paragraph in both the generator and the doc.


## Implementation report

# Task 12 report

## Result

- Updated `resume` help to describe interactive resume-and-attach behavior.
- Added generator-owned operator guidance for `q`/`p`/`s`/`?`, confirmed selected-run stop, detach survival, live-versus-ended resume, JSON `--no-tui`, the XDG theme path, and plain fallback.
- Regenerated `docs/operations.md` from `ovcaq.cli.render_command_reference` output.
- Added the delivered TUI/CLI feature entry under Unreleased / Added.

## Verification

- `python docs/dev/tmp/run_bounded.py 300 -- uv run pytest -q --tb=line tests/runtime/test_runtime_cli.py::test_live_parser_inventory_and_generated_operations_include_runtime_commands tests/runtime/test_supervisor_cli.py::test_parser_inventory_and_reference_expose_the_same_lifecycle_commands` — exit 0; 2 passed, 2 pytest cleanup warnings, 0 failed, 0 skipped.
- `python docs/dev/tmp/run_bounded.py 60 -- uv run ovcaq --help` — exit 0; live help contains `resume and attach to the project run`.
- `python docs/dev/tmp/run_bounded.py 60 -- uv run python -c 'from ovcaq.cli import render_command_reference; print(render_command_reference(), end="")'` — exit 0 after approved cache access; output used for the generated artifact.
- `python docs/dev/tmp/run_bounded.py 60 -- awk '/^def render_command_reference/{flag=1} flag{count++} /^def _path_operation/{print count-1; exit}' src/ovcaq/cli.py` — exit 0; 42 computed lines.
- `python docs/dev/tmp/run_bounded.py 60 -- wc -l src/ovcaq/cli.py` — exit 0; 692 lines.
- `python docs/dev/tmp/run_bounded.py 60 -- git diff --check -- src/ovcaq/cli.py docs/operations.md CHANGELOG.md` — exit 0; no output.
- `python docs/dev/tmp/run_bounded.py 60 -- git diff --numstat -- src/ovcaq/cli.py docs/operations.md CHANGELOG.md` — exit 0; counts: CHANGELOG 1/0, operations 14/0, cli 15/1.

## Retained failure evidence

- Six initial bounded reads used the wrong runner shape (`60 sed ...`) and exited 1 because the runner attempted to execute `-n`; rerunning as `60 -- sed ...` succeeded.
- The first generator invocation exited 2 because sandboxed uv could not initialize `/Users/bob/.cache/uv`; the exact command succeeded with approved cache access.

## ASSUMPTIONS

- “Regenerate” permits capturing the renderer's exact stdout and applying that output to the tracked generated file with `apply_patch`, as required by the workspace editing rules.
- “Selected-run stop” is accurately described as confirmation-bound because the live TUI confirmation names the selected run before invoking its control service.

## FILES_TOUCHED

- `src/ovcaq/cli.py`
- `docs/operations.md`
- `CHANGELOG.md`
- `docs/dev/tmp/r12-ivan-report.md`


## Main verification

..                                                                       [100%]
=============================== warnings summary ===============================
.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-230885d4-8d85-46eb-b37d-30fc59c8d53d
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-230885d4-8d85-46eb-b37d-30fc59c8d53d'
    warnings.warn(

.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95
  /Users/bob/git/src/github.com/buvis/ovcaq/.venv/lib/python3.13/site-packages/_pytest/pathlib.py:95: PytestWarning: (rm_rf) error removing /private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-6238e9e0-1885-46d3-b2db-12f35a3b53ad
  <class 'OSError'>: [Errno 66] Directory not empty: '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/pytest-of-bob/garbage-6238e9e0-1885-46d3-b2db-12f35a3b53ad'
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 2 warnings in 0.14s

{
  "command": [
    "uv",
    "run",
    "pytest",
    "-q",
    "--tb=line",
    "tests/runtime/test_runtime_cli.py::test_live_parser_inventory_and_generated_operations_include_runtime_commands",
    "tests/runtime/test_supervisor_cli.py::test_parser_inventory_and_reference_expose_the_same_lifecycle_commands"
  ],
  "exit": 0,
  "timeout_seconds": 300
}

## Live help

usage: ovcaq [-h] [--root PATH] [--json]
             {init,state,workflow,status,doctor,logs,run,attach,pause,resume,stop,capability} ...

Orchestration, Visibility, and Control for Agent Queues

positional arguments:
  {init,state,workflow,status,doctor,logs,run,attach,pause,resume,stop,capability}
    init                initialize OVCAQ state
    state               inspect or mutate OVCAQ state
    workflow            apply deterministic workflow operations
    status              show state, run, and retained evidence health
    doctor              check runtime health and capabilities
    logs                locate or follow retained session evidence
    run                 launch and attach, or supervise in the foreground with
                        --no-tui
    attach              attach the TUI to a live run
    pause               request a pause at the next boundary
    resume              clear pause; interactively launch or attach
    stop                signal the verified foreground supervisor
    capability          manage batch capabilities

options:
  -h, --help            show this help message and exit
  --root PATH
  --json

{
  "command": [
    "uv",
    "run",
    "ovcaq",
    "--help"
  ],
  "exit": 0,
  "timeout_seconds": 60
}