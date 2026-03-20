#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Dict, Optional, Any, TypedDict, Union
import time
import threading

from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Float32MultiArray, Int32, Int32MultiArray
from geometry_msgs.msg import Twist, Vector3
from paint_interfaces.msg import TeensyStatus, TeensyYaw, MoveWinchLength

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer


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


# Fields set locally by UI actions that must survive ROS status updates
_USER_CONTROLLED_FIELDS = (
    'relay_enabled',
    'stability_enabled',
    'auto_correction_enabled',
    'roller_steering_enabled',
    'swing_damping_enabled',
    'spray_gun_leveling_enabled',
)


class TeensyController(QObject):
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
    
    def __init__(self, robot_controller):
        super().__init__()
        self._robot_controller = robot_controller  # Store reference to the robot controller
        
        # Initialize status variables with default values instead of empty dictionary
        self._status: TeensyStatusDict = {
            'available': False,
            'top_rail_position': 0.0,
            'top_rail_speed': 0.0,
            'top_rail_current': 0.0,
            'arm_rail_position': 0.0,
            'arm_rail_speed': 0.0,
            'arm_rail_current': 0.0,
            'arm_extension_dist': 0.0,
            'arm_sensor_dist': 0.0,
            'voltage': 20,
            'temperature': 0.0,
            'current': 0.0,
            'run_time': 0,
            'loop_time': 0,
            'loop_time_counter': 0,
            'relay_on': False,
            'relay_enabled': False,
            'enabled': False,
            'left_prop_position': 0.0,
            'left_prop_pwm': 0,
            'right_prop_position': 0.0,
            'right_prop_pwm': 0,
            'imu_acc_x': 0.0,
            'imu_acc_y': 0.0,
            'imu_acc_z': 0.0,
            'imu_angular_acc_x': 0.0,
            'imu_angular_acc_y': 0.0,
            'imu_angular_acc_z': 0.0,
            'imu_pitch': 0.0,
            'imu_roll': 0.0,
            'imu_yaw': 0.0,
            'spray_gun_pitch': 0.0,
            'gimbal_pitch_motor_angle': 0.0,
            'gimbal_pitch_motor_current': 0.0,
            'gimbal_pitch_motor_temp': 0.0,
            'gimbal_roll_motor_angle': 0.0,
            'gimbal_roll_motor_current': 0.0,
            'gimbal_roll_motor_temp': 0.0,
            'spray_gun_trigger': False,
            'spray_gun_leveling_enabled': False,
            'auto_correction_enabled': False,
            'yaw_enabled': False,
            'yaw_command': 80.0,
            'yaw_pid_p': 0.0,
            'yaw_pid_i': 0.0,
            'yaw_pid_d': 0.0,
            'yaw_pwm': 0,
            'target_yaw': 0.0,
            'valve_turn': 0.0,
            'valve_motor_current': 0,
            'valve_position': 0.0,
            'valve_rate': 0.0,
            'total_volume': 0.0,
            'valve_motor_connected': False,
            'flow_meter_connected': False
        }
        
        self._status_lock = threading.Lock()
        self._last_status_update_time = 0
        self._last_ui_update_time = 0
        self._last_ui_update_interval = 0.1  # seconds
        self._connection_timeout = 1.0  # seconds
        self._available = False
        
        # Member state variables
        self._enabled = False
        self._relay_enabled = False
        self._stability_enabled = False
        self._spray_gun_leveling_enabled = False
        self._auto_correction_enabled = False
        self._spray_gun_led_on = False
        self._target_yaw = 0.0
        self._roller_steering_enabled = False
        self._swing_damping_enabled = False
        # Get thrust_force from settings_manager if available, otherwise use default
        if hasattr(robot_controller, 'settings_manager'):
            self._thrust_force = robot_controller.settings_manager.get('thrust_force') or -1.0
            # Subscribe to settings changes
            robot_controller.settings_manager.thrust_force_changed.connect(self._on_thrust_force_setting_changed)
        else:
            self._thrust_force = -1.0
        self._thrust_force_enabled = False
        
        # Thrust force ramping state
        self._current_thrust_force = 0.0  # Current ramped thrust value
        self._target_thrust_force = 0.0   # Target thrust value (either 0 or _thrust_force)
        self._last_published_thrust = 0.0  # Last published value to avoid redundant messages
        if hasattr(robot_controller, 'settings_manager'):
            self._thrust_ramp_rate = robot_controller.settings_manager.get('thrust_ramp_rate', 1.0)
            robot_controller.settings_manager.thrust_ramp_rate_changed.connect(self._on_thrust_ramp_rate_changed)
        else:
            self._thrust_ramp_rate = 1.0
        
        # Configure publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
        
        # Create connection check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms
        
        # Create thrust ramping timer (10Hz)
        self._thrust_ramp_timer = QTimer(self)
        self._thrust_ramp_timer.timeout.connect(self._update_thrust_ramp)
        self._thrust_ramp_timer.start(100)  # 100ms = 10Hz
        
    def _setup_publishers(self):
        """Set up ROS publishers for Teensy control"""
        self.teensy_relay_pub = self._robot_controller.create_publisher(Bool, 'teensy/relay/cmd', 1)
        self.teensy_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/enable/cmd', 1)
        self.ef_move_top_rail_speed_pub = self._robot_controller.create_publisher(Float32, 'teensy/top_rail/speed/cmd', 1)
        self.ef_home_top_rail_pub = self._robot_controller.create_publisher(Bool, 'teensy/top_rail/home/cmd', 1)
        self.ef_move_arm_rail_speed_pub = self._robot_controller.create_publisher(Float32, 'teensy/arm_rail/speed/cmd', 1)
        self.ef_move_arm_rail_pos_pub = self._robot_controller.create_publisher(Int32, 'teensy/arm/extend/cmd', 1)
        self.ef_home_arm_rail_pub = self._robot_controller.create_publisher(Bool, 'teensy/arm/home/cmd', 1)
        self.prop_left_pwm_pub = self._robot_controller.create_publisher(Int32, 'teensy/prop/left/pwm/cmd', 1)
        self.prop_right_pwm_pub = self._robot_controller.create_publisher(Int32, 'teensy/prop/right/pwm/cmd', 1)
        self.prop_left_joint_pub = self._robot_controller.create_publisher(Float32, 'teensy/prop/left/joint/cmd', 1)
        self.prop_right_joint_pub = self._robot_controller.create_publisher(Float32, 'teensy/prop/right/joint/cmd', 1)
        self.ef_spray_trigger_pub = self._robot_controller.create_publisher(Int32, 'teensy/spray_gun/trigger/cmd', 1)
        self.ef_spray_pitch_speed_pub = self._robot_controller.create_publisher(Int32, 'teensy/spray_gun/pitch/speed/cmd', 1)
        self.ef_spray_pitch_pub = self._robot_controller.create_publisher(Float32MultiArray, 'teensy/spray_gun/pitch/angle/cmd', 1)
        self.ef_spray_led_pub = self._robot_controller.create_publisher(Bool, 'teensy/spray_gun/led/cmd', 1)
        # Stability controller publishers (decoupled force and yaw control)
        self.stability_enable_pub = self._robot_controller.create_publisher(Bool, 'stability_controller/enable/cmd', 1)
        self.stability_yaw_enable_pub = self._robot_controller.create_publisher(Bool, 'stability_controller/yaw_control/enable/cmd', 1)
        self.stability_yaw_angle_pub = self._robot_controller.create_publisher(Float32, 'stability_controller/yaw_control/angle/cmd', 1)
        self.stability_short_param_pub = self._robot_controller.create_publisher(TeensyYaw, 'stability_controller/yaw_control/short_params/cmd', 1)
        self.stability_long_param_pub = self._robot_controller.create_publisher(TeensyYaw, 'stability_controller/yaw_control/long_params/cmd', 1)
        self.stability_auto_correction_enable_pub = self._robot_controller.create_publisher(Bool, 'stability_controller/yaw_control/auto_correction/cmd', 1)
        self.stability_force_pub = self._robot_controller.create_publisher(Twist, 'stability_controller/force/cmd', 1)
        self.ef_spray_level_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/spray_gun/leveling_enable/cmd', 1)
        self.ef_lidar_power_pub = self._robot_controller.create_publisher(Bool, 'unilidar/power', 1)
        self.ef_tap_freq_pub = self._robot_controller.create_publisher(Int32MultiArray, 'teensy/tapper/tap_freq/cmd', 1)
        self.ef_tap_once_pub = self._robot_controller.create_publisher(Int32, 'teensy/tapper/tap_once/cmd', 1)
        self.ef_tap_stop_pub = self._robot_controller.create_publisher(Bool, 'teensy/tapper/stop/cmd', 1)
        self.roller_steering_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/roller/steering/enable/cmd', 1)
        self.swing_damping_enable_pub = self._robot_controller.create_publisher(Bool, 'stability_controller/swing_damping/enable/cmd', 1)


    def _setup_subscribers(self):
        """Set up ROS subscribers"""
        self._robot_controller.create_subscription(
            TeensyStatus,
            'teensy/status',
            self._status_callback,
            10
        )
    
    # --- Publish helpers to reduce boilerplate ---
    
    def _publish_float32(self, publisher, value: float):
        msg = Float32()
        msg.data = float(value)
        publisher.publish(msg)
    
    def _publish_int32(self, publisher, value: int):
        msg = Int32()
        msg.data = int(value)
        publisher.publish(msg)
    
    def _publish_bool(self, publisher, value: bool):
        msg = Bool()
        msg.data = value
        publisher.publish(msg)
    
    def _check_availability(self):
        """Check if the Teensy is still connected"""
        current_time = time.time()
        
        # Calculate time since last status update
        time_since_last_update = current_time - self._last_status_update_time
        
        # If it's been too long since the last update, consider disconnected
        if time_since_last_update > self._connection_timeout:
            if self._available:
                self._available = False
                print(f"Teensy considered disconnected: {time_since_last_update:.1f}s since last status update")
                self.connection_changed.emit(False)
        elif not self._available:
            self._available = True
            print("Teensy connection established")
            self.connection_changed.emit(True)
    
    def _status_callback(self, msg: TeensyStatus):
        """Process incoming TeensyStatus messages from ROS"""
        try:
            # Convert milliseconds to hours, minutes, seconds
            total_seconds = int(msg.runtime / 1000)  # Convert ms to seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            formatted_runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            # Build new status dict, then swap atomically under lock
            new_status = {
                'available': True,
                'top_rail_position': msg.top_rail_position,
                'top_rail_speed': msg.top_rail_speed,
                'top_rail_current': msg.top_rail_current,
                'arm_rail_position': msg.arm_rail_position,
                'arm_rail_speed': msg.arm_rail_speed,
                'arm_rail_current': msg.arm_rail_current,
                'arm_extension_dist': msg.arm_extension_dist,
                'arm_sensor_dist': msg.arm_sensor_dist,
                'voltage': msg.voltage,
                'temperature': msg.temperature,
                'current': msg.current,
                'run_time': msg.runtime,  # Keep formatted runtime as string
                'loop_time': msg.looptime,
                'loop_time_counter': msg.looptime_counter,
                'relay_on': bool(msg.relay_on),
                'enabled': msg.enabled,
                'left_prop_position': msg.left_prop_position / 100,
                'left_prop_pwm': msg.left_prop_pwm,
                'right_prop_position': msg.right_prop_position / 100,
                'right_prop_pwm': msg.right_prop_pwm,
                'imu_acc_x': msg.linear_acceleration.x,
                'imu_acc_y': msg.linear_acceleration.y,
                'imu_acc_z': msg.linear_acceleration.z,
                'imu_angular_acc_x': msg.angular_velocity.x,
                'imu_angular_acc_y': msg.angular_velocity.y,
                'imu_angular_acc_z': msg.angular_velocity.z,
                'imu_pitch': msg.orientation.x,
                'imu_roll': msg.orientation.y,
                'imu_yaw': msg.orientation.z,
                'spray_gun_pitch': msg.spray_gun_pitch,
                'gimbal_pitch_motor_angle': msg.gimbal_pitch_motor_angle,
                'gimbal_pitch_motor_current': msg.gimbal_pitch_motor_current,
                'gimbal_pitch_motor_temp': msg.gimbal_pitch_motor_temp,
                'gimbal_roll_motor_angle': msg.gimbal_roll_motor_angle,
                'gimbal_roll_motor_current': msg.gimbal_roll_motor_current,
                'gimbal_roll_motor_temp': msg.gimbal_roll_motor_temp,
                'spray_gun_trigger': msg.spray_gun_trigger,
                'yaw_enabled': msg.yaw_enabled,
                'yaw_command': msg.yaw_command,
                'yaw_pid_p': msg.yaw_pid_p,
                'yaw_pid_i': msg.yaw_pid_i,
                'yaw_pid_d': msg.yaw_pid_d,
                # Add member state variables for QML access
                'target_yaw': msg.yaw_command
            }

            with self._status_lock:
                # Preserve user-controlled fields that aren't in the ROS message
                for field in _USER_CONTROLLED_FIELDS:
                    new_status[field] = self._status.get(field, False)
                self._status = new_status

            current_time = time.time()
            self._last_status_update_time = current_time

            # Throttle UI updates to avoid overwhelming the UI
            # Emit signal OUTSIDE lock to prevent deadlock
            time_since_last_update = current_time - self._last_ui_update_time
            if time_since_last_update > self._last_ui_update_interval:
                self._last_ui_update_time = current_time
                self.status_changed.emit(new_status)
            
        except Exception as e:
            print(f"Error in Teensy status callback: {e}")
    
    def get_status(self) -> TeensyStatusDict:
        """Get current Teensy status"""
        with self._status_lock:
            return self._status.copy()
    
    @Slot(str, result='QVariant')
    def get_status_value(self, key: str) -> Any:
        """Get a specific status value by key"""
        with self._status_lock:
            return self._status.get(key)
    
    @Slot(str, result=str)
    def get_formatted_value(self, key: str) -> str:
        """Get a specific status value formatted as a string"""
        value = self._status.get(key)
        
        # Handle numeric values with appropriate formatting
        if isinstance(value, float):
            if key in ['imu_pitch', 'imu_roll', 'imu_yaw']:
                return f"{value:.2f}"
            elif key == 'temperature':
                return f"{value:.1f}"
            else:
                return f"{value:.2f}"
        
        # Just return string representation for other types
        return str(value)
    
    #############################################
    ### UI Control Methods (Slots)
    #############################################
    
    @Slot(bool)
    def setEnabled(self, enabled: bool):
        """Enable/disable Teensy control"""
        self._publish_bool(self.teensy_enable_pub, enabled)
        self._robot_controller.get_logger().info(f'Teensy {"enabled" if enabled else "disabled"}')
        self.status_changed.emit(self._status)
    
    @Slot(bool)
    def setRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self._relay_enabled = enabled
        self._status['relay_enabled'] = enabled
        self._publish_bool(self.teensy_relay_pub, enabled)
        self._robot_controller.get_logger().info(f'Teensy relay {"enabled" if enabled else "disabled"}')
        self.status_changed.emit(self._status)
    
    @Slot(float)
    def setTopRailSpeed(self, speed: float):
        """Set the top rail speed"""
        self._publish_float32(self.ef_move_top_rail_speed_pub, speed)

    @Slot(bool)
    def homeTopRail(self, home: bool):
        """Home the top rail"""
        self._publish_bool(self.ef_home_top_rail_pub, True)
        self._robot_controller.show_popup("Homing Top Rail", "Homing top rail", "info")
    
    @Slot(float)
    def setArmRailSpeed(self, speed: float):
        """Set the arm rail speed"""
        self._publish_float32(self.ef_move_arm_rail_speed_pub, speed)

    @Slot(int)
    def extendArm(self, dist: int):
        self._publish_int32(self.ef_move_arm_rail_pos_pub, dist)
        self._robot_controller.show_popup("Extending Arm", f"Extending arm to {dist} mm", "info")

    @Slot(bool)
    def homeArm(self, home: bool):
        """Home the arm rail"""
        self._publish_bool(self.ef_home_arm_rail_pub, home)

    @Slot(int)
    def setLeftPropPWM(self, pwm: int):
        """Set the left propeller PWM"""
        self._publish_int32(self.prop_left_pwm_pub, pwm)
    
    @Slot(int)
    def setRightPropPWM(self, pwm: int):
        """Set the right propeller PWM"""
        self._publish_int32(self.prop_right_pwm_pub, pwm)
    
    @Slot(float)
    def setLeftPropJoint(self, position: float):
        """Set the left propeller joint position"""
        self._publish_float32(self.prop_left_joint_pub, position)
    
    @Slot(float)
    def setRightPropJoint(self, position: float):
        """Set the right propeller joint position"""
        self._publish_float32(self.prop_right_joint_pub, position)
    
    @Slot(int)
    def setSprayTrigger(self, value: int):
        """Set the spray gun trigger value"""
        self._publish_int32(self.ef_spray_trigger_pub, value)
    
    @Slot(int)
    def setSprayPitchSpeed(self, speed: int):
        """Set the spray gun pitch speed"""
        self._publish_int32(self.ef_spray_pitch_speed_pub, speed)

    @Slot(bool)
    def setSprayGunLevelingEnabled(self, enabled: bool):
        """Enable/disable spray gun leveling"""
        self._robot_controller.get_logger().info(f'Spray gun leveling {"enabled" if enabled else "disabled"}')
        self._publish_bool(self.ef_spray_level_enable_pub, enabled)
        self._spray_gun_leveling_enabled = enabled
        self.spray_gun_leveling_changed.emit(enabled)

    @Slot(float, float)
    def setSprayGunPitchAngle(self, angle: float, speed: float):
        """Set the spray gun pitch angle and speed"""
        self._robot_controller.get_logger().info(f'Setting spray gun pitch angle to {angle} with speed {speed}')
        msg = Float32MultiArray()
        msg.data = [float(angle), float(speed)]
        self.ef_spray_pitch_pub.publish(msg)

    @Slot(float, float, float, float, float)
    def demoAction(self, pitch_angle: float, pitch_speed: float, cable_length: float, cable_speed: float, force_y: float):
        """Perform a demo action with the spray gun"""
        self.setSprayGunPitchAngle(pitch_angle, pitch_speed)
        self._robot_controller.winch_controller.move_absolute(cable_length, cable_speed)
        self.set_ef_force(0.0, force_y)

    @Slot(bool)
    def setSprayGunLED(self, on: bool):
        """Turn the spray gun LED on/off"""
        self._robot_controller.get_logger().info(f'Spray gun LED {"on" if on else "off"}')
        self._publish_bool(self.ef_spray_led_pub, on)
        self._spray_gun_led_on = on
        self.spray_gun_led_changed.emit(on)

    @Slot(bool)
    def setLidarPower(self, on: bool):
        """Turn the Lidar power on/off"""
        self._robot_controller.get_logger().info(f'Lidar power {"on" if on else "off"}')
        self._publish_bool(self.ef_lidar_power_pub, on)

    @Slot(bool)
    def setStabilityEnabled(self, enabled: bool):
        """Enable/disable stability controller (master enable for force and yaw control)"""
        self._stability_enabled = enabled
        self._status['stability_enabled'] = enabled
        self._publish_bool(self.stability_enable_pub, enabled)
        self._robot_controller.get_logger().info(f'Stability controller {"enabled" if enabled else "disabled"}')
        self.stability_enabled_changed.emit(enabled)
        self.status_changed.emit(self._status)

    @Slot(bool)
    def setYawEnabled(self, enabled: bool):
        """Enable/disable yaw control"""
        self._publish_bool(self.stability_yaw_enable_pub, enabled)

    @Slot(bool)
    def setAutoCorrectonEnabled(self, enabled: bool):
        """Enable/disable yaw auto correction"""
        self._auto_correction_enabled = enabled
        self._status['auto_correction_enabled'] = enabled
        self._publish_bool(self.stability_auto_correction_enable_pub, enabled)
        self._robot_controller.get_logger().info(f'Auto correction {"enabled" if enabled else "disabled"}')
        self.auto_correction_enabled_changed.emit(enabled)
        self.status_changed.emit(self._status)

    @Slot(bool)
    def setRollerSteeringEnabled(self, enabled: bool):
        """Enable/disable roller steering"""
        self._roller_steering_enabled = enabled
        self._status['roller_steering_enabled'] = enabled
        self._publish_bool(self.roller_steering_enable_pub, enabled)
        self._robot_controller.get_logger().info(f'Roller steering {"enabled" if enabled else "disabled"}')
        self.roller_steering_enabled_changed.emit(enabled)
        self.status_changed.emit(self._status)

    @Slot(bool)
    def setSwingDampingEnabled(self, enabled: bool):
        """Enable/disable swing damping"""
        self._swing_damping_enabled = enabled
        self._status['swing_damping_enabled'] = enabled
        self._publish_bool(self.swing_damping_enable_pub, enabled)
        self._robot_controller.get_logger().info(f'Swing damping {"enabled" if enabled else "disabled"}')
        self.swing_damping_enabled_changed.emit(enabled)
        self.status_changed.emit(self._status)

    @Slot(float)
    def setYawAngle(self, angle: float):
        """Set the yaw angle"""
        self._publish_float32(self.stability_yaw_angle_pub, angle)

    @Slot(float, float, float)
    def setShortParams(self, p: float, i: float, d: float):
        """Set the yaw PID parameters """
        msg = TeensyYaw()
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        self.stability_short_param_pub.publish(msg)

    @Slot(float, float, float)
    def setLongParams(self, p: float, i: float, d: float):
        """Set the yaw PID parameters"""
        msg = TeensyYaw()
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        self.stability_long_param_pub.publish(msg)

    @Slot(float, float)
    def startTapFreq(self, power: float, period: float):
        """Start tapping the frequency"""
        self._robot_controller.get_logger().info(f'Starting tap frequency with Power: {power} Period: {period}')
        msg = Int32MultiArray()
        msg.data = [int(power), int(period*1000)]
        self.ef_tap_freq_pub.publish(msg)

    @Slot(float)
    def tapOnce(self, power: float):
        """ Tap once"""
        self._robot_controller.get_logger().info(f'Tapping once with Power: {power}')
        self._publish_int32(self.ef_tap_once_pub, int(power))

    @Slot(float)
    def tapStop(self, power: float):
        """ Stop tapping"""
        self._robot_controller.get_logger().info(f'Stopping tap with Power: {power}')
        self._publish_bool(self.ef_tap_stop_pub, True)

    @Slot(bool)
    def setThrustForceEnabled(self, enabled: bool):
        """Toggle thrust force on/off with ramping (QML callable)"""
        self.set_thrust_force_enabled(enabled)
    
    @Slot(bool)
    def setThrustForceInstant(self, enabled: bool):
        """Toggle thrust force on/off instantly without ramping (QML callable)"""
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
        self._robot_controller.get_logger().info(f'Yaw control {"enabled" if enabled else "disabled"} with Target: {target} P:{p} I:{i} D:{d} PWM:{pwm}')

    def set_ef_force(self, Fx: float, Fy: float):
        """Internal method to send EF force values"""
        # Create a Twist message for EF force
        msg = Twist()
        msg.linear = Vector3(x=Fx, y=Fy, z=0.0)
        
        # Publish to the appropriate topic
        if hasattr(self, 'stability_force_pub'):
            self.stability_force_pub.publish(msg)
            self._robot_controller.get_logger().info(f'Sent EF force: Fx={Fx}, Fy={Fy}')
        else:
            self._robot_controller.get_logger().error("Stability force publisher not initialized. Cannot send force values.")
    
    # Define a property to expose the entire status dictionary
    def get_all_status(self) -> TeensyStatusDict:
        return self._status
    
    # Define a property for availability
    def get_available(self) -> bool:
        return self._available
    
    # Define Qt properties
    available = Property(bool, get_available, notify=connection_changed)
    all_status = Property(dict, get_all_status, notify=status_changed)
    spray_gun_leveling_enabled = Property(bool, lambda self: self._spray_gun_leveling_enabled, notify=spray_gun_leveling_changed)
    spray_gun_led_on = Property(bool, lambda self: self._spray_gun_led_on, notify=spray_gun_led_changed)
    auto_correction_enabled = Property(bool, lambda self: self._auto_correction_enabled, notify=auto_correction_enabled_changed)
    stability_enabled = Property(bool, lambda self: self._stability_enabled, notify=stability_enabled_changed)
    roller_steering_enabled = Property(bool, lambda self: self._roller_steering_enabled, notify=roller_steering_enabled_changed)
    swing_damping_enabled = Property(bool, lambda self: self._swing_damping_enabled, notify=swing_damping_enabled_changed)
    
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
            self._robot_controller.get_logger().info(f'Thrust force set to {self._thrust_force:.2f}')
    
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
                self._robot_controller.get_logger().info(f'Thrust force enabled: ramping to {self._thrust_force:.2f}')
            else:
                # Set target to 0, ramping will handle the rest
                self._target_thrust_force = 0.0
                self._robot_controller.get_logger().info('Thrust force disabled: ramping to 0.0')
    
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
                self._robot_controller.get_logger().info(f'Thrust force enabled instantly: {self._thrust_force:.2f}')
            else:
                self._current_thrust_force = 0.0
                self._target_thrust_force = 0.0
                self.set_ef_force(0.0, 0.0)
                self._robot_controller.get_logger().info('Thrust force disabled instantly')
    
    thrust_force = Property(float, get_thrust_force, set_thrust_force, notify=thrust_force_changed)
    thrust_force_enabled = Property(bool, get_thrust_force_enabled, set_thrust_force_enabled, notify=thrust_force_enabled_changed)
    
    def _on_thrust_force_setting_changed(self, new_value: float):
        """Handle thrust_force change from SettingsManager"""
        # Update internal value without re-triggering setting save
        clamped_value = max(-1.0, min(1.0, new_value))
        if self._thrust_force != clamped_value:
            self._thrust_force = clamped_value
            self.thrust_force_changed.emit(self._thrust_force)
            print(f"[TeensyController] Thrust force updated from settings: {clamped_value}")
    
    def _on_thrust_ramp_rate_changed(self, new_value: float):
        """Handle thrust_ramp_rate change from SettingsManager"""
        self._thrust_ramp_rate = new_value
        print(f"[TeensyController] Thrust ramp rate updated to: {new_value}")
    
    def _update_thrust_ramp(self):
        """Update ramped thrust force at 10Hz"""
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
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
        if hasattr(self, '_thrust_ramp_timer') and self._thrust_ramp_timer.isActive():
            self._thrust_ramp_timer.stop()