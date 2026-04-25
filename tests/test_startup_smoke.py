"""Headless startup smoke tests for the QML shell and safety runtime wiring."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSize, Signal, Slot, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickImageProvider

from paint_controller.core.application import _teardown_qml_runtime
from paint_controller.core.settings import SettingsManager
from paint_controller.core.state_store import StateStore


class DynamicObject(QObject):
    def __init__(self, **properties) -> None:
        super().__init__()
        for key, value in properties.items():
            self.setProperty(key, value)


class FakeBackend(QObject):
    showPopupRequested = Signal(str, str, str, int)
    closePopupRequested = Signal()
    toggleSidebarRequested = Signal()
    toggleVideoOverlayRequested = Signal(bool, str)
    updateVideoSourceRequested = Signal(str)
    emergency_overlay_changed = Signal(bool, float, float)
    emergency_triggered = Signal()
    frame_ready = Signal()
    status_updated = Signal()


class FakeStreamHandler(QObject):
    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()


class FakeScreenManager(DynamicObject):
    screens_changed = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot(result=int)
    def get_screen_count(self) -> int:
        return 1


class FakeManualCommandHandler(QObject):
    @Slot(str, result=bool)
    def isCommandSupported(self, command_name: str) -> bool:
        return command_name != "Move to Position"

    @Slot(str, "QVariantMap", result=bool)
    def executeCommand(self, _command_name: str, _parameter_values) -> bool:
        return True


class BlankImageProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, image_id, size, requested_size):
        image = QImage(4, 4, QImage.Format_RGB32)
        image.fill(QColor("black"))
        if size is not None:
            size.setWidth(4)
            size.setHeight(4)
        return image


def _qml_import_url(path: Path) -> str:
    return QUrl.fromLocalFile(f"{path}/").toString()


def _assert_component_ready(qtbot, component: QQmlComponent) -> None:
    qtbot.waitUntil(lambda: component.isReady() or component.isError(), timeout=2000)
    assert component.isReady(), [str(error) for error in component.errors()]


def _teensy_all_status() -> DynamicObject:
    return DynamicObject(
        voltage=24.0,
        current=0.0,
        temperature=35.0,
        run_time=0.0,
        loop_time=1000.0,
        loop_time_counter=1.0,
        relay_on=False,
        enabled=True,
        arm_extension_dist=0.0,
        arm_rail_current=0.0,
        gimbal_pitch_motor_current=0.0,
        imu_pitch=0.0,
        imu_roll=0.0,
        imu_yaw=0.0,
        imu_acc_x=0.0,
        imu_acc_y=0.0,
        imu_acc_z=0.0,
        imu_angular_acc_x=0.0,
        imu_angular_acc_y=0.0,
        imu_angular_acc_z=0.0,
    )


def _settings_manager(monkeypatch, tmp_path: Path) -> SettingsManager:
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager()


def _context_objects(monkeypatch, tmp_path: Path) -> dict[str, QObject]:
    availability = DynamicObject(BASE=True, EF=True)
    ping_times = DynamicObject(BASE="42", END_EFFECTOR="38")
    settings_manager = _settings_manager(monkeypatch, tmp_path)

    return {
        "stateStore": StateStore(),
        "backend": FakeBackend(),
        "overlayController": DynamicObject(
            show_overlay=False,
            left_selected_index=0,
            right_selected_index=0,
            active_menu="",
            control_options=[],
        ),
        "workFlowRunner": DynamicObject(is_running=False),
        "warningHandler": DynamicObject(active_warning=""),
        "baseStreamHandler": FakeStreamHandler(),
        "wheelController": DynamicObject(
            available=True,
            enabled=True,
            left_motor_available=True,
            right_motor_available=True,
            left_wheel_speed=0.0,
            right_wheel_speed=0.0,
            left_wheel_current=0.0,
            right_wheel_current=0.0,
        ),
        "winchController": DynamicObject(
            available=True,
            cable_length=0.0,
            cable_speed=0.0,
            motor_voltage=24.0,
            motor_temperature=25.0,
            winch_torque=0.0,
        ),
        "steamDeckHandler": DynamicObject(),
        "windMonitor": DynamicObject(speed=0.0, direction=0.0),
        "teensyController": DynamicObject(available=True, all_status=_teensy_all_status()),
        "esp32ValveController": DynamicObject(
            valve_position=0.0,
            valve_rate=0.0,
            valve_motor_current=0.0,
            total_volume=0.0,
        ),
        "lidarController": DynamicObject(distance=0.0, angle=0.0),
        "heartbeatHandler": DynamicObject(
            controller_online=True,
            controller_status=0x01,
            base_online=True,
            base_status=0x00,
            ef_online=True,
            ef_status=0x00,
        ),
        "controlProcessor": DynamicObject(
            left_control_mode="None",
            left_control_value="",
            right_control_mode="None",
            right_control_value="",
        ),
        "manualCommandHandler": FakeManualCommandHandler(),
        "sshHandler": DynamicObject(deviceAvailability=availability, devicePingTimes=ping_times),
        "systemMonitor": DynamicObject(
            battery_level=100,
            battery_percentage=100,
            battery_remaining_time="--",
            battery_time_remaining="--",
            cpu_temperature=0.0,
        ),
        "screenRecorder": DynamicObject(isRecording=False, is_recording=False, recording_duration=0),
        "rosBagRecorder": DynamicObject(isRecording=False, is_recording=False),
        "settingsManager": settings_manager,
        "screenManager": FakeScreenManager(),
        "baseTopViewController": DynamicObject(enabled=False),
    }


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
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


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
    )
    assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings


def test_system_control_workspace_loads_with_required_properties(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    systemcontrol_import_url = _qml_import_url(qml_dir / "features" / "systemcontrol")

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

    SystemControlWorkspace {{
        anchors.fill: parent
        showOverlay: true
        activeMenu: "system"
    }}
}}
'''.encode(),
        QUrl("inmemory:SystemControlWorkspaceHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


@pytest.mark.parametrize("video_source", ["image://ef_live/frame", "image://base_front_live/frame"])
def test_video_fullscreen_workspace_loads_with_stream_context(monkeypatch, tmp_path, qt_app, qtbot, video_source):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    video_import_url = _qml_import_url(qml_dir / "features" / "video")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

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
import "{video_import_url}"

Item {{
    width: 1280
    height: 800

    VideoFullscreenWorkspace {{
        anchors.fill: parent
        active: true
        videoSource: "{video_source}"
    }}
}}
'''.encode(),
        QUrl("inmemory:VideoFullscreenWorkspaceHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


def test_video_fullscreen_overlay_wrapper_loads_with_stream_context(monkeypatch, tmp_path, qt_app, qtbot):
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlay_import_url = _qml_import_url(qml_dir / "overlays" / "video")

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))
    engine.addImageProvider("ef_live", BlankImageProvider())
    engine.addImageProvider("base_front_live", BlankImageProvider())
    engine.addImageProvider("base_rear_live", BlankImageProvider())

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
import "{overlay_import_url}"

Item {{
    width: 1280
    height: 800

    VideoFullscreenOverlay {{
        anchors.fill: parent
        active: true
        videoSource: "image://base_front_live/frame"
    }}
}}
'''.encode(),
        QUrl("inmemory:VideoFullscreenOverlayHarness.qml"),
    )

    _assert_component_ready(qtbot, component)

    root = component.create()
    try:
        assert root is not None, [str(error) for error in component.errors()]
        qt_app.processEvents()

        fatal_warning_fragments = (
            "failed to load component",
            "no such file or directory",
            "is not a type",
            "required property",
        )
        assert not any(fragment in warning.lower() for warning in warnings for fragment in fatal_warning_fragments), warnings
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()


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
    width: 1280
    height: 800

    property var pageRegistry: [
        {{ pageIndex: 0, buttonKey: "home", component: homeComponent }},
        {{ pageIndex: 8, buttonKey: "settings", component: settingsComponent }}
    ]

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
        stackView: fakeStackView
        pageRegistry: parent.pageRegistry
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

        fake_stack_view = root.findChild(QObject, "fakeStackView")
        assert fake_stack_view is not None

        select_bar.navigateToPage(8)
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 8
        assert fake_stack_view.property("targetIndex") == 8
        assert select_bar.property("selectedPageKey") == "settings"
        assert fake_stack_view.property("lastComponent") is not None

        select_bar.navigateToPage(404)
        qt_app.processEvents()

        assert fake_stack_view.property("currentIndex") == 8
        assert select_bar.property("selectedPageKey") == "settings"
    finally:
        if root is not None:
            root.deleteLater()
            qt_app.processEvents()