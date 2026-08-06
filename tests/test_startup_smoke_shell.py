"""Shell and navigation startup smoke tests."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtTest import QTest

from paint_controller.core.application import _teardown_qml_runtime
from tests.qml_warning_assert import assert_no_fatal_qml_warnings
from tests.startup_smoke_support import (
    BlankImageProvider,
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

    assert_no_fatal_qml_warnings(warnings)


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

    assert_no_fatal_qml_warnings(warnings)


def test_main_window_video_overlay_stays_active_when_navigating_away(
    monkeypatch, tmp_path, qt_app, qtbot
):
    """Fullscreen video is owned by overlayHost, not by the current shell route.

    Navigating to a non-home page must not hide an active video overlay; the DOT
    toggle path flips overlayHost.video_fullscreen_active from any route.
    """
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
    # Default FakeOverlayHost starts with video_fullscreen_active=True (startup default).
    assert context_objects["overlayHost"].video_fullscreen_active is True
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
            shellRouter.navigateTo("settings")
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
        assert video_overlay.property("active") is True
        assert context_objects["shellRouter"].currentRoute == "settings"
        assert context_objects["overlayHost"].video_fullscreen_active is True

        # Toggle path while already off home (DOT → overlayHost flip).
        context_objects["overlayHost"].hide_video_fullscreen()
        qt_app.processEvents()
        assert video_overlay.property("active") is False

        context_objects["overlayHost"].show_video_fullscreen("image://base_front_live/frame")
        qt_app.processEvents()
        assert video_overlay.property("active") is True
        assert context_objects["shellRouter"].currentRoute == "settings"

        assert_no_fatal_qml_warnings(warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def _stack_page_object_name(stack_view: QObject) -> str | None:
    """Return objectName of StackView.currentItem (empty if missing)."""
    current = stack_view.property("currentItem")
    if current is None:
        return None
    name = current.property("objectName")
    return str(name) if name is not None else ""


def test_main_window_navigation_updates_selected_page_key(monkeypatch, tmp_path, qt_app, qtbot):
    """Route change must swap StackView content, not only currentRoute/currentIndex."""
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
            shellRouter.navigateTo("settings")
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
        # Allow StackView replace transition to settle.
        qtbot.waitUntil(
            lambda: _stack_page_object_name(root.findChild(QObject, "stackView")) == "pageSettings",
            timeout=2000,
        )

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert context_objects["shellRouter"].currentRoute == "settings"
        assert stack_view.property("currentIndex") == 6
        # currentItem objectName is the replace contract; StackView may keep the
        # exit item alive briefly during the replace transition.
        assert _stack_page_object_name(stack_view) == "pageSettings"
        assert root.findChild(QObject, "pageSettings") is not None

        assert_no_fatal_qml_warnings(warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_navigation_round_trip_restores_home_and_video(monkeypatch, tmp_path, qt_app, qtbot):
    """home → settings → home must restore stack page and video overlay active flag."""
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
    objectName: "mainWindowRoundTripHarness"
    property bool routeScenarioComplete: false

    Timer {{
        interval: 0
        running: true
        repeat: false
        onTriggered: {{
            shellRouter.navigateTo("settings")
            shellRouter.navigateTo("home")
            rootWindow.routeScenarioComplete = true
        }}
    }}
}}
'''.encode(),
        QUrl("inmemory:MainWindowRoundTripHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]

        qtbot.waitUntil(lambda: root.property("routeScenarioComplete") is True, timeout=2000)
        qt_app.processEvents()
        qtbot.waitUntil(
            lambda: _stack_page_object_name(root.findChild(QObject, "stackView")) == "pageHome",
            timeout=2000,
        )

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert context_objects["shellRouter"].currentRoute == "home"
        assert stack_view.property("currentIndex") == 0
        assert _stack_page_object_name(stack_view) == "pageHome"

        video_overlay = root.findChild(QObject, "videoFullscreenOverlayMain")
        assert video_overlay is not None
        assert video_overlay.property("active") is True

        assert_no_fatal_qml_warnings(warnings)
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
            shellRouter.navigateTo("settings")
            shellRouter.navigateTo("missing")
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
        qtbot.waitUntil(
            lambda: _stack_page_object_name(root.findChild(QObject, "stackView")) == "pageSettings",
            timeout=2000,
        )

        stack_view = root.findChild(QObject, "stackView")
        assert stack_view is not None
        assert context_objects["shellRouter"].currentRoute == "settings"
        assert stack_view.property("currentIndex") == 6
        assert _stack_page_object_name(stack_view) == "pageSettings"
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_main_window_select_bar_click_navigates_to_base_route(monkeypatch, tmp_path, qt_app, qtbot):
    """SelectBar click → route + StackView page swap when video is not covering chrome.

    Fullscreen video intentionally covers the entire main window (including SelectBar).
    This click path uses video off so QTest can reach nav delegates. Stack replace
    under an active video overlay is covered by the programmatic navigation tests.
    """
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
    # Fullscreen video covers SelectBar by design; disable it so clicks reach nav.
    context_objects["overlayHost"] = FakeOverlayHost(video_fullscreen_active=False)
    ctx = engine.rootContext()
    for name, obj in context_objects.items():
        ctx.setContextProperty(name, obj)

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load"
    window = engine.rootObjects()[0]

    shell_router = context_objects["shellRouter"]
    assert shell_router.currentRoute == "home"

    video_overlay = window.findChild(QObject, "videoFullscreenOverlayMain")
    assert video_overlay is not None
    assert video_overlay.property("active") is False

    # repeater.itemAt() returns None from Python; the delegates are the visual
    # children of the Repeater's parent Column.
    repeater = window.findChild(QObject, "navButtonRepeater")
    assert repeater is not None
    nav_delegates = [item for item in repeater.parentItem().childItems() if item.property("buttonKey") is not None]
    assert len(nav_delegates) > 0, "SelectBar rendered zero nav delegates — shellRouter wiring regression"
    assert len(nav_delegates) == len(shell_router.routeRegistry)

    home_delegate = next((item for item in nav_delegates if item.property("buttonKey") == "home"), None)
    base_delegate = next((item for item in nav_delegates if item.property("buttonKey") == "base"), None)
    assert home_delegate is not None
    assert base_delegate is not None
    assert home_delegate.property("isSelected") is True
    assert base_delegate.property("isSelected") is False

    click_point = base_delegate.mapToScene(QPointF(base_delegate.width() / 2, base_delegate.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, click_point)

    qtbot.waitUntil(lambda: shell_router.currentRoute == "base", timeout=2000)
    qt_app.processEvents()
    qtbot.waitUntil(
        lambda: _stack_page_object_name(window.findChild(QObject, "stackView")) == "pageBase",
        timeout=2000,
    )

    assert base_delegate.property("isSelected") is True
    assert home_delegate.property("isSelected") is False

    stack_view = window.findChild(QObject, "stackView")
    assert stack_view is not None
    # "base" has order 1 in the route registry (FakeShellRouter / models/shell_router.py).
    assert stack_view.property("currentIndex") == 1
    assert _stack_page_object_name(stack_view) == "pageBase"
    assert window.findChild(QObject, "pageBase") is not None

    assert_no_fatal_qml_warnings(warnings)


def test_main_window_video_overlay_covers_full_window_on_home(monkeypatch, tmp_path, qt_app):
    """Default home video must be full-window (not inset beside SelectBar)."""
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    qml_path = qml_dir / "core" / "MainWindow.qml"

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

    engine.load(QUrl.fromLocalFile(str(qml_path)))
    qt_app.processEvents()

    assert engine.rootObjects(), "MainWindow.qml failed to load"
    window = engine.rootObjects()[0]
    video_overlay = window.findChild(QObject, "videoFullscreenOverlayMain")
    assert video_overlay is not None
    assert video_overlay.property("active") is True
    assert float(video_overlay.property("x")) == 0.0
    assert float(video_overlay.property("width")) == float(window.width())


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

    assert_no_fatal_qml_warnings(warnings)


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

    QtObject {{
        id: fakeShellRouter
        objectName: "fakeShellRouter"
        property var routeRegistry: [
            {{ key: "home", title: "Home", iconSource: "", iconScale: 0.6, order: 0 }},
            {{ key: "settings", title: "Settings", iconSource: "", iconScale: 0.6, order: 1 }}
        ]
        property string currentRoute: "home"
        property int currentRouteOrder: 0

        function navigateTo(route) {{
            for (var i = 0; i < routeRegistry.length; i++) {{
                if (routeRegistry[i].key === route) {{
                    if (currentRoute !== route) {{
                        currentRoute = route
                        currentRouteOrder = routeRegistry[i].order
                    }}
                    return true
                }}
            }}
            return false
        }}

        function routeOrder(route) {{
            for (var i = 0; i < routeRegistry.length; i++) {{
                if (routeRegistry[i].key === route) {{
                    return routeRegistry[i].order
                }}
            }}
            return -1
        }}
    }}

    QtObject {{
        id: fakeStackView
        objectName: "fakeStackView"
        property int currentIndex: fakeShellRouter.currentRouteOrder
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
        shellRouter: fakeShellRouter
        shellConnectivityStatus: harnessRoot.shellConnectivityStatusModel
    }}

    Connections {{
        target: fakeShellRouter
        function onCurrentRouteChanged() {{
            var route = fakeShellRouter.currentRoute
            var order = fakeShellRouter.routeOrder(route)
            fakeStackView.targetIndex = order
            fakeStackView.replace(fakeStackView.currentItem, route === "home" ? homeComponent : settingsComponent)
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
        fake_shell_router = root.findChild(QObject, "fakeShellRouter")
        assert fake_shell_router is not None
        assert select_bar.property("navigationCount") == 2
        assert connection_status_panel.property("baseIpAddress") == "10.0.0.2"
        assert connection_status_panel.property("efIpAddress") == "10.0.0.3"

        select_bar.navigateToPage("settings")
        qt_app.processEvents()

        assert fake_stack_view.property("targetIndex") == 1
        assert fake_shell_router.property("currentRoute") == "settings"
        assert fake_stack_view.property("lastComponent") is not None

        select_bar.navigateToPage("missing")
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 1
        assert fake_shell_router.property("currentRoute") == "settings"
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

        assert_no_fatal_qml_warnings(warnings)
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()
