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
from paint_controller.handlers.safety_coordinator import SafetyCoordinator
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.handlers.warnings import WarningHandler
from paint_controller.services.ros_bag_recorder import RosBagRecorder
from paint_controller.services.screen_manager import ScreenManager
from paint_controller.services.screen_recorder import ScreenRecorder
from paint_controller.services.workflow.hardware import HardwareControllers
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
    input_handler: UIInputHandler
    emergency_handler: EmergencyButtonHandler

    # Services
    ssh_controller: UISSHController
    screen_manager: ScreenManager
    screen_recorder: ScreenRecorder
    ros_bag_recorder: RosBagRecorder
    workflow_runner: WorkFlowRunner

    def cleanup(self, logger: Any = None) -> None:
        """Cleanup all controllers in reverse creation order."""
        cleanup_order = [
            'workflow_runner',
            'ros_bag_recorder', 'screen_recorder', 'screen_manager',
            'ssh_controller',
            'emergency_handler', 'input_handler',
            'control_processor', 'overlay_controller',
            'heartbeat_handler',
            'teensy_controller', 'winch_controller',
            'wind_monitor', 'lidar_controller',
            'esp32_valve_controller', 'wheel_controller',
            'system_monitor',
        ]
        for name in cleanup_order:
            ctrl = getattr(self, name, None)
            if ctrl and hasattr(ctrl, 'cleanup'):
                try:
                    ctrl.cleanup()
                except Exception as e:
                    if logger:
                        logger.error(f'Error cleaning up {name}: {e}')


def create_controllers(
    node: Any,
    settings_manager: Any,
    state_store: Any,
    steam_deck_handler: SteamDeckHandler,
    show_popup_fn: Any,
    close_popup_fn: Any,
    config: Any,
) -> ControllerBundle:
    """
    Create all controllers with explicit dependency injection.

    Args:
        node: PaintRosNode instance (ROS2 node for pub/sub)
        settings_manager: SettingsManager instance
        state_store: StateStore instance (shared mutable state)
        steam_deck_handler: SteamDeckHandler instance
        show_popup_fn: Callable for showing UI popups (QtBridge.show_popup)
        config: RobotConfig with hardware configuration

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
    teensy = TeensyController(node, settings_manager=settings_manager, winch_controller=winch, show_popup_fn=show_popup_fn)
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
    # OverlayController and ControlProcessor have a circular dependency:
    #   Overlay reads control_processor for selected option dispatch
    #   ControlProcessor reads overlay for get_left/right_selected_option
    # Resolve by creating overlay first, wiring control_processor after.
    overlay = OverlayController(teensy=teensy)

    control_processor = ControlProcessor(
        wheel=wheel,
        winch=winch,
        teensy=teensy,
        esp32_valve=esp32_valve,
        overlay=overlay,
        heartbeat_handler=heartbeat,
        settings_manager=settings_manager,
        state_store=state_store,
    )
    cast(Any, overlay).set_control_processor(control_processor)

    hardware = cast(Any, HardwareControllers).from_controllers(teensy, winch, esp32_valve)
    workflow_runner = WorkFlowRunner(node, hardware)

    input_handler = UIInputHandler(
        teensy=teensy,
        overlay=overlay,
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

    logger.info('All controllers created with explicit DI')

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
        input_handler=input_handler,
        emergency_handler=emergency,
        ssh_controller=ssh,
        screen_manager=screen_mgr,
        screen_recorder=screen_rec,
        ros_bag_recorder=ros_bag,
        workflow_runner=workflow_runner,
    )
