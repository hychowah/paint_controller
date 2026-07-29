"""Startup smoke tests for the workflow editor surface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from tests.startup_smoke_support import _assert_component_ready, _context_objects, _qml_import_url


def test_edit_workflow_tab_loads_with_workflow_editor(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "overlays" / "systemcontrol")

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
    width: 1280
    height: 800

    EditWorkFlowTab {{
        objectName: "editWorkflowTab"
        anchors.fill: parent
        workflowEditor: systemControlServices.workflowEditor
    }}
}}
'''.encode(),
        QUrl("inmemory:EditWorkFlowTabHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        assert root.findChild(QObject, "editWorkflowTab") is not None

        qt_app.processEvents()

        fatal_warning_fragments = (
            "required property",
            "referenceerror",
            "failed to create",
            "failed to load component",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), (
            warnings
        )
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()
