"""Direct tests for SignalWiring."""

from __future__ import annotations

from paint_controller.core.signal_wiring import SignalWiring, SignalWiringPorts
from tests.controller_factory_runtime_support import (
    _ControlProcessorRecorder,
    _EmergencyHandlerRecorder,
    _InputHandlerRecorder,
    _QtBridgeRecorder,
    _SafetyCoordinatorRecorder,
    _StatusTimerRecorder,
    _SteamDeckHandlerRecorder,
    _SystemMonitorRecorder,
    _VideoHandlerRecorder,
    _WheelControllerRecorder,
)


def _make_ports(**overrides) -> SignalWiringPorts:
    """Return minimal SignalWiringPorts for unit tests."""
    video_runtime = overrides.pop("video_runtime", None) or _VideoRuntimeRecorderForWiring()
    fields = {
        "bundle": type(
            "Bundle",
            (),
            {
                "input_handler": _InputHandlerRecorder(),
                "emergency_handler": _EmergencyHandlerRecorder(),
                "control_processor": _ControlProcessorRecorder(),
                "wheel_controller": _WheelControllerRecorder(),
                "safety_coordinator": _SafetyCoordinatorRecorder(),
                "system_monitor": _SystemMonitorRecorder(),
            },
        )(),
        "node": type(
            "Node",
            (),
            {"get_logger": lambda self: type("Logger", (), {"error": lambda *args: None})()},
        )(),
        "state_store": _StateStoreRecorderForWiring(),
        "qt_bridge": _QtBridgeRecorder(),
        "video_stream_handler": _VideoHandlerRecorder(),
        "steam_deck_handler": _SteamDeckHandlerRecorder(),
        "overlay_host": _OverlayHostRecorderForWiring(),
        "video_runtime": video_runtime,
        "update_rate": 30.0,
        "deferred_video_startup": lambda: None,
        "ros_thread": None,
    }
    fields.update(overrides)
    return SignalWiringPorts(**fields)


class _StateStoreRecorderForWiring:
    def __init__(self) -> None:
        self.control_mode_changed = _SignalRecorderForWiring()
        self.control_mode = "ef"
        self.display_message = ""


class _SignalRecorderForWiring:
    def __init__(self) -> None:
        self.connections: list[tuple[object, tuple]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))


class _OverlayHostRecorderForWiring:
    def __init__(self) -> None:
        self.sources: list[str] = []
        self.toggles: list[tuple[bool, str]] = []

    def set_video_fullscreen_source(self, source: str) -> None:
        self.sources.append(source)

    def toggle_video_fullscreen(self, source: str) -> None:
        self.toggles.append((True, source))


class _VideoRuntimeRecorderForWiring:
    def __init__(self) -> None:
        self.topBar = _VideoRuntimeTopBarRecorderForWiring()


class _VideoRuntimeTopBarRecorderForWiring:
    def __init__(self) -> None:
        self.endEffectorVideoRequested = _SignalRecorderForWiring()
        self.baseVideoRequested = _SignalRecorderForWiring()


def test_wire_connects_control_mode_and_emergency() -> None:
    ports = _make_ports()
    SignalWiring(ports).wire()

    assert len(ports.state_store.control_mode_changed.connections) == 1
    assert len(ports.bundle.emergency_handler.overlay_changed.connections) == 1
    assert len(ports.bundle.emergency_handler.emergency_triggered.connections) == 1


def test_wire_registers_steam_deck_callbacks() -> None:
    ports = _make_ports()
    SignalWiring(ports).wire()

    assert [button for button, _ in ports.steam_deck_handler.callbacks] == [
        "up",
        "down",
        "left",
        "right",
        "r4",
        "l4",
        "menu",
        "switch",
        "l5",
        "r5",
        "dot",
        "a",
        "l1",
    ]


def test_wire_connects_status_tick() -> None:
    ports = _make_ports()
    SignalWiring(ports).wire()

    assert len(ports.qt_bridge.status_updated.connections) == 1


def test_wire_connects_ros_thread_error_to_display_message(qt_app) -> None:
    """TD-039: RosThread.error_occurred surfaces on StateStore.display_message."""
    from PySide6.QtCore import QObject, Signal

    class _FakeRosThread(QObject):
        error_occurred = Signal(str)

    ros_thread = _FakeRosThread()
    ports = _make_ports(ros_thread=ros_thread)
    wiring = SignalWiring(ports)
    wiring.wire()

    ros_thread.error_occurred.emit("spin failed once")
    qt_app.processEvents()

    assert ports.state_store.display_message == "ROS: spin failed once"

    # Identical text is suppressed by the wiring throttle/dedupe.
    ros_thread.error_occurred.emit("spin failed once")
    qt_app.processEvents()
    assert ports.state_store.display_message == "ROS: spin failed once"


def test_wire_connects_video_top_bar_requests() -> None:
    video_runtime = _VideoRuntimeRecorderForWiring()
    ports = _make_ports(video_runtime=video_runtime)
    SignalWiring(ports).wire()

    assert len(video_runtime.topBar.endEffectorVideoRequested.connections) == 1
    assert len(video_runtime.topBar.baseVideoRequested.connections) == 1


def test_start_timers_creates_status_timer_and_starts_monitor(monkeypatch) -> None:
    from paint_controller.core import signal_wiring as signal_wiring_module

    timer_recorder = _StatusTimerRecorder()

    def fake_qtimer_factory():
        return timer_recorder

    fake_qtimer_factory.singleShot = lambda _ms, _callback: None
    monkeypatch.setattr(signal_wiring_module, "QTimer", fake_qtimer_factory)

    ports = _make_ports()
    status_timer = SignalWiring(ports).start_timers()

    assert status_timer is timer_recorder
    assert timer_recorder.started is True
    assert ports.bundle.system_monitor.monitoring_started is True


def test_start_timers_requires_bundle() -> None:
    ports = _make_ports(bundle=None)
    try:
        SignalWiring(ports).start_timers()
        assert False, "start_timers() should require a bundle"
    except RuntimeError as exc:
        assert "ControllerBundle" in str(exc)


def test_wire_requires_bundle() -> None:
    ports = _make_ports(bundle=None)
    try:
        SignalWiring(ports).wire()
        assert False, "wire() should require a bundle"
    except RuntimeError as exc:
        assert "ControllerBundle" in str(exc)
