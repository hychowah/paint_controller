"""Direct tests for the QML-facing workflow editor session."""

from __future__ import annotations

from paint_controller.services.workflow.document import SCHEMA_VERSION
from paint_controller.services.workflow.document_compile import compile_document_to_actions
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
        fields = editor.param_fields("winch_absolute")
        assert [f["key"] for f in fields] == ["length", "speed", "acceleration"]
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


def test_workflow_editor_member_palette_is_action_only(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        kinds = {entry["kind"] for entry in editor.member_palette}
        types = {entry["type"] for entry in editor.member_palette}
        assert kinds == {"action"}
        assert "parallel" not in types
        assert "time_wait" not in types
        assert "valve_turn" in types
        assert "winch_absolute" in types
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_authoring_add_remove_type_param_reorder(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    errors: list[str] = []
    editor.error_occurred.connect(errors.append)
    try:
        editor.new_document("parallel_auth")
        assert editor.selected_member_index == -1
        assert editor.add_step("parallel") is True
        assert editor.selected_member_index == 0
        step = editor.steps[0]
        assert step["kind"] == "parallel"
        assert len(step["members"]) == 2
        assert step["members"][0]["type"] == "valve_turn"
        assert step["members"][1]["type"] == "spray_gimbal"

        # set_param must not touch parallel members
        before = [dict(m["params"]) for m in step["members"]]
        assert editor.set_param("turn_value", 99.0) is False
        after = editor.steps[0]["members"]
        assert [dict(m["params"]) for m in after] == before

        # Edit non-zero member params
        editor.select_member(1)
        assert editor.selected_member_index == 1
        assert editor.set_member_param(1, "angle", 45.0) is True
        assert editor.steps[0]["members"][1]["params"]["angle"] == 45.0

        # Add member selects new index; unique types
        assert editor.add_member("winch_absolute") is True
        assert editor.selected_member_index == 2
        assert editor.steps[0]["members"][2]["type"] == "winch_absolute"
        assert editor.set_member_param(2, "length", 500) is True

        # Illegal types
        assert editor.add_member("time_wait") is False
        assert editor.add_member("parallel") is False
        assert editor.add_member("not_real") is False
        assert editor.add_member("") is False
        assert len(editor.steps[0]["members"]) == 3

        # Type change keeps id, resets params
        editor.select_member(0)
        member_id = editor.steps[0]["members"][0]["id"]
        assert editor.set_member_type("arm_extend") is True
        m0 = editor.steps[0]["members"][0]
        assert m0["id"] == member_id
        assert m0["type"] == "arm_extend"
        assert "distance" in m0["params"]
        assert "turn_value" not in m0["params"]

        # Reject illegal set_member_type
        assert editor.set_member_type("time_wait") is False
        assert editor.set_member_type("parallel") is False
        assert editor.steps[0]["members"][0]["type"] == "arm_extend"

        # Reorder: move selected down then up
        editor.select_member(0)
        assert editor.move_selected_member_down() is True
        assert editor.selected_member_index == 1
        assert editor.steps[0]["members"][1]["type"] == "arm_extend"
        assert editor.move_selected_member_up() is True
        assert editor.selected_member_index == 0
        assert editor.steps[0]["members"][0]["type"] == "arm_extend"

        # Remove until one; refuse last
        editor.select_member(2)
        assert editor.remove_selected_member() is True
        assert len(editor.steps[0]["members"]) == 2
        editor.select_member(1)
        assert editor.remove_selected_member() is True
        assert len(editor.steps[0]["members"]) == 1
        assert editor.remove_selected_member() is False
        assert len(editor.steps[0]["members"]) == 1
        assert any("at least one member" in e for e in errors)
        assert editor.is_dirty is True
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_remove_primary_promotes_next(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("promo")
        assert editor.add_step("parallel") is True
        m0_id = editor.steps[0]["members"][0]["id"]
        m1_id = editor.steps[0]["members"][1]["id"]
        editor.select_member(0)
        assert editor.remove_selected_member() is True
        assert editor.steps[0]["members"][0]["id"] == m1_id
        assert m0_id not in {m["id"] for m in editor.steps[0]["members"]}
        assert editor.selected_member_index == 0
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_set_member_type_preserves_timing(qt_app, tmp_path) -> None:
    (tmp_path / "with_timing.yaml").write_text(
        """
schema_version: 2
name: with_timing
loop: false
steps:
  - id: pg
    kind: parallel
    continue: wait_complete
    members:
      - id: a
        type: valve_turn
        params: { turn_value: 1.0 }
      - id: b
        type: spray_gimbal
        params: { angle: 10.0, speed: 5.0 }
        timing:
          mode: after_start
          offset_ms: 100
""".strip(),
        encoding="utf-8",
    )
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.load_document("with_timing")
        assert editor.selected_member_index == -1
        editor.select_step(0)
        assert editor.selected_member_index == 0
        editor.select_member(1)
        assert editor.set_member_type("ef_force") is True
        m1 = editor.steps[0]["members"][1]
        assert m1["id"] == "b"
        assert m1["type"] == "ef_force"
        assert m1["timing"]["offset_ms"] == 100
        assert "fx" in m1["params"]
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_selection_lifecycle_on_load_new_remove(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("life")
        assert editor.selected_member_index == -1
        assert editor.add_step("parallel") is True
        assert editor.selected_member_index == 0
        assert editor.add_step("valve_turn") is True
        assert editor.selected_member_index == -1
        editor.select_step(0)
        assert editor.selected_member_index == 0
        editor.select_member(1)
        assert editor.selected_member_index == 1

        editor.new_document("fresh")
        assert editor.selected_member_index == -1

        assert editor.add_step("parallel") is True
        assert editor.add_step("winch_absolute") is True
        editor.select_step(0)
        assert editor.selected_member_index == 0
        editor.select_step(1)
        assert editor.selected_member_index == -1
        editor.select_step(0)
        assert editor.remove_selected_step() is True
        # Remaining step is action
        assert editor.steps[0]["kind"] == "action"
        assert editor.selected_member_index == -1
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_compile_after_reorder_primary_semantics(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("compile_pg")
        assert editor.add_step("parallel") is True
        m0_id = editor.steps[0]["members"][0]["id"]
        m1_id = editor.steps[0]["members"][1]["id"]
        editor.select_member(1)
        assert editor.move_selected_member_up() is True
        assert editor.steps[0]["members"][0]["id"] == m1_id
        assert editor.steps[0]["members"][1]["id"] == m0_id

        actions = compile_document_to_actions(editor.get_internal_document())
        assert len(actions) == 2
        primary, secondary = actions[0], actions[1]
        assert primary["id"] == m1_id
        assert primary["wait_for_completion"] is True
        assert secondary["id"] == m0_id
        assert secondary["wait_for_completion"] is False
        assert secondary["trigger"]["reference_action"] == m1_id
        assert secondary["trigger"]["timing_mode"] == "after_start"
        assert secondary["trigger"]["offset_ms"] == 0
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_id_uniqueness_across_groups(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("ids")
        assert editor.add_step("parallel") is True
        assert editor.add_step("parallel") is True
        assert editor.add_member("arm_extend") is True
        editor.select_step(0)
        assert editor.add_member("ef_force") is True

        ids: list[str] = []
        for step in editor.steps:
            ids.append(step["id"])
            for member in step["members"]:
                ids.append(member["id"])
        assert len(ids) == len(set(ids))
    finally:
        catalog.cleanup()


def test_workflow_editor_parallel_save_load_round_trip_order(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("pg_round")
        assert editor.add_step("parallel") is True
        assert editor.set_member_type("winch_absolute") is True
        assert editor.set_member_param(0, "length", 2200) is True
        editor.select_member(1)
        assert editor.set_member_type("valve_turn") is True
        assert editor.set_member_param(1, "turn_value", 12.5) is True
        assert editor.add_member("arm_extend") is True
        assert editor.set_member_param(2, "distance", 80) is True
        # Make arm_extend primary
        editor.select_member(2)
        assert editor.move_selected_member_up() is True
        assert editor.move_selected_member_up() is True
        expected = [
            (m["id"], m["type"], dict(m["params"])) for m in editor.steps[0]["members"]
        ]
        assert editor.save() is True

        editor.new_document("other")
        assert editor.selected_member_index == -1
        loaded = editor.load_document("pg_round")
        assert editor.selected_member_index == -1
        members = loaded["steps"][0]["members"]
        actual = [(m["id"], m["type"], dict(m["params"])) for m in members]
        assert actual == expected
        assert actual[0][1] == "arm_extend"
    finally:
        catalog.cleanup()


def test_workflow_editor_set_member_type_requires_selection(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    try:
        editor.new_document("sel")
        assert editor.add_step("valve_turn") is True
        assert editor.set_member_type("spray_gimbal") is False
        assert editor.add_member("spray_gimbal") is False
        assert editor.remove_selected_member() is False
        assert editor.move_selected_member_up() is False
    finally:
        catalog.cleanup()
