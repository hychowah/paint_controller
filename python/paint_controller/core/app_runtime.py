"""Application runtime orchestration for the paint controller."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from typing import Any

import rclpy
from PySide6.QtCore import QCoreApplication, QEvent, QTimer, QUrl, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from paint_controller.core.config import RuntimeDefaults
from paint_controller.core.ros_node import RosThread
from paint_controller.core.settings import SettingsManager
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.services.base_top_view_service import BaseTopViewService
from paint_controller.services.video_stream import VideoStreamHandler
from paint_controller.utils.qt_env import ensure_pyside6_windows_dll_path

logger = logging.getLogger(__name__)

_EXPECTED_CONTEXT_PROPERTY_NAMES = (
    "stateStore",
    "backend",
    "shellState",
    "overlayController",
    "workFlowRunner",
    "warningHandler",
    "baseStreamHandler",
    "wheelController",
    "winchController",
    "steamDeckHandler",
    "windMonitor",
    "teensyController",
    "esp32ValveController",
    "lidarController",
    "heartbeatHandler",
    "controlProcessor",
    "manualCommandHandler",
    "deviceActionHandler",
    "deviceOperationsHandler",
    "sshHandler",
    "systemMonitor",
    "screenRecorder",
    "rosBagRecorder",
    "workflowEditor",
    "settingsManager",
    "screenManager",
    "baseTopViewController",
)


def teardown_qml_runtime(
    engine: QQmlApplicationEngine,
    app: QApplication,
    log_shutdown,
) -> None:
    """Destroy QML root objects before backend QObject cleanup begins."""
    try:
        root_objects = list(engine.rootObjects())

        for root in root_objects:
            try:
                close = getattr(root, "close", None)
                if callable(close):
                    close()
            except Exception as exc:
                logger.debug("Error closing QML root object: %s", exc)

        for root in root_objects:
            try:
                root.deleteLater()
            except Exception as exc:
                logger.debug("Error deleting QML root object: %s", exc)

        engine.clearComponentCache()
        engine.deleteLater()

        for _ in range(5):
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            app.processEvents()

        log_shutdown(f"QML runtime torn down ({len(root_objects)} root object(s))")
    except Exception as exc:
        logger.error("Error tearing down QML runtime: %s", exc)


class AppRuntime:
    """Own startup wiring, event-loop execution, and shutdown sequencing."""

    def __init__(self, argv: list[str], on_app_created: Callable[[QApplication], None] | None = None):
        self.argv = list(argv)
        self._on_app_created = on_app_created
        self.config = RuntimeDefaults()
        self._startup_t0 = time.perf_counter()
        self._shutdown_started = False
        self._context_properties: dict[str, object] = {}
        self._heartbeat_status_error = None

        self.app: QApplication | None = None
        self.state_store = None
        self.node = None
        self.settings_manager: SettingsManager | None = None
        self.steam_deck_handler: SteamDeckHandler | None = None
        self.video_stream_handler: VideoStreamHandler | None = None
        self.base_top_view_service: BaseTopViewService | None = None
        self.ros_thread: RosThread | None = None
        self.engine: QQmlApplicationEngine | None = None
        self.qt_bridge = None
        self.bundle = None
        self.shell_state = None
        self.status_timer: QTimer | None = None
        self.qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qml')

        try:
            self._bootstrap()
        except Exception:
            self.shutdown()
            raise

    def _log_startup(self, stage: str) -> None:
        elapsed_ms = (time.perf_counter() - self._startup_t0) * 1000.0
        logger.warning("[startup +%7.1f ms] %s", elapsed_ms, stage)

    def _bootstrap(self) -> None:
        rclpy.init()
        self._log_startup("ROS initialized")
        self._log_startup("Runtime defaults loaded")

        ensure_pyside6_windows_dll_path()

        self.app = QApplication(self.argv)
        if self._on_app_created is not None:
            self._on_app_created(self.app)
        self._log_startup("QApplication created")

        self._setup_core_objects()
        self._setup_video_services()

        assert self.steam_deck_handler is not None
        self.steam_deck_handler.start()
        self._log_startup("Steam Deck handler started")

        assert self.node is not None
        self.ros_thread = RosThread(self.node)
        self.ros_thread.start()
        self._log_startup("ROS thread started")

        self._setup_qml_engine()
        self._create_controller_bundle()
        self._wire_steam_deck_callbacks()
        self._wire_signals()
        self._register_context_properties()
        self._load_qml()
        self._start_timers()

    def _setup_core_objects(self) -> None:
        from paint_controller.core.ros_node import PaintRosNode
        from paint_controller.core.state_store import StateStore

        self.state_store = StateStore()
        self.node = PaintRosNode(state_store=self.state_store)
        self._log_startup("PaintRosNode created")

        self.settings_manager = SettingsManager(show_popup_fn=None)
        self.steam_deck_handler = SteamDeckHandler(deadzone=self.config.joystick_deadzone)
        self._log_startup("Core state/services created")

    def _setup_video_services(self) -> None:
        assert self.node is not None
        assert self.settings_manager is not None

        self.video_stream_handler = VideoStreamHandler(self.config.video_port, ros_node=self.node)
        self.base_top_view_service = BaseTopViewService(
            self.video_stream_handler,
            settings_manager=self.settings_manager,
        )
        self._log_startup("Video and camera services created")

    def _setup_qml_engine(self) -> None:
        from paint_controller.core.qt_bridge import QtBridge

        assert self.node is not None
        assert self.state_store is not None
        assert self.video_stream_handler is not None
        assert self.base_top_view_service is not None

        self.engine = QQmlApplicationEngine()
        self.engine.addImageProvider("ef_live", self.video_stream_handler.ef_image_provider)
        self.engine.addImageProvider("base_front_live", self.video_stream_handler.front_image_provider)
        self.engine.addImageProvider("base_rear_live", self.video_stream_handler.rear_image_provider)
        self.engine.addImageProvider("base_top_view", self.base_top_view_service.image_provider)
        self._log_startup("QML engine and image providers ready")

        self.engine.addImportPath(self.qml_dir)
        self.qt_bridge = QtBridge(self.engine, self.state_store, logger=self.node.get_logger())
        self._log_startup("Qt bridge created")

        assert self.settings_manager is not None
        self.settings_manager._show_popup_fn = self.qt_bridge.show_popup

    def _create_controller_bundle(self) -> None:
        from paint_controller.core.controller_factory import create_controllers
        from paint_controller.models.shell_state import ShellState

        assert self.node is not None
        assert self.settings_manager is not None
        assert self.state_store is not None
        assert self.steam_deck_handler is not None
        assert self.qt_bridge is not None
        assert self.base_top_view_service is not None

        self.bundle = create_controllers(
            node=self.node,
            settings_manager=self.settings_manager,
            state_store=self.state_store,
            steam_deck_handler=self.steam_deck_handler,
            video_stream_handler=self.video_stream_handler,
            show_popup_fn=self.qt_bridge.show_popup,
            close_popup_fn=self.qt_bridge.close_popup,
        )
        self._log_startup("Controller bundle created")

        self.qt_bridge.set_base_top_view_service(self.base_top_view_service)
        self.qt_bridge.set_input_handler(self.bundle.input_handler)
        self.shell_state = ShellState(screen_manager=self.bundle.screen_manager)

    def _wire_steam_deck_callbacks(self) -> None:
        assert self.bundle is not None
        assert self.steam_deck_handler is not None
        assert self.qt_bridge is not None

        input_handler = self.bundle.input_handler
        self.steam_deck_handler.register_button_callback('up', input_handler.on_up_pressed)
        self.steam_deck_handler.register_button_callback('down', input_handler.on_down_pressed)
        self.steam_deck_handler.register_button_callback('left', input_handler.on_left_pressed)
        self.steam_deck_handler.register_button_callback('right', input_handler.on_right_pressed)
        self.steam_deck_handler.register_button_callback('r4', input_handler.on_r4_pressed)
        self.steam_deck_handler.register_button_callback('l4', input_handler.on_l4_pressed)
        self.steam_deck_handler.register_button_callback('menu', input_handler.on_menu_pressed)
        self.steam_deck_handler.register_button_callback('switch', input_handler.on_switch_pressed)
        self.steam_deck_handler.register_button_callback('l5', input_handler.on_l5_pressed)
        self.steam_deck_handler.register_button_callback('r5', input_handler.on_r5_pressed)
        self.steam_deck_handler.register_button_callback('dot', self.qt_bridge.toggle_fullscreen)
        self.steam_deck_handler.register_button_callback('a', self.qt_bridge.toggle_lidar_overlay)
        self.steam_deck_handler.register_button_callback('l1', input_handler.on_l1_pressed)

    def _wire_signals(self) -> None:
        from paint_controller.utils.constants import HeartbeatStatus

        assert self.bundle is not None
        assert self.node is not None
        assert self.qt_bridge is not None
        assert self.state_store is not None
        assert self.video_stream_handler is not None
        assert self.steam_deck_handler is not None

        self._heartbeat_status_error = HeartbeatStatus.ERROR
        self.state_store.control_mode_changed.connect(self.qt_bridge.update_fullscreen_video_source)
        self.bundle.emergency_handler.overlay_changed.connect(self.qt_bridge.emergency_overlay_changed.emit)
        self.bundle.emergency_handler.emergency_triggered.connect(self.qt_bridge.emergency_triggered.emit)
        self.video_stream_handler.endEffectorFrameReady.connect(self.qt_bridge.frame_ready.emit)
        self.bundle.wheel_controller.error_state_changed.connect(
            self._on_wheel_motor_error,
            Qt.QueuedConnection,
        )
        self.qt_bridge.status_updated.connect(self._on_status_tick)

    def _on_wheel_motor_error(self, has_error, error_message) -> None:
        if not has_error:
            return

        assert self.bundle is not None
        assert self.node is not None
        assert self.qt_bridge is not None

        self.node.get_logger().error(f'Wheel motor error detected: {error_message}')
        self.bundle.safety_coordinator.halt_all_effectors(
            f"Wheel motor error detected: {error_message}",
            heartbeat_state=self._heartbeat_status_error,
        )
        self.qt_bridge.show_popup("MOTOR ERROR", error_message, "error", 5000)
        self.qt_bridge.emergency_triggered.emit()

    def _on_status_tick(self) -> None:
        assert self.bundle is not None
        assert self.steam_deck_handler is not None

        input_state = self.steam_deck_handler.get_current_state()
        self.bundle.control_processor.process_input(input_state)
        self.bundle.emergency_handler.check_emergency_button(input_state.get('buttons', {}))

    def _build_context_properties(self) -> dict[str, object]:
        assert self.bundle is not None
        assert self.state_store is not None
        assert self.qt_bridge is not None
        assert self.shell_state is not None
        assert self.video_stream_handler is not None
        assert self.steam_deck_handler is not None
        assert self.settings_manager is not None
        assert self.base_top_view_service is not None

        return {
            "stateStore": self.state_store,
            "backend": self.qt_bridge,
            "shellState": self.shell_state,
            "overlayController": self.bundle.overlay_controller,
            "workFlowRunner": self.bundle.workflow_runner,
            "warningHandler": self.bundle.warning_handler,
            "baseStreamHandler": self.video_stream_handler,
            "wheelController": self.bundle.wheel_controller,
            "winchController": self.bundle.winch_controller,
            "steamDeckHandler": self.steam_deck_handler,
            "windMonitor": self.bundle.wind_monitor,
            "teensyController": self.bundle.teensy_controller,
            "esp32ValveController": self.bundle.esp32_valve_controller,
            "lidarController": self.bundle.lidar_controller,
            "heartbeatHandler": self.bundle.heartbeat_handler,
            "controlProcessor": self.bundle.control_processor,
            "manualCommandHandler": self.bundle.manual_command_handler,
            "deviceActionHandler": self.bundle.device_action_handler,
            "deviceOperationsHandler": self.bundle.device_operations_handler,
            "sshHandler": self.bundle.ssh_controller,
            "systemMonitor": self.bundle.system_monitor,
            "screenRecorder": self.bundle.screen_recorder,
            "rosBagRecorder": self.bundle.ros_bag_recorder,
            "workflowEditor": self.bundle.workflow_editor,
            "settingsManager": self.settings_manager,
            "screenManager": self.bundle.screen_manager,
            "baseTopViewController": self.base_top_view_service,
        }

    def _register_context_properties(self) -> None:
        assert self.engine is not None
        assert self.node is not None

        context = self.engine.rootContext()
        self._context_properties = self._build_context_properties()
        expected_names = set(_EXPECTED_CONTEXT_PROPERTY_NAMES)
        actual_names = set(self._context_properties)

        missing_names = sorted(expected_names - actual_names)
        unexpected_names = sorted(actual_names - expected_names)
        if missing_names or unexpected_names:
            self.node.get_logger().error(
                f"Context-property contract mismatch. Missing: {missing_names}; unexpected: {unexpected_names}"
            )

        for name, obj in self._context_properties.items():
            context.setContextProperty(name, obj)

    def _load_qml(self) -> None:
        assert self.engine is not None
        assert self.node is not None

        qml_path = os.path.join(self.qml_dir, 'core', 'MainWindow.qml')
        self.engine.load(QUrl.fromLocalFile(qml_path))
        if not self.engine.rootObjects():
            raise RuntimeError(f"Failed to load QML root: {qml_path}")
        self._log_startup("MainWindow QML loaded")

        context = self.engine.rootContext()
        for name in _EXPECTED_CONTEXT_PROPERTY_NAMES:
            if context.contextProperty(name) is None:
                self.node.get_logger().error(f"Missing QML context property: {name}")

    def _start_timers(self) -> None:
        assert self.bundle is not None
        assert self.qt_bridge is not None

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.qt_bridge.status_updated.emit)
        self.status_timer.start(int(1000 / self.config.update_rate))
        self._log_startup("Status timer started")

        self.bundle.system_monitor.start_monitoring(interval_ms=1000)
        self._log_startup("System monitoring started")

        QTimer.singleShot(200, self._deferred_video_startup)
        self._log_startup("Deferred video startup scheduled")

    def _deferred_video_startup(self) -> None:
        assert self.video_stream_handler is not None

        self._log_startup("Deferred video startup begin")
        started_count = self.video_stream_handler.start_all_streams()
        self._log_startup(f"Deferred video startup end: started {started_count} stream(s)")

    def exec(self) -> int:
        assert self.app is not None
        self._log_startup("Entering Qt event loop")
        return self.app.exec()

    def shutdown(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True

        shutdown_t0 = time.perf_counter()

        def log_shutdown(stage: str) -> None:
            elapsed_ms = (time.perf_counter() - shutdown_t0) * 1000.0
            logger.warning("[shutdown +%7.1f ms] %s", elapsed_ms, stage)

        logger.info("Starting emergency shutdown sequence...")
        log_shutdown("Shutdown sequence started")

        try:
            if self.status_timer is not None:
                self.status_timer.stop()
            log_shutdown("Qt timers stopped")
        except Exception as error:
            logger.error("Error stopping timers: %s", error)

        if self.engine is not None and self.app is not None:
            teardown_qml_runtime(self.engine, self.app, log_shutdown)
            self.engine = None

        try:
            if self.ros_thread is not None:
                self.ros_thread.request_shutdown()
                if not self.ros_thread.wait(2000):
                    logger.warning("ROS thread did not exit cleanly, forcing termination...")
                    self.ros_thread.terminate()
                    self.ros_thread.wait(500)
            log_shutdown("ROS thread stopped")
        except Exception as error:
            logger.error("Error shutting down ROS thread: %s", error)

        try:
            if self.bundle is not None and self.node is not None:
                self.bundle.cleanup(self.node.get_logger())
                log_shutdown("Controller bundle cleaned up")
            if self.base_top_view_service is not None:
                self.base_top_view_service.cleanup()
                log_shutdown("Base top view service cleaned up")
            if self.video_stream_handler is not None:
                self.video_stream_handler.cleanup()
                log_shutdown("Video stream handler cleaned up")
            if self.steam_deck_handler is not None:
                self.steam_deck_handler.cleanup()
                log_shutdown("Steam Deck handler cleaned up")
        except Exception as error:
            logger.error("Error during cleanup: %s", error)

        try:
            if self.node is not None:
                self.node.cleanup()
                self.node.destroy_node()
                log_shutdown("ROS node cleaned up and destroyed")
        except Exception as error:
            logger.error("Error during ROS node cleanup: %s", error)

        try:
            if rclpy.ok():
                rclpy.shutdown()
            log_shutdown("ROS context shutdown complete")
        except Exception as error:
            logger.error("Error during ROS shutdown: %s", error)

        logger.info("Emergency shutdown sequence complete")
