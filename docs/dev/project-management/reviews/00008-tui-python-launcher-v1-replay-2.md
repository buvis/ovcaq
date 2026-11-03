## Fail-first replay (computed, do not re-judge)

Touched tests from HEAD, run against the pre-change code at `5544b1fc9c27`
(HEAD's test files overlaid on a base worktree). A test that passes there
does not pin this change. A behavior-preserving refactor's tests pass by
design, so weigh the PRD's intent before raising one. `mech-check` is the finder.

replay: skipped (runner did not complete: Command '['uv', 'run', 'pytest', '-q', '-rA', '--rootdir', '/private/var/folders/m6/1mnc9pdn28d5vdxy4hxyr1m40000gn/T/replay-30o5156f/wt', '-p', 'no:cacheprovider', '--continue-on-collection-errors', 'tests/integration/test_control_commit_identity.py', 'tests/integration/test_guarded_run_mutation.py', 'tests/integration/test_launcher_outcomes.py', 'tests/integration/test_native_telemetry_identity.py', 'tests/integration/test_observer_terminal_cleanup.py', 'tests/integration/test_observer_terminal_viewers.py', 'tests/integration/test_supervisor_live_telemetry.py', 'tests/integration/test_terminal_lifecycle.py', 'tests/integration/test_viewer_fallback.py', 'tests/runtime/test_attach.py', 'tests/runtime/test_session_metrics.py', 'tests/runtime/test_supervisor_cli.py', 'tests/state/test_cli.py', 'tests/state/test_commands.py', 'tests/state/test_guarded_service.py', 'tests/tui/test_app.py', 'tests/tui/test_app_ended_selection.py', 'tests/tui/test_app_poll_responsiveness.py', 'tests/tui/test_model.py', 'tests/tui/test_model_elapsed_duration.py', 'tests/tui/test_model_live_evidence.py', 'tests/tui/test_theme_persistence.py']' timed out after 600.0 seconds)
