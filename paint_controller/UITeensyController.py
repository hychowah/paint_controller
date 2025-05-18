#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Dict, Optional, Any, Union
import time

from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Int32
from paint_interfaces.msg import TeensyStatus, TeensyYaw

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer


class TeensyController(QObject):
    # Define Qt signals
    status_changed = Signal(dict)
    connection_changed = Signal(bool)
    spray_gun_leveling_changed = Signal(bool)
    spray_gun_led_changed = Signal(bool)
    
    def __init__(self, robot_controller):
        super().__init__()
        self._robot_controller = robot_controller  # Store reference to the robot controller
        
        # Initialize status variables with default values instead of empty dictionary
        self._status = {
            'available': False,
            'top_rail_position': 0.0,
            'top_rail_speed': 0.0,
            'top_rail_current': 0.0,
            'arm_rail_position': 0.0,
            'arm_rail_speed': 0.0,
            'arm_rail_current': 0.0,
            'arm_extension_dist': 0.0,
            'arm_sensor_dist': 0.0,
            'voltage': 21.3,
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
            'spray_gun_motor_angle': 0.0,
            'spray_gun_motor_current': 0.0,
            'spray_gun_motor_temp': 0.0,
            'spray_gun_trigger': 0,
            'spray_gun_leveling_enabled': False,
            'yaw_enabled': False,
            'yaw_command': 80.0,
            'yaw_pid_p': 0.0,
            'yaw_pid_i': 0.0,
            'yaw_pid_d': 0.0,
            'yaw_pwm': 0,
            'target_yaw': 0.0
        }
        
        self._last_status_update_time = 0
        self._last_ui_update_time = 0
        self._last_ui_update_interval = 0.1  # seconds
        self._connection_timeout = 1.0  # seconds
        self._available = False
        
        # Member state variables
        self._enabled = False
        self._relay_enabled = False
        self._spray_gun_leveling_enabled = False
        self._spray_gun_led_on = False
        self._target_yaw = 0.0
        
        # Configure publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
        
        # Create connection check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms
        
    def _setup_publishers(self):
        """Set up ROS publishers for Teensy control"""
        self.teensy_relay_pub = self._robot_controller.create_publisher(Bool, 'teensy/relay/cmd', 1)
        self.teensy_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/enable/cmd', 1)
        self.ef_move_top_rail_speed_pub = self._robot_controller.create_publisher(Float32, 'teensy/top_rail/speed/cmd', 1)
        self.ef_move_arm_rail_speed_pub = self._robot_controller.create_publisher(Float32, 'teensy/arm_rail/speed/cmd', 1)
        self.ef_move_arm_rail_pos_pub = self._robot_controller.create_publisher(Int32, 'teensy/arm/extend/cmd', 1)
        self.prop_left_pwm_pub = self._robot_controller.create_publisher(Int32, 'teensy/prop/left/pwm/cmd', 1)
        self.prop_right_pwm_pub = self._robot_controller.create_publisher(Int32, 'teensy/prop/right/pwm/cmd', 1)
        self.prop_left_joint_pub = self._robot_controller.create_publisher(Float32, 'teensy/prop/left/joint/cmd', 1)
        self.prop_right_joint_pub = self._robot_controller.create_publisher(Float32, 'teensy/prop/right/joint/cmd', 1)
        self.ef_spray_trigger_pub = self._robot_controller.create_publisher(Int32, 'teensy/spray_gun/trigger/cmd', 1)
        self.ef_spray_gimbal_speed_pub = self._robot_controller.create_publisher(Int32, 'teensy/spray_gun/gimbal/speed/cmd', 1)
        self.ef_spray_led_pub = self._robot_controller.create_publisher(Bool, 'teensy/spray_gun/led/cmd', 1)
        self.ef_yaw_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/yaw_control/enable/cmd', 1)
        self.ef_yaw_angle_pub = self._robot_controller.create_publisher(Float32, 'teensy/yaw_control/angle/cmd', 1)
        self.ef_yaw_param_pub = self._robot_controller.create_publisher(TeensyYaw, 'teensy/yaw_control/params/cmd', 1)
        self.ef_spray_level_enable_pub = self._robot_controller.create_publisher(Bool, 'teensy/spray_gun/leveling_enable/cmd', 1)


    def _setup_subscribers(self):
        """Set up ROS subscribers"""
        self._robot_controller.create_subscription(
            TeensyStatus,
            'teensy/status',
            self._status_callback,
            10
        )
    
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

            # Store values with original types (not as strings)
            self._status = {
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
                'spray_gun_motor_angle': msg.spray_gun_motor_angle,
                'spray_gun_motor_current': msg.spray_gun_motor_current,
                'spray_gun_motor_temp': msg.spray_gun_motor_temp,
                'spray_gun_trigger': msg.spray_gun_trigger,
                'yaw_enabled': msg.yaw_enabled,
                'yaw_command': msg.yaw_command / 100.0,
                'yaw_pid_p': msg.yaw_pid_p,
                'yaw_pid_i': msg.yaw_pid_i,
                'yaw_pid_d': msg.yaw_pid_d,
                'yaw_pwm': msg.yaw_pwm,
                # Add member state variables for QML access
                'target_yaw': self._target_yaw
            }

            current_time = time.time()
            self._last_status_update_time = current_time

            # Throttle UI updates to avoid overwhelming the UI
            time_since_last_update = current_time - self._last_ui_update_time
            if time_since_last_update > self._last_ui_update_interval:
                self._last_ui_update_time = current_time
                self.status_changed.emit(self._status)
            
        except Exception as e:
            print(f"Error in Teensy status callback: {e}")
    
    def get_status(self) -> Dict:
        """Get current Teensy status"""
        return self._status.copy()
    
    @Slot(str, result='QVariant')
    def get_status_value(self, key: str) -> Any:
        """Get a specific status value by key"""
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
        msg = Bool()
        msg.data = enabled
        self.teensy_enable_pub.publish(msg)
        self._robot_controller.get_logger().info(f'Teensy {"enabled" if enabled else "disabled"}')
        
        # Emit status changed signal for UI updates
        self.status_changed.emit(self._status)
    
    @Slot(bool)
    def setRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self._relay_enabled = enabled
        self._status['relay_enabled'] = enabled
        
        msg = Bool()
        msg.data = enabled
        self.teensy_relay_pub.publish(msg)
        self._robot_controller.get_logger().info(f'Teensy relay {"enabled" if enabled else "disabled"}')
        
        # Emit status changed signal for UI updates
        self.status_changed.emit(self._status)
    
    @Slot(float)
    def setTopRailSpeed(self, speed: float):
        """Set the top rail speed"""
        msg = Float32()
        msg.data = float(speed)
        self.ef_move_top_rail_speed_pub.publish(msg)
    
    @Slot(float)
    def setArmRailSpeed(self, speed: float):
        """Set the arm rail speed"""
        msg = Float32()
        msg.data = float(speed)
        self.ef_move_arm_rail_speed_pub.publish(msg)

    @Slot(int)
    def extendArm(self, dist: int):
        msg = Int32()
        msg.data = int(dist)
        self.ef_move_arm_rail_pos_pub.publish(msg)
        self._robot_controller.show_popup("Extending Arm", f"Extending arm to {dist} mm", "info")
    
    @Slot(int)
    def setLeftPropPWM(self, pwm: int):
        """Set the left propeller PWM"""
        msg = Int32()
        msg.data = int(pwm)
        self.prop_left_pwm_pub.publish(msg)
    
    @Slot(int)
    def setRightPropPWM(self, pwm: int):
        """Set the right propeller PWM"""
        msg = Int32()
        msg.data = int(pwm)
        self.prop_right_pwm_pub.publish(msg)
    
    @Slot(float)
    def setLeftPropJoint(self, position: float):
        """Set the left propeller joint position"""
        msg = Float32()
        msg.data = float(position)
        self.prop_left_joint_pub.publish(msg)
    
    @Slot(float)
    def setRightPropJoint(self, position: float):
        """Set the right propeller joint position"""
        msg = Float32()
        msg.data = float(position)
        self.prop_right_joint_pub.publish(msg)
    
    @Slot(int)
    def setSprayTrigger(self, value: int):
        """Set the spray gun trigger value"""
        msg = Int32()
        msg.data = int(value)
        self.ef_spray_trigger_pub.publish(msg)
    
    @Slot(int)
    def setSprayGimbalSpeed(self, speed: int):
        """Set the spray gun gimbal speed"""
        msg = Int32()
        msg.data = int(speed)
        self.ef_spray_gimbal_speed_pub.publish(msg)

    @Slot(bool)
    def setSprayGunLevelingEnabled(self, enabled: bool):
        """Enable/disable spray gun leveling"""
        self._robot_controller.get_logger().info(f'Spray gun leveling {"enabled" if enabled else "disabled"}')
        msg = Bool()
        msg.data = enabled
        self.ef_spray_level_enable_pub.publish(msg)
        self._spray_gun_leveling_enabled = enabled
        self.spray_gun_leveling_changed.emit(enabled)

    @Slot(bool)
    def setSprayGunLED(self, on: bool):
        """Turn the spray gun LED on/off"""
        self._robot_controller.get_logger().info(f'Spray gun LED {"on" if on else "off"}')
        msg = Bool()
        msg.data = on
        self.ef_spray_led_pub.publish(msg)
        self._spray_gun_led_on = on
        self.spray_gun_led_changed.emit(on)

    @Slot(bool)
    def setYawEnabled(self, enabled: bool):
        """Enable/disable yaw control"""
        msg = Bool()
        msg.data = enabled
        self.ef_yaw_enable_pub.publish(msg)

    @Slot(float)
    def setYawAngle(self, angle: float):
        """Set the yaw angle"""
        msg = Float32()
        msg.data = float(angle)
        self.ef_yaw_angle_pub.publish(msg)

    @Slot(float, float, float)
    def setYawParams(self, p: float, i: float, d: float):
        """Set the yaw PID parameters"""
        msg = TeensyYaw()
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        self.ef_yaw_param_pub.publish(msg)
    
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
    
    # Define a property to expose the entire status dictionary
    def get_all_status(self) -> Dict:
        return self._status
    
    # Define a property for availability
    def get_available(self) -> bool:
        return self._available
    
    # Define Qt properties
    available = Property(bool, get_available, notify=connection_changed)
    all_status = Property(dict, get_all_status, notify=status_changed)
    spray_gun_leveling_enabled = Property(bool, lambda self: self._spray_gun_leveling_enabled, notify=spray_gun_leveling_changed)
    spray_gun_led_on = Property(bool, lambda self: self._spray_gun_led_on, notify=spray_gun_led_changed)
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()