"""Direct tests for the QML-facing workflow editor persistence boundary."""

from __future__ import annotations

import json

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


def test_workflow_editor_reads_existing_workflow_data(qt_app, tmp_path) -> None:
    (tmp_path / "demo.yaml").write_text("name: demo\nactions: []\n", encoding="utf-8")
    editor, catalog = _make_editor(tmp_path)

    try:
        assert editor.workflow_list == ["demo"]
        workflow_json = editor.get_workflow_data("demo")
        assert json.loads(workflow_json) == {"name": "demo", "actions": []}
    finally:
        catalog.cleanup()


def test_workflow_editor_save_and_delete_refresh_shared_catalog(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    events: list[list[str]] = []
    editor.workflow_list_changed.connect(lambda: events.append(list(editor.workflow_list)))

    try:
        assert editor.save_workflow_data("alpha", json.dumps({"description": "demo", "actions": []})) is True
        assert "alpha" in editor.workflow_list
        assert json.loads(editor.get_workflow_data("alpha"))["name"] == "alpha"
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


def test_workflow_editor_normalizes_saved_documents_and_marks_runtime_stale(qt_app, tmp_path) -> None:
    editor, catalog = _make_editor(tmp_path)
    runtime_guard = _RuntimeGuard()
    editor.attach_runtime(runtime_guard)

    try:
        assert editor.save_workflow_data(
            "alpha",
            json.dumps(
                {
                    "description": 42,
                    "loop": 1,
                    "actions": [
                        {"type": "valve_turn", "params": {"turn_value": 25.0}},
                        {"id": "named", "name": "", "type": "winch_absolute", "params": {"length": 50}},
                    ],
                }
            ),
        ) is True

        saved_workflow = json.loads(editor.get_workflow_data("alpha"))
        assert saved_workflow["name"] == "alpha"
        assert saved_workflow["description"] == "42"
        assert saved_workflow["loop"] is True
        assert saved_workflow["actions"][0]["id"] == "action_0"
        assert saved_workflow["actions"][0]["name"] == "action_0"
        assert saved_workflow["actions"][1]["name"] == "named"
        assert runtime_guard.saved_names == ["alpha"]
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
        assert editor.save_workflow_data("alpha", json.dumps({"actions": []})) is False
        assert errors[-1] == "save blocked"

        runtime_guard.save_error = None
        assert editor.save_workflow_data("alpha", json.dumps({"actions": {}})) is False
        assert errors[-1] == "Error saving workflow: Workflow actions must be a list"

        runtime_guard.delete_error = "delete blocked"
        assert editor.delete_workflow("alpha") is False
        assert errors[-1] == "delete blocked"
        assert "alpha" in editor.workflow_list
    finally:
        catalog.cleanup()