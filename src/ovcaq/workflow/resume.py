"""Authoritative pure resume-target mapping for v1 state."""

from __future__ import annotations

from ovcaq.state.schema import State


def resume_target(state: State) -> str:
    """Describe the next action from committed v1 state only."""
    operation = state["recovery"]["operation"]
    if operation is not None:
        return f"reconcile {operation['kind']} {operation['id']} for {operation['prd']}"

    phase = state["work"]["phase"]
    if phase == "paused":
        pause_reason = state["control"]["pause_reason"]
        if pause_reason is not None and pause_reason["site"] == "review_cap":
            return (
                "cap-pause resume handler: present unresolved findings, "
                "branch resume/abandon"
            )
        return "paused: await user"

    if phase == "review":
        if "review" in state["work"]["completed_phases"]:
            return "skip review -> done"
        cycle = max(1, state["review"]["cycle"])
        return f"run review loop at cycle {cycle}"

    if phase == "build":
        tasks = state["tasks"]
        if tasks:
            pending = next(
                (task for task in tasks if task["status"] != "completed"),
                None,
            )
            if pending is None:
                return "all tasks done -> review gate"
            return f"continue build at first non-completed task {pending['id']}"
        if state["batch"]["catchup"]["completed_at"] is not None:
            return "skip catchup -> planning"
        return "build: catchup then planning"

    if phase == "done":
        return "done"
    return f"unknown phase: {phase}"
