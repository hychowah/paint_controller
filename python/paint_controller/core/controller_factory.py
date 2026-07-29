"""Factory for creating all controllers with explicit dependency injection."""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from paint_controller.controllers.esp32_valve import ESP32ValveController
from paint_controller.controllers.lidar import LidarController
from paint_controller.controllers.ssh import UISSHController
from paint_controller.controllers.system_monitor import SystemMonitor
from paint_controller.controllers.teensy import TeensyController
from paint_controller.controllers.wheel import WheelController
from paint_controller.controllers.winch import WinchController
from paint_controller.controllers.wind_monitor import WindMonitor
from paint_controller.handlers.control_processor import ControlProcessor
from paint_controller.handlers.emergency import EmergencyButtonHandler
from paint_controller.handlers.heartbeat import UIHeartbeatHandler
from paint_controller.handlers.input import UIInputHandler
from paint_controller.handlers.manual_commands import ManualCommandHandler
from paint_controller.handlers.safety_coordinator import SafetyCoordinator
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.handlers.warnings import WarningHandler
from paint_controller.models.admin_action_gate import AdminActionGate
from paint_controller.models.base_top_view_actions import BaseTopViewActions
from paint_controller.models.joystick_selection import JoystickSelectionModel
from paint_controller.models.recording_actions import RecordingActions
from paint_controller.models.system_actions import SystemActions
from paint_controller.models.teensy_actions import TeensyActions
from paint_controller.models.tuning_actions import TuningActions
from paint_controller.models.wheel_actions import WheelActions
from paint_controller.models.winch_actions import WinchActions
from paint_controller.services.ros_bag_recorder import RosBagRecorder
from paint_controller.services.screen_manager import ScreenManager
from paint_controller.services.screen_recorder import ScreenRecorder
from paint_controller.services.workflow.hardware import HardwareControllers
from paint_controller.services.workflow.workflow_catalog import WorkflowCatalog
from paint_controller.services.workflow.workflow_editor import WorkflowEditor
from paint_controller.services.workflow.workflow_runner import WorkFlowRunner
from paint_controller.ui.overlay import OverlayController

# Reverse-ish teardown order for fields that implement cleanup().
# Test: every bundle field with a callable cleanup must appear here (TD-051).
# Fields without cleanup (actions, gate, selection_model, …) are intentionally omitted.
_CLEANUP_ORDER: tuple[str, ...] = (
    "workflow_runner",
    "workflow_catalog",
    "ros_bag_recorder",
    "screen_recorder",
    "screen_manager",
    "ssh_controller",
    "overlay_controller",
    "heartbeat_handler",
    "teensy_controller",
    "winch_controller",
    "wind_monitor",
    "lidar_controller",
    "esp32_valve_controller",
    "wheel_controller",
    "system_monitor",
)


def _bundle_fields_with_cleanup(bundle: object) -> set[str]:
    """Return dataclass field names whose current values expose cleanup()."""
    names: set[str] = set()
    for f in fields(bundle):  # type: ignore[arg-type]
        obj = getattr(bundle, f.name, None)
        if obj is not None and callable(getattr(obj, "cleanup", None)):
            names.add(f.name)
    return names


@dataclass
class ControllerBundle:
    """All controllers and handlers created by the factory.

    Cleanup-bearing hardware/services are torn down via ``_CLEANUP_ORDER``.
    Policy shells (*Actions, gate, selection_model) have no cleanup by design.
    """

    # Independent
    warning_handler: WarningHandler
    system_monitor: SystemMonitor

    # ROS2 controllers
    wheel_controller: WheelController
    esp32_valve_controller: ESP32ValveController
    lidar_controller: LidarController
    wind_monitor: WindMonitor
    winch_controller: WinchController
    teensy_controller: TeensyController
    heartbeat_handler: UIHeartbeatHandler
    safety_coordinator: SafetyCoordinator

    # Cross-controller handlers
    selection_model: JoystickSelectionModel
    overlay_controller: OverlayController
    control_processor: ControlProcessor
    admin_action_gate: AdminActionGate
    manual_command_handler: ManualCommandHandler
    recording_actions: RecordingActions
    teensy_actions: TeensyActions
    system_actions: SystemActions
    wheel_actions: WheelActions
    winch_actions: WinchActions
    tuning_actions: TuningActions
    base_top_view_actions: BaseTopViewActions
    input_handler: UIInputHandler
    emergency_handler: EmergencyButtonHandler

    # Services
    ssh_controller: UISSHController
    screen_manager: ScreenManager
    screen_recorder: ScreenRecorder
    ros_bag_recorder: RosBagRecorder
    workflow_catalog: WorkflowCatalog
    workflow_editor: WorkflowEditor
    workflow_runner: WorkFlowRunner

    def cleanup(self, logger: Any = None) -> None:
        """Cleanup cleanup-bearing members; order from ``_CLEANUP_ORDER`` then leftovers."""
        known = set(_CLEANUP_ORDER)
        ordered = [n for n in _CLEANUP_ORDER if getattr(self, n, None) is not None]
        leftovers = sorted(_bundle_fields_with_cleanup(self) - known)
        if leftovers and logger is not None:
            logger.warning(
                "ControllerBundle cleanup found unlisted cleanup() fields: %s — update _CLEANUP_ORDER",
                leftovers,
            )
        for name in ordered + leftovers:
            ctrl = getattr(self, name, None)
            cleanup_fn = getattr(ctrl, "cleanup", None) if ctrl is not None else None
            if not callable(cleanup_fn):
                continue
            try:
                cleanup_fn()
            except Exception as e:
                if logger:
                    logger.error(f"Error cleaning up {name}: {e}")


