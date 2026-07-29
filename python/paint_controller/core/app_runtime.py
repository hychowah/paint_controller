"""Application runtime orchestration for the paint controller."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable

import rclpy
from PySide6.QtCore import QCoreApplication, QEvent, QTimer, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from paint_controller.core import qml_context_composer
from paint_controller.core.config import RuntimeDefaults
from paint_controller.core.qml_context_composer import QmlComposePorts, QmlContextComposer
from paint_controller.core.ros_node import RosThread
from paint_controller.core.settings import SettingsManager
from paint_controller.core.signal_wiring import SignalWiring, SignalWiringPorts
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.models.action_legality_model import ActionLegalityModel
from paint_controller.models.capability_catalog import CapabilityCatalog
from paint_controller.models.shell_router import ShellRouter
from paint_controller.services.base_top_view_service import BaseTopViewService
from paint_controller.services.video_stream import VideoStreamHandler
from paint_controller.utils.qt_env import ensure_pyside6_windows_dll_path

logger = logging.getLogger(__name__)


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
        # Sole home for QML façades after compose (TD-047): do not mirror context
        # keys back onto self.* — consumers use this map, ControllerBundle, or shell.
        self._context_properties: dict[str, object] = {}

        self.app: QApplication | None = None
        self.state_store = None
        self.node = None
        self.settings_manager: SettingsManager | None = None
        self.capability_catalog: CapabilityCatalog | None = None
        self.steam_deck_handler: SteamDeckHandler | None = None
        self.video_stream_handler: VideoStreamHandler | None = None
        self.base_top_view_service: BaseTopViewService | None = None
        self.ros_thread: RosThread | None = None
        self.engine: QQmlApplicationEngine | None = None
        self.qt_bridge = None
        self.bundle = None
        # Shell / policy created on the composition root (not context mirrors).
        self.shell_state = None
        self.shell_router: ShellRouter | None = None
        self.overlay_host = None
        self.action_legality = None
        self.status_timer: QTimer | None = None
        self.qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qml")

        self._composer: QmlContextComposer | None = None
        self._signal_wiring: SignalWiring | None = None

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
        self._activate_default_video_overlay()
        # TD-050: production UI collaborators must be non-None before QML load.
        self._finalize_ui_ports()

        video_runtime = self._context_properties.get("videoRuntime")
        self._signal_wiring = SignalWiring(self._build_signal_wiring_ports(video_runtime))
        self._signal_wiring.wire()
        self._register_context_properties()
        self._load_qml()
        self.status_timer = self._signal_wiring.start_timers()

    def _setup_core_objects(self) -> None:
        from paint_controller.core.ros_node import PaintRosNode
        from paint_controller.core.state_store import StateStore

        self.state_store = StateStore()
        self.node = PaintRosNode(state_store=self.state_store)
        self._log_startup("PaintRosNode created")

        self.settings_manager = SettingsManager(show_popup_fn=None)
        self.capability_catalog = CapabilityCatalog(settings_manager=self.settings_manager)
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

        engine = QQmlApplicationEngine()
        self.engine = engine
        engine.addImageProvider("ef_live", self.video_stream_handler.ef_image_provider)
        engine.addImageProvider("base_front_live", self.video_stream_handler.front_image_provider)
        engine.addImageProvider("base_rear_live", self.video_stream_handler.rear_image_provider)
        engine.addImageProvider("base_top_view", self.base_top_view_service.image_provider)
        self._log_startup("QML engine and image providers ready")

        engine.addImportPath(self.qml_dir)
        self.qt_bridge = QtBridge(engine, self.state_store, logger=self.node.get_logger())
        self._log_startup("Qt bridge created")

        assert self.settings_manager is not None
        # TD-050: public setter only — no private-field poke.
        self.settings_manager.set_show_popup_fn(self.qt_bridge.show_popup)

    def _create_controller_bundle(self) -> None:
        from paint_controller.core.controller_factory import create_controllers
        from paint_controller.models.overlay_host_policy import OverlayHostPolicy
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
            capability_catalog=self.capability_catalog,
            state_store=self.state_store,
            steam_deck_handler=self.steam_deck_handler,
            video_stream_handler=self.video_stream_handler,
            base_top_view_service=self.base_top_view_service,
            show_popup_fn=self.qt_bridge.show_popup,
            close_popup_fn=self.qt_bridge.close_popup,
        )
        self._log_startup("Controller bundle created")

        # TD-036 / TD-050: gate is factory-created; inject via public API only.
        assert self.settings_manager is not None
        self.settings_manager.set_admin_action_gate(self.bundle.admin_action_gate)

        self.qt_bridge.set_base_top_view_service(self.base_top_view_service)
        self.qt_bridge.set_input_handler(self.bundle.input_handler)
        self.shell_state = ShellState(screen_manager=self.bundle.screen_manager)
        self.shell_router = ShellRouter(parent=self.shell_state)
        self.overlay_host = OverlayHostPolicy(shell_state=self.shell_state)
        self.action_legality = ActionLegalityModel(
            admin_action_gate=self.bundle.admin_action_gate,
            capability_catalog=self.capability_catalog,
        )

        self._composer = QmlContextComposer(self._build_compose_ports())
        # Façades stay in this map only (TD-047); QML registration and SignalWiring
        # read from here / bundle rather than AppRuntime attribute mirrors.
        self._context_properties = self._composer.compose()

    def _build_compose_ports(self) -> QmlComposePorts:
        """Explicit ports for the context composer — not the whole AppRuntime."""
        return QmlComposePorts(
            bundle=self.bundle,
            video_stream_handler=self.video_stream_handler,
            base_top_view_service=self.base_top_view_service,
            qt_bridge=self.qt_bridge,
            shell_state=self.shell_state,
            shell_router=self.shell_router,
            overlay_host=self.overlay_host,
            action_legality=self.action_legality,
            settings_manager=self.settings_manager,
        )

    def _build_signal_wiring_ports(self, video_runtime: object) -> SignalWiringPorts:
        """Explicit ports for signal wiring — not the whole AppRuntime."""
        return SignalWiringPorts(
            bundle=self.bundle,
            node=self.node,
            state_store=self.state_store,
            qt_bridge=self.qt_bridge,
            video_stream_handler=self.video_stream_handler,
            steam_deck_handler=self.steam_deck_handler,
            overlay_host=self.overlay_host,
            video_runtime=video_runtime,
            update_rate=self.config.update_rate,
            deferred_video_startup=self._deferred_video_startup,
            ros_thread=self.ros_thread,
        )

    def _activate_default_video_overlay(self) -> None:
        """Show the fullscreen video overlay on startup with the current control-mode source."""
        assert self.overlay_host is not None
        assert self.qt_bridge is not None

        video_source = self.qt_bridge._video_source_for_control_mode()
        self.overlay_host.show_video_fullscreen(video_source)
        self._log_startup(f"Default video overlay activated: {video_source}")

    def _finalize_ui_ports(self) -> None:
        """Assert required UI collaborators are non-None before QML load (TD-050)."""
        assert self.settings_manager is not None
        assert self.qt_bridge is not None
        self.settings_manager.require_ui_ports()
        self.qt_bridge.require_ui_ports()

    def _register_context_properties(self) -> None:
        assert self.engine is not None
        assert self.node is not None

        context = self.engine.rootContext()
        expected_names = set(qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES)
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

        qml_path = os.path.join(self.qml_dir, "core", "MainWindow.qml")
        self.engine.load(QUrl.fromLocalFile(qml_path))
        if not self.engine.rootObjects():
            raise RuntimeError(f"Failed to load QML root: {qml_path}")
        self._log_startup("MainWindow QML loaded")

        context = self.engine.rootContext()
        for name in qml_context_composer._EXPECTED_CONTEXT_PROPERTY_NAMES:
            if context.contextProperty(name) is None:
                self.node.get_logger().error(f"Missing QML context property: {name}")

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
                try:
                    self.status_timer.timeout.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self.status_timer.deleteLater()
                self.status_timer = None
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
            # rclpy.ok() is public at runtime; stubs often omit it.
            if getattr(rclpy, "ok", lambda: False)():
                rclpy.shutdown()
            log_shutdown("ROS context shutdown complete")
        except Exception as error:
            logger.error("Error during ROS shutdown: %s", error)

        logger.info("Emergency shutdown sequence complete")
