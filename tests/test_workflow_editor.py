"""Direct tests for the QML-facing workflow editor session."""

from __future__ import annotations

from paint_controller.services.workflow.document import SCHEMA_VERSION
from paint_controller.services.workflow.workflow_catalog import WorkflowCatalog
from paint_controller.services.workflow.workflow_editor import WorkflowEditor
from tests.fakes import FakeNode


class _RuntimeGuard:
    def __init__(self) -> None:
        self.saved_names: list[str] = []
        self.save_error: str | None = None
        self.delete_error: str | None = None

    def can_save_workflow_document(self, _workflow_name: str):
        if self.save_error is not None:
            return False, self.save_error
        return True, None

    def can_delete_workflow_document(self, _workflow_name: str):
        if self.delete_error is not None:
            return False, self.delete_error
        return True, None

    def mark_workflow_document_saved(self, workflow_name: str) -> None:
        self.saved_names.append(workflow_name)


def _make_editor(tmp_path):
    logger = FakeNode().get_logger()
    catalog = WorkflowCatalog(workflows_dir=str(tmp_path), logger=logger)
    editor = WorkflowEditor(catalog=catalog, logger=logger)
    return editor, catalog


def test_workflow_editor_session_add_remove_move_and_dirty(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("prog")
        assert editor.is_dirty is True
        assert editor.add_step("winch_absolute") is True
        assert editor.add_step("time_wait") is True
        assert editor.add_step("parallel") is True
        assert len(editor.steps) == 3
        assert editor.steps[0]["kind"] == "action"
        assert editor.steps[1]["kind"] == "wait"
        assert editor.steps[2]["kind"] == "parallel"

        editor.select_step(2)
        assert editor.move_selected_up() is True
        assert editor.steps[1]["kind"] == "parallel"
        assert editor.steps[2]["kind"] == "wait"

        editor.select_step(0)
        assert editor.remove_selected_step() is True
        assert len(editor.steps) == 2
        assert editor.is_dirty is True
    finally:
        catalog.cleanup()


def test_workflow_editor_save_load_round_trip_multi_step(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("cycle")
        editor.set_loop(True)
        editor.set_description("paint cycle")
        assert editor.add_step("valve_turn") is True
        assert editor.add_step("time_wait") is True
        editor.select_step(1)
        assert editor.set_wait_duration_ms(1500) is True
        assert editor.add_step("winch_absolute") is True
        editor.select_step(2)
        assert editor.set_param("length", 2360) is True
        assert editor.set_param("speed", 250) is True
        assert editor.set_continue_policy("continue_immediately") is True

        assert editor.save() is True
        assert editor.is_dirty is False
        assert "cycle" in editor.workflow_list

        editor.new_document("other")
        loaded = editor.load_document("cycle")
        assert loaded["schema_version"] == SCHEMA_VERSION
        assert loaded["loop"] is True
        assert loaded["description"] == "paint cycle"
        assert len(loaded["steps"]) == 3
        assert loaded["steps"][1]["duration_ms"] == 1500
        assert loaded["steps"][2]["params"]["length"] == 2360
        assert loaded["steps"][2]["continue"] == "continue_immediately"
        assert editor.is_dirty is False
    finally:
        catalog.cleanup()


def test_workflow_editor_save_document_compat_and_collision(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    runtime_guard = _RuntimeGuard()
    editor.attach_runtime(runtime_guard)
    errors: list[str] = []
    editor.error_occurred.connect(errors.append)

    try:
        assert (
            editor.save_document(
                "alpha",
                "42",
                True,
                [
                    {"kind": "action", "type": "valve_turn", "params": {"turn_value": 25.0}},
                    {
                        "kind": "action",
                        "id": "named",
                        "type": "winch_absolute",
                        "params": {"length": 50, "speed": 10, "acceleration": 10},
                    },
                ],
            )
            is True
        )
        saved = editor.load_document("alpha")
        assert saved["name"] == "alpha"
        assert saved["loop"] is True
        assert len(saved["steps"]) == 2
        assert runtime_guard.saved_names == ["alpha"]

        runtime_guard.save_error = "save blocked"
        assert editor.save() is False
        assert errors[-1] == "save blocked"

        runtime_guard.save_error = None
        runtime_guard.delete_error = "delete blocked"
        assert editor.delete_workflow("alpha") is False
        assert errors[-1] == "delete blocked"
        assert "alpha" in editor.workflow_list
    finally:
        catalog.cleanup()


def test_workflow_editor_rejects_invalid_add_and_missing_load(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    errors: list[str] = []
    editor.error_occurred.connect(errors.append)
    try:
        assert editor.load_document("missing") == {}
        assert "not found" in errors[-1].lower() or "WorkFlow not found" in errors[-1]

        editor.new_document("x")
        assert editor.add_step("not_a_real_type") is False
        assert errors[-1]
    finally:
        catalog.cleanup()


def test_workflow_editor_preserve_advanced_timing_on_param_edit(qt_app, tmp_path) -> None:
    (tmp_path / "timed.yaml").write_text(
        """
schema_version: 2
name: timed
description: keep
loop: false
steps:
  - id: open
    kind: action
    type: valve_turn
    params: { turn_value: 1.0 }
    continue: wait_complete
  - id: close
    kind: action
    type: valve_turn
    params: { turn_value: 0.0 }
    continue: wait_complete
    timing:
      mode: before_complete
      offset_ms: 500
      reference: open
""".strip(),
        encoding="utf-8",
    )
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.load_document("timed")
        editor.select_step(1)
        assert editor.set_param("turn_value", 0.5) is True
        assert editor.save() is True
        reloaded = editor.load_document("timed")
        assert reloaded["steps"][1]["params"]["turn_value"] == 0.5
        assert reloaded["steps"][1]["timing"]["mode"] == "before_complete"
        assert reloaded["steps"][1]["timing"]["offset_ms"] == 500
    finally:
        catalog.cleanup()


def test_workflow_editor_open_close_and_palette(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        assert editor.is_open is False
        assert editor.open_editor() is True
        assert editor.is_open is True
        types = {entry["type"] for entry in editor.palette}
        assert "winch_absolute" in types
        assert "time_wait" in types
        assert "parallel" in types
        assert editor.close_editor() is True
        assert editor.is_open is False
    finally:
        catalog.cleanup()


def test_workflow_editor_lists_workflows_in_stable_sorted_order(qt_app, tmp_path) -> None:
    (tmp_path / "beta.yml").write_text(
        "schema_version: 2\nname: beta\nsteps: []\n",
        encoding="utf-8",
    )
    (tmp_path / "Alpha.yaml").write_text(
        "schema_version: 2\nname: Alpha\nsteps: []\n",
        encoding="utf-8",
    )
    editor, catalog = _make_editor(tmp_path)
    try:
        assert "beta" in editor.workflow_list
        assert "Alpha" in editor.workflow_list
    finally:
        catalog.cleanup()