# TD-055.10: decision rule for new QObjects
# - Device adapters, control-plane handlers, *Actions, workflow services → factory (this module)
# - Shell policy (ShellState/Router/OverlayHost) and ActionLegalityModel → AppRuntime after factory
# - QML façades → QmlContextComposer


def _build_device_adapters(
    node: Any,
    settings_manager: Any,
    state_store: Any,
    logger: Any,
    command_bus: Any = None,
) -> dict[str, Any]:
    """Device I/O adapters + safety/heartbeat (no presentation)."""
    # TD-054: command_bus binds ROS command pubs (sole raw publish on RosThread.pump).
    wheel = WheelController(node, command_bus=command_bus)
    esp32_valve = ESP32ValveController(node)
    lidar = LidarController(node)
    wind_monitor = WindMonitor(node)
    winch = WinchController(node, settings_manager=settings_manager, command_bus=command_bus)
    teensy = TeensyController(node, settings_manager=settings_manager, command_bus=command_bus)
    safety_coordinator = SafetyCoordinator(
        winch=winch,
        teensy=teensy,
        wheel=wheel,
        esp32_valve=esp32_valve,
        state_store=state_store,
        logger=logger,
        command_bus=command_bus,
    )
    heartbeat = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=safety_coordinator)
    return {
        "wheel": wheel,
        "esp32_valve": esp32_valve,
        "lidar": lidar,
        "wind_monitor": wind_monitor,
        "winch": winch,
        "teensy": teensy,
        "safety_coordinator": safety_coordinator,
        "heartbeat": heartbeat,
    }


def _build_control_plane(
    devices: dict[str, Any],
    *,
    settings_manager: Any,
    capability_catalog: Any,
    state_store: Any,
    steam_deck_handler: SteamDeckHandler,
    show_popup_fn: Any,
    close_popup_fn: Any,
    logger: Any,
) -> dict[str, Any]:
    """Selection, teleop, input, emergency, admin gate, manual commands."""
    selection_model = JoystickSelectionModel()
    overlay = OverlayController(selection_model=selection_model)
    control_processor = ControlProcessor(
        wheel=devices["wheel"],
        winch=devices["winch"],
        teensy=devices["teensy"],
        esp32_valve=devices["esp32_valve"],
        selection_model=selection_model,
        heartbeat_handler=devices["heartbeat"],
        settings_manager=settings_manager,
        state_store=state_store,
        safety_coordinator=devices["safety_coordinator"],
    )
    admin_action_gate = AdminActionGate(
        capability_catalog=capability_catalog,
        state_store=state_store,
        settings_manager=settings_manager,
    )
    manual_command_handler = ManualCommandHandler(
        teensy=devices["teensy"],
        winch=devices["winch"],
        logger=logger,
    )
    input_handler = UIInputHandler(
        teensy=devices["teensy"],
        overlay=overlay,
        selection_model=selection_model,
        control_processor=control_processor,
        settings_manager=settings_manager,
        state_store=state_store,
        show_popup_fn=show_popup_fn,
        close_popup_fn=close_popup_fn,
    )
    emergency = EmergencyButtonHandler(
        steam_deck_handler=steam_deck_handler,
        winch=devices["winch"],
        teensy=devices["teensy"],
        wheel=devices["wheel"],
        show_popup_fn=show_popup_fn,
        logger=logger,
        settings_manager=settings_manager,
        state_store=state_store,
        safety_coordinator=devices["safety_coordinator"],
        esp32_valve=devices["esp32_valve"],
    )
    return {
        "selection_model": selection_model,
        "overlay": overlay,
        "control_processor": control_processor,
        "admin_action_gate": admin_action_gate,
        "manual_command_handler": manual_command_handler,
        "input_handler": input_handler,
        "emergency": emergency,
    }


def _build_presentation_actions(
    devices: dict[str, Any],
    control: dict[str, Any],
    *,
    video_stream_handler: Any,
    base_top_view_service: Any,
    screen_rec: ScreenRecorder,
    ros_bag: RosBagRecorder,
    logger: Any,
) -> dict[str, Any]:
    """QML feature-root *Actions (presentation command boundary)."""
    gate = control["admin_action_gate"]
    return {
        "recording_actions": RecordingActions(
            video_stream_handler=video_stream_handler,
            screen_recorder=screen_rec,
            ros_bag_recorder=ros_bag,
            logger=logger,
        ),
        "teensy_actions": TeensyActions(
            teensy=devices["teensy"], logger=logger, admin_action_gate=gate
        ),
        "system_actions": SystemActions(heartbeat_handler=devices["heartbeat"], logger=logger),
        "wheel_actions": WheelActions(
            wheel=devices["wheel"], admin_action_gate=gate, logger=logger
        ),
        "winch_actions": WinchActions(
            winch=devices["winch"], admin_action_gate=gate, logger=logger
        ),
        "tuning_actions": TuningActions(
            teensy=devices["teensy"], admin_action_gate=gate, logger=logger
        ),
        "base_top_view_actions": BaseTopViewActions(
            base_top_view_service=base_top_view_service,
            admin_action_gate=gate,
            logger=logger,
        ),
    }


