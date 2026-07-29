"""Factory for creating all controllers with explicit dependency injection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

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


@dataclass
class ControllerBundle:
    """All controllers and handlers created by the factory."""

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
        """Cleanup all controllers in reverse creation order."""
        cleanup_order = [
            "workflow_editor",
            "workflow_runner",
            "workflow_catalog",
            "ros_bag_recorder",
            "screen_recorder",
            "screen_manager",
            "ssh_controller",
            "emergency_handler",
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
        for name in cleanup_order:
            ctrl = getattr(self, name, None)
            if ctrl and hasattr(ctrl, "cleanup"):
                try:
                    ctrl.cleanup()
                except Exception as e:
                    if logger:
                        logger.error(f"Error cleaning up {name}: {e}")


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
) -> ControllerBundle:
    """
    Create all controllers with explicit dependency injection.

    Args:
        node: PaintRosNode instance (ROS2 node for pub/sub)
        settings_manager: SettingsManager instance
        state_store: StateStore instance (shared mutable state)
        steam_deck_handler: SteamDeckHandler instance
        show_popup_fn: Callable for showing UI popups (QtBridge.show_popup)

    Returns:
        ControllerBundle with all controllers wired together
    """
    logger = node.get_logger()

    # === Layer 1: Independent controllers ===
    warning_handler = WarningHandler()
    system_monitor = SystemMonitor()

    # === Layer 2: ROS2-only controllers (need node for pub/sub) ===
    wheel = WheelController(node)
    esp32_valve = ESP32ValveController(node)
    lidar = LidarController(node)
    wind_monitor = WindMonitor(node)

    # === Layer 3: ROS2 + settings controllers ===
    winch = WinchController(node, settings_manager=settings_manager)
    teensy = TeensyController(
        node, settings_manager=settings_manager, winch_controller=winch, show_popup_fn=show_popup_fn
    )
    safety_coordinator = SafetyCoordinator(
        winch=winch,
        teensy=teensy,
        wheel=wheel,
        esp32_valve=esp32_valve,
        state_store=state_store,
        logger=logger,
    )
    heartbeat = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=safety_coordinator)

    # === Layer 4: Cross-controller handlers ===
    selection_model = JoystickSelectionModel()
    overlay = OverlayController(selection_model=selection_model)

    control_processor = ControlProcessor(
        wheel=wheel,
        winch=winch,
        teensy=teensy,
        esp32_valve=esp32_valve,
        selection_model=selection_model,
        heartbeat_handler=heartbeat,
        settings_manager=settings_manager,
        state_store=state_store,
    )

    admin_action_gate = AdminActionGate(
        capability_catalog=capability_catalog,
        state_store=state_store,
        settings_manager=settings_manager,
    )

    manual_command_handler = ManualCommandHandler(
        teensy=teensy,
        winch=winch,
        logger=logger,
    )

    hardware = cast(Any, HardwareControllers).from_controllers(teensy, winch, esp32_valve)
    workflow_catalog = WorkflowCatalog(logger=logger)
    workflow_editor = WorkflowEditor(catalog=workflow_catalog, logger=logger)
    workflow_runner = WorkFlowRunner(node, hardware, logger=logger, catalog=workflow_catalog)
    if hasattr(workflow_editor, "attach_runtime"):
        workflow_editor.attach_runtime(workflow_runner)

    input_handler = UIInputHandler(
        teensy=teensy,
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
        winch=winch,
        teensy=teensy,
        wheel=wheel,
        show_popup_fn=show_popup_fn,
        logger=logger,
        settings_manager=settings_manager,
        state_store=state_store,
        safety_coordinator=safety_coordinator,
        esp32_valve=esp32_valve,
    )

    # === Layer 5: Services ===
    ssh = UISSHController(show_popup_fn=show_popup_fn)
    screen_mgr = ScreenManager(node=node)
    screen_rec = ScreenRecorder(screen_manager=screen_mgr)
    ros_bag = RosBagRecorder(show_popup_fn=show_popup_fn)

    recording_actions = RecordingActions(
        video_stream_handler=video_stream_handler,
        screen_recorder=screen_rec,
        ros_bag_recorder=ros_bag,
        logger=logger,
    )

    teensy_actions = TeensyActions(
        teensy=teensy,
        logger=logger,
        admin_action_gate=admin_action_gate,
    )

    system_actions = SystemActions(
        heartbeat_handler=heartbeat,
        logger=logger,
    )

    wheel_actions = WheelActions(
        wheel=wheel,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )

    winch_actions = WinchActions(
        winch=winch,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )

    tuning_actions = TuningActions(
        teensy=teensy,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )

    base_top_view_actions = BaseTopViewActions(
        base_top_view_service=base_top_view_service,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )

    logger.info("All controllers created with explicit DI")

    return ControllerBundle(
        warning_handler=warning_handler,
        system_monitor=system_monitor,
        wheel_controller=wheel,
        esp32_valve_controller=esp32_valve,
        lidar_controller=lidar,
        wind_monitor=wind_monitor,
        winch_controller=winch,
        teensy_controller=teensy,
        heartbeat_handler=heartbeat,
        safety_coordinator=safety_coordinator,
        overlay_controller=overlay,
        control_processor=control_processor,
        admin_action_gate=admin_action_gate,
        manual_command_handler=manual_command_handler,
        recording_actions=recording_actions,
        teensy_actions=teensy_actions,
        system_actions=system_actions,
        wheel_actions=wheel_actions,
        winch_actions=winch_actions,
        tuning_actions=tuning_actions,
        base_top_view_actions=base_top_view_actions,
        input_handler=input_handler,
        emergency_handler=emergency,
        ssh_controller=ssh,
        screen_manager=screen_mgr,
        screen_recorder=screen_rec,
        ros_bag_recorder=ros_bag,
        workflow_catalog=workflow_catalog,
        workflow_editor=workflow_editor,
        workflow_runner=workflow_runner,
    )
