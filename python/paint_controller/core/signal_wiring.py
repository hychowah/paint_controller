"""Centralize signal connections and timer wiring for AppRuntime."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QTimer, Qt

if TYPE_CHECKING:
    from paint_controller.core.app_runtime import AppRuntime

logger = logging.getLogger(__name__)


class SignalWiring:
    """Owns Steam Deck callbacks, Qt signal routing, and timer startup."""

    def __init__(self, runtime: AppRuntime) -> None:
        self._runtime = runtime

    def wire(self) -> None:
        """Connect all runtime signals and Steam Deck button callbacks."""
        from paint_controller.utils.constants import HeartbeatStatus

        runtime = self._runtime
        bundle = runtime.bundle
        if bundle is None:
            raise RuntimeError("ControllerBundle is required before wiring signals")

        node = runtime.node
        state_store = runtime.state_store
        qt_bridge = runtime.qt_bridge
        video_stream_handler = runtime.video_stream_handler
        steam_deck_handler = runtime.steam_deck_handler
        overlay_host = runtime.overlay_host
        video_runtime = runtime.video_runtime

        if node is None:
            raise RuntimeError("ROS node is required before wiring signals")
        if state_store is None:
            raise RuntimeError("StateStore is required before wiring signals")
        if qt_bridge is None:
            raise RuntimeError("QtBridge is required before wiring signals")
        if video_stream_handler is None:
            raise RuntimeError("VideoStreamHandler is required before wiring signals")
        if steam_deck_handler is None:
            raise RuntimeError("SteamDeckHandler is required before wiring signals")
        if overlay_host is None:
            raise RuntimeError("OverlayHostPolicy is required before wiring signals")
        if video_runtime is None:
            raise RuntimeError("VideoRuntime is required before wiring signals")

        runtime._heartbeat_status_error = HeartbeatStatus.ERROR
        state_store.control_mode_changed.connect(qt_bridge.update_fullscreen_video_source)
        bundle.emergency_handler.overlay_changed.connect(qt_bridge.emergency_overlay_changed.emit)
        bundle.emergency_handler.emergency_triggered.connect(qt_bridge.emergency_triggered.emit)
        video_stream_handler.endEffectorFrameReady.connect(qt_bridge.frame_ready.emit)
        bundle.wheel_controller.error_state_changed.connect(
            self._on_wheel_motor_error,
            Qt.QueuedConnection,
        )
        qt_bridge.status_updated.connect(self._on_status_tick)

        video_runtime.topBar.endEffectorVideoRequested.connect(
            lambda: overlay_host.set_video_fullscreen_source("image://ef_live/frame")
        )
        video_runtime.topBar.baseVideoRequested.connect(
            lambda: overlay_host.set_video_fullscreen_source("image://base_front_live/frame")
        )
        qt_bridge.toggleVideoOverlayRequested.connect(
            lambda _active, video_source: overlay_host.toggle_video_fullscreen(video_source)
        )
        qt_bridge.updateVideoSourceRequested.connect(
            overlay_host.set_video_fullscreen_source
        )

        self._wire_steam_deck_callbacks()

    def _wire_steam_deck_callbacks(self) -> None:
        runtime = self._runtime
        bundle = runtime.bundle
        steam_deck_handler = runtime.steam_deck_handler
        qt_bridge = runtime.qt_bridge

        if bundle is None or steam_deck_handler is None or qt_bridge is None:
            return

        input_handler = bundle.input_handler
        steam_deck_handler.register_button_callback('up', input_handler.on_up_pressed)
        steam_deck_handler.register_button_callback('down', input_handler.on_down_pressed)
        steam_deck_handler.register_button_callback('left', input_handler.on_left_pressed)
        steam_deck_handler.register_button_callback('right', input_handler.on_right_pressed)
        steam_deck_handler.register_button_callback('r4', input_handler.on_r4_pressed)
        steam_deck_handler.register_button_callback('l4', input_handler.on_l4_pressed)
        steam_deck_handler.register_button_callback('menu', input_handler.on_menu_pressed)
        steam_deck_handler.register_button_callback('switch', input_handler.on_switch_pressed)
        steam_deck_handler.register_button_callback('l5', input_handler.on_l5_pressed)
        steam_deck_handler.register_button_callback('r5', input_handler.on_r5_pressed)
        steam_deck_handler.register_button_callback('dot', qt_bridge.toggle_fullscreen)
        steam_deck_handler.register_button_callback('a', qt_bridge.toggle_lidar_overlay)
        steam_deck_handler.register_button_callback('l1', input_handler.on_l1_pressed)

    def _on_wheel_motor_error(self, has_error, error_message) -> None:
        if not has_error:
            return

        runtime = self._runtime
        bundle = runtime.bundle
        node = runtime.node
        qt_bridge = runtime.qt_bridge

        if bundle is None or node is None or qt_bridge is None:
            return

        from paint_controller.utils.constants import HeartbeatStatus

        node.get_logger().error(f'Wheel motor error detected: {error_message}')
        bundle.safety_coordinator.halt_all_effectors(
            f"Wheel motor error detected: {error_message}",
            heartbeat_state=HeartbeatStatus.ERROR,
        )
        qt_bridge.show_popup("MOTOR ERROR", error_message, "error", 5000)
        qt_bridge.emergency_triggered.emit()

    def _on_status_tick(self) -> None:
        runtime = self._runtime
        bundle = runtime.bundle
        steam_deck_handler = runtime.steam_deck_handler

        if bundle is None or steam_deck_handler is None:
            return

        input_state = steam_deck_handler.get_current_state()
        bundle.control_processor.process_input(input_state)
        bundle.emergency_handler.check_emergency_button(input_state.get('buttons', {}))

    def start_timers(self) -> None:
        """Create and start the status timer and system monitor."""
        runtime = self._runtime
        bundle = runtime.bundle
        qt_bridge = runtime.qt_bridge

        if bundle is None or qt_bridge is None:
            raise RuntimeError("ControllerBundle and QtBridge are required before starting timers")

        runtime.status_timer = QTimer()
        assert runtime.status_timer is not None
        runtime.status_timer.timeout.connect(qt_bridge.status_updated.emit)
        runtime.status_timer.start(int(1000 / runtime.config.update_rate))

        bundle.system_monitor.start_monitoring(interval_ms=1000)

        QTimer.singleShot(200, runtime._deferred_video_startup)


def wire(runtime: AppRuntime) -> None:
    """Convenience entry point matching the master-plan function signature."""
    SignalWiring(runtime).wire()


def start_timers(runtime: AppRuntime) -> None:
    """Convenience entry point matching the master-plan function signature."""
    SignalWiring(runtime).start_timers()
