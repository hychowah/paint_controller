"""Direct tests for the QML-facing workflow editor persistence boundary."""

from __future__ import annotations

import json

from paint_controller.services.workflow.workflow_catalog import WorkflowCatalog
from paint_controller.services.workflow.workflow_editor import WorkflowEditor
from tests.fakes import FakeNode


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