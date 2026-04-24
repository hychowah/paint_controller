"""Direct tests for the controller factory and bounded AppRuntime seams."""

from __future__ import annotations

import importlib
from dataclasses import dataclass

from tests.fakes import FakeNode


class _CleanupRecorder:
    def __init__(self, name: str, call_log: list[str]) -> None:
        self.name = name
        self.call_log = call_log
        self.cleanup_calls = 0

    def cleanup(self) -> None:
        self.cleanup_calls += 1
        self.call_log.append(self.name)


class _LoggerRecorder:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.infos: list[str] = []

    def info(self, message: str) -> None:
        self.infos.append(message)

    def error(self, message: str) -> None:
        self.errors.append(message)


def _controller_factory_module():
    return importlib.import_module("paint_controller.core.controller_factory")


def _app_runtime_module():
    return importlib.import_module("paint_controller.core.app_runtime")


def test_controller_bundle_cleanup_runs_reverse_order_and_logs_errors() -> None:
    module = _controller_factory_module()
    call_log: list[str] = []
    logger = _LoggerRecorder()

    def cleanup_factory(name: str):
        return _CleanupRecorder(name, call_log)

    class BrokenCleanup:
        def cleanup(self) -> None:
            raise RuntimeError("boom")

    bundle = module.ControllerBundle(
        warning_handler=object(),
        system_monitor=cleanup_factory("system_monitor"),
        wheel_controller=cleanup_factory("wheel_controller"),
        esp32_valve_controller=cleanup_factory("esp32_valve_controller"),
        lidar_controller=cleanup_factory("lidar_controller"),
        wind_monitor=cleanup_factory("wind_monitor"),
        winch_controller=cleanup_factory("winch_controller"),
        teensy_controller=cleanup_factory("teensy_controller"),
        heartbeat_handler=cleanup_factory("heartbeat_handler"),
        safety_coordinator=object(),
        overlay_controller=cleanup_factory("overlay_controller"),
        control_processor=cleanup_factory("control_processor"),
        input_handler=cleanup_factory("input_handler"),
        emergency_handler=BrokenCleanup(),
        ssh_controller=cleanup_factory("ssh_controller"),
        screen_manager=cleanup_factory("screen_manager"),
        screen_recorder=cleanup_factory("screen_recorder"),
        ros_bag_recorder=cleanup_factory("ros_bag_recorder"),
        workflow_runner=cleanup_factory("workflow_runner"),
    )

    bundle.cleanup(logger)

    assert call_log == [
        "workflow_runner",
        "ros_bag_recorder",
        "screen_recorder",
        "screen_manager",
        "ssh_controller",
        "input_handler",
        "control_processor",
        "overlay_controller",
        "heartbeat_handler",
        "teensy_controller",
        "winch_controller",
        "wind_monitor",
        "lidar_controller",
        "esp32_valve_controller",
        "wheel_controller",
        "system_monitor",
    ]
    assert logger.errors == ["Error cleaning up emergency_handler: boom"]


def test_create_controllers_wires_dependency_graph(monkeypatch) -> None:
    module = _controller_factory_module()
    construction_log: list[tuple[str, tuple, dict]] = []

    def record(name: str):
        class Recorded:
            def __init__(self, *args, **kwargs) -> None:
                construction_log.append((name, args, kwargs))
                self.args = args
                self.kwargs = kwargs
                self.set_control_processor_calls = []

            def set_control_processor(self, processor) -> None:
                self.set_control_processor_calls.append(processor)

        return Recorded

    hardware_calls: list[tuple[object, object, object]] = []

    class FakeHardwareControllers:
        @classmethod
        def from_controllers(cls, teensy, winch, esp32):
            hardware_calls.append((teensy, winch, esp32))
            return "hardware-bundle"

    monkeypatch.setattr(module, "WarningHandler", record("WarningHandler"))
    monkeypatch.setattr(module, "SystemMonitor", record("SystemMonitor"))
    monkeypatch.setattr(module, "WheelController", record("WheelController"))
    monkeypatch.setattr(module, "ESP32ValveController", record("ESP32ValveController"))
    monkeypatch.setattr(module, "LidarController", record("LidarController"))
    monkeypatch.setattr(module, "WindMonitor", record("WindMonitor"))
    monkeypatch.setattr(module, "WinchController", record("WinchController"))
    monkeypatch.setattr(module, "TeensyController", record("TeensyController"))
    monkeypatch.setattr(module, "SafetyCoordinator", record("SafetyCoordinator"))
    monkeypatch.setattr(module, "UIHeartbeatHandler", record("UIHeartbeatHandler"))
    monkeypatch.setattr(module, "OverlayController", record("OverlayController"))
    monkeypatch.setattr(module, "ControlProcessor", record("ControlProcessor"))
    monkeypatch.setattr(module, "WorkFlowRunner", record("WorkFlowRunner"))
    monkeypatch.setattr(module, "UIInputHandler", record("UIInputHandler"))
    monkeypatch.setattr(module, "EmergencyButtonHandler", record("EmergencyButtonHandler"))
    monkeypatch.setattr(module, "UISSHController", record("UISSHController"))
    monkeypatch.setattr(module, "ScreenManager", record("ScreenManager"))
    monkeypatch.setattr(module, "ScreenRecorder", record("ScreenRecorder"))
    monkeypatch.setattr(module, "RosBagRecorder", record("RosBagRecorder"))
    monkeypatch.setattr(module, "HardwareControllers", FakeHardwareControllers)

    node = FakeNode()
    settings_manager = object()
    state_store = object()
    steam_deck_handler = object()
    show_popup = object()
    close_popup = object()

    bundle = module.create_controllers(
        node=node,
        settings_manager=settings_manager,
        state_store=state_store,
        steam_deck_handler=steam_deck_handler,
        show_popup_fn=show_popup,
        close_popup_fn=close_popup,
    )

    assert hardware_calls == [(
        bundle.teensy_controller,
        bundle.winch_controller,
        bundle.esp32_valve_controller,
    )]
    assert bundle.workflow_runner.args == (node, "hardware-bundle")
    assert bundle.overlay_controller.set_control_processor_calls == [bundle.control_processor]
    assert bundle.input_handler.kwargs["close_popup_fn"] is close_popup
    assert bundle.emergency_handler.kwargs["safety_coordinator"] is bundle.safety_coordinator
    assert bundle.screen_recorder.kwargs["screen_manager"] is bundle.screen_manager
    assert node.get_logger().records[-1].message == "All controllers created with explicit DI"


@dataclass
class _ContextRecorder:
    properties: dict[str, object]

    def setContextProperty(self, name: str, obj: object) -> None:
        self.properties[name] = obj


class _EngineRecorder:
    def __init__(self) -> None:
        self.context = _ContextRecorder({})

    def rootContext(self) -> _ContextRecorder:
        return self.context


class _SignalRecorder:
    def __init__(self) -> None:
        self.connections: list[tuple[object, tuple]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))


class _SteamDeckHandlerRecorder:
    def __init__(self) -> None:
        self.callbacks: list[tuple[str, object]] = []

    def register_button_callback(self, button_name: str, callback) -> None:
        self.callbacks.append((button_name, callback))


class _InputHandlerRecorder:
    def on_up_pressed(self) -> None: pass
    def on_down_pressed(self) -> None: pass
    def on_left_pressed(self) -> None: pass
    def on_right_pressed(self) -> None: pass
    def on_r4_pressed(self) -> None: pass
    def on_l4_pressed(self) -> None: pass
    def on_menu_pressed(self) -> None: pass
    def on_switch_pressed(self) -> None: pass
    def on_l5_pressed(self) -> None: pass
    def on_r5_pressed(self) -> None: pass
    def on_l1_pressed(self) -> None: pass


class _QtBridgeRecorder:
    def __init__(self) -> None:
        self.status_updated = _SignalRecorder()
        self.emergency_overlay_changed = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.emergency_triggered = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.frame_ready = type("Emitter", (), {"emit": lambda self, *args: None})()
        self.show_popup_calls: list[tuple[str, str, str, int]] = []
        self.base_top_view_service = None
        self.input_handler = None

    def show_popup(self, title: str, message: str, popup_type: str, delay: int) -> None:
        self.show_popup_calls.append((title, message, popup_type, delay))

    def close_popup(self) -> None:
        pass

    def toggle_fullscreen(self) -> None:
        pass

    def toggle_lidar_overlay(self) -> None:
        pass

    def set_base_top_view_service(self, service) -> None:
        self.base_top_view_service = service

    def set_input_handler(self, input_handler) -> None:
        self.input_handler = input_handler


class _WheelControllerRecorder:
    def __init__(self) -> None:
        self.error_state_changed = _SignalRecorder()


class _EmergencyHandlerRecorder:
    def __init__(self) -> None:
        self.overlay_changed = _SignalRecorder()
        self.emergency_triggered = _SignalRecorder()

    def check_emergency_button(self, _buttons) -> None:
        pass


class _ControlProcessorRecorder:
    def process_input(self, _input_state) -> None:
        pass


class _VideoHandlerRecorder:
    def __init__(self) -> None:
        self.endEffectorFrameReady = _SignalRecorder()
        self.started = 0

    def start_all_streams(self) -> int:
        self.started += 1
        return 4


class _SafetyCoordinatorRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def halt_all_effectors(self, reason: str, heartbeat_state=None) -> None:
        self.calls.append((reason, heartbeat_state))


class _StatusTimerRecorder:
    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        self.stopped = True


class _WaitableRecorder:
    def __init__(self, name: str, call_log: list[str]) -> None:
        self.name = name
        self.call_log = call_log
        self.shutdown_requested = False
        self.wait_calls: list[int] = []
        self.terminated = False

    def request_shutdown(self) -> None:
        self.shutdown_requested = True
        self.call_log.append(f"{self.name}.request_shutdown")

    def wait(self, timeout: int) -> bool:
        self.wait_calls.append(timeout)
        self.call_log.append(f"{self.name}.wait({timeout})")
        return True

    def terminate(self) -> None:
        self.terminated = True
        self.call_log.append(f"{self.name}.terminate")


def _runtime_without_bootstrap(monkeypatch):
    module = _app_runtime_module()
    monkeypatch.setattr(module.AppRuntime, "_bootstrap", lambda self: None)
    return module, module.AppRuntime(argv=[])


def test_app_runtime_create_bundle_and_register_context_properties(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)

    runtime.node = FakeNode()
    runtime.settings_manager = type("Settings", (), {"_show_popup_fn": None})()
    runtime.state_store = object()
    runtime.steam_deck_handler = _SteamDeckHandlerRecorder()
    runtime.base_top_view_service = object()
    runtime.qt_bridge = _QtBridgeRecorder()
    runtime.engine = _EngineRecorder()
    runtime.bundle = type(
        "Bundle",
        (),
        {
            "overlay_controller": object(),
            "workflow_runner": object(),
            "warning_handler": object(),
            "wheel_controller": _WheelControllerRecorder(),
            "winch_controller": object(),
            "wind_monitor": object(),
            "teensy_controller": object(),
            "esp32_valve_controller": object(),
            "lidar_controller": object(),
            "heartbeat_handler": object(),
            "control_processor": _ControlProcessorRecorder(),
            "ssh_controller": object(),
            "system_monitor": object(),
            "screen_manager": object(),
            "screen_recorder": object(),
            "ros_bag_recorder": object(),
            "input_handler": _InputHandlerRecorder(),
            "emergency_handler": _EmergencyHandlerRecorder(),
            "safety_coordinator": _SafetyCoordinatorRecorder(),
        },
    )()
    runtime.video_stream_handler = _VideoHandlerRecorder()

    create_calls: list[dict[str, object]] = []

    def fake_create_controllers(**kwargs):
        create_calls.append(kwargs)
        return runtime.bundle

    fake_factory = type("FactoryModule", (), {"create_controllers": staticmethod(fake_create_controllers)})
    monkeypatch.setitem(importlib.import_module("sys").modules, "paint_controller.core.controller_factory", fake_factory)

    runtime._create_controller_bundle()
    runtime._register_context_properties()
    runtime._wire_steam_deck_callbacks()

    assert create_calls[0]["show_popup_fn"] == runtime.qt_bridge.show_popup
    assert create_calls[0]["close_popup_fn"] == runtime.qt_bridge.close_popup
    assert runtime.qt_bridge.base_top_view_service is runtime.base_top_view_service
    assert runtime.qt_bridge.input_handler is runtime.bundle.input_handler
    assert set(runtime.engine.context.properties) == set(module._EXPECTED_CONTEXT_PROPERTY_NAMES)
    assert [button for button, _ in runtime.steam_deck_handler.callbacks] == [
        "up", "down", "left", "right", "r4", "l4", "menu", "switch", "l5", "r5", "dot", "a", "l1"
    ]


