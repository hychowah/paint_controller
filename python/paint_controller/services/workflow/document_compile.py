"""Compile schema_version 2 documents into flat executor action lists."""

from __future__ import annotations

from typing import Any

from .document import (
    CONTINUE_WAIT_COMPLETE,
    KIND_ACTION,
    KIND_PARALLEL,
    KIND_WAIT,
    ActionMember,
    WorkflowDocument,
    WorkflowStep,
)
from .estimate import estimate_duration_ms


def compile_document_to_actions(document: WorkflowDocument) -> list[dict[str, Any]]:
    """Expand a v2 document into legacy-compatible scheduled actions.

    The existing ActionScheduler / WorkFlowExecutor consume this flat list.
    """
    document.validate()
    actions: list[dict[str, Any]] = []

    for step in document.steps:
        if step.kind == KIND_WAIT:
            actions.append(_compile_wait_step(step))
        elif step.kind == KIND_ACTION:
            actions.append(_compile_action_step(step))
        elif step.kind == KIND_PARALLEL:
            actions.extend(_compile_parallel_step(step))
        else:
            raise ValueError(f"unknown step kind {step.kind!r}")

    return actions


def _compile_wait_step(step: WorkflowStep) -> dict[str, Any]:
    duration_ms = int(step.duration_ms or 0)
    return {
        "id": step.id,
        "name": step.id,
        "type": "time_wait",
        "params": {"duration_ms": duration_ms},
        "estimated_duration": duration_ms,
        "wait_for_completion": True,
    }


def _compile_action_step(step: WorkflowStep) -> dict[str, Any]:
    assert step.type is not None
    action: dict[str, Any] = {
        "id": step.id,
        "name": step.id,
        "type": step.type,
        "params": dict(step.params),
        "wait_for_completion": step.continue_policy == CONTINUE_WAIT_COMPLETE,
    }
    duration_ms = _estimate_duration_ms(step.type, step.params)
    if duration_ms is not None:
        action["estimated_duration"] = duration_ms
    trigger = _timing_to_trigger(step.timing)
    if trigger is not None:
        action["trigger"] = trigger
    # Preserve raw timing for round-trip when compile is inverted via migrate
    if step.timing is not None:
        action["_timing"] = dict(step.timing)
    return action


def _compile_parallel_step(step: WorkflowStep) -> list[dict[str, Any]]:
    if not step.members:
        raise ValueError(f"parallel step {step.id} has no members")

    members = list(step.members)
    primary = members[0]
    primary_duration = _estimate_duration_ms(primary.type, primary.params) or 500
    max_duration = primary_duration
    for member in members[1:]:
        d = _estimate_duration_ms(member.type, member.params) or 0
        if d > max_duration:
            max_duration = d

    compiled: list[dict[str, Any]] = []
    primary_action = _member_to_action(
        primary,
        wait_for_completion=step.continue_policy == CONTINUE_WAIT_COMPLETE,
        estimated_duration=max_duration,
        trigger=None,
    )
    compiled.append(primary_action)

    for member in members[1:]:
        trigger = _timing_to_trigger(member.timing)
        if trigger is None:
            trigger = {
                "reference_action": primary.id,
                "timing_mode": "after_start",
                "offset_ms": 0,
            }
        elif "reference_action" not in trigger and "reference" not in trigger:
            trigger = dict(trigger)
            trigger["reference_action"] = primary.id
        # Normalize reference key
        if "reference" in trigger and "reference_action" not in trigger:
            trigger = dict(trigger)
            trigger["reference_action"] = trigger.pop("reference")

        compiled.append(
            _member_to_action(
                member,
                wait_for_completion=False,
                estimated_duration=_estimate_duration_ms(member.type, member.params),
                trigger=trigger,
            )
        )

    return compiled


def _member_to_action(
    member: ActionMember,
    *,
    wait_for_completion: bool,
    estimated_duration: int | None,
    trigger: dict[str, Any] | None,
) -> dict[str, Any]:
    action: dict[str, Any] = {
        "id": member.id,
        "name": member.id,
        "type": member.type,
        "params": dict(member.params),
        "wait_for_completion": wait_for_completion,
    }
    if estimated_duration is not None:
        action["estimated_duration"] = int(estimated_duration)
    if trigger is not None:
        action["trigger"] = trigger
    if member.timing is not None:
        action["_timing"] = dict(member.timing)
    return action


def _timing_to_trigger(timing: dict[str, Any] | None) -> dict[str, Any] | None:
    if not timing:
        return None
    mode = timing.get("mode") or timing.get("timing_mode")
    if not mode:
        return None
    trigger: dict[str, Any] = {
        "timing_mode": mode,
        "offset_ms": int(timing.get("offset_ms", 0) or 0),
    }
    ref = timing.get("reference") or timing.get("reference_action")
    if ref:
        trigger["reference_action"] = ref
    if "position_mm" in timing:
        trigger["position_mm"] = timing["position_mm"]
    if "wait_for_reference_complete" in timing:
        trigger["wait_for_reference_complete"] = timing["wait_for_reference_complete"]
    return trigger


def _estimate_duration_ms(action_type: str, params: dict[str, Any]) -> int | None:
    """Stamp compile output using the shared estimate SOT."""
    if not action_type:
        return None
    return int(round(estimate_duration_ms(action_type, params)))


def load_workflow_mapping(raw: Any, *, default_name: str | None = None) -> dict[str, Any]:
    """Normalize any on-disk YAML into a runtime mapping with steps + compiled actions."""
    from .document_migrate import migrate_raw_to_document

    document = migrate_raw_to_document(raw, default_name=default_name)
    actions = compile_document_to_actions(document)
    mapping = document.to_dict()
    mapping["actions"] = actions
    return mapping
