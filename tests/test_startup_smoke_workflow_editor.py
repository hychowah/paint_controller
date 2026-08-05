"""Startup smoke tests for the full-page workflow editor surface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from tests.startup_smoke_support import _assert_component_ready, _context_objects, _qml_import_url
from tests.qml_warning_assert import assert_no_fatal_qml_warnings


def test_workflow_editor_workspace_loads_and_opens(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    workflow_import_url = _qml_import_url(qml_dir / "features" / "workflow")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{workflow_import_url}"

Item {{
    width: 1280
    height: 800

    WorkflowEditorWorkspace {{
        objectName: "workflowEditorWorkspace"
        anchors.fill: parent
        workflowEditor: systemControlServices.workflowEditor
        overlayController: overlayController
    }}
}}
'''.encode(),
        QUrl("inmemory:WorkflowEditorWorkspaceHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        workspace = root.findChild(QObject, "workflowEditorWorkspace")
        assert workspace is not None

        editor = context_objects["systemControlServices"].workflowEditor
        assert editor.open_editor() is True
        qt_app.processEvents()
        assert editor.is_open is True

        # Source contract: palette exposes action/wait/parallel kinds for touch authoring
        kinds = {entry["kind"] for entry in editor.palette}
        assert "action" in kinds
        assert "wait" in kinds
        assert "parallel" in kinds

        assert_no_fatal_qml_warnings(warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_workflow_tab_has_edit_entry_not_system_control_tab(monkeypatch, tmp_path, qt_app, qtbot):
    """WorkFlow tab hosts Edit; Edit WorkFlow is not a System Control tab path."""
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "overlays" / "systemcontrol")

    # Static contract: SystemControlWorkspace no longer lists Edit WorkFlow tab
    workspace_qml = (qml_dir / "features" / "systemcontrol" / "SystemControlWorkspace.qml").read_text(
        encoding="utf-8"
    )
    assert "Edit WorkFlow" not in workspace_qml
    assert "EditWorkFlowTab" not in workspace_qml

    workflow_tab_qml = (qml_dir / "overlays" / "systemcontrol" / "WorkFlowTab.qml").read_text(encoding="utf-8")
    assert "open_editor" in workflow_tab_qml
    assert 'text: "Edit"' in workflow_tab_qml

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{systemcontrol_import_url}"

Item {{
    width: 800
    height: 600

    WorkFlowTab {{
        objectName: "workFlowTab"
        anchors.fill: parent
        workflowRunner: systemControlServices.workflowRunner
        workflowEditor: systemControlServices.workflowEditor
        overlayController: overlayController
    }}
}}
'''.encode(),
        QUrl("inmemory:WorkFlowTabEditHarness.qml"),
    )
    _assert_component_ready(qtbot, component)
    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        assert root.findChild(QObject, "workFlowTab") is not None
        assert_no_fatal_qml_warnings(warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()