def test_app_runtime_shutdown_cleans_resources_in_order(monkeypatch) -> None:
    module, runtime = _runtime_without_bootstrap(monkeypatch)
    call_log: list[str] = []

    runtime.status_timer = _StatusTimerRecorder()
    engine_obj = object()
    app_obj = object()
    runtime.engine = engine_obj
    runtime.app = app_obj
    runtime.ros_thread = _WaitableRecorder("ros_thread", call_log)
    runtime.bundle = type("Bundle", (), {"cleanup": lambda self, logger: call_log.append("bundle.cleanup")})()
    runtime.base_top_view_service = _CleanupRecorder("base_top_view_service.cleanup", call_log)
    runtime.video_stream_handler = _CleanupRecorder("video_stream_handler.cleanup", call_log)
    runtime.steam_deck_handler = _CleanupRecorder("steam_deck_handler.cleanup", call_log)
    node = FakeNode()
    cleanup_calls: list[str] = []
    node.cleanup = lambda: cleanup_calls.append("node.cleanup")  # type: ignore[attr-defined]
    original_destroy_node = node.destroy_node
    node.destroy_node = lambda: (cleanup_calls.append("node.destroy_node"), original_destroy_node())[1]  # type: ignore[assignment]
    runtime.node = node
    runtime._shutdown_started = False

    teardown_calls: list[tuple[object, object]] = []
    monkeypatch.setattr(module, "teardown_qml_runtime", lambda engine, app, _log: teardown_calls.append((engine, app)))
    monkeypatch.setattr(module.rclpy, "ok", lambda: True)
    shutdown_calls: list[str] = []
    monkeypatch.setattr(module.rclpy, "shutdown", lambda: shutdown_calls.append("shutdown"))

    runtime.shutdown()

    assert runtime.status_timer.stopped is True
    assert teardown_calls == [(engine_obj, app_obj)]
    assert call_log == [
        "ros_thread.request_shutdown",
        "ros_thread.wait(2000)",
        "bundle.cleanup",
        "base_top_view_service.cleanup",
        "video_stream_handler.cleanup",
        "steam_deck_handler.cleanup",
    ]
    assert cleanup_calls == ["node.cleanup", "node.destroy_node"]
    assert shutdown_calls == ["shutdown"]
    assert runtime.engine is None


def test_app_runtime_init_shuts_down_when_bootstrap_fails(monkeypatch) -> None:
    module = _app_runtime_module()
    shutdown_calls: list[module.AppRuntime] = []

    def fake_bootstrap(self) -> None:
        self.ros_thread = object()
        raise RuntimeError("bootstrap failed")

    def fake_shutdown(self) -> None:
        shutdown_calls.append(self)

    monkeypatch.setattr(module.AppRuntime, "_bootstrap", fake_bootstrap)
    monkeypatch.setattr(module.AppRuntime, "shutdown", fake_shutdown)

    try:
        module.AppRuntime(argv=[])
    except RuntimeError as exc:
        assert str(exc) == "bootstrap failed"
    else:
        assert False, "AppRuntime constructor should re-raise bootstrap errors"

    assert len(shutdown_calls) == 1