"""Versioned workflow document model (schema_version 2).

Pure Python — no Qt. Single source of truth for editor session and compile.
Advanced ``timing`` maps on steps/members are reserved and preserved on edit.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from .action_schema import (
    get_action_type,
    param_fields_for_type,
    registry_palette_entries,
    validate_action_params,
)

SCHEMA_VERSION = 2

CONTINUE_WAIT_COMPLETE = "wait_complete"
CONTINUE_IMMEDIATELY = "continue_immediately"
CONTINUE_POLICIES = frozenset({CONTINUE_WAIT_COMPLETE, CONTINUE_IMMEDIATELY})

KIND_ACTION = "action"
KIND_WAIT = "wait"
KIND_PARALLEL = "parallel"
STEP_KINDS = frozenset({KIND_ACTION, KIND_WAIT, KIND_PARALLEL})


def _require_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _coerce_params(params: Any) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict):
        try:
            params = dict(params)
        except Exception as exc:
            raise ValueError("params must be an object") from exc
    return dict(params)


def _coerce_timing(timing: Any) -> dict[str, Any] | None:
    if timing is None:
        return None
    if not isinstance(timing, dict):
        try:
            timing = dict(timing)
        except Exception as exc:
            raise ValueError("timing must be an object") from exc
    return dict(timing)


@dataclass
class ActionMember:
    """One action inside a parallel group (or shared action payload shape)."""

    id: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] | None = None  # reserved advanced timing

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "params": deepcopy(self.params),
        }
        if self.timing is not None:
            data["timing"] = deepcopy(self.timing)
        return data

    @classmethod
    def from_dict(cls, raw: Any, *, index: int, prefix: str = "m") -> ActionMember:
        if not isinstance(raw, dict):
            try:
                raw = dict(raw)
            except Exception as exc:
                raise ValueError(f"member {index + 1} must be an object") from exc
        member_id = raw.get("id")
        if not isinstance(member_id, str) or not member_id.strip():
            member_id = f"{prefix}{index}"
        else:
            member_id = member_id.strip()
        action_type = _require_str(raw.get("type"), field_name=f"member {member_id} type")
        params = _coerce_params(raw.get("params"))
        timing = _coerce_timing(raw.get("timing"))
        return cls(id=member_id, type=action_type, params=params, timing=timing)


@dataclass
class WorkflowStep:
    """One ordered program step."""

    id: str
    kind: str
    # action
    type: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    continue_policy: str = CONTINUE_WAIT_COMPLETE
    # wait
    duration_ms: int | None = None
    # parallel
    members: list[ActionMember] = field(default_factory=list)
    # reserved advanced timing (action steps)
    timing: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id, "kind": self.kind}
        if self.kind == KIND_ACTION:
            data["type"] = self.type
            data["params"] = deepcopy(self.params)
            data["continue"] = self.continue_policy
            if self.timing is not None:
                data["timing"] = deepcopy(self.timing)
        elif self.kind == KIND_WAIT:
            data["duration_ms"] = int(self.duration_ms or 0)
        elif self.kind == KIND_PARALLEL:
            data["continue"] = self.continue_policy
            data["members"] = [m.to_dict() for m in self.members]
        return data

    @classmethod
    def from_dict(cls, raw: Any, *, index: int) -> WorkflowStep:
        if not isinstance(raw, dict):
            try:
                raw = dict(raw)
            except Exception as exc:
                raise ValueError(f"step {index + 1} must be an object") from exc

        step_id = raw.get("id")
        if not isinstance(step_id, str) or not step_id.strip():
            step_id = f"step_{index:02d}"
        else:
            step_id = step_id.strip()

        kind = raw.get("kind")
        if not isinstance(kind, str) or kind not in STEP_KINDS:
            raise ValueError(f"step {step_id}: kind must be one of {sorted(STEP_KINDS)}")

        continue_policy = raw.get("continue", CONTINUE_WAIT_COMPLETE)
        if continue_policy not in CONTINUE_POLICIES:
            raise ValueError(f"step {step_id}: invalid continue policy {continue_policy!r}")

        if kind == KIND_ACTION:
            action_type = _require_str(raw.get("type"), field_name=f"step {step_id} type")
            params = _coerce_params(raw.get("params"))
            timing = _coerce_timing(raw.get("timing"))
            return cls(
                id=step_id,
                kind=KIND_ACTION,
                type=action_type,
                params=params,
                continue_policy=str(continue_policy),
                timing=timing,
            )

        if kind == KIND_WAIT:
            duration = raw.get("duration_ms", 0)
            try:
                duration_ms = int(duration)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"step {step_id}: duration_ms must be an integer") from exc
            if duration_ms <= 0:
                raise ValueError(f"step {step_id}: duration_ms must be > 0")
            return cls(id=step_id, kind=KIND_WAIT, duration_ms=duration_ms)

        # parallel
        members_raw = raw.get("members", [])
        if not isinstance(members_raw, list) or len(members_raw) < 1:
            raise ValueError(f"step {step_id}: parallel requires at least one member")
        members = [
            ActionMember.from_dict(item, index=i, prefix=f"{step_id}_m") for i, item in enumerate(members_raw)
        ]
        return cls(
            id=step_id,
            kind=KIND_PARALLEL,
            continue_policy=str(continue_policy),
            members=members,
        )


@dataclass
class WorkflowDocument:
    """Operator-facing workflow program document."""

    name: str
    description: str = ""
    loop: bool = False
    steps: list[WorkflowStep] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "description": self.description,
            "loop": bool(self.loop),
            "steps": [step.to_dict() for step in self.steps],
        }

    def to_qml_map(self) -> dict[str, Any]:
        """QML-friendly document map (same shape as to_dict)."""
        return self.to_dict()

    def steps_as_qml_list(self) -> list[dict[str, Any]]:
        return [step.to_dict() for step in self.steps]

    def validate(self) -> None:
        """Raise ValueError if the document is illegal."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("workflow name must be a non-empty string")
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported schema_version {self.schema_version}")

        seen_ids: set[str] = set()
        for index, step in enumerate(self.steps):
            if step.id in seen_ids:
                raise ValueError(f"duplicate step id {step.id!r}")
            seen_ids.add(step.id)

            if step.kind == KIND_ACTION:
                assert step.type is not None
                validate_action_params(step.type, step.params, action_name=f"step {step.id}")
            elif step.kind == KIND_WAIT:
                if step.duration_ms is None or step.duration_ms <= 0:
                    raise ValueError(f"step {step.id}: duration_ms must be > 0")
            elif step.kind == KIND_PARALLEL:
                if not step.members:
                    raise ValueError(f"step {step.id}: parallel requires members")
                member_ids: set[str] = set()
                for member in step.members:
                    if member.id in member_ids or member.id in seen_ids:
                        raise ValueError(f"duplicate member/step id {member.id!r}")
                    member_ids.add(member.id)
                    validate_action_params(member.type, member.params, action_name=f"member {member.id}")
                seen_ids.update(member_ids)
            else:
                raise ValueError(f"step {index}: unknown kind {step.kind!r}")

    @classmethod
    def from_dict(cls, raw: Any, *, default_name: str | None = None) -> WorkflowDocument:
        if raw is None:
            raw = {}
        if not isinstance(raw, dict):
            raise ValueError("workflow document must be a mapping")

        name = raw.get("name") or default_name or ""
        name = _require_str(name, field_name="name") if str(name).strip() else (default_name or "")
        if not name:
            raise ValueError("workflow name is required")

        schema_version = raw.get("schema_version", SCHEMA_VERSION)
        try:
            schema_version = int(schema_version)
        except (TypeError, ValueError) as exc:
            raise ValueError("schema_version must be an integer") from exc

        steps_raw = raw.get("steps", [])
        if steps_raw is None:
            steps_raw = []
        if not isinstance(steps_raw, list):
            raise ValueError("steps must be a list")

        steps = [WorkflowStep.from_dict(item, index=i) for i, item in enumerate(steps_raw)]
        doc = cls(
            name=name,
            description=str(raw.get("description", "")),
            loop=bool(raw.get("loop", False)),
            steps=steps,
            schema_version=schema_version,
        )
        doc.validate()
        return doc

    @classmethod
    def empty(cls, name: str = "untitled") -> WorkflowDocument:
        return cls(name=name, description="", loop=False, steps=[])


def palette_entries() -> list[dict[str, Any]]:
    """QML list of addable step types — derived from the action registry."""
    return registry_palette_entries()


def default_params_for_type(action_type: str) -> dict[str, Any]:
    """Sensible defaults for a new palette action from schema defaults."""
    if action_type == "time_wait":
        return {"duration_ms": 1000}
    if action_type == "winch_absolute":
        return {"length": 1000, "speed": 100, "acceleration": 10}
    if action_type == "winch_increment":
        return {"length": 100, "speed": 50, "acceleration": 10}
    action = get_action_type(action_type)
    if action is None:
        return {}
    # Prefer schema defaults, then fill remaining required with zeros
    merged = action.param_spec.with_defaults({})
    for name, field in action.param_spec.fields.items():
        if name not in merged:
            if field.default is not None:
                merged[name] = field.default
            elif field.py_type is int:
                merged[name] = 0
            elif field.py_type is float:
                merged[name] = 0.0
            else:
                merged[name] = None
    return merged


def param_fields_for_editor(action_type: str) -> list[dict[str, Any]]:
    """Re-export registry field list for the editor session."""
    return param_fields_for_type(action_type)
