"""Direct tests for controller-factory wiring and admin gate behavior."""

from __future__ import annotations

import importlib

from tests.controller_factory_runtime_support import _CleanupRecorder, _controller_factory_module, _LoggerRecorder
from tests.fakes import FakeNode


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
        admin_action_gate=object(),
        manual_command_handler=object(),
        recording_actions=object(),
        teensy_actions=object(),
        system_actions=object(),
        wheel_actions=object(),
        winch_actions=object(),
        tuning_actions=object(),
        base_top_view_actions=object(),
        input_handler=cleanup_factory("input_handler"),
        emergency_handler=BrokenCleanup(),
        ssh_controller=cleanup_factory("ssh_controller"),
        screen_manager=cleanup_factory("screen_manager"),
        screen_recorder=cleanup_factory("screen_recorder"),
        ros_bag_recorder=cleanup_factory("ros_bag_recorder"),
        workflow_catalog=cleanup_factory("workflow_catalog"),
        workflow_editor=cleanup_factory("workflow_editor"),
        workflow_runner=cleanup_factory("workflow_runner"),
    )

    bundle.cleanup(logger)

    assert call_log == [
        "workflow_editor",
        "workflow_runner",
        "workflow_catalog",
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
    monkeypatch.setattr(module, "JoystickSelectionModel", record("JoystickSelectionModel"))
    monkeypatch.setattr(module, "OverlayController", record("OverlayController"))
    monkeypatch.setattr(module, "ControlProcessor", record("ControlProcessor"))
    monkeypatch.setattr(module, "AdminActionGate", record("AdminActionGate"))
    monkeypatch.setattr(module, "ManualCommandHandler", record("ManualCommandHandler"))
    monkeypatch.setattr(module, "RecordingActions", record("RecordingActions"))
    monkeypatch.setattr(module, "TeensyActions", record("TeensyActions"))
    monkeypatch.setattr(module, "SystemActions", record("SystemActions"))
    monkeypatch.setattr(module, "WheelActions", record("WheelActions"))
    monkeypatch.setattr(module, "WinchActions", record("WinchActions"))
    monkeypatch.setattr(module, "TuningActions", record("TuningActions"))
    monkeypatch.setattr(module, "BaseTopViewActions", record("BaseTopViewActions"))
    monkeypatch.setattr(module, "WorkflowCatalog", record("WorkflowCatalog"))
    monkeypatch.setattr(module, "WorkflowEditor", record("WorkflowEditor"))
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
    video_stream_handler = object()
    base_top_view_service = object()
    show_popup = object()
    close_popup = object()

    bundle = module.create_controllers(
        node=node,
        settings_manager=settings_manager,
        capability_catalog=object(),
        state_store=state_store,
        steam_deck_handler=steam_deck_handler,
        video_stream_handler=video_stream_handler,
        base_top_view_service=base_top_view_service,
        show_popup_fn=show_popup,
        close_popup_fn=close_popup,
    )

    assert hardware_calls == [
        (
            bundle.teensy_controller,
            bundle.winch_controller,
            bundle.esp32_valve_controller,
        )
    ]
    assert bundle.workflow_catalog.kwargs["logger"] is node.get_logger()
    assert bundle.workflow_editor.kwargs["catalog"] is bundle.workflow_catalog
    assert bundle.workflow_editor.kwargs["logger"] is node.get_logger()
    assert bundle.overlay_controller.kwargs["selection_model"] is not None
    assert bundle.control_processor.kwargs["selection_model"] is bundle.overlay_controller.kwargs["selection_model"]
    assert bundle.workflow_runner.args == (node, "hardware-bundle")
    assert bundle.workflow_runner.kwargs["logger"] is node.get_logger()
    assert bundle.workflow_runner.kwargs["catalog"] is bundle.workflow_catalog
    assert bundle.admin_action_gate.kwargs["capability_catalog"] is not None
    assert bundle.admin_action_gate.kwargs["state_store"] is state_store
    assert bundle.manual_command_handler.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.manual_command_handler.kwargs["winch"] is bundle.winch_controller
    assert bundle.manual_command_handler.kwargs["logger"] is node.get_logger()
    assert not hasattr(bundle, "device_action_handler")
    assert bundle.recording_actions.kwargs["video_stream_handler"] is video_stream_handler
    assert bundle.recording_actions.kwargs["screen_recorder"] is bundle.screen_recorder
    assert bundle.recording_actions.kwargs["ros_bag_recorder"] is bundle.ros_bag_recorder
    assert bundle.recording_actions.kwargs["logger"] is node.get_logger()
    assert bundle.teensy_actions.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.teensy_actions.kwargs["logger"] is node.get_logger()
    assert bundle.teensy_actions.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.system_actions.kwargs["heartbeat_handler"] is bundle.heartbeat_handler
    assert bundle.system_actions.kwargs["logger"] is node.get_logger()
    assert bundle.wheel_actions.kwargs["wheel"] is bundle.wheel_controller
    assert bundle.wheel_actions.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.wheel_actions.kwargs["logger"] is node.get_logger()
    assert bundle.winch_actions.kwargs["winch"] is bundle.winch_controller
    assert bundle.winch_actions.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.winch_actions.kwargs["logger"] is node.get_logger()
    assert bundle.tuning_actions.kwargs["teensy"] is bundle.teensy_controller
    assert bundle.tuning_actions.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.tuning_actions.kwargs["logger"] is node.get_logger()
    assert bundle.base_top_view_actions.kwargs["base_top_view_service"] is base_top_view_service
    assert bundle.base_top_view_actions.kwargs["admin_action_gate"] is bundle.admin_action_gate
    assert bundle.base_top_view_actions.kwargs["logger"] is node.get_logger()
    assert bundle.input_handler.kwargs["selection_model"] is bundle.overlay_controller.kwargs["selection_model"]
    assert bundle.input_handler.kwargs["close_popup_fn"] is close_popup
    assert bundle.emergency_handler.kwargs["safety_coordinator"] is bundle.safety_coordinator
    assert bundle.screen_recorder.kwargs["screen_manager"] is bundle.screen_manager
    assert node.get_logger().records[-1].message == "All controllers created with explicit DI"


def test_admin_action_gate_evaluates_idle_default_and_live_exceptions() -> None:
    gate_module = importlib.import_module("paint_controller.models.admin_action_gate")

    class FakeCapabilityCatalog:
        def getActionCapability(self, key: str):
            mapping = {
                "tuning.short_yaw_pid": {
                    "title": "Short Yaw PID",
                    "legalStateClass": "tuning-calibration",
                },
                "status.winch_enable": {
                    "title": "Winch Enable Toggle",
                    "legalStateClass": "status-admin",
                },
            }
            return mapping.get(key, {})

    state_store = type("StateStore", (), {"controller_heartbeat_state": 1})()
    # Force enforcement on (dev default is off).
    settings = type("Settings", (), {"get": lambda self, k, d=None: True})()
    gate = gate_module.AdminActionGate(
        capability_catalog=FakeCapabilityCatalog(),
        state_store=state_store,
        settings_manager=settings,
    )

    tuning_eval = gate.evaluate("tuning.short_yaw_pid")
    status_eval = gate.evaluate("status.winch_enable")

    assert tuning_eval["allowed"] is False
    assert tuning_eval["reason"] == "Short Yaw PID requires the system to be idle"
    # status-admin toggles allowed in any heartbeat when enforced.
    assert status_eval["allowed"] is True


def test_admin_action_gate_allows_emergency_override_in_error_state() -> None:
    gate_module = importlib.import_module("paint_controller.models.admin_action_gate")
    state_store = type("StateStore", (), {"controller_heartbeat_state": 3})()
    gate = gate_module.AdminActionGate(capability_catalog=None, state_store=state_store)

    evaluation = gate.evaluate("winch.emergency_stop")

    assert evaluation["allowed"] is True
