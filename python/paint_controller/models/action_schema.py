"""Pure action-schema types for co-located gated-action integrity metadata.

No PySide6 / ROS imports. ``*Actions`` modules declare ``ACTION_SCHEMAS`` using
these types; ``capability_catalog._ACTION_CAPABILITIES`` remains the explicit
runtime source of truth. Integrity tests assert schema ↔ catalog parity for
``legalStateClass`` and ``authority``.
"""

from __future__ import annotations

from dataclasses import dataclass

from paint_controller.models.action_keys import ActionKey


@dataclass(frozen=True)
class ActionSchema:
    """Authoring metadata for one gated discrete action."""

    key: ActionKey
    title: str
    legal_state_class: str
    authority: str


def schema_map(*schemas: ActionSchema) -> dict[ActionKey, ActionSchema]:
    """Build an ``ACTION_SCHEMAS`` dict; keys must be unique."""
    result: dict[ActionKey, ActionSchema] = {}
    for schema in schemas:
        if schema.key in result:
            raise ValueError(f"Duplicate ActionSchema for {schema.key!r}")
        result[schema.key] = schema
    return result
