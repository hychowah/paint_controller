"""Centralize signal connections and timer wiring via explicit ports (TD-047)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt, QTimer

from paint_controller.utils.constants import ControlMode
from paint_controller.utils.perf_counters import PERF, timed_section

logger = logging.getLogger(__name__)

# Throttle ROS thread error messages so varying spin errors do not thrash TopBar.
_ROS_ERROR_DISPLAY_INTERVAL_S = 2.0


@dataclass(frozen=True)
class SignalWiringPorts:
    """Dependencies SignalWiring needs — no AppRuntime service locator."""

    bundle: Any
    node: Any
    state_store: Any
    qt_bridge: Any
    video_stream_handler: Any
    steam_deck_handler: Any
    overlay_host: Any
    video_runtime: Any
    update_rate: float
    deferred_video_startup: Callable[[], None]
    ros_thread: Any | None = None


class SignalWiring:
    """Owns Steam Deck callbacks, Qt signal routing, and timer startup."""

    def __init__(self, ports: SignalWiringPorts) -> None:
        self._ports = ports
        self._last_ros_error_display_at = 0.0
        self._last_ros_error_message = ""

    def wire(self) -> None:
        """Connect all runtime signals and Steam Deck button callbacks."""
        ports = self._ports
        bundle = ports.bundle
        if bundle is None:
            raise RuntimeError("ControllerBundle is required before wiring signals")

        node = ports.node
        state_store = ports.state_store
        qt_bridge = ports.qt_bridge
        video_stream_handler = ports.video_stream_handler
        steam_deck_handler = ports.steam_deck_handler
        overlay_host = ports.overlay_host
        video_runtime = ports.video_runtime

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

        state_store.control_mode_changed.connect(qt_bridge.update_fullscreen_video_source)
        bundle.emergency_handler.overlay_changed.connect(qt_bridge.emergency_overlay_changed.emit)
        bundle.emergency_handler.emergency_triggered.connect(qt_bridge.emergency_triggered.emit)
        bundle.exit_hold_handler.overlay_changed.connect(qt_bridge.exit_overlay_changed.emit)
        video_stream_handler.endEffectorFrameReady.connect(qt_bridge.frame_ready.emit)
        bundle.wheel_controller.error_state_changed.connect(
            self._on_wheel_motor_error,
            Qt.QueuedConnection,
        )
        qt_bridge.status_updated.connect(self._on_status_tick)

        ros_thread = ports.ros_thread
        if ros_thread is not None and hasattr(ros_thread, "error_occurred"):
            ros_thread.error_occurred.connect(
                self._on_ros_thread_error,
                Qt.QueuedConnection,
            )

        # Stream switch ≡ control mode switch (sticks + control_mode). Video feed
        # follows via control_mode_changed → update_fullscreen_video_source.
        # Pass .value so session state always stores "ef" / "base" (not enum repr).
        video_runtime.topBar.endEffectorVideoRequested.connect(
            lambda: bundle.input_handler.switch_control_mode(ControlMode.END_EFFECTOR.value)
        )
        video_runtime.topBar.baseVideoRequested.connect(
            lambda: bundle.input_handler.switch_control_mode(ControlMode.BASE.value)
        )
        qt_bridge.toggleVideoOverlayRequested.connect(
            lambda _active, video_source: overlay_host.toggle_video_fullscreen(video_source)
        )
        qt_bridge.updateVideoSourceRequested.connect(overlay_host.set_video_fullscreen_source)
        # P-02: lazy-start the feed implied by the active image:// source.
        qt_bridge.updateVideoSourceRequested.connect(
            lambda video_source: video_stream_handler.ensure_stream_for_image_url(video_source)
        )

        self._wire_steam_deck_callbacks()

    def _on_ros_thread_error(self, message: str) -> None:
        """Surface ROS spin/context failures without flooding the status bar."""
        text = str(message or "").strip() or "unknown ROS error"
        logger.error("ROS thread error: %s", text)

        now = time.monotonic()
        # Same text: StateStore also dedupes; skip re-entry noise.
        if text == self._last_ros_error_message:
            return
        # Varying spin errors: throttle TopBar updates.
        if (now - self._last_ros_error_display_at) < _ROS_ERROR_DISPLAY_INTERVAL_S:
            return

        state_store = self._ports.state_store
        if state_store is None:
            return

        self._last_ros_error_message = text
        self._last_ros_error_display_at = now
        state_store.display_message = f"ROS: {text}"

    def _wire_steam_deck_callbacks(self) -> None:
        ports = self._ports
        bundle = ports.bundle
        steam_deck_handler = ports.steam_deck_handler
        qt_bridge = ports.qt_bridge

        if bundle is None or steam_deck_handler is None or qt_bridge is None:
            return

        input_handler = bundle.input_handler
        steam_deck_handler.register_button_callback("up", input_handler.on_up_pressed)
        steam_deck_handler.register_button_callback("down", input_handler.on_down_pressed)
        steam_deck_handler.register_button_callback("left", input_handler.on_left_pressed)
        steam_deck_handler.register_button_callback("right", input_handler.on_right_pressed)
        steam_deck_handler.register_button_callback("r4", input_handler.on_r4_pressed)
        steam_deck_handler.register_button_callback("l4", input_handler.on_l4_pressed)
        steam_deck_handler.register_button_callback("menu", input_handler.on_menu_pressed)
        # Switch is hold-to-exit (ExitHoldHandler), not a press callback.
        steam_deck_handler.register_button_callback("l5", input_handler.on_l5_pressed)
        steam_deck_handler.register_button_callback("r5", input_handler.on_r5_pressed)
        steam_deck_handler.register_button_callback("dot", qt_bridge.toggle_fullscreen)
        steam_deck_handler.register_button_callback("a", qt_bridge.toggle_lidar_overlay)
        steam_deck_handler.register_button_callback("l1", input_handler.on_l1_pressed)

    def _on_wheel_motor_error(self, has_error, error_message) -> None:
        if not has_error:
            return

        ports = self._ports
        bundle = ports.bundle
        node = ports.node
        qt_bridge = ports.qt_bridge

        if bundle is None or node is None or qt_bridge is None:
            return

        from paint_controller.utils.constants import HeartbeatStatus

        node.get_logger().error(f"Wheel motor error detected: {error_message}")
        bundle.safety_coordinator.halt_all_effectors(
            f"Wheel motor error detected: {error_message}",
            heartbeat_state=HeartbeatStatus.ERROR,
        )
        qt_bridge.show_popup("MOTOR ERROR", error_message, "error", 5000)
        qt_bridge.emergency_triggered.emit()

    def _on_status_tick(self) -> None:
        ports = self._ports
        bundle = ports.bundle
        steam_deck_handler = ports.steam_deck_handler

        if bundle is None or steam_deck_handler is None:
            return

        with timed_section("status_tick"):
            PERF.incr("status_tick")
            input_state = steam_deck_handler.get_current_state()
            buttons = input_state.get("buttons", {})
            # TD-054: e-stop poll before teleop so a held e-stop latches before stick cmds.
            bundle.emergency_handler.check_emergency_button(buttons)
            bundle.exit_hold_handler.check_exit_button(buttons)
            bundle.control_processor.process_input(input_state)

    def start_timers(self) -> QTimer:
        """Create and start the status timer and system monitor.

        Returns the status timer so the composition root owns lifetime assignment.
        """
        ports = self._ports
        bundle = ports.bundle
        qt_bridge = ports.qt_bridge

        if bundle is None or qt_bridge is None:
            raise RuntimeError("ControllerBundle and QtBridge are required before starting timers")

        # Parent to qt_bridge so the timer is not a process-orphan QObject (TD-051).
        status_timer = QTimer(qt_bridge)
        status_timer.timeout.connect(qt_bridge.status_updated.emit)
        status_timer.start(int(1000 / ports.update_rate))

        bundle.system_monitor.start_monitoring(interval_ms=1000)

        QTimer.singleShot(200, ports.deferred_video_startup)
        return status_timer
