"""Startup smoke tests for the Home page surface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from tests.startup_smoke_support import BlankImageProvider, _assert_component_ready, _context_objects, _qml_import_url


def test_page_home_loads_with_explicit_video_runtime(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    home_import_url = _qml_import_url(qml_dir / "pages" / "home")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["baseStreamHandler"] = None
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{home_import_url}"

Item {{
    width: 1280
    height: 800

    property var shellConnectivityStatusModel: ({{
        baseReachable: true,
        endEffectorReachable: false,
        baseOnline: true,
        endEffectorOnline: false
    }})

    QtObject {{
        id: videoFeedsModel
        signal endEffectorFrameReady()
        signal baseFrontFrameReady()
        signal baseRearFrameReady()
    }}

    QtObject {{
        id: videoRuntimeModel
        property QtObject feeds: videoFeedsModel
    }}

    PageHome {{
        objectName: "pageHome"
        anchors.fill: parent
        shellConnectivityStatus: parent.shellConnectivityStatusModel
        videoRuntime: videoRuntimeModel
    }}
}}
'''.encode(),
        QUrl("inmemory:PageHomeHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        assert root.findChild(QObject, "pageHome") is not None

        qt_app.processEvents()

        fatal_warning_fragments = (
            "required property",
            "cannot read property 'feeds' of undefined",
            "cannot read property 'basestreamhandler' of undefined",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()