"""Reusable test doubles for ROS-like interfaces."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FakeLogRecord:
    level: str
    message: str


@dataclass
class FakeLogger:
    records: list[FakeLogRecord] = field(default_factory=list)

    @staticmethod
    def _format(message: str, *args: Any) -> str:
        if not args:
            return message
        return message % args

    def debug(self, message: str, *args: Any) -> None:
        self.records.append(FakeLogRecord("debug", self._format(message, *args)))

    def info(self, message: str, *args: Any) -> None:
        self.records.append(FakeLogRecord("info", self._format(message, *args)))

    def warning(self, message: str, *args: Any) -> None:
        self.records.append(FakeLogRecord("warning", self._format(message, *args)))

    def error(self, message: str, *args: Any) -> None:
        self.records.append(FakeLogRecord("error", self._format(message, *args)))


@dataclass
class FakePublisher:
    msg_type: Any
    topic: str
    qos: int
    bus: FakeRosBus | None = None
    published_messages: list[Any] = field(default_factory=list)

    def publish(self, message: Any) -> None:
        # Validate message type matches the declared publisher type, just as
        # real DDS would reject a type mismatch at the middleware boundary.
        assert isinstance(message, self.msg_type), (
            f"FakePublisher({self.topic}): expected {self.msg_type.__name__}, got {type(message).__name__}"
        )
        self.published_messages.append(message)
        if self.bus is not None:
            self.bus.publish(self.topic, message)


@dataclass
class FakeSubscription:
    msg_type: Any
    topic: str
    callback: Callable[[Any], None]
    qos: int


@dataclass
class FakeRosBus:
    subscriptions_by_topic: dict[str, list[FakeSubscription]] = field(default_factory=dict)

    def register_subscription(self, subscription: FakeSubscription) -> None:
        self.subscriptions_by_topic.setdefault(subscription.topic, []).append(subscription)

    def unregister_subscription(self, subscription: FakeSubscription) -> None:
        subscriptions = self.subscriptions_by_topic.get(subscription.topic)
        if subscriptions is None:
            return
        if subscription in subscriptions:
            subscriptions.remove(subscription)
        if not subscriptions:
            del self.subscriptions_by_topic[subscription.topic]

    def publish(self, topic: str, message: Any) -> None:
        # Shallow-copy the message before delivery so that subscriber mutations
        # do not affect the publisher's object, matching real DDS serialisation
        # semantics where publisher and subscriber get independent copies.
        for subscription in list(self.subscriptions_by_topic.get(topic, [])):
            subscription.callback(copy.copy(message))


@dataclass
class FakeTimer:
    interval_sec: float
    callback: Callable[[], None]
    cancelled: bool = False

    def trigger(self) -> None:
        if not self.cancelled:
            self.callback()

    def cancel(self) -> None:
        self.cancelled = True


class FakeNode:
    """Small ROS-node-like test double for controller tests."""

    def __init__(self, bus: FakeRosBus | None = None) -> None:
        self.bus = bus
        self.logger = FakeLogger()
        self.publishers: list[FakePublisher] = []
        self.subscriptions: list[FakeSubscription] = []
        self.timers: list[FakeTimer] = []
        self.destroyed_publishers: list[FakePublisher] = []
        self.destroyed_subscriptions: list[FakeSubscription] = []
        self.destroyed_timers: list[FakeTimer] = []
        self.destroyed = False

    def get_logger(self) -> FakeLogger:
        return self.logger

    def create_publisher(self, msg_type: Any, topic: str, qos: int) -> FakePublisher:
        publisher = FakePublisher(msg_type=msg_type, topic=topic, qos=qos, bus=self.bus)
        self.publishers.append(publisher)
        return publisher

    def create_subscription(
        self,
        msg_type: Any,
        topic: str,
        callback: Callable[[Any], None],
        qos: int,
    ) -> FakeSubscription:
        subscription = FakeSubscription(
            msg_type=msg_type,
            topic=topic,
            callback=callback,
            qos=qos,
        )
        self.subscriptions.append(subscription)
        if self.bus is not None:
            self.bus.register_subscription(subscription)
        return subscription

    def create_timer(self, interval_sec: float, callback: Callable[[], None]) -> FakeTimer:
        timer = FakeTimer(interval_sec=interval_sec, callback=callback)
        self.timers.append(timer)
        return timer

    def destroy_publisher(self, publisher: FakePublisher) -> None:
        self.destroyed_publishers.append(publisher)
        if publisher in self.publishers:
            self.publishers.remove(publisher)

    def destroy_subscription(self, subscription: FakeSubscription) -> None:
        self.destroyed_subscriptions.append(subscription)
        if self.bus is not None:
            self.bus.unregister_subscription(subscription)
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)

    def destroy_timer(self, timer: FakeTimer) -> None:
        timer.cancel()
        self.destroyed_timers.append(timer)
        if timer in self.timers:
            self.timers.remove(timer)

    def destroy_node(self) -> None:
        self.destroyed = True


# ---------------------------------------------------------------------------
# Controller fakes for ControlProcessor tests
# ---------------------------------------------------------------------------


class FakeWheel:
    """Minimal WheelController double tracking every speed/position command."""

    def __init__(self) -> None:
        self.left_speed_commands: list[float] = []
        self.right_speed_commands: list[float] = []
        self.position_commands: list[tuple] = []
        self.emergency_stop_calls = 0

    def command_left_wheel_speed(self, speed: float) -> None:
        self.left_speed_commands.append(speed)

    def command_right_wheel_speed(self, speed: float) -> None:
        self.right_speed_commands.append(speed)

    def command_position(self, left_mm: float, right_mm: float, rpm_limit: float, relative: bool) -> bool:
        self.position_commands.append((left_mm, right_mm, rpm_limit, relative))
        return True

    def emergency_stop(self) -> None:
        self.emergency_stop_calls += 1


class FakeWinch:
    """Minimal WinchController double with configurable availability/brake state."""

    def __init__(self, available: bool = True, motor_brake: bool = False) -> None:
        self._available = available
        self._motor_brake = motor_brake
        self.speed_commands: list[float] = []
        self.rpm_commands: list[float] = []

    def get_available(self) -> bool:
        return self._available

    def get_motor_brake(self) -> bool:
        return self._motor_brake

    def command_speed_mmps(self, value: float) -> None:
        self.speed_commands.append(value)

    def command_speed_rpm(self, value: float) -> None:
        self.rpm_commands.append(value)


class FakeTeensyPublisher:
    """Minimal publisher double for Teensy topic publishers."""

    def __init__(self) -> None:
        self.published: list[Any] = []

    def publish(self, msg: Any) -> None:
        self.published.append(msg)


class FakeTeensy:
    """Minimal TeensyController double tracking every command."""

    def __init__(self) -> None:
        self.prop_left_joint_pub = FakeTeensyPublisher()
        self.prop_right_joint_pub = FakeTeensyPublisher()
        self.ef_move_arm_rail_speed_pub = FakeTeensyPublisher()
        self.ef_spray_trigger_pub = FakeTeensyPublisher()
        self.ef_move_top_rail_speed_pub = FakeTeensyPublisher()
        self.prop_left_pwm_pub = FakeTeensyPublisher()
        self.prop_right_pwm_pub = FakeTeensyPublisher()
        self.ef_spray_pitch_speed_pub = FakeTeensyPublisher()
        self.yaw_commands: list[float] = []
        self.rail_speed_commands: list[float] = []
        self.force_commands: list[tuple] = []
        self.trigger_values: list[int] = []
        self._imu_yaw: float = 0.0

    def setYawAngle(self, angle: float) -> None:
        self.yaw_commands.append(angle)

    def setArmRailSpeed(self, value: float) -> None:
        self.rail_speed_commands.append(value)

    def set_ef_force(self, fx: float, fy: float) -> None:
        self.force_commands.append((fx, fy))

    def setSprayTrigger(self, value: int) -> None:
        self.trigger_values.append(value)

    def get_status_value(self, key: str) -> Any:
        if key == "imu_yaw":
            return self._imu_yaw
        return 0.0


class FakeEsp32Valve:
    """Minimal ESP32ValveController double."""

    def __init__(self) -> None:
        self.valve_turn_commands: list[float] = []

    def setValveTurn(self, value: float) -> None:
        self.valve_turn_commands.append(value)


class FakeOverlay:
    """Minimal OverlayController double with configurable left/right option."""

    def __init__(self, left: str = "None", right: str = "None") -> None:
        self._left = left
        self._right = right

    def get_left_selected_option(self) -> str:
        return self._left

    def get_right_selected_option(self) -> str:
        return self._right

    def display_name_for_option(self, option: str) -> str:
        return option


class FakeHeartbeatHandler:
    """Minimal UIHeartbeatHandler double with configurable status values."""

    def __init__(self, base_status: int = 0x00, ef_status: int = 0x00) -> None:
        self._base_status = base_status
        self._ef_status = ef_status

    def get_base_status(self) -> int:
        return self._base_status

    def get_ef_status(self) -> int:
        return self._ef_status


class FakeStateStore:
    """Minimal StateStore double."""

    def __init__(self) -> None:
        self.display_message: str = ""
        self.control_mode: str = "base"
        self.controller_heartbeat_state: int = 0