def _build_workflow_and_services(
    node: Any,
    devices: dict[str, Any],
    *,
    show_popup_fn: Any,
    logger: Any,
) -> dict[str, Any]:
    """Workflow runtime + screen/SSH/recording services."""
    hardware = HardwareControllers.from_controllers(
        devices["teensy"], devices["winch"], devices["esp32_valve"]
    )
    workflow_catalog = WorkflowCatalog(logger=logger)
    workflow_editor = WorkflowEditor(catalog=workflow_catalog, logger=logger)
    workflow_runner = WorkFlowRunner(node, hardware, logger=logger, catalog=workflow_catalog)
    workflow_editor.attach_runtime(workflow_runner)
    ssh = UISSHController(show_popup_fn=show_popup_fn)
    screen_mgr = ScreenManager(node=node)
    screen_rec = ScreenRecorder(screen_manager=screen_mgr)
    ros_bag = RosBagRecorder(show_popup_fn=show_popup_fn)
    return {
        "hardware": hardware,
        "workflow_catalog": workflow_catalog,
        "workflow_editor": workflow_editor,
        "workflow_runner": workflow_runner,
        "ssh": ssh,
        "screen_mgr": screen_mgr,
        "screen_rec": screen_rec,
        "ros_bag": ros_bag,
    }


def create_controllers(
    node: Any,
    settings_manager: Any,
    capability_catalog: Any,
    state_store: Any,
    steam_deck_handler: SteamDeckHandler,
    video_stream_handler: Any,
    base_top_view_service: Any,
    show_popup_fn: Any,
    close_popup_fn: Any,
    command_bus: Any = None,
) -> ControllerBundle:
    """Compose runtime graph from subsystem builders (TD-055 Phase 10)."""
    logger = node.get_logger()

    warning_handler = WarningHandler()
    system_monitor = SystemMonitor()

    devices = _build_device_adapters(
        node, settings_manager, state_store, logger, command_bus=command_bus
    )
    control = _build_control_plane(
        devices,
        settings_manager=settings_manager,
        capability_catalog=capability_catalog,
        state_store=state_store,
        steam_deck_handler=steam_deck_handler,
        show_popup_fn=show_popup_fn,
        close_popup_fn=close_popup_fn,
        logger=logger,
    )

    services = _build_workflow_and_services(
        node, devices, show_popup_fn=show_popup_fn, logger=logger
    )
    # Late bind: coordinator exists before runner; halt must stop execution without join.
    safety = devices["safety_coordinator"]
    runner = services["workflow_runner"]
    bind_stop = getattr(safety, "bind_execution_stop", None)
    if callable(bind_stop):
        bind_stop(runner)
    bind_gate = getattr(runner, "bind_motion_gate", None)
    if callable(bind_gate):
        bind_gate(lambda: safety.continuous_motion_allowed)

    actions = _build_presentation_actions(
        devices,
        control,
        video_stream_handler=video_stream_handler,
        base_top_view_service=base_top_view_service,
        screen_rec=services["screen_rec"],
        ros_bag=services["ros_bag"],
        logger=logger,
    )

    logger.info("All controllers created with explicit DI")

    return ControllerBundle(
        warning_handler=warning_handler,
        system_monitor=system_monitor,
        wheel_controller=devices["wheel"],
        esp32_valve_controller=devices["esp32_valve"],
        lidar_controller=devices["lidar"],
        wind_monitor=devices["wind_monitor"],
        winch_controller=devices["winch"],
        teensy_controller=devices["teensy"],
        heartbeat_handler=devices["heartbeat"],
        safety_coordinator=devices["safety_coordinator"],
        selection_model=control["selection_model"],
        overlay_controller=control["overlay"],
        control_processor=control["control_processor"],
        admin_action_gate=control["admin_action_gate"],
        manual_command_handler=control["manual_command_handler"],
        recording_actions=actions["recording_actions"],
        teensy_actions=actions["teensy_actions"],
        system_actions=actions["system_actions"],
        wheel_actions=actions["wheel_actions"],
        winch_actions=actions["winch_actions"],
        tuning_actions=actions["tuning_actions"],
        base_top_view_actions=actions["base_top_view_actions"],
        input_handler=control["input_handler"],
        emergency_handler=control["emergency"],
        ssh_controller=services["ssh"],
        screen_manager=services["screen_mgr"],
        screen_recorder=services["screen_rec"],
        ros_bag_recorder=services["ros_bag"],
        workflow_catalog=services["workflow_catalog"],
        workflow_editor=services["workflow_editor"],
        workflow_runner=services["workflow_runner"],
    )
