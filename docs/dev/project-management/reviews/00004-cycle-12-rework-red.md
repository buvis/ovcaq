# Cycle 12 repair: chronological installed regression

Product baseline: `39ecaf4f95c79df6a88c30e4626386a352d1505b`.
Tests committed before implementation at `0fdf3d644f0695c02c10544a06c2f8455e7551e3`.

Command: `mise exec -- uv run pytest tests/packaging/test_rework_12.py -q --basetemp /private/tmp/ovcaq-r12-red`

Exit 1; runner summary: `4 failed in 0.81s`.

- `test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit[new]`: real child exits 73 before parent fsync; fresh installed retry returns 0 but lacks project-parent confirmation.
- `test_installed_retry_and_replay_confirm_ancestry_after_abrupt_exit[new/nested]`: real child exits 73 before parent fsync; fresh installed retry returns 0 but lacks required ancestry confirmation.
- `test_installed_concurrent_creation_confirms_and_preserves_peer_directory[False]`: racer returns 2 with `FileExistsError` instead of successful parent confirmation.
- `test_installed_concurrent_creation_confirms_and_preserves_peer_directory[True]`: racer returns 2 with `FileExistsError`; `failed_parent` remains false, so the required fsync failure path was never reached.

Test-author isolation, installed-module origins, authoritative state preservation through the injected crashes, and process cleanup are asserted by the committed tests. Mechanical test-shape review emitted no findings. This records syscall durability evidence, not physical power-loss testing.
