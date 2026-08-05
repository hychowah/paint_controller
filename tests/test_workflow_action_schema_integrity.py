"""Integrity tests for the workflow ActionType registry."""

from __future__ import annotations

from paint_controller.services.workflow.action_schema import (
    ACTION_TYPES,
    CompletionKind,
    EstimateMode,
    _ACTION_TYPE_MAP,
    build_action_description,
    get_action_type,
    param_fields_for_type,
    palette_action_types,
    registry_palette_entries,
    validate_action_params,
)
from paint_controller.services.workflow.actions import ActionRegistry
from paint_controller.services.workflow.document import palette_entries
from paint_controller.services.workflow.hardware import HardwareControllers


class _FakeHardware(HardwareControllers):
    pass


def _registry() -> ActionRegistry:
    return ActionRegistry(_FakeHardware())


def test_every_action_type_has_registered_handler() -> None:
    registry = _registry()
    for action_type in ACTION_TYPES:
        assert registry.has_handler(action_type.name), f"No handler registered for {action_type.name!r}"


def test_every_registered_handler_has_action_type() -> None:
    registry = _registry()
    for name in registry._handlers:
        assert get_action_type(name) is not None, f"Registered handler {name!r} missing from ACTION_TYPES"


def test_action_type_map_is_complete() -> None:
    assert len(_ACTION_TYPE_MAP) == len(ACTION_TYPES)
    for action_type in ACTION_TYPES:
        assert _ACTION_TYPE_MAP[action_type.name] is action_type


def test_every_type_has_estimate_and_completion_policies() -> None:
    for action_type in ACTION_TYPES:
        est = action_type.metadata.estimate
        comp = action_type.metadata.completion
        assert est is not None and est.mode
        assert est.mode in {
            EstimateMode.FIXED_MS,
            EstimateMode.DURATION_MS_PARAM,
            EstimateMode.ABS_PARAM_OVER_SPEED,
            EstimateMode.SIGNED_PARAM_OVER_SPEED,
        }
        assert comp is not None and comp.kind
        assert comp.kind in {
            CompletionKind.TIMED,
            CompletionKind.FEEDBACK,
            CompletionKind.HYBRID,
            CompletionKind.IMMEDIATE,
        }
        if comp.kind in (CompletionKind.FEEDBACK, CompletionKind.HYBRID):
            assert comp.feedback is not None
            assert comp.feedback.reader_key
            assert comp.feedback.target_param


def test_palette_entries_subset_of_registered_types() -> None:
    registered = {a.name for a in ACTION_TYPES}
    for entry in registry_palette_entries():
        if entry["type"] == "parallel":
            continue  # structural step, not an ActionType
        assert entry["type"] in registered
    for action in palette_action_types():
        assert action.metadata.palette is True
        assert action.name in registered


def test_document_palette_derives_from_registry() -> None:
    from_reg = registry_palette_entries()
    from_doc = palette_entries()
    assert from_doc == from_reg
    types = {e["type"] for e in from_doc}
    assert "winch_absolute" in types
    assert "time_wait" in types
    assert "parallel" in types
    assert "teensy_gimbal" not in types  # legacy alias not on palette


def test_param_fields_for_type_matches_schema_keys() -> None:
    fields = param_fields_for_type("winch_absolute")
    keys = [f["key"] for f in fields]
    assert keys == ["length", "speed", "acceleration"]
    assert all("label" in f for f in fields)
    valve = param_fields_for_type("valve_turn")
    assert [f["key"] for f in valve] == ["turn_value"]
    assert param_fields_for_type("not_a_type") == []


def test_schema_description_matches_known_templates() -> None:
    assert build_action_description("winch_increment", {"length": 100, "speed": 50}) == "Move 100mm down at 50mm/s"
    assert build_action_description("winch_increment", {"length": -100, "speed": 50}) == "Move 100mm up at 50mm/s"
    assert build_action_description("winch_absolute", {"length": 500, "speed": 50}) == "Move to 500mm at 50mm/s"
    assert build_action_description("valve_turn", {"turn_value": 0.0}) == "Close valve"
    assert build_action_description("valve_turn", {"turn_value": 25.0}) == "Open valve to 25.0"
    assert build_action_description("spray_gimbal", {"angle": 45.0, "speed": 10.0}) == "Gimbal to 45.0° at 10.0°/s"
    assert build_action_description("arm_extend", {"distance": 200}) == "Extend arm to 200mm"
    assert build_action_description("ef_force", {"fx": 1.0, "fy": 2.0}) == "Set force Fx=1.0, Fy=2.0"


def test_validate_action_params_accepts_valid_params() -> None:
    validate_action_params("winch_increment", {"length": 100, "speed": 50, "acceleration": 15}, action_name="test")
    validate_action_params("valve_turn", {"turn_value": 25.0}, action_name="test")
    validate_action_params("spray_gimbal", {"angle": 45.0}, action_name="test")


def test_validate_action_params_rejects_missing_required() -> None:
    try:
        validate_action_params("winch_increment", {"speed": 50}, action_name="test")
    except ValueError as exc:
        assert "missing required param" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_validate_action_params_rejects_unknown_type() -> None:
    try:
        validate_action_params("not_a_real_type", {}, action_name="test")
    except ValueError as exc:
        assert "unknown action type" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_validate_action_params_rejects_unknown_param() -> None:
    try:
        validate_action_params("winch_increment", {"length": 100, "bogus": 1}, action_name="test")
    except ValueError as exc:
        assert "unknown param" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_validate_action_params_rejects_out_of_range() -> None:
    try:
        validate_action_params("winch_increment", {"length": 100, "acceleration": 100}, action_name="test")
    except ValueError as exc:
        assert "above max" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_winch_metadata_matches_scheduler_expectations() -> None:
    for name in ("winch_increment", "winch_absolute", "winch_move_absolute"):
        action = get_action_type(name)
        assert action is not None
        assert action.metadata.is_winch_action is True
        assert action.metadata.supports_position_trigger is True

    for name in ("valve_turn", "spray_gimbal", "arm_extend", "ef_force"):
        action = get_action_type(name)
        assert action is not None
        assert action.metadata.is_winch_action is False
