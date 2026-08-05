"""Pure tests for workflow document model, migrate, and compile."""

from __future__ import annotations

from pathlib import Path

import yaml

from paint_controller.services.workflow.document import (
    CONTINUE_IMMEDIATELY,
    CONTINUE_WAIT_COMPLETE,
    KIND_ACTION,
    KIND_PARALLEL,
    KIND_WAIT,
    SCHEMA_VERSION,
    WorkflowDocument,
    WorkflowStep,
    default_params_for_type,
    palette_entries,
)
from paint_controller.services.workflow.document_compile import (
    compile_document_to_actions,
    load_workflow_mapping,
)
from paint_controller.services.workflow.document_migrate import migrate_raw_to_document
from paint_controller.services.workflow.scheduler import ActionScheduler


SAMPLES_DIR = (
    Path(__file__).resolve().parents[1]
    / "python"
    / "paint_controller"
    / "resource"
    / "workflows"
)


def test_empty_document_validates_and_compiles_to_empty_actions() -> None:
    doc = WorkflowDocument.empty("untitled")
    doc.validate()
    assert compile_document_to_actions(doc) == []


def test_add_action_wait_parallel_compile_schedule() -> None:
    doc = WorkflowDocument(
        name="demo",
        loop=True,
        steps=[
            WorkflowStep(
                id="w1",
                kind=KIND_ACTION,
                type="winch_absolute",
                params={"length": 1000, "speed": 100, "acceleration": 10},
                continue_policy=CONTINUE_WAIT_COMPLETE,
            ),
            WorkflowStep(id="wait1", kind=KIND_WAIT, duration_ms=1000),
            WorkflowStep(
                id="p1",
                kind=KIND_PARALLEL,
                continue_policy=CONTINUE_WAIT_COMPLETE,
                members=[
                    __import__(
                        "paint_controller.services.workflow.document", fromlist=["ActionMember"]
                    ).ActionMember(
                        id="valve",
                        type="valve_turn",
                        params={"turn_value": 3.0},
                    ),
                    __import__(
                        "paint_controller.services.workflow.document", fromlist=["ActionMember"]
                    ).ActionMember(
                        id="gimbal",
                        type="spray_gimbal",
                        params={"angle": 12.0, "speed": 10.0},
                    ),
                ],
            ),
            WorkflowStep(
                id="w2",
                kind=KIND_ACTION,
                type="winch_absolute",
                params={"length": 2000, "speed": 50, "acceleration": 10},
                continue_policy=CONTINUE_IMMEDIATELY,
            ),
        ],
    )
    doc.validate()
    actions = compile_document_to_actions(doc)
    types = [a["type"] for a in actions]
    assert types == ["winch_absolute", "time_wait", "valve_turn", "spray_gimbal", "winch_absolute"]
    assert actions[1]["params"]["duration_ms"] == 1000
    assert actions[2]["wait_for_completion"] is True
    assert actions[3]["trigger"]["reference_action"] == "valve"
    assert actions[3]["trigger"]["timing_mode"] == "after_start"
    assert actions[4]["wait_for_completion"] is False

    scheduled = ActionScheduler().build_schedule(actions)
    assert len(scheduled) == 5
    # parallel members share start time
    valve_t = next(s.scheduled_time for s in scheduled if s.action_id == "valve")
    gimbal_t = next(s.scheduled_time for s in scheduled if s.action_id == "gimbal")
    assert valve_t == gimbal_t


def test_document_round_trip_dict_preserves_advanced_timing() -> None:
    raw = {
        "schema_version": SCHEMA_VERSION,
        "name": "timed",
        "description": "keep timing",
        "loop": False,
        "steps": [
            {
                "id": "open",
                "kind": "action",
                "type": "valve_turn",
                "params": {"turn_value": 1.0},
                "continue": "wait_complete",
            },
            {
                "id": "close",
                "kind": "action",
                "type": "valve_turn",
                "params": {"turn_value": 0.0},
                "continue": "wait_complete",
                "timing": {
                    "mode": "before_complete",
                    "offset_ms": 500,
                    "reference": "open",
                },
            },
        ],
    }
    doc = WorkflowDocument.from_dict(raw)
    dumped = doc.to_dict()
    assert dumped["steps"][1]["timing"]["mode"] == "before_complete"
    assert dumped["steps"][1]["timing"]["offset_ms"] == 500
    reloaded = WorkflowDocument.from_dict(dumped)
    assert reloaded.steps[1].timing == doc.steps[1].timing

    actions = compile_document_to_actions(doc)
    assert actions[1]["trigger"]["timing_mode"] == "before_complete"
    assert actions[1]["trigger"]["reference_action"] == "open"
    assert actions[1]["trigger"]["offset_ms"] == 500


def test_migrate_and_compile_all_sample_workflows() -> None:
    assert SAMPLES_DIR.is_dir()
    samples = sorted(SAMPLES_DIR.glob("*.yaml")) + sorted(SAMPLES_DIR.glob("*.yml"))
    assert samples, "expected sample workflows on disk"
    for path in samples:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        doc = migrate_raw_to_document(raw, default_name=path.stem)
        assert doc.schema_version == SCHEMA_VERSION
        assert doc.name
        actions = compile_document_to_actions(doc)
        assert isinstance(actions, list)
        # Must be schedulable
        ActionScheduler().build_schedule(actions)
        mapping = load_workflow_mapping(raw, default_name=path.stem)
        assert mapping["schema_version"] == SCHEMA_VERSION
        assert mapping["actions"] == actions


def test_migrate_legacy_sequential_wait_for_completion() -> None:
    raw = {
        "name": "ascend",
        "description": "ascend",
        "actions": [
            {
                "id": "Ascend_to_top",
                "name": "winch_move",
                "type": "winch_absolute",
                "params": {"length": 7639, "speed": 200, "acceleration": 10},
                "wait_for_completion": True,
            }
        ],
    }
    doc = migrate_raw_to_document(raw)
    assert len(doc.steps) == 1
    assert doc.steps[0].kind == KIND_ACTION
    assert doc.steps[0].type == "winch_absolute"
    assert doc.steps[0].continue_policy == CONTINUE_WAIT_COMPLETE
    actions = compile_document_to_actions(doc)
    assert actions[0]["params"]["length"] == 7639


def test_validate_rejects_unknown_type_and_bad_wait() -> None:
    try:
        WorkflowDocument.from_dict(
            {
                "schema_version": 2,
                "name": "bad",
                "steps": [{"id": "x", "kind": "action", "type": "not_a_type", "params": {}}],
            }
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown action type" in str(exc)

    try:
        WorkflowDocument.from_dict(
            {
                "schema_version": 2,
                "name": "bad_wait",
                "steps": [{"id": "w", "kind": "wait", "duration_ms": 0}],
            }
        )
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "duration_ms" in str(exc)


def test_palette_entries_include_core_kinds() -> None:
    entries = palette_entries()
    kinds = {e["kind"] for e in entries}
    types = {e["type"] for e in entries}
    assert KIND_ACTION in kinds
    assert KIND_WAIT in kinds
    assert KIND_PARALLEL in kinds
    assert "winch_absolute" in types
    assert "valve_turn" in types
    assert "spray_gimbal" in types
    assert "time_wait" in types
    assert default_params_for_type("winch_absolute")["speed"] == 100
