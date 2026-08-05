#!/usr/bin/env python3

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any, TypedDict, cast

from geometry_msgs.msg import Twist, Vector3
from paint_interfaces.msg import TeensyStatus, TeensyYaw
from PySide6.QtCore import QTimer, Signal
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Float32MultiArray, Int32, Int32MultiArray

from paint_controller.controllers._base import RosStatusController
from paint_controller.core.ros_telemetry import RosTelemetryBridge

if TYPE_CHECKING:
    from paint_controller.core.ros_io import RosCommandBus
    from paint_controller.core.settings import SettingsManager


class TeensyStatusDict(TypedDict, total=False):
    """Type hints for Teensy status dict. All fields optional (populated incrementally)."""

    # ROS-driven fields (from TeensyStatus message)
    available: bool
    top_rail_position: float
    top_rail_speed: float
    top_rail_current: float
    arm_rail_position: float
    arm_rail_speed: float
    arm_rail_current: float
    arm_extension_dist: float
    arm_sensor_dist: float
    voltage: float
    temperature: float
    current: float
    run_time: int
    loop_time: float
    loop_time_counter: int
    relay_on: bool
    enabled: bool
    left_prop_position: float
    left_prop_pwm: int
    right_prop_position: float
    right_prop_pwm: int
    imu_acc_x: float
    imu_acc_y: float
    imu_acc_z: float
    imu_angular_acc_x: float
    imu_angular_acc_y: float
    imu_angular_acc_z: float
    imu_pitch: float
    imu_roll: float
    imu_yaw: float
    spray_gun_pitch: float
    gimbal_pitch_motor_angle: float
    gimbal_pitch_motor_current: float
    gimbal_pitch_motor_temp: float
    gimbal_roll_motor_angle: float
    gimbal_roll_motor_current: float
    gimbal_roll_motor_temp: float
    spray_gun_trigger: bool
    yaw_enabled: bool
    yaw_command: float
    yaw_pid_p: float
    yaw_pid_i: float
    yaw_pid_d: float
    yaw_pwm: int
    target_yaw: float
    valve_turn: float
    valve_motor_current: int
    valve_position: float
    valve_rate: float
    total_volume: float
    valve_motor_connected: bool
    flow_meter_connected: bool
    # User-controlled fields (set locally, NOT from ROS message)
    relay_enabled: bool
    stability_enabled: bool
    auto_correction_enabled: bool
    roller_steering_enabled: bool
    swing_damping_enabled: bool
    spray_gun_leveling_enabled: bool
    lidar_power: bool


# Fields set locally by UI actions that must survive ROS status updates
_USER_CONTROLLED_FIELDS = (
    "relay_enabled",
    "stability_enabled",
    "auto_correction_enabled",
    "roller_steering_enabled",
    "swing_damping_enabled",
    "spray_gun_leveling_enabled",
    "lidar_power",
)


