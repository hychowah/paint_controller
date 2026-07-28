"""Direct tests for the QML-facing workflow editor persistence boundary."""

from __future__ import annotations

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


def test_workflow_editor_load_document_shapes_existing_workflow(qt_app, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text(
        "name: demo\ndescription: hello\nloop: true\nactions: []\n",
        encoding="utf-8",
    )
    editor, catalog = _make_editor(tmp_path)

    try:
        assert editor.workflow_list == ["demo"]
        document = editor.load_document("demo")
        assert document == {
            "name": "demo",
            "description": "hello",
            "loop": True,
            "actions": [],
        }
    finally:
        catalog.cleanup()


def test_workflow_editor_save_document_and_delete_refresh_shared_catalog(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    events: list[list[str]] = []
    editor.workflow_list_changed.connect(lambda: events.append(list(editor.workflow_list)))

    try:
        assert editor.save_document("alpha", "demo", False, []) is True
        assert "alpha" in editor.workflow_list
        assert editor.load_document("alpha")["name"] == "alpha"
        assert editor.delete_workflow("alpha") is True
        assert "alpha" not in editor.workflow_list
        assert events[0] == ["alpha"]
        assert events[-1] == []
    finally:
        catalog.cleanup()


def test_workflow_editor_lists_workflows_in_stable_sorted_order(qt_app, tmp_path) -> None:
    (tmp_path / "beta.yml").write_text("name: beta\nactions: []\n", encoding="utf-8")
    (tmp_path / "Alpha.yaml").write_text("name: alpha\nactions: []\n", encoding="utf-8")
    (tmp_path / "alpha.yml").write_text("name: alpha\nactions: []\n", encoding="utf-8")
    editor, catalog = _make_editor(tmp_path)

    try:
        assert editor.workflow_list == ["Alpha", "alpha", "beta"] or editor.workflow_list == ["alpha", "beta"]
    finally:
        catalog.cleanup()


def test_workflow_editor_save_document_normalizes_and_marks_runtime_stale(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    runtime_guard = _RuntimeGuard()
    editor.attach_runtime(runtime_guard)

    try:
        assert (
            editor.save_document(
                "alpha",
                "42",
                True,
                [
                    {"type": "valve_turn", "params": {"turn_value": 25.0}},
                    {"id": "named", "name": "", "type": "winch_absolute", "params": {"length": 50}},
                ],
            )
            is True
        )

        saved_workflow = editor.load_document("alpha")
        assert saved_workflow["name"] == "alpha"
        assert saved_workflow["description"] == "42"
        assert saved_workflow["loop"] is True
        assert saved_workflow["actions"][0]["id"] == "action_0"
        assert saved_workflow["actions"][0]["name"] == "action_0"
        assert saved_workflow["actions"][1]["name"] == "named"
        assert runtime_guard.saved_names == ["alpha"]
    finally:
        catalog.cleanup()


def test_workflow_editor_save_document_round_trip_preserves_params_and_triggers(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)

    try:
        actions = [
            {
                "id": "move",
                "name": "Move Winch",
                "type": "winch_absolute",
                "params": {"length": 420, "speed": 35},
                "trigger": {"type": "delay", "offset_ms": 100},
                "estimated_duration": 5.0,
            }
        ]
        assert editor.save_document("roundtrip", "paint cycle", True, actions) is True

        reloaded = editor.load_document("roundtrip")
        assert reloaded["name"] == "roundtrip"
        assert reloaded["description"] == "paint cycle"
        assert reloaded["loop"] is True
        assert reloaded["actions"][0]["params"]["length"] == 420
        assert reloaded["actions"][0]["params"]["speed"] == 35
        assert reloaded["actions"][0]["trigger"]["offset_ms"] == 100
        assert reloaded["actions"][0]["estimated_duration"] == 5.0
    finally:
        catalog.cleanup()


def test_workflow_editor_rejects_runtime_conflicts_and_invalid_documents(qt_app, tmp_path) -> None:
    (tmp_path / "alpha.yaml").write_text("name: alpha\nactions: []\n", encoding="utf-8")
    editor, catalog = _make_editor(tmp_path)
    runtime_guard = _RuntimeGuard()
    editor.attach_runtime(runtime_guard)
    errors: list[str] = []
    editor.error_occurred.connect(errors.append)

    try:
        runtime_guard.save_error = "save blocked"
        assert editor.save_document("alpha", "", False, []) is False
        assert errors[-1] == "save blocked"

        runtime_guard.save_error = None
        # Missing action type is rejected by shared normalize path.
        assert editor.save_document("alpha", "", False, [{"params": {}}]) is False
        assert "missing a type" in errors[-1]

        runtime_guard.delete_error = "delete blocked"
        assert editor.delete_workflow("alpha") is False
        assert errors[-1] == "delete blocked"
        assert "alpha" in editor.workflow_list
    finally:
        catalog.cleanup()


def test_workflow_editor_load_document_emits_error_for_missing_workflow(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    errors: list[str] = []
    editor.error_occurred.connect(errors.append)

    try:
        assert editor.load_document("missing") == {}
        assert errors[-1] == "WorkFlow not found: missing"
    finally:
        catalog.cleanup()
