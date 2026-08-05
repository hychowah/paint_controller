"""Migrate legacy workflow YAML (flat actions + triggers) to schema_version 2."""

from __future__ import annotations

from typing import Any

from .document import (
    CONTINUE_IMMEDIATELY,
    CONTINUE_WAIT_COMPLETE,
    KIND_ACTION,
    KIND_PARALLEL,
    KIND_WAIT,
    SCHEMA_VERSION,
    ActionMember,
    WorkflowDocument,
    WorkflowStep,
)


def is_v2_document(raw: Any) -> bool:
    return isinstance(raw, dict) and int(raw.get("schema_version", 0) or 0) == SCHEMA_VERSION


def migrate_raw_to_document(raw: Any, *, default_name: str | None = None) -> WorkflowDocument:
    """Convert raw YAML mapping (v1 or v2) into a validated WorkflowDocument."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("workflow document must be a mapping")

    if is_v2_document(raw):
        return WorkflowDocument.from_dict(raw, default_name=default_name)

    return _migrate_legacy_actions(raw, default_name=default_name)


def _migrate_legacy_actions(raw: dict[str, Any], *, default_name: str | None) -> WorkflowDocument:
    name = str(raw.get("name") or default_name or "untitled").strip() or "untitled"
    description = str(raw.get("description", ""))
    loop = bool(raw.get("loop", False))

    actions = raw.get("actions", [])
    if actions is None:
        actions = []
    if not isinstance(actions, list):
        raise ValueError("legacy workflow actions must be a list")

    steps: list[WorkflowStep] = []
    # Group co-started actions (after_start offset 0 relative to a previous id)
    # into parallel steps when possible; otherwise sequential with preserved timing.

    index = 0
    consumed: set[int] = set()

    while index < len(actions):
        if index in consumed:
            index += 1
            continue

        action = actions[index]
        if not isinstance(action, dict):
            try:
                action = dict(action)
            except Exception as exc:
                raise ValueError(f"legacy action {index + 1} must be an object") from exc

        action_id = str(action.get("id") or f"action_{index}")
        action_type = action.get("type")
        if not isinstance(action_type, str) or not action_type.strip():
            raise ValueError(f"legacy action {index + 1} missing type")

        # Find later actions that start with this one (after_start, offset 0)
        parallel_members: list[tuple[int, dict[str, Any]]] = [(index, action)]
        for j in range(index + 1, len(actions)):
            if j in consumed:
                continue
            other = actions[j]
            if not isinstance(other, dict):
                continue
            trigger = other.get("trigger") or {}
            if not isinstance(trigger, dict):
                continue
            if (
                trigger.get("reference_action") == action_id
                and trigger.get("timing_mode", "after_start") == "after_start"
                and int(trigger.get("offset_ms", 0) or 0) == 0
            ):
                parallel_members.append((j, other))
                consumed.add(j)

        if len(parallel_members) > 1:
            members: list[ActionMember] = []
            for mi, (src_i, src) in enumerate(parallel_members):
                mid = str(src.get("id") or f"{action_id}_m{mi}")
                mtype = str(src.get("type"))
                mparams = dict(src.get("params") or {})
                timing = _timing_from_legacy_trigger(src.get("trigger"))
                # Primary has no trigger timing in parallel group
                if mi == 0:
                    timing = None
                members.append(ActionMember(id=mid, type=mtype, params=mparams, timing=timing))
            wait_for = bool(action.get("wait_for_completion", True))
            steps.append(
                WorkflowStep(
                    id=action_id,
                    kind=KIND_PARALLEL,
                    continue_policy=CONTINUE_WAIT_COMPLETE if wait_for else CONTINUE_IMMEDIATELY,
                    members=members,
                )
            )
        else:
            steps.append(_legacy_action_to_step(action, index=index))

        consumed.add(index)
        index += 1

    doc = WorkflowDocument(
        name=name,
        description=description,
        loop=loop,
        steps=steps,
        schema_version=SCHEMA_VERSION,
    )
    doc.validate()
    return doc


def _legacy_action_to_step(action: dict[str, Any], *, index: int) -> WorkflowStep:
    action_id = str(action.get("id") or f"action_{index}")
    action_type = str(action.get("type")).strip()
    params = dict(action.get("params") or {})
    wait_for = bool(action.get("wait_for_completion", True))
    continue_policy = CONTINUE_WAIT_COMPLETE if wait_for else CONTINUE_IMMEDIATELY
    timing = _timing_from_legacy_trigger(action.get("trigger"))

    # Estimated-only waits without device type are rare; treat estimated_duration-only
    # valve/noop as action. Pure waits were not first-class in legacy.

    if action_type == "time_wait":
        duration_ms = int(params.get("duration_ms") or action.get("estimated_duration") or 0)
        if duration_ms <= 0:
            duration_ms = 1000
        return WorkflowStep(id=action_id, kind=KIND_WAIT, duration_ms=duration_ms)

    return WorkflowStep(
        id=action_id,
        kind=KIND_ACTION,
        type=action_type,
        params=params,
        continue_policy=continue_policy,
        timing=timing,
    )


def _timing_from_legacy_trigger(trigger: Any) -> dict[str, Any] | None:
    if not trigger or not isinstance(trigger, dict):
        return None
    mode = trigger.get("timing_mode")
    if not mode:
        return None
    # after_start with 0 offset and handled as parallel — still store non-trivial timing
    offset_ms = int(trigger.get("offset_ms", 0) or 0)
    if mode == "after_start" and offset_ms == 0:
        return None
    timing: dict[str, Any] = {
        "mode": mode,
        "offset_ms": offset_ms,
    }
    ref = trigger.get("reference_action")
    if ref:
        timing["reference"] = ref
    if "position_mm" in trigger:
        timing["position_mm"] = trigger["position_mm"]
    if "wait_for_reference_complete" in trigger:
        timing["wait_for_reference_complete"] = trigger["wait_for_reference_complete"]
    return timing