class TeensyController(RosStatusController):
    # Define Qt signals
    status_changed = Signal(dict)
    connection_changed = Signal(bool)
    spray_gun_leveling_changed = Signal(bool)
    spray_gun_led_changed = Signal(bool)
    auto_correction_enabled_changed = Signal(bool)
    stability_enabled_changed = Signal(bool)
    thrust_force_changed = Signal(float)
    thrust_force_enabled_changed = Signal(bool)
    roller_steering_enabled_changed = Signal(bool)
    swing_damping_enabled_changed = Signal(bool)

    def __init__(
        self,
        node: Node,
        settings_manager: SettingsManager | None = None,
        command_bus: RosCommandBus | None = None,
        *,
        io_shell: object | None = None,
    ) -> None:
        super().__init__(node, io_shell=io_shell)  # type: ignore[arg-type]
        self._settings_manager = settings_manager
        self._command_bus = command_bus

        # Initialize status variables with default values instead of empty dictionary
        self._status: TeensyStatusDict = {
            "available": False,
            "top_rail_position": 0.0,
            "top_rail_speed": 0.0,
            "top_rail_current": 0.0,
            "arm_rail_position": 0.0,
            "arm_rail_speed": 0.0,
            "arm_rail_current": 0.0,
            "arm_extension_dist": 0.0,
            "arm_sensor_dist": 0.0,
            "voltage": 20,
            "temperature": 0.0,
            "current": 0.0,
            "run_time": 0,
            "loop_time": 0,
            "loop_time_counter": 0,
            "relay_on": False,
            "relay_enabled": False,
            "enabled": False,
            "left_prop_position": 0.0,
            "left_prop_pwm": 0,
            "right_prop_position": 0.0,
            "right_prop_pwm": 0,
            "imu_acc_x": 0.0,
            "imu_acc_y": 0.0,
            "imu_acc_z": 0.0,
            "imu_angular_acc_x": 0.0,
            "imu_angular_acc_y": 0.0,
            "imu_angular_acc_z": 0.0,
            "imu_pitch": 0.0,
            "imu_roll": 0.0,
            "imu_yaw": 0.0,
            "spray_gun_pitch": 0.0,
            "gimbal_pitch_motor_angle": 0.0,
            "gimbal_pitch_motor_current": 0.0,
            "gimbal_pitch_motor_temp": 0.0,
            "gimbal_roll_motor_angle": 0.0,
            "gimbal_roll_motor_current": 0.0,
            "gimbal_roll_motor_temp": 0.0,
            "spray_gun_trigger": False,
            "spray_gun_leveling_enabled": False,
            "auto_correction_enabled": False,
            "yaw_enabled": False,
            "yaw_command": 80.0,
            "yaw_pid_p": 0.0,
            "yaw_pid_i": 0.0,
            "yaw_pid_d": 0.0,
            "yaw_pwm": 0,
            "target_yaw": 0.0,
            "valve_turn": 0.0,
            "valve_motor_current": 0,
            "valve_position": 0.0,
            "valve_rate": 0.0,
            "total_volume": 0.0,
            "valve_motor_connected": False,
            "flow_meter_connected": False,
            "lidar_power": False,
        }

        self._status_lock = threading.Lock()
        self._last_ui_update_time = 0
        self._last_ui_update_interval = 0.1  # seconds

        # Member state variables
        self._enabled = False
        self._relay_enabled = False
        self._stability_enabled = False
        self._spray_gun_leveling_enabled = False
        self._auto_correction_enabled = False
        self._spray_gun_led_on = False
        self._lidar_power = False
        self._target_yaw = 0.0
        self._roller_steering_enabled = False
        self._swing_damping_enabled = False
        # Get thrust_force from settings_manager if available, otherwise use default
        if self._settings_manager is not None:
            self._thrust_force = self._settings_manager.get("thrust_force") or -1.0
            self._settings_manager.thrust_force_changed.connect(self._on_thrust_force_setting_changed)
        else:
            self._thrust_force = -1.0
        self._thrust_force_enabled = False

        # Thrust force ramping state
        self._current_thrust_force = 0.0  # Current ramped thrust value
        self._target_thrust_force = 0.0  # Target thrust value (either 0 or _thrust_force)
        self._last_published_thrust = 0.0  # Last published value to avoid redundant messages
        if self._settings_manager is not None:
            self._thrust_ramp_rate = self._settings_manager.get("thrust_ramp_rate", 1.0)
            self._settings_manager.thrust_ramp_rate_changed.connect(self._on_thrust_ramp_rate_changed)
        else:
            self._thrust_ramp_rate = 1.0

        # TD-056 residual + Level C P2: bridge parented to io_shell.
        self._telemetry = RosTelemetryBridge(
            self._apply_status_snapshot, parent=self._lifetime_parent()
        )

        # Configure publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()

        # Create connection check timer
        self._start_availability_timer()

        # Create thrust ramping timer (10Hz)
        self._thrust_ramp_timer = QTimer(self)
        self._thrust_ramp_timer.timeout.connect(self._update_thrust_ramp)
        self._thrust_ramp_timer.start(100)  # 100ms = 10Hz

    def _bind_cmd(self, publisher: Any, *, continuous: bool = False) -> Any:
        """TD-054: wrap command publishers; call sites keep ``.publish(msg)``."""
        bus = self._command_bus
        if bus is None:
            return publisher
        from paint_controller.core.ros_io import TrafficKind

        kind = TrafficKind.CONTINUOUS if continuous else TrafficKind.ONESHOT
        return bus.bind(publisher, kind=kind)

    def _setup_publishers(self) -> None:
        """Set up ROS publishers for Teensy control (TD-054 bound when command_bus set)."""
        self.teensy_relay_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/relay/cmd", 1))
        self.teensy_enable_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/enable/cmd", 1))
        self.ef_move_top_rail_speed_pub = self._bind_cmd(
            self._node.create_publisher(Float32, "teensy/top_rail/speed/cmd", 1),
            continuous=True,
        )
        self.ef_home_top_rail_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/top_rail/home/cmd", 1))
        self.ef_move_arm_rail_speed_pub = self._bind_cmd(
            self._node.create_publisher(Float32, "teensy/arm_rail/speed/cmd", 1),
            continuous=True,
        )
        self.ef_move_arm_rail_pos_pub = self._bind_cmd(
            self._node.create_publisher(Int32, "teensy/arm/extend/cmd", 1)
        )
        self.ef_home_arm_rail_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/arm/home/cmd", 1))
        self.prop_left_pwm_pub = self._bind_cmd(
            self._node.create_publisher(Int32, "teensy/prop/left/pwm/cmd", 1),
            continuous=True,
        )
        self.prop_right_pwm_pub = self._bind_cmd(
            self._node.create_publisher(Int32, "teensy/prop/right/pwm/cmd", 1),
            continuous=True,
        )
        self.prop_left_joint_pub = self._bind_cmd(
            self._node.create_publisher(Float32, "teensy/prop/left/joint/cmd", 1),
            continuous=True,
        )
        self.prop_right_joint_pub = self._bind_cmd(
            self._node.create_publisher(Float32, "teensy/prop/right/joint/cmd", 1),
            continuous=True,
        )
        self.ef_spray_trigger_pub = self._bind_cmd(
            self._node.create_publisher(Int32, "teensy/spray_gun/trigger/cmd", 1),
            continuous=True,
        )
        self.ef_spray_pitch_speed_pub = self._bind_cmd(
            self._node.create_publisher(Int32, "teensy/spray_gun/pitch/speed/cmd", 1),
            continuous=True,
        )
        self.ef_spray_pitch_pub = self._bind_cmd(
            self._node.create_publisher(Float32MultiArray, "teensy/spray_gun/pitch/angle/cmd", 1)
        )
        self.ef_spray_led_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/spray_gun/led/cmd", 1))
        # Stability controller publishers (decoupled force and yaw control)
        self.stability_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "stability_controller/enable/cmd", 1)
        )
        self.stability_yaw_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "stability_controller/yaw_control/enable/cmd", 1)
        )
        self.stability_yaw_angle_pub = self._bind_cmd(
            self._node.create_publisher(Float32, "stability_controller/yaw_control/angle/cmd", 1)
        )
        self.stability_short_param_pub = self._bind_cmd(
            self._node.create_publisher(TeensyYaw, "stability_controller/yaw_control/short_params/cmd", 1)
        )
        self.stability_long_param_pub = self._bind_cmd(
            self._node.create_publisher(TeensyYaw, "stability_controller/yaw_control/long_params/cmd", 1)
        )
        self.stability_auto_correction_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "stability_controller/yaw_control/auto_correction/cmd", 1)
        )
        self.stability_force_pub = self._bind_cmd(
            self._node.create_publisher(Twist, "stability_controller/force/cmd", 1),
            continuous=True,
        )
        self.ef_spray_level_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "teensy/spray_gun/leveling_enable/cmd", 1)
        )
        self.ef_lidar_power_pub = self._bind_cmd(self._node.create_publisher(Bool, "unilidar/power", 1))
        self.ef_tap_freq_pub = self._bind_cmd(
            self._node.create_publisher(Int32MultiArray, "teensy/tapper/tap_freq/cmd", 1)
        )
        self.ef_tap_once_pub = self._bind_cmd(self._node.create_publisher(Int32, "teensy/tapper/tap_once/cmd", 1))
        self.ef_tap_stop_pub = self._bind_cmd(self._node.create_publisher(Bool, "teensy/tapper/stop/cmd", 1))
        self.roller_steering_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "teensy/roller/steering/enable/cmd", 1)
        )
        self.swing_damping_enable_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "stability_controller/swing_damping/enable/cmd", 1)
        )

    def _setup_subscribers(self) -> None:
        """Set up ROS subscribers"""
        self._node.create_subscription(TeensyStatus, "teensy/status", self._status_callback, 10)

    # --- Publish helpers to reduce boilerplate ---

    def _publish_float32(self, publisher: Any, value: float) -> None:
        msg = Float32()
        msg.data = float(value)
        publisher.publish(msg)

    def _publish_int32(self, publisher: Any, value: int) -> None:
        msg = Int32()
        msg.data = int(value)
        publisher.publish(msg)

    def _publish_bool(self, publisher: Any, value: bool) -> None:
        msg = Bool()
        msg.data = value
        publisher.publish(msg)

    def _check_availability(self) -> None:
        """Check if the Teensy is still connected"""
        current_time = time.time()

        # Calculate time since last status update
        time_since_last_update = current_time - self._last_status_update_time

        # If it's been too long since the last update, consider disconnected
        if time_since_last_update > self._connection_timeout:
            if self.set_available(False):
                self._node.get_logger().warning(
                    f"Teensy considered disconnected: {time_since_last_update:.1f}s since last status update"
                )
                self.connection_changed.emit(False)
        elif self.set_available(True):
            self._node.get_logger().info("Teensy connection established")
            self.connection_changed.emit(True)

    def _get_status_snapshot(self) -> TeensyStatusDict:
        with self._status_lock:
            return self._status.copy()

    def _update_status_fields(self, **fields: Any) -> TeensyStatusDict:
        with self._status_lock:
            self._status.update(cast(TeensyStatusDict, fields))
            return self._status.copy()

    @staticmethod
    def _device_snapshot_from_msg(msg: TeensyStatus) -> dict[str, Any]:
        """ROS-derived fields only — never includes _USER_CONTROLLED_FIELDS."""
        return {
            "available": True,
            "top_rail_position": msg.top_rail_position,
            "top_rail_speed": msg.top_rail_speed,
            "top_rail_current": msg.top_rail_current,
            "arm_rail_position": msg.arm_rail_position,
            "arm_rail_speed": msg.arm_rail_speed,
            "arm_rail_current": msg.arm_rail_current,
            "arm_extension_dist": msg.arm_extension_dist,
            "arm_sensor_dist": msg.arm_sensor_dist,
            "voltage": msg.voltage,
            "temperature": msg.temperature,
            "current": msg.current,
            "run_time": msg.runtime,
            "loop_time": msg.looptime,
            "loop_time_counter": msg.looptime_counter,
            "relay_on": bool(msg.relay_on),
            "enabled": msg.enabled,
            "left_prop_position": msg.left_prop_position / 100,
            "left_prop_pwm": msg.left_prop_pwm,
            "right_prop_position": msg.right_prop_position / 100,
            "right_prop_pwm": msg.right_prop_pwm,
            "imu_acc_x": msg.linear_acceleration.x,
            "imu_acc_y": msg.linear_acceleration.y,
            "imu_acc_z": msg.linear_acceleration.z,
            "imu_angular_acc_x": msg.angular_velocity.x,
            "imu_angular_acc_y": msg.angular_velocity.y,
            "imu_angular_acc_z": msg.angular_velocity.z,
            "imu_pitch": msg.orientation.x,
            "imu_roll": msg.orientation.y,
            "imu_yaw": msg.orientation.z,
            "spray_gun_pitch": msg.spray_gun_pitch,
            "gimbal_pitch_motor_angle": msg.gimbal_pitch_motor_angle,
            "gimbal_pitch_motor_current": msg.gimbal_pitch_motor_current,
            "gimbal_pitch_motor_temp": msg.gimbal_pitch_motor_temp,
            "gimbal_roll_motor_angle": msg.gimbal_roll_motor_angle,
            "gimbal_roll_motor_current": msg.gimbal_roll_motor_current,
            "gimbal_roll_motor_temp": msg.gimbal_roll_motor_temp,
            "spray_gun_trigger": msg.spray_gun_trigger,
            "yaw_enabled": msg.yaw_enabled,
            "yaw_command": msg.yaw_command,
            "yaw_pid_p": msg.yaw_pid_p,
            "yaw_pid_i": msg.yaw_pid_i,
            "yaw_pid_d": msg.yaw_pid_d,
            "target_yaw": msg.yaw_command,
            "recv_mono": time.time(),
        }

    def _status_callback(self, msg: TeensyStatus) -> None:
        """ROS spin: post device POD only — no status_changed emit."""
        try:
            self._telemetry.post(self._device_snapshot_from_msg(msg))
        except Exception as e:
            self._node.get_logger().error(f"Error in Teensy status callback: {e}")

    def _apply_status_snapshot(self, snap: object) -> None:
        """Main thread: merge ROS device keys; preserve user-controlled fields."""
        if not isinstance(snap, dict):
            self._node.get_logger().error(f"Teensy apply expected dict, got {type(snap)}")
            return

        recv = float(snap.get("recv_mono", time.time()))
        device_keys = {k: v for k, v in snap.items() if k != "recv_mono" and k not in _USER_CONTROLLED_FIELDS}

        with self._status_lock:
            self._status.update(cast(TeensyStatusDict, device_keys))
            status_snapshot = self._status.copy()

        self._last_status_update_time = recv

        current_time = time.time()
        time_since_last_update = current_time - self._last_ui_update_time
        if time_since_last_update > self._last_ui_update_interval:
            self._last_ui_update_time = current_time
            self.status_changed.emit(status_snapshot)

    def get_status(self) -> TeensyStatusDict:
        """Get current Teensy status"""
        return self._get_status_snapshot()

    def get_status_value(self, key: str) -> Any:
        """Get a specific status value by key"""
        with self._status_lock:
            return self._status.get(key)

    #############################################
    ### Device command methods (plain HAL — QML via TeensyActions / TuningActions)
    ### Presentation formatting lives in TeensyStatus / pure helpers, not here.
    #############################################

    def setEnabled(self, enabled: bool):
        """Enable/disable Teensy control"""
        self._publish_bool(self.teensy_enable_pub, enabled)
        self._node.get_logger().info(f"Teensy {'enabled' if enabled else 'disabled'}")
        self.status_changed.emit(self._get_status_snapshot())

    def setRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self._relay_enabled = enabled
        status_snapshot = self._update_status_fields(relay_enabled=enabled)
        self._publish_bool(self.teensy_relay_pub, enabled)
        self._node.get_logger().info(f"Teensy relay {'enabled' if enabled else 'disabled'}")
        self.status_changed.emit(status_snapshot)

    def setTopRailSpeed(self, speed: float):
        """Set the top rail speed"""
        self._publish_float32(self.ef_move_top_rail_speed_pub, speed)

    def homeTopRail(self, home: bool):
        """Home the top rail"""
        self._publish_bool(self.ef_home_top_rail_pub, True)

    def setArmRailSpeed(self, speed: float):
        """Set the arm rail speed"""
        self._publish_float32(self.ef_move_arm_rail_speed_pub, speed)

    def extendArm(self, dist: int):
        self._publish_int32(self.ef_move_arm_rail_pos_pub, dist)

    def homeArm(self, home: bool):
        """Home the arm rail"""
        self._publish_bool(self.ef_home_arm_rail_pub, home)

    def setLeftPropPWM(self, pwm: int):
        """Set the left propeller PWM"""
        self._publish_int32(self.prop_left_pwm_pub, pwm)

    def setRightPropPWM(self, pwm: int):
        """Set the right propeller PWM"""
        self._publish_int32(self.prop_right_pwm_pub, pwm)

    def setLeftPropJoint(self, position: float):
        """Set the left propeller joint position"""
        self._publish_float32(self.prop_left_joint_pub, position)

    def setRightPropJoint(self, position: float):
        """Set the right propeller joint position"""
        self._publish_float32(self.prop_right_joint_pub, position)

    def setSprayTrigger(self, value: int):
        """Set the spray gun trigger value"""
        self._publish_int32(self.ef_spray_trigger_pub, value)

    def setSprayPitchSpeed(self, speed: int):
        """Set the spray gun pitch speed"""
        self._publish_int32(self.ef_spray_pitch_speed_pub, speed)

    def setSprayGunLevelingEnabled(self, enabled: bool):
        """Enable/disable spray gun leveling"""
        self._node.get_logger().info(f"Spray gun leveling {'enabled' if enabled else 'disabled'}")
        self._publish_bool(self.ef_spray_level_enable_pub, enabled)
        self._spray_gun_leveling_enabled = enabled
        status_snapshot = self._update_status_fields(spray_gun_leveling_enabled=enabled)
        self.spray_gun_leveling_changed.emit(enabled)
        self.status_changed.emit(status_snapshot)

    def setSprayGunPitchAngle(self, angle: float, speed: float):
        """Set the spray gun pitch angle and speed"""
        self._node.get_logger().info(f"Setting spray gun pitch angle to {angle} with speed {speed}")
        msg = Float32MultiArray()
        msg.data = [float(angle), float(speed)]
        self.ef_spray_pitch_pub.publish(msg)

    def setSprayGunLED(self, on: bool):
        """Turn the spray gun LED on/off"""
        self._node.get_logger().info(f"Spray gun LED {'on' if on else 'off'}")
        self._publish_bool(self.ef_spray_led_pub, on)
        self._spray_gun_led_on = on
        self.spray_gun_led_changed.emit(on)

    def setLidarPower(self, on: bool):
        """Turn the Lidar power on/off"""
        self._node.get_logger().info(f"Lidar power {'on' if on else 'off'}")
        self._lidar_power = on
        status_snapshot = self._update_status_fields(lidar_power=on)
        self._publish_bool(self.ef_lidar_power_pub, on)
        self.status_changed.emit(status_snapshot)

    def setStabilityEnabled(self, enabled: bool):
        """Enable/disable stability controller (master enable for force and yaw control)"""
        self._stability_enabled = enabled
        status_snapshot = self._update_status_fields(stability_enabled=enabled)
        self._publish_bool(self.stability_enable_pub, enabled)
        self._node.get_logger().info(f"Stability controller {'enabled' if enabled else 'disabled'}")
        self.stability_enabled_changed.emit(enabled)
        self.status_changed.emit(status_snapshot)

    def setYawEnabled(self, enabled: bool):
        """Enable/disable yaw control"""
        self._publish_bool(self.stability_yaw_enable_pub, enabled)

    def setAutoCorrectionEnabled(self, enabled: bool):
        """Enable/disable yaw auto correction"""
        self._auto_correction_enabled = enabled
        status_snapshot = self._update_status_fields(auto_correction_enabled=enabled)
        self._publish_bool(self.stability_auto_correction_enable_pub, enabled)
        self._node.get_logger().info(f"Auto correction {'enabled' if enabled else 'disabled'}")
        self.auto_correction_enabled_changed.emit(enabled)
        self.status_changed.emit(status_snapshot)

    def setRollerSteeringEnabled(self, enabled: bool):
        """Enable/disable roller steering"""
        self._roller_steering_enabled = enabled
        status_snapshot = self._update_status_fields(roller_steering_enabled=enabled)
        self._publish_bool(self.roller_steering_enable_pub, enabled)
        self._node.get_logger().info(f"Roller steering {'enabled' if enabled else 'disabled'}")
        self.roller_steering_enabled_changed.emit(enabled)
        self.status_changed.emit(status_snapshot)

    def setSwingDampingEnabled(self, enabled: bool):
        """Enable/disable swing damping"""
        self._swing_damping_enabled = enabled
        status_snapshot = self._update_status_fields(swing_damping_enabled=enabled)
        self._publish_bool(self.swing_damping_enable_pub, enabled)
        self._node.get_logger().info(f"Swing damping {'enabled' if enabled else 'disabled'}")
        self.swing_damping_enabled_changed.emit(enabled)
        self.status_changed.emit(status_snapshot)

    def setYawAngle(self, angle: float):
        """Set the yaw angle"""
        self._publish_float32(self.stability_yaw_angle_pub, angle)

    def setShortParams(self, p: float, i: float, d: float):
        """Set the yaw PID parameters"""
        msg = TeensyYaw()
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        self.stability_short_param_pub.publish(msg)

    def setLongParams(self, p: float, i: float, d: float):
        """Set the yaw PID parameters"""
        msg = TeensyYaw()
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        self.stability_long_param_pub.publish(msg)

    def startTapFreq(self, power: float, period: float):
        """Start tapping the frequency"""
        self._node.get_logger().info(f"Starting tap frequency with Power: {power} Period: {period}")
        msg = Int32MultiArray()
        msg.data = [int(power), int(period * 1000)]
        self.ef_tap_freq_pub.publish(msg)

    def tapOnce(self, power: float):
        """Tap once"""
        self._node.get_logger().info(f"Tapping once with Power: {power}")
        self._publish_int32(self.ef_tap_once_pub, int(power))

    def tapStop(self, power: float):
        """Stop tapping"""
        self._node.get_logger().info(f"Stopping tap with Power: {power}")
        self._publish_bool(self.ef_tap_stop_pub, True)

    def setThrustForceEnabled(self, enabled: bool):
        """Toggle thrust force on/off with ramping."""
        self.set_thrust_force_enabled(enabled)

    def setThrustForceInstant(self, enabled: bool):
        """Toggle thrust force on/off instantly without ramping."""
        self.set_thrust_force_instant(enabled)

    def _set_yaw_control(self, enabled: bool, target: float, p: float, i: float, d: float, pwm: int):
        """Internal method to send yaw control message"""
        msg = TeensyYaw()
        msg.yaw_enabled = enabled
        msg.yaw_command = target
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        msg.yaw_pwm = pwm
        self.ef_yaw_control_pub.publish(msg)
        self._node.get_logger().info(
            f"Yaw control {'enabled' if enabled else 'disabled'} with Target: {target} P:{p} I:{i} D:{d} PWM:{pwm}"
        )

    def set_ef_force(self, Fx: float, Fy: float):
        """Internal method to send EF force values"""
        # Create a Twist message for EF force
        msg = Twist()
        msg.linear = Vector3(x=Fx, y=Fy, z=0.0)

        # Publish to the appropriate topic
        if hasattr(self, "stability_force_pub"):
            self.stability_force_pub.publish(msg)
            self._node.get_logger().info(f"Sent EF force: Fx={Fx}, Fy={Fy}")
        else:
            self._node.get_logger().error("Stability force publisher not initialized. Cannot send force values.")

    def get_all_status(self) -> TeensyStatusDict:
        return self._get_status_snapshot()

    # Plain Python properties (Level B) — QML surface is TeensyStatus / Actions.
    @property
    def available(self) -> bool:
        return self.get_available()

    @property
    def all_status(self) -> TeensyStatusDict:
        return self.get_all_status()

    @property
    def spray_gun_leveling_enabled(self) -> bool:
        return self._spray_gun_leveling_enabled

    @property
    def spray_gun_led_on(self) -> bool:
        return self._spray_gun_led_on

    @property
    def auto_correction_enabled(self) -> bool:
        return self._auto_correction_enabled

    @property
    def stability_enabled(self) -> bool:
        return self._stability_enabled

    @property
    def roller_steering_enabled(self) -> bool:
        return self._roller_steering_enabled

    @property
    def swing_damping_enabled(self) -> bool:
        return self._swing_damping_enabled

    def get_thrust_force(self) -> float:
        """Get current thrust force value"""
        return self._thrust_force

    def set_thrust_force(self, value: float) -> None:
        """Set thrust force value with range constraint [-1.0, 1.0]"""
        # Clamp value to [-1.0, 1.0]
        clamped_value = max(-1.5, min(1.5, value))

        if self._thrust_force != clamped_value:
            self._thrust_force = clamped_value
            self.thrust_force_changed.emit(self._thrust_force)
            self._node.get_logger().info(f"Thrust force set to {self._thrust_force:.2f}")

    def get_thrust_force_enabled(self) -> bool:
        """Get current thrust force enabled state"""
        return self._thrust_force_enabled

    def set_thrust_force_enabled(self, enabled: bool) -> None:
        """Toggle thrust force on/off with ramping"""
        if self._thrust_force_enabled != enabled:
            self._thrust_force_enabled = enabled
            self.thrust_force_enabled_changed.emit(self._thrust_force_enabled)

            if enabled:
                # Set target to current thrust force, ramping will handle the rest
                self._target_thrust_force = self._thrust_force
                self._node.get_logger().info(f"Thrust force enabled: ramping to {self._thrust_force:.2f}")
            else:
                # Set target to 0, ramping will handle the rest
                self._target_thrust_force = 0.0
                self._node.get_logger().info("Thrust force disabled: ramping to 0.0")

    def set_thrust_force_instant(self, enabled: bool) -> None:
        """Toggle thrust force on/off instantly (without ramping)"""
        if self._thrust_force_enabled != enabled:
            self._thrust_force_enabled = enabled
            self.thrust_force_enabled_changed.emit(self._thrust_force_enabled)

            # Set both current and target immediately for instant response
            if enabled:
                self._current_thrust_force = self._thrust_force
                self._target_thrust_force = self._thrust_force
                self.set_ef_force(0.0, self._thrust_force)
                self._node.get_logger().info(f"Thrust force enabled instantly: {self._thrust_force:.2f}")
            else:
                self._current_thrust_force = 0.0
                self._target_thrust_force = 0.0
                self.set_ef_force(0.0, 0.0)
                self._node.get_logger().info("Thrust force disabled instantly")

    @property
    def thrust_force(self) -> float:
        return self.get_thrust_force()

    @thrust_force.setter
    def thrust_force(self, value: float) -> None:
        self.set_thrust_force(value)

    @property
    def thrust_force_enabled(self) -> bool:
        return self.get_thrust_force_enabled()

    @thrust_force_enabled.setter
    def thrust_force_enabled(self, value: bool) -> None:
        self.set_thrust_force_enabled(value)

    def _on_thrust_force_setting_changed(self, new_value: float):
        """Handle thrust_force change from SettingsManager"""
        # Update internal value without re-triggering setting save
        clamped_value = max(-1.0, min(1.0, new_value))
        if self._thrust_force != clamped_value:
            self._thrust_force = clamped_value
            self.thrust_force_changed.emit(self._thrust_force)
            self._node.get_logger().info(f"Thrust force updated from settings: {clamped_value}")

    def _on_thrust_ramp_rate_changed(self, new_value: float):
        """Handle thrust_ramp_rate change from SettingsManager"""
        self._thrust_ramp_rate = new_value
        self._node.get_logger().info(f"Thrust ramp rate updated to: {new_value}")

    def suppress_continuous_thrust(self) -> None:
        """TD-054: zero thrust ramp state and publish zero force (safety halt)."""
        was_enabled = self._thrust_force_enabled
        self._thrust_force_enabled = False
        self._target_thrust_force = 0.0
        self._current_thrust_force = 0.0
        if was_enabled:
            self.thrust_force_enabled_changed.emit(False)
        if abs(self._last_published_thrust) > 0.001:
            self.set_ef_force(0.0, 0.0)
            self._last_published_thrust = 0.0

    def _update_thrust_ramp(self):
        """Update ramped thrust force at 10Hz"""
        # TD-054: after suppress_continuous_thrust, target and current stay 0.
        # Calculate the delta based on ramp rate (thrust/second)
        # At 10Hz, each step is 0.1 seconds
        ramp_step = self._thrust_ramp_rate * 0.1  # 0.1 second per update

        # Calculate the difference between current and target
        delta = self._target_thrust_force - self._current_thrust_force

        # Only update if we haven't reached the target
        if abs(delta) < ramp_step:
            # Reached target, set exactly and publish once if changed
            if self._current_thrust_force != self._target_thrust_force:
                self._current_thrust_force = self._target_thrust_force
                # Only publish if the value has changed meaningfully
                if abs(self._current_thrust_force - self._last_published_thrust) > 0.001:
                    self.set_ef_force(0.0, self._current_thrust_force)
                    self._last_published_thrust = self._current_thrust_force
        else:
            # Move towards target by ramp_step
            if delta > 0:
                self._current_thrust_force += ramp_step
            else:
                self._current_thrust_force -= ramp_step
            # Only publish if the value has changed meaningfully (>0.001 threshold)
            if abs(self._current_thrust_force - self._last_published_thrust) > 0.001:
                self.set_ef_force(0.0, self._current_thrust_force)
                self._last_published_thrust = self._current_thrust_force

    def cleanup(self) -> None:
        """Clean up resources when shutting down"""
        super().cleanup()
        if hasattr(self, "_thrust_ramp_timer") and self._thrust_ramp_timer.isActive():
            self._thrust_ramp_timer.stop()
