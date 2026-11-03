CLOSURE | resolved | `CodexDriver.probe()` (binary check, exact 0.160.0 version pin, `login status` auth check) never runs in production; `build_driver` and `supervisor_cli` build the driver without probing it | `src/ovcaq/supervisor_cli.py` `_run` now calls `driver = build_driver(root, args.agent)` then `health = driver.probe()` and raises `CommandError` if `not health.healthy`, before `Supervisor(...)` is built. The probe is generic (no Codex-specific runtime policy). `test_run_rejects_unhealthy_adapter_before_agent_execution` checks the agent marker is never written for a wrong version or a failed login.

CLOSURE | resolved | The TUI Activity panel shows only lanes; Codex command, file-change, MCP, web, plan and message activity is decoded but never displayed | `ProjectObserver._observe_activity` now records `tool.*` and `activity.message` events into `ProjectView.activity`, and `activity_panel` appends them after the lane lines. The tests render both `codex` and `claude` providers with no lanes and see the tool, message and plan text, with markup kept literal.

LOW | src/ovcaq/tui/model.py:578 | `_observe_activity` keys items on `payload.get("message_id", "")` and `payload.get("tool_id", "")`. Events that omit the id all share one key, so later messages or tools silently overwrite earlier ones. | Fall back to a per-event unique key (for example a counter or timestamp) when the id is missing, or record a gap.

LOW | src/ovcaq/tui/model.py:590 | `payload.get("name", previous.label ...)` only falls back when the key is absent. A terminal event carrying `name: None` renders the label "None". | Treat a falsy or None name as absent: `payload.get("name") or (previous.label if previous else "tool")`.

LOW | src/ovcaq/tui/panels.py:91 | "no lanes observed" is still emitted when activity items follow it, which reads as contradictory (the notes say this is kept for compatibility). | Add the marker only when both lanes and activity are empty, if compatibility allows.

LOW | src/ovcaq/supervisor_cli.py:148 | `_report_runtime_error` now either returns the error or raises, depending on its type. The bare `raise` in `_run` is unreachable for the `CommandError` and unknown-exception paths, and the contract of the "report" function is muddled. | Split report from mapping, for example `_report_runtime_error` only writes the report and a separate `_as_command_error(error)` returns the mapped exception that `_run` raises.

LOW | src/ovcaq/tui/model.py:536 | The `persistent = [*self._gaps, *(...)]` to `list(...)`/`extend(...)` rewrite is unrelated to either finding. | Drop it from this diff, or surface it as its own change.

LOW | CHANGELOG.md:53 | The new entries are separated from the existing `### Fixed` bullets by a blank line, unlike the single-bullet-per-line style around them. | Remove the blank line so all `Fixed` bullets stay in one list.
