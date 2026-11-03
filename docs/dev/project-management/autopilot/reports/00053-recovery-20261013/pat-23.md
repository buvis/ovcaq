CLOSURE | resolved | `test_unrelated_item_type_does_not_transition_lane` and `test_unrelated_event_type_does_not_transition_lane` are line-for-line copies that differ in one `collab_record` keyword | The diff removes both tests and adds `test_unrelated_discriminator_does_not_transition_lane`, parametrized over `[{"item_type": "command_execution"}, {"event_type": "thread.started"}]` and passed as `**override`.

CLOSURE | resolved | Both tests run once per close status (interrupted, shutdown, not_found), so 6 cases run where 2 would do. Fix: drop the `child_status` parametrize and use "shutdown" | The `child_status` parametrize is gone, and both `collab_record("shutdown", ...)` calls use a fixed status. Two cases remain (ids `item-type` and `event-type`). The no-lane-transition assertion and the follow-up `LANE_FAILED == ["child"]` assertion are unchanged. The recorded run shows 32 passed.

NO FINDINGS
