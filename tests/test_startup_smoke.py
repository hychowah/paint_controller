"""Headless startup smoke tests for the QML shell and safety runtime wiring."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSize, Signal, Slot, QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlApplicationEngine
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


def _settings_manager(monkeypatch, tmp_path: Path) -> SettingsManager:
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager()


def _context_objects(monkeypatch, tmp_path: Path) -> dict[str, QObject]:
    availability = DynamicObject(BASE=True, EF=True)
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
        "wheelController": DynamicObject(available=True, left_wheel_speed=0.0, right_wheel_speed=0.0),
        "winchController": DynamicObject(available=True),
        "steamDeckHandler": DynamicObject(),
        "windMonitor": DynamicObject(speed=0.0, direction=0.0),
        "teensyController": DynamicObject(available=True),
        "esp32ValveController": DynamicObject(valve_position=0.0),
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
        "sshHandler": DynamicObject(deviceAvailability=availability),
        "systemMonitor": DynamicObject(
            battery_percentage=100,
            battery_time_remaining="--",
            cpu_temperature=0.0,
        ),
        "screenRecorder": DynamicObject(isRecording=False),
        "rosBagRecorder": DynamicObject(isRecording=False),
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