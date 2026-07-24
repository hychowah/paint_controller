"""Shell and navigation startup smoke tests."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from paint_controller.core.application import _teardown_qml_runtime
from tests.startup_smoke_support import (
    BlankImageProvider,
    DynamicObject,
    FakeLauncherAdmin,
    FakeOverlayHost,
    _assert_component_ready,
    _context_objects,
    _qml_import_url,
)


def test_main_window_loads_offscreen_with_context_properties(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load"
    for name in context_objects:
        assert ctx.contextProperty(name) is not None

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
        "manualcommandhandler' of undefined",
        "workflowrunner' of undefined",
        "workfloweditor' of undefined",
        "cannot read property 'controls' of undefined",
        "cannot read property 'feeds' of undefined",
        "cannot read property 'topbar' of undefined",
        "referenceerror: workflowrunner is not defined",
        "detected function \"onendeffectorframeready\"",
        "detected function \"onbasefrontframeready\"",
        "detected function \"onbaserearframeready\"",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_main_window_video_overlay_is_active_by_default(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load"

    root = engine.rootObjects()[0]
    video_overlay = root.findChild(QObject, "videoFullscreenOverlayMain")
    assert video_overlay is not None
    assert video_overlay.property("active") is True

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
        "cannot read property 'controls' of undefined",
        "cannot read property 'feeds' of undefined",
        "cannot read property 'topbar' of undefined",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_main_window_video_overlay_hides_when_navigating_away(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

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
import "{core_import_url}"

MainWindow {{
    id: rootWindow
    objectName: "mainWindowRouteOverlayHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            rootWindow.navigateToPage("settings")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowRouteOverlayHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()

        video_overlay = root.findChild(QObject, "videoFullscreenOverlayMain")
        assert video_overlay is not None
        assert video_overlay.property("active") is False
        assert root.property("selectedPageKey") == "settings"

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_navigation_updates_selected_page_key(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

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
import "{core_import_url}"

MainWindow {{
    id: rootWindow
    objectName: "mainWindowHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            rootWindow.navigateToPage("settings")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowRouteHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert root.property("selectedPageKey") == "settings"
        assert stack_view.property("currentIndex") == 6
        assert stack_view.property("targetIndex") == 6

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_invalid_navigation_keeps_previous_route(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import "{core_import_url}"

MainWindow {{
    id: rootWindow
    objectName: "mainWindowInvalidRouteHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            rootWindow.navigateToPage("settings")
            rootWindow.navigateToPage("missing")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowInvalidRouteHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert root.property("selectedPageKey") == "settings"
        assert stack_view.property("currentIndex") == 6
        assert stack_view.property("targetIndex") == 6
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_teardown_does_not_emit_null_binding_warnings(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())
    engine.addImageProvider("base_top_view", BlankImageProvider())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load before teardown"

    warning_count_before_teardown = len(warnings)

    _teardown_qml_runtime(engine, qt_app, lambda _stage: None)

    for _ in range(5):
        qt_app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        qt_app.processEvents()

    teardown_warnings = warnings[warning_count_before_teardown:]
    null_binding_fragment = "cannot read property"
    undefined_assignment_fragment = "unable to assign [undefined]"
    assert not any(
        null_binding_fragment in warning.lower() or undefined_assignment_fragment in warning.lower()
        for warning in teardown_warnings
    ), teardown_warnings


def test_multi_screen_monitor_window_loads_offscreen(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "overlays" / "MultiScreenListUI.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

    context_objects = _context_objects(monkeypatch, tmp_path)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MultiScreenListUI.qml failed to load"

    fatal_warning_fragments = (
        "failed to load component",
        "no such file or directory",
        "is not a type",
        "cannot read property 'distance'",
        "cannot read property 'angle'",
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_multi_screen_monitor_window_consumes_overlay_host_matrix(monkeypatch, tmp_path, qt_app):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "overlays" / "MultiScreenListUI.qml"

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

    context_objects = _context_objects(monkeypatch, tmp_path)
    context_objects["overlayHost"] = FakeOverlayHost(
        video_fullscreen_active=True,
        video_fullscreen_source="image://base_front_live/frame",
    )
    context_objects["overlayHost"]._system_control_on_main_surface = False
    context_objects["overlayHost"]._system_control_on_secondary_surface = True
    context_objects["overlayHost"]._joystick_overlay_on_main_surface = False
    context_objects["overlayHost"]._joystick_overlay_on_secondary_surface = True
    context_objects["overlayHost"]._emergency_overlay_on_main_surface = True
    context_objects["overlayHost"]._emergency_overlay_on_secondary_surface = True
    context_objects["overlayHost"]._video_fullscreen_on_main_surface = True
    context_objects["overlayHost"]._video_fullscreen_on_secondary_surface = False

    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MultiScreenListUI.qml failed to load with overlay host matrix"

    root = engine.rootObjects()[0]
    assert root.findChild(QObject, "systemControlMenuSecondary").property("visible") is True
    assert root.findChild(QObject, "joystickOverlaySecondary").property("visible") is True
    assert root.findChild(QObject, "emergencyOverlaySecondary").property("visible") is True
    assert root.findChild(QObject, "videoFullscreenOverlaySecondary").property("active") is False


def test_select_bar_navigates_via_explicit_page_registry(qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    core_import_url = _qml_import_url(qml_dir / "core")
    navigation_import_url = _qml_import_url(qml_dir / "navigation")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    component = QQmlComponent(engine)
    component.setData(
        f'''
import QtQuick
import QtQuick.Controls
import "{core_import_url}"
import "{navigation_import_url}"

Item {{
    id: harnessRoot
    width: 1280
    height: 800
    property string selectedPageKey: "home"
    property var shellConnectivityStatusModel: ({{
        winchAvailable: true,
        wheelAvailable: true,
        endEffectorAvailable: false,
        baseOnline: true,
        baseStatus: 0,
        endEffectorOnline: false,
        endEffectorStatus: 2,
        baseIpAddress: "10.0.0.2",
        endEffectorIpAddress: "10.0.0.3"
    }})

    property var pageRegistry: [
        {{ routeOrder: 0, buttonKey: "home", buttonText: "Home", component: homeComponent }},
        {{ routeOrder: 1, buttonKey: "settings", buttonText: "Settings", component: settingsComponent }}
    ]

    function getPageConfig(pageKey) {{
        for (var i = 0; i < pageRegistry.length; i++) {{
            if (pageRegistry[i].buttonKey === pageKey) {{
                return pageRegistry[i]
            }}
        }}
        return null
    }}

    QtObject {{
        id: fakeStackView
        objectName: "fakeStackView"
        property int currentIndex: 0
        property int targetIndex: 0
        property var currentItem: null
        property var lastComponent: null

        function replace(currentItemArg, targetComponentArg) {{
            currentItem = currentItemArg
            lastComponent = targetComponentArg
        }}
    }}

    Component {{
        id: homeComponent
        Item {{ objectName: "homePage" }}
    }}

    Component {{
        id: settingsComponent
        Item {{ objectName: "settingsPage" }}
    }}

    SelectBar {{
        id: selectBar
        objectName: "selectBar"
        pageRegistry: harnessRoot.pageRegistry
        selectedPageKey: harnessRoot.selectedPageKey
        shellConnectivityStatus: harnessRoot.shellConnectivityStatusModel
        onNavigateRequested: function(pageKey) {{
            var targetPage = harnessRoot.getPageConfig(pageKey)
            if (!targetPage) {{
                return
            }}

            harnessRoot.selectedPageKey = targetPage.buttonKey
            fakeStackView.targetIndex = targetPage.routeOrder
            fakeStackView.replace(fakeStackView.currentItem, targetPage.component)
            fakeStackView.currentIndex = targetPage.routeOrder
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:SelectBarHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        select_bar = root.findChild(QObject, "selectBar")
        assert select_bar is not None

        connection_status_panel = root.findChild(QObject, "connectionStatusPanel")
        assert connection_status_panel is not None

        fake_stack_view = root.findChild(QObject, "fakeStackView")
        assert fake_stack_view is not None
        assert select_bar.property("navigationCount") == 2
        assert connection_status_panel.property("baseIpAddress") == "10.0.0.2"
        assert connection_status_panel.property("efIpAddress") == "10.0.0.3"

        select_bar.navigateToPage("settings")
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 1
        assert fake_stack_view.property("targetIndex") == 1
        assert select_bar.property("selectedPageKey") == "settings"
        assert fake_stack_view.property("lastComponent") is not None

        select_bar.navigateToPage("missing")
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 1
        assert select_bar.property("selectedPageKey") == "settings"
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_page_launcher_loads_with_shell_connectivity_status(qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    home_import_url = _qml_import_url(qml_dir / "pages" / "home")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.rootContext().setContextProperty("launcherAdmin", FakeLauncherAdmin())

    warnings = []
    engine.warnings.connect(lambda errs: warnings.extend(str(err) for err in errs))

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
        endEffectorReachable: false
    }})
    property var launcherAdminModel: launcherAdmin

    PageLauncher {{
        objectName: "pageLauncher"
        anchors.fill: parent
        shellConnectivityStatus: parent.shellConnectivityStatusModel
        launcherAdmin: parent.launcherAdminModel
    }}
}}
'''.encode(),
        QUrl("inmemory:PageLauncherHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        assert root.findChild(QObject, "pageLauncher") is not None

        qt_app.processEvents()

        fatal_warning_fragments = (
            "required property",
            "cannot read property",
            "referenceerror",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()