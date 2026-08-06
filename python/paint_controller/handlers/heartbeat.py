#!/usr/bin/env python3

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot
from rclpy.node import Node
from std_msgs.msg import Empty, UInt8

from paint_controller.core.ros_telemetry import RosTelemetryBridge
from paint_controller.utils.constants import HeartbeatStatus

if TYPE_CHECKING:
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.safety_coordinator import SafetyCoordinator

HeartbeatChannel = Literal["controller", "base", "ef"]


@dataclass(frozen=True, slots=True)
class HeartbeatTick:
    """POD from ROS spin → main apply (TD-056 residual cleanup)."""

    channel: HeartbeatChannel
    recv_mono: float
    status: int


class UIHeartbeatHandler(QObject):
    """Monitor remote heartbeats; clear-error command; UI properties.

    TD-056 residual cleanup:
    - ROS callbacks only ``post`` :class:`HeartbeatTick` (no QObject mutation).
    - Main apply owns online/status/StateStore refresh.
    - Outbound ``/controller/heartbeat`` is **not** owned here (PaintRosNode only);
      clear-error uses dedicated ``/clear/error``.
    """

    controller_status_changed = Signal()
    base_status_changed = Signal()
    ef_status_changed = Signal()
    controller_online_changed = Signal()
    base_online_changed = Signal()
    ef_online_changed = Signal()
    status_message_changed = Signal()

    def __init__(
        self,
        node: Node,
        state_store: StateStore | None = None,
        safety_coordinator: SafetyCoordinator | None = None,
    ) -> None:
        super().__init__()
        self._node = node
        self._state_store = state_store
        self._safety_coordinator = safety_coordinator

        self._controller_status = int(getattr(state_store, "controller_heartbeat_state", HeartbeatStatus.IDLE.value))
        self._base_status = HeartbeatStatus.IDLE.value
        self._ef_status = HeartbeatStatus.IDLE.value
        self._controller_online = False
        self._base_online = False
        self._ef_online = False
        self._status_message = "System initializing..."

        self._controller_last_seen = 0.0
        self._base_last_seen = 0.0
        self._ef_last_seen = 0.0
        self._heartbeat_timeout = 1.0

        # One bridge per channel so last-wins coalesce cannot drop a sibling channel.
        self._controller_bridge = RosTelemetryBridge(self._apply_heartbeat_tick, parent=self)
        self._base_bridge = RosTelemetryBridge(self._apply_heartbeat_tick, parent=self)
        self._ef_bridge = RosTelemetryBridge(self._apply_heartbeat_tick, parent=self)

        self._setup_publishers()
        self._setup_subscribers()

        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)

        self._node.get_logger().info("UIHeartbeatHandler initialized")

    def _set_runtime_state(self, value: int, *, allow_downgrade_from_error: bool = False) -> None:
        if self._state_store is None:
            return

        try:
            new_state = HeartbeatStatus(value)
        except ValueError:
            return

        try:
            current_state = HeartbeatStatus(self._state_store.controller_heartbeat_state)
        except (TypeError, ValueError):
            current_state = HeartbeatStatus.IDLE

        if (
            current_state == HeartbeatStatus.ERROR
            and new_state != HeartbeatStatus.ERROR
            and not allow_downgrade_from_error
        ):
            return

        self._state_store.controller_heartbeat_state = int(new_state)

    def _refresh_runtime_state(self) -> None:
        if self._state_store is None:
            return

        try:
            current_state = HeartbeatStatus(self._state_store.controller_heartbeat_state)
        except (TypeError, ValueError):
            current_state = HeartbeatStatus.IDLE

        if current_state == HeartbeatStatus.ERROR:
            return

        if self.are_any_components_in_error():
            self._set_runtime_state(HeartbeatStatus.ERROR.value)
        elif not self._base_online or not self._ef_online:
            self._set_runtime_state(HeartbeatStatus.WARNING.value)
        elif self.are_any_components_in_warning():
            self._set_runtime_state(HeartbeatStatus.WARNING.value)
        elif self._controller_online and self._base_online and self._ef_online:
            self._set_runtime_state(HeartbeatStatus.ONTASK.value)

    def _handle_heartbeat_loss(self, message: str) -> None:
        self.set_status_message(message)
        if self._safety_coordinator is not None:
            self._safety_coordinator.halt_all_effectors(
                message,
                heartbeat_state=HeartbeatStatus.WARNING,
            )
        else:
            self._set_runtime_state(HeartbeatStatus.WARNING.value)
        self._node.get_logger().warning(message)

    def _setup_publishers(self) -> None:
        """Clear-error only — outbound /controller/heartbeat owned by PaintRosNode."""
        self._clear_error_pub = self._node.create_publisher(Empty, "/clear/error", 10)
        self._node.get_logger().info("Publishers initialized: /clear/error (heartbeat outbound: PaintRosNode)")

    def _setup_subscribers(self) -> None:
        self._controller_heartbeat_sub = self._node.create_subscription(
            UInt8, "/controller/heartbeat", self._controller_heartbeat_callback, 10
        )
        self._base_heartbeat_sub = self._node.create_subscription(
            UInt8, "/base/heartbeat", self._base_heartbeat_callback, 10
        )
        self._ef_heartbeat_sub = self._node.create_subscription(
            UInt8, "/ef/heartbeat", self._ef_heartbeat_callback, 10
        )
        self._node.get_logger().info("Heartbeat subscribers initialized")

    def _pending_recv_mono(self, bridge: RosTelemetryBridge) -> float | None:
        """Return recv_mono of a queued tick if present (UI apply lag ≠ peer loss)."""
        pending = bridge.pending_snapshot()
        if isinstance(pending, HeartbeatTick):
            return float(pending.recv_mono)
        return None

    def _effective_last_seen(self, last_seen: float, bridge: RosTelemetryBridge) -> float:
        """Max of last applied tick and any pending receive time.

        Heartbeats are posted from the ROS thread with wall recv time; main-thread
        apply may lag during QML work. Loss detection must not treat a queued
        recent post as silence (false "Controller heartbeat lost" during UI stalls).
        """
        pending_recv = self._pending_recv_mono(bridge)
        if pending_recv is None:
            return last_seen
        return max(last_seen, pending_recv)

    def _check_availability(self) -> None:
        """Main-thread timer: offline detection + halt on loss."""
        current_time = time.time()

        if (
            current_time - self._effective_last_seen(self._controller_last_seen, self._controller_bridge)
            > self._heartbeat_timeout
        ):
            if self._controller_online:
                self.set_controller_online(False)
                self._handle_heartbeat_loss("Controller heartbeat lost")

        if (
            current_time - self._effective_last_seen(self._base_last_seen, self._base_bridge)
            > self._heartbeat_timeout
        ):
            if self._base_online:
                self.set_base_online(False)
                self._handle_heartbeat_loss("Base robot heartbeat lost")

        if (
            current_time - self._effective_last_seen(self._ef_last_seen, self._ef_bridge)
            > self._heartbeat_timeout
        ):
            if self._ef_online:
                self.set_ef_online(False)
                self._handle_heartbeat_loss("End effector heartbeat lost")

    def _post_tick(self, channel: HeartbeatChannel, msg: UInt8) -> None:
        tick = HeartbeatTick(channel=channel, recv_mono=time.time(), status=int(msg.data))
        if channel == "controller":
            self._controller_bridge.post(tick)
        elif channel == "base":
            self._base_bridge.post(tick)
        else:
            self._ef_bridge.post(tick)

    def _controller_heartbeat_callback(self, msg: UInt8) -> None:
        try:
            self._post_tick("controller", msg)
        except Exception as e:
            self._node.get_logger().error(f"Error in controller heartbeat callback: {e}")

    def _base_heartbeat_callback(self, msg: UInt8) -> None:
        try:
            self._post_tick("base", msg)
        except Exception as e:
            self._node.get_logger().error(f"Error in base heartbeat callback: {e}")

    def _ef_heartbeat_callback(self, msg: UInt8) -> None:
        try:
            self._post_tick("ef", msg)
        except Exception as e:
            self._node.get_logger().error(f"Error in EF heartbeat callback: {e}")

    def _apply_heartbeat_tick(self, tick: object) -> None:
        """Main thread: update online/status/StateStore from a channel tick."""
        if not isinstance(tick, HeartbeatTick):
            self._node.get_logger().error(f"Heartbeat apply expected HeartbeatTick, got {type(tick)}")
            return

        channel = tick.channel
        status = int(tick.status)
        recv = float(tick.recv_mono)

        if channel == "controller":
            self._controller_last_seen = recv
            if not self._controller_online:
                self.set_controller_online(True)
                self.set_status_message("Controller heartbeat restored")
                self._node.get_logger().info("Controller heartbeat restored")
            if self._controller_status != status:
                self.set_controller_status(status)
                self._node.get_logger().info(
                    f"Controller status changed to: {self._status_to_string(status)}"
                )
                if status == HeartbeatStatus.WARNING.value:
                    self.set_status_message("Controller warning")
                elif status == HeartbeatStatus.ERROR.value:
                    self.set_status_message("Controller error")
                self._set_runtime_state(status)
            self._refresh_runtime_state()
            return

        if channel == "base":
            self._base_last_seen = recv
            if not self._base_online:
                self.set_base_online(True)
                self.set_status_message("Base robot heartbeat restored")
                self._node.get_logger().info("Base heartbeat restored")
            if self._base_status != status:
                self.set_base_status(status)
                self._node.get_logger().info(f"Base status changed to: {self._status_to_string(status)}")
                if status == HeartbeatStatus.WARNING.value:
                    self.set_status_message("Base robot warning")
                elif status == HeartbeatStatus.ERROR.value:
                    self.set_status_message("Base robot error")
            self._refresh_runtime_state()
            return

        # ef
        self._ef_last_seen = recv
        if not self._ef_online:
            self.set_ef_online(True)
            self.set_status_message("End effector heartbeat restored")
            self._node.get_logger().info("EF heartbeat restored")
        if self._ef_status != status:
            self.set_ef_status(status)
            self._node.get_logger().info(f"EF status changed to: {self._status_to_string(status)}")
            if status == HeartbeatStatus.WARNING.value:
                self.set_status_message("End effector warning")
            elif status == HeartbeatStatus.ERROR.value:
                self.set_status_message("End effector error")
        self._refresh_runtime_state()

    def get_controller_status(self) -> int:
        return self._controller_status

    def set_controller_status(self, value: int) -> None:
        if self._controller_status != value:
            self._controller_status = value
            self.controller_status_changed.emit()

    def get_base_status(self) -> int:
        return self._base_status

    def set_base_status(self, value: int) -> None:
        if self._base_status != value:
            self._base_status = value
            self.base_status_changed.emit()

    def get_ef_status(self) -> int:
        return self._ef_status

    def set_ef_status(self, value: int) -> None:
        if self._ef_status != value:
            self._ef_status = value
            self.ef_status_changed.emit()

    def get_controller_online(self) -> bool:
        return self._controller_online

    def set_controller_online(self, value: bool) -> None:
        if self._controller_online != value:
            self._controller_online = value
            self.controller_online_changed.emit()

    def get_base_online(self) -> bool:
        return self._base_online

    def set_base_online(self, value: bool) -> None:
        if self._base_online != value:
            self._base_online = value
            self.base_online_changed.emit()

    def get_ef_online(self) -> bool:
        return self._ef_online

    def set_ef_online(self, value: bool) -> None:
        if self._ef_online != value:
            self._ef_online = value
            self.ef_online_changed.emit()

    def get_status_message(self) -> str:
        return self._status_message

    def set_status_message(self, value: str) -> None:
        if self._status_message != value:
            self._status_message = value
            self.status_message_changed.emit()

    controller_status = Property(int, get_controller_status, notify=controller_status_changed)
    base_status = Property(int, get_base_status, notify=base_status_changed)
    ef_status = Property(int, get_ef_status, notify=ef_status_changed)
    controller_online = Property(bool, get_controller_online, notify=controller_online_changed)
    base_online = Property(bool, get_base_online, notify=base_online_changed)
    ef_online = Property(bool, get_ef_online, notify=ef_online_changed)
    status_message = Property(str, get_status_message, notify=status_message_changed)

    @Slot(str, result=bool)
    def is_component_online(self, component_name: str) -> bool:
        if component_name == "controller":
            return self._controller_online
        if component_name == "base":
            return self._base_online
        if component_name == "ef":
            return self._ef_online
        return False

    @Slot(str, result=int)
    def get_component_status(self, component_name: str) -> int:
        if component_name == "controller":
            return self._controller_status
        if component_name == "base":
            return self._base_status
        if component_name == "ef":
            return self._ef_status
        return HeartbeatStatus.IDLE.value

    @Slot(str, result=str)
    def get_status_string(self, component_name: str) -> str:
        return self._status_to_string(self.get_component_status(component_name))

    @Slot(str, result=str)
    def get_status_color(self, component_name: str) -> str:
        if not self.is_component_online(component_name):
            return "gray"
        status_code = self.get_component_status(component_name)
        if status_code == HeartbeatStatus.IDLE.value:
            return "blue"
        if status_code == HeartbeatStatus.ONTASK.value:
            return "green"
        if status_code == HeartbeatStatus.WARNING.value:
            return "yellow"
        if status_code == HeartbeatStatus.ERROR.value:
            return "red"
        return "gray"

    @Slot()
    def are_all_components_online(self) -> bool:
        return self._controller_online and self._base_online and self._ef_online

    @Slot()
    def are_any_components_in_error(self) -> bool:
        return (
            self._controller_status == HeartbeatStatus.ERROR.value
            or self._base_status == HeartbeatStatus.ERROR.value
            or self._ef_status == HeartbeatStatus.ERROR.value
        )

    @Slot()
    def are_any_components_in_warning(self) -> bool:
        return (
            self._controller_status == HeartbeatStatus.WARNING.value
            or self._base_status == HeartbeatStatus.WARNING.value
            or self._ef_status == HeartbeatStatus.WARNING.value
        )

    def _status_to_string(self, status_code: int) -> str:
        status_map = {
            HeartbeatStatus.IDLE.value: "IDLE",
            HeartbeatStatus.ONTASK.value: "ONTASK",
            HeartbeatStatus.WARNING.value: "WARNING",
            HeartbeatStatus.ERROR.value: "ERROR",
            HeartbeatStatus.CLEAR_ERROR.value: "CLEAR_ERROR",
        }
        return status_map.get(status_code, f"UNKNOWN({status_code})")

    @Slot()
    def clear_error_state(self) -> None:
        """Publish clear-error and clear local latch via coordinator / StateStore."""
        self._node.get_logger().info("Sending clear error command")
        try:
            self._clear_error_pub.publish(Empty())
            self._node.get_logger().info("Published clear command to /clear/error topic")
        except Exception as e:
            self._node.get_logger().error(f"Error publishing to /clear/error: {e}")

        if self._safety_coordinator is not None:
            self._safety_coordinator.clear_error_state()
        else:
            self._set_runtime_state(HeartbeatStatus.IDLE.value, allow_downgrade_from_error=True)

        self.set_status_message("Clearing errors...")

    def cleanup(self) -> None:
        if hasattr(self, "_availability_timer") and self._availability_timer.isActive():
            self._availability_timer.stop()
        self._node.get_logger().info("UIHeartbeatHandler cleaned up")
