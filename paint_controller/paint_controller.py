#!/usr/bin/env python3

import sys
import os
import time
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
import yaml
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Float64, Bool, Float32, Int32
from sensor_msgs.msg import LaserScan
from cv_bridge import CvBridge
from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput, TeensyStatus, TeensyYaw

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickImageProvider

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp

#############################################
### Configuration
#############################################

@dataclass
class RobotConfig:
    """Robot configuration parameters"""
    video_port: int = 5000
    update_rate: float = 30.0  # Hz
    watchdog_timeout: float = 1.0  # seconds
    joystick_deadzone: float = 0.1
    max_winch_speed: float = 1000.0
    video_width: int = 640
    video_height: int = 480

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> RobotConfig:
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return RobotConfig(**config_dict)
        except Exception as e:
            print(f"Error loading config: {e}")
            return RobotConfig()
        

#############################################
### UI Data Model
#############################################

class UIDataModel(QObject):
    # Motor Status Signals
    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(str)
    winchCurrentChanged = Signal(str)
    winchAvailableChanged = Signal(bool)
    winchTorqueChanged = Signal(str)
    winchTemperatureChanged = Signal(str)
    winchVoltageChanged = Signal(str)
    winchBrakeChanged = Signal(bool)
    winchEnabledChanged = Signal(bool)
    
    # Wheel Status Signals
    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    wheelAvailableChanged = Signal(bool)
    
    # Control Mode Signals
    leftJoystickControlChanged = Signal(str)
    rightJoystickControlChanged = Signal(str)

    # Input Signals
    leftJoystickXChanged = Signal(int)
    leftJoystickYChanged = Signal(int)
    rightJoystickXChanged = Signal(int)
    rightJoystickYChanged = Signal(int)
    leftTriggerChanged = Signal(int)
    rightTriggerChanged = Signal(int)
    dpadUpChanged = Signal(bool)
    dpadDownChanged = Signal(bool)
    dpadLeftChanged = Signal(bool)
    dpadRightChanged = Signal(bool)
    buttonAChanged = Signal(bool)
    buttonBChanged = Signal(bool)
    buttonXChanged = Signal(bool)
    buttonYChanged = Signal(bool)
    buttonL1Changed = Signal(bool)
    buttonR1Changed = Signal(bool)
    buttonMenuChanged = Signal(bool)
    imuPitchChanged = Signal(int)
    imuRollChanged = Signal(int)
    imuYawChanged = Signal(int)

    displayMessageChanged = Signal(str)

    # Teensy Properties
    topRailPositionChanged = Signal(str)
    topRailSpeedChanged = Signal(str)
    topRailCurrentChanged = Signal(str)
    armRailPositionChanged = Signal(str)
    armRailSpeedChanged = Signal(str)
    armRailCurrentChanged = Signal(str)

    teensyVoltageChanged = Signal(str)
    teensyTemperatureChanged = Signal(str)
    teensyCurrentChanged = Signal(str)
    teensyRunTimeChanged = Signal(str)
    teensyLoopTimeChanged = Signal(str)
    teensyLoopTimeCounterChanged = Signal(str)

    leftPropPosiionChanged = Signal(str)
    leftPropPWMChanged = Signal(str)
    rightPropPositionChanged = Signal(str)
    rightPropPWMChanged = Signal(str)

    teeensyImuAccXChanged = Signal(str)
    teeensyImuAccYChanged = Signal(str)
    teeensyImuAccZChanged = Signal(str)
    teeensyImuAngularAccXChanged = Signal(str)
    teeensyImuAngularAccYChanged = Signal(str)
    teeensyImuAngularAccZChanged = Signal(str)
    teensyImuPitchChanged = Signal(float)
    teensyImuRollChanged = Signal(float)
    teensyImuYawChanged = Signal(float)

    teensyYawEnabledChanged = Signal(bool)
    teensyYawCommandChanged = Signal(str)
    teensyYawPidPChanged = Signal(str)
    teensyYawPidIChanged = Signal(str)
    teensyYawPidDChanged = Signal(str)
    teensyYawPWMChanged = Signal(str)

    teensyRelay1Changed = Signal(bool)
    teensyEnabledChanged = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._winch_data = {
            'length': '0.00',
            'speed': '0.00',
            'current': '0.00',
            'available': False,
            'torque': '0.00',
            'temperature': '0.00',
            'voltage': '0.00',
            'brake': True,
            'enabled': False
        }
        
        self._wheel_data = {
            'left_speed': '0.00',
            'right_speed': '0.00',
            'left_current': '0.00',
            'right_current': '0.00',
            'available': False
        }
        
        self._control_modes = {
            'left_joystick': 'None',
            'right_joystick': 'None'
        }

        self._input_state = {
            'left_stick': {'x': 0, 'y': 0},
            'right_stick': {'x': 0, 'y': 0},
            'triggers': {'left': 0, 'right': 0},
            'dpad': {
                'up': False,
                'down': False,
                'left': False,
                'right': False
            },
            'buttons': {
                'a': False,
                'b': False,
                'x': False,
                'y': False,
                'l1': False,
                'r1': False,
                'menu': False
            },
            'imu': {
                'pitch': 0,
                'roll': 0,
                'yaw': 0
            }
        }

        self._display_message = ""
        self._winch_enabled = False

        self._teensy_relay_enabled = False
        self._teensy_enabled = False
        self._teensy_data = {
            'top_rail_position': '0.00',
            'top_rail_speed': '0.00',
            'top_rail_current': '0.00',
            'arm_rail_position': '0.00',
            'arm_rail_speed': '0.00',
            'arm_rail_current': '0.00',
            'voltage': '0.00',
            'temperature': '0.00',
            'current': '0.00',
            'run_time': '0.00',
            'loop_time': '0.00',
            'loop_time_counter': '0.00',
            'left_prop_position': '0.00',
            'left_prop_pwm': '0.00',
            'right_prop_position': '0.00',
            'right_prop_pwm': '0.00',
            'imu_acc_x': '0.00',
            'imu_acc_y': '0.00',
            'imu_acc_z': '0.00',
            'imu_angular_acc_x': '0.00',
            'imu_angular_acc_y': '0.00',
            'imu_angular_acc_z': '0.00',
            'imu_pitch': '0.00',
            'imu_roll': '0.00',
            'imu_yaw': '0.00',
            'yaw_enabled': False,
            'yaw_command': '0.00',
            'yaw_pid_p': '0.00',
            'yaw_pid_i': '0.00',
            'yaw_pid_d': '0.00',
            'yaw_pwm': '0.00'
        }

    ## Winch Properties
    @Property(bool, notify=winchEnabledChanged)
    def winch_enabled(self):
        return self._winch_enabled
    
    @winch_enabled.setter
    def winch_enabled(self, value):
        if self._winch_enabled != value:
            self._winch_enabled = value
            self.winchEnabledChanged.emit(value)

    @Property(str, notify=winchLengthChanged)
    def winch_length(self):
        return self._winch_data['length']
    
    @winch_length.setter
    def winch_length(self, value):
        if self._winch_data['length'] != value:
            self._winch_data['length'] = value
            self.winchLengthChanged.emit(value)

    @Property(bool, notify=winchAvailableChanged)
    def winch_available(self):
        return self._winch_data['available']
    
    @winch_available.setter
    def winch_available(self, value):
        if self._winch_data['available'] != value:
            self._winch_data['available'] = value
            self.winchAvailableChanged.emit(value)

    @Property(str, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_data['speed']
    
    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_data['speed'] != value:
            self._winch_data['speed'] = value
            self.winchSpeedChanged.emit(value)
    
    @Property(str, notify=winchCurrentChanged)
    def winch_current(self):
        return self._winch_data['current']
    
    @winch_current.setter
    def winch_current(self, value):
        if self._winch_data['current'] != value:
            self._winch_data['current'] = value
            self.winchCurrentChanged.emit(value)
    
    @Property(str, notify=winchTorqueChanged)
    def winch_torque(self):
        return self._winch_data['torque']
    
    @winch_torque.setter
    def winch_torque(self, value):
        if self._winch_data['torque'] != value:
            self._winch_data['torque'] = value
            self.winchTorqueChanged.emit(value)

    @Property(str, notify=winchTemperatureChanged)
    def winch_temperature(self):
        return self._winch_data['temperature']
    
    @winch_temperature.setter
    def winch_temperature(self, value):
        if self._winch_data['temperature'] != value:
            self._winch_data['temperature'] = value
            self.winchTemperatureChanged.emit(value)
    
    @Property(str, notify=winchVoltageChanged)
    def winch_voltage(self):
        return self._winch_data['voltage']
    
    @winch_voltage.setter
    def winch_voltage(self, value):
        if self._winch_data['voltage'] != value:
            self._winch_data['voltage'] = value
            self.winchVoltageChanged.emit(value)

    @Property(bool, notify=winchBrakeChanged)
    def winch_brake(self):
        return self._winch_data['brake']
    
    @winch_brake.setter
    def winch_brake(self, value):
        if self._winch_data['brake'] != value:
            self._winch_data['brake'] = value
            self.winchBrakeChanged.emit(value)

    # Wheel Properties
    @Property(str, notify=leftSpeedChanged)
    def left_wheel_speed(self):
        return self._wheel_data['left_speed']
    
    @left_wheel_speed.setter
    def left_wheel_speed(self, value):
        if self._wheel_data['left_speed'] != value:
            self._wheel_data['left_speed'] = value
            self.leftSpeedChanged.emit(value)

    # Control Mode Properties
    @Property(str, notify=leftJoystickControlChanged)
    def left_joystick_control(self):
        return self._control_modes['left_joystick']
    
    @left_joystick_control.setter
    def left_joystick_control(self, value):
        if self._control_modes['left_joystick'] != value:
            self._control_modes['left_joystick'] = value
            self.leftJoystickControlChanged.emit(value)

    @Property(str, notify=rightJoystickControlChanged)
    def right_joystick_control(self):
        return self._control_modes['right_joystick']
    
    @right_joystick_control.setter
    def right_joystick_control(self, value):
        if self._control_modes['right_joystick'] != value:
            self._control_modes['right_joystick'] = value
            self.rightJoystickControlChanged.emit(value)

    # Input Properties
    @Property(int, notify=leftJoystickXChanged)
    def left_joystick_x(self):
        return self._input_state['left_stick']['x']
    
    @left_joystick_x.setter
    def left_joystick_x(self, value):
        if self._input_state['left_stick']['x'] != value:
            self._input_state['left_stick']['x'] = value
            self.leftJoystickXChanged.emit(value)

    @Property(int, notify=leftJoystickYChanged)
    def left_joystick_y(self):
        return self._input_state['left_stick']['y']
    
    @left_joystick_y.setter
    def left_joystick_y(self, value):
        if self._input_state['left_stick']['y'] != value:
            self._input_state['left_stick']['y'] = value
            self.leftJoystickYChanged.emit(value)

    @Property(int, notify=rightJoystickXChanged)
    def right_joystick_x(self):
        return self._input_state['right_stick']['x']
    
    @right_joystick_x.setter
    def right_joystick_x(self, value):
        if self._input_state['right_stick']['x'] != value:
            self._input_state['right_stick']['x'] = value
            self.rightJoystickXChanged.emit(value)

    @Property(int, notify=rightJoystickYChanged)
    def right_joystick_y(self):
        return self._input_state['right_stick']['y']
    
    @right_joystick_y.setter
    def right_joystick_y(self, value):
        if self._input_state['right_stick']['y'] != value:
            self._input_state['right_stick']['y'] = value
            self.rightJoystickYChanged.emit(value)

    @Property(int, notify=leftTriggerChanged)
    def left_trigger(self):
        return self._input_state['triggers']['left']
    
    @left_trigger.setter
    def left_trigger(self, value):
        if self._input_state['triggers']['left'] != value:
            self._input_state['triggers']['left'] = value
            self.leftTriggerChanged.emit(value)

    @Property(int, notify=rightTriggerChanged)
    def right_trigger(self):
        return self._input_state['triggers']['right']
    
    @right_trigger.setter
    def right_trigger(self, value):
        if self._input_state['triggers']['right'] != value:
            self._input_state['triggers']['right'] = value
            self.rightTriggerChanged.emit(value)

    @Property(bool, notify=dpadUpChanged)
    def dpad_up(self):
        return self._input_state['dpad']['up']
    
    @dpad_up.setter
    def dpad_up(self, value):
        if self._input_state['dpad']['up'] != value:
            self._input_state['dpad']['up'] = value
            self.dpadUpChanged.emit(value)

    @Property(bool, notify=dpadDownChanged)
    def dpad_down(self):
        return self._input_state['dpad']['down']
    
    @dpad_down.setter
    def dpad_down(self, value):
        if self._input_state['dpad']['down'] != value:
            self._input_state['dpad']['down'] = value
            self.dpadDownChanged.emit(value)

    @Property(bool, notify=dpadLeftChanged)
    def dpad_left(self):
        return self._input_state['dpad']['left']
    
    @dpad_left.setter
    def dpad_left(self, value):
        if self._input_state['dpad']['left'] != value:
            self._input_state['dpad']['left'] = value
            self.dpadLeftChanged.emit(value)

    @Property(bool, notify=dpadRightChanged)
    def dpad_right(self):
        return self._input_state['dpad']['right']
    
    @dpad_right.setter
    def dpad_right(self, value):
        if self._input_state['dpad']['right'] != value:
            self._input_state['dpad']['right'] = value
            self.dpadRightChanged.emit(value)

    @Property(bool, notify=buttonAChanged)
    def button_a(self):
        return self._input_state['buttons']['a']
    
    @button_a.setter
    def button_a(self, value):
        if self._input_state['buttons']['a'] != value:
            self._input_state['buttons']['a'] = value
            self.buttonAChanged.emit(value)

    @Property(bool, notify=buttonBChanged)
    def button_b(self):
        return self._input_state['buttons']['b']
    
    @button_b.setter
    def button_b(self, value):
        if self._input_state['buttons']['b'] != value:
            self._input_state['buttons']['b'] = value
            self.buttonBChanged.emit(value)

    @Property(bool, notify=buttonXChanged)
    def button_x(self):
        return self._input_state['buttons']['x']
    
    @button_x.setter
    def button_x(self, value):
        if self._input_state['buttons']['x'] != value:
            self._input_state['buttons']['x'] = value
            self.buttonXChanged.emit(value)

    @Property(bool, notify=buttonYChanged)
    def button_y(self):
        return self._input_state['buttons']['y']
    
    @button_y.setter
    def button_y(self, value):
        if self._input_state['buttons']['y'] != value:
            self._input_state['buttons']['y'] = value
            self.buttonYChanged.emit(value)

    @Property(bool, notify=buttonL1Changed)
    def button_l1(self):
        return self._input_state['buttons']['l1']
    
    @button_l1.setter
    def button_l1(self, value):
        if self._input_state['buttons']['l1'] != value:
            self._input_state['buttons']['l1'] = value
            self.buttonL1Changed.emit(value)

    @Property(bool, notify=buttonR1Changed)
    def button_r1(self):
        return self._input_state['buttons']['r1']
    
    @button_r1.setter
    def button_r1(self, value):
        if self._input_state['buttons']['r1'] != value:
            self._input_state['buttons']['r1'] = value
            self.buttonR1Changed.emit(value)

    @Property(bool, notify=buttonMenuChanged)
    def button_menu(self):
        return self._input_state['buttons']['menu']
    
    @button_menu.setter
    def button_menu(self, value):
        if self._input_state['buttons']['menu'] != value:
            self._input_state['buttons']['menu'] = value
            self.buttonMenuChanged.emit(value)

    @Property(int, notify=imuPitchChanged)
    def imu_pitch(self):
        return self._input_state['imu']['pitch']
    
    @imu_pitch.setter
    def imu_pitch(self, value):
        if self._input_state['imu']['pitch'] != value:
            self._input_state['imu']['pitch'] = value
            self.imuPitchChanged.emit(value)

    @Property(int, notify=imuRollChanged)
    def imu_roll(self):
        return self._input_state['imu']['roll']
    
    @imu_roll.setter
    def imu_roll(self, value):
        if self._input_state['imu']['roll'] != value:
            self._input_state['imu']['roll'] = value
            self.imuRollChanged.emit(value)

    @Property(int, notify=imuYawChanged)
    def imu_yaw(self):
        return self._input_state['imu']['yaw']
    
    @imu_yaw.setter
    def imu_yaw(self, value):
        if self._input_state['imu']['yaw'] != value:
            self._input_state['imu']['yaw'] = value
            self.imuYawChanged.emit(value)

    @Property(str, notify=displayMessageChanged)
    def display_message(self):
        return self._display_message
    
    @display_message.setter
    def display_message(self, value):
        if self._display_message != value:
            self._display_message = value
            self.displayMessageChanged.emit(value)

    # Teensy Properties
    @Property(bool, notify=teensyEnabledChanged)
    def teensy_enabled(self):
        return self._teensy_enabled
    
    @teensy_enabled.setter
    def teensy_enabled(self, value):
        if self._teensy_enabled != value:
            self._teensy_enabled = value
            self.teensyEnabledChanged.emit(value)

    @Property(bool, notify=teensyRelay1Changed)
    def teensy_relay_enabled(self):
        return self._teensy_relay_enabled
    
    @teensy_relay_enabled.setter
    def teensy_relay_enabled(self, value):
        if self._teensy_relay_enabled != value:
            self._teensy_relay_enabled = value
            self.teensyRelay1Changed.emit(value)

    @Property(str, notify=topRailPositionChanged)
    def top_rail_position(self):
        return self._teensy_data['top_rail_position']
    
    @top_rail_position.setter
    def top_rail_position(self, value):
        if self._teensy_data['top_rail_position'] != value:
            self._teensy_data['top_rail_position'] = value
            self.topRailPositionChanged.emit(value)

    @Property(str, notify=topRailSpeedChanged)
    def top_rail_speed(self):
        return self._teensy_data['top_rail_speed']
    
    @top_rail_speed.setter
    def top_rail_speed(self, value):
        if self._teensy_data['top_rail_speed'] != value:
            self._teensy_data['top_rail_speed'] = value
            self.topRailSpeedChanged.emit(value)

    @Property(str, notify=topRailCurrentChanged)
    def top_rail_current(self):
        return self._teensy_data['top_rail_current']
    
    @top_rail_current.setter
    def top_rail_current(self, value):
        if self._teensy_data['top_rail_current'] != value:
            self._teensy_data['top_rail_current'] = value
            self.topRailCurrentChanged.emit(value)

    @Property(str, notify=armRailPositionChanged)
    def arm_rail_position(self):
        return self._teensy_data['arm_rail_position']
    
    @arm_rail_position.setter
    def arm_rail_position(self, value):
        if self._teensy_data['arm_rail_position'] != value:
            self._teensy_data['arm_rail_position'] = value
            self.armRailPositionChanged.emit(value)

    @Property(str, notify=armRailSpeedChanged)
    def arm_rail_speed(self):
        return self._teensy_data['arm_rail_speed']
    
    @arm_rail_speed.setter
    def arm_rail_speed(self, value):
        if self._teensy_data['arm_rail_speed'] != value:
            self._teensy_data['arm_rail_speed'] = value
            self.armRailSpeedChanged.emit(value)

    @Property(str, notify=armRailCurrentChanged)
    def arm_rail_current(self):
        return self._teensy_data['arm_rail_current']
    
    @arm_rail_current.setter
    def arm_rail_current(self, value):
        if self._teensy_data['arm_rail_current'] != value:
            self._teensy_data['arm_rail_current'] = value
            self.armRailCurrentChanged.emit(value)

    @Property(str, notify=teensyVoltageChanged)
    def teensy_voltage(self):
        return self._teensy_data['voltage']
    
    @teensy_voltage.setter
    def teensy_voltage(self, value):
        if self._teensy_data['voltage'] != value:
            self._teensy_data['voltage'] = value
            self.teensyVoltageChanged.emit(value)

    @Property(str, notify=teensyTemperatureChanged)
    def teensy_temperature(self):
        return self._teensy_data['temperature']
    
    @teensy_temperature.setter
    def teensy_temperature(self, value):
        if self._teensy_data['temperature'] != value:
            self._teensy_data['temperature'] = value
            self.teensyTemperatureChanged.emit(value)

    @Property(str, notify=teensyCurrentChanged)
    def teensy_current(self):
        return self._teensy_data['current']
    
    @teensy_current.setter
    def teensy_current(self, value):
        if self._teensy_data['current'] != value:
            self._teensy_data['current'] = value
            self.teensyCurrentChanged.emit(value)

    @Property(str, notify=teensyRunTimeChanged)
    def teensy_run_time(self):
        return self._teensy_data['run_time']
    
    @teensy_run_time.setter
    def teensy_run_time(self, value):
        if self._teensy_data['run_time'] != value:
            self._teensy_data['run_time'] = value
            self.teensyRunTimeChanged.emit(value)

    @Property(str, notify=teensyLoopTimeChanged)
    def teensy_loop_time(self):
        return self._teensy_data['loop_time']
    
    @teensy_loop_time.setter
    def teensy_loop_time(self, value):
        if self._teensy_data['loop_time'] != value:
            self._teensy_data['loop_time'] = value
            self.teensyLoopTimeChanged.emit(value)

    @Property(str, notify=teensyLoopTimeCounterChanged)
    def teensy_loop_time_counter(self):
        return self._teensy_data['loop_time_counter']
    
    @teensy_loop_time_counter.setter
    def teensy_loop_time_counter(self, value):
        if self._teensy_data['loop_time_counter'] != value:
            self._teensy_data['loop_time_counter'] = value
            self.teensyLoopTimeCounterChanged.emit(value)

    @Property(str, notify=leftPropPosiionChanged)
    def left_prop_position(self):
        return self._teensy_data['left_prop_position']
    
    @left_prop_position.setter
    def left_prop_position(self, value):
        if self._teensy_data['left_prop_position'] != value:
            self._teensy_data['left_prop_position'] = value
            self.leftPropPosiionChanged.emit(value)

    @Property(str, notify=leftPropPWMChanged)
    def left_prop_pwm(self):
        return self._teensy_data['left_prop_pwm']
    
    @left_prop_pwm.setter
    def left_prop_pwm(self, value):
        if self._teensy_data['left_prop_pwm'] != value:
            self._teensy_data['left_prop_pwm'] = value
            self.leftPropPWMChanged.emit(value)

    @Property(str, notify=rightPropPositionChanged)
    def right_prop_position(self):
        return self._teensy_data['right_prop_position']
    
    @right_prop_position.setter
    def right_prop_position(self, value):
        if self._teensy_data['right_prop_position'] != value:
            self._teensy_data['right_prop_position'] = value
            self.rightPropPositionChanged.emit(value)

    @Property(str, notify=rightPropPWMChanged)
    def right_prop_pwm(self):
        return self._teensy_data['right_prop_pwm']
    
    @right_prop_pwm.setter
    def right_prop_pwm(self, value):
        if self._teensy_data['right_prop_pwm'] != value:
            self._teensy_data['right_prop_pwm'] = value
            self.rightPropPWMChanged.emit(value)

    @Property(str, notify=teeensyImuAccXChanged)
    def teensy_imu_acc_x(self):
        return self._teensy_data['imu_acc_x']
    
    @teensy_imu_acc_x.setter
    def teensy_imu_acc_x(self, value):
        if self._teensy_data['imu_acc_x'] != value:
            self._teensy_data['imu_acc_x'] = value
            self.teeensyImuAccXChanged.emit(value)

    @Property(str, notify=teeensyImuAccYChanged)
    def teensy_imu_acc_y(self):
        return self._teensy_data['imu_acc_y']
    
    @teensy_imu_acc_y.setter
    def teensy_imu_acc_y(self, value):
        if self._teensy_data['imu_acc_y'] != value:
            self._teensy_data['imu_acc_y'] = value
            self.teeensyImuAccYChanged.emit(value)

    @Property(str, notify=teeensyImuAccZChanged)
    def teensy_imu_acc_z(self):
        return self._teensy_data['imu_acc_z']
    
    @teensy_imu_acc_z.setter
    def teensy_imu_acc_z(self, value):
        if self._teensy_data['imu_acc_z'] != value:
            self._teensy_data['imu_acc_z'] = value
            self.teeensyImuAccZChanged.emit(value)

    @Property(str, notify=teeensyImuAngularAccXChanged)
    def teensy_imu_angular_acc_x(self):
        return self._teensy_data['imu_angular_acc_x']
    
    @teensy_imu_angular_acc_x.setter
    def teensy_imu_angular_acc_x(self, value):
        if self._teensy_data['imu_angular_acc_x'] != value:
            self._teensy_data['imu_angular_acc_x'] = value
            self.teeensyImuAngularAccXChanged.emit(value)

    @Property(str, notify=teeensyImuAngularAccYChanged)
    def teensy_imu_angular_acc_y(self):
        return self._teensy_data['imu_angular_acc_y']
    
    @teensy_imu_angular_acc_y.setter
    def teensy_imu_angular_acc_y(self, value):
        if self._teensy_data['imu_angular_acc_y'] != value:
            self._teensy_data['imu_angular_acc_y'] = value
            self.teeensyImuAngularAccYChanged.emit(value)

    @Property(str, notify=teeensyImuAngularAccZChanged)
    def teensy_imu_angular_acc_z(self):
        return self._teensy_data['imu_angular_acc_z']
    
    @teensy_imu_angular_acc_z.setter
    def teensy_imu_angular_acc_z(self, value):
        if self._teensy_data['imu_angular_acc_z'] != value:
            self._teensy_data['imu_angular_acc_z'] = value
            self.teeensyImuAngularAccZChanged.emit(value)

    @Property(float, notify=teensyImuPitchChanged)  # Changed from str to float
    def teensy_imu_pitch(self):
        return float(self._teensy_data['imu_pitch'])  # Convert to float
        
    @teensy_imu_pitch.setter
    def teensy_imu_pitch(self, value):
        value = float(value)  # Ensure value is float
        if self._teensy_data['imu_pitch'] != value:
            self._teensy_data['imu_pitch'] = value
            self.teensyImuPitchChanged.emit(value)

    @Property(float, notify=teensyImuRollChanged)  # Changed from str to float
    def teensy_imu_roll(self):
        return float(self._teensy_data['imu_roll'])
        
    @teensy_imu_roll.setter
    def teensy_imu_roll(self, value):
        value = float(value)
        if self._teensy_data['imu_roll'] != value:
            self._teensy_data['imu_roll'] = value
            self.teensyImuRollChanged.emit(value)

    @Property(float, notify=teensyImuYawChanged)  # Changed from str to float
    def teensy_imu_yaw(self):
        return float(self._teensy_data['imu_yaw'])
        
    @teensy_imu_yaw.setter
    def teensy_imu_yaw(self, value):
        value = float(value)
        if self._teensy_data['imu_yaw'] != value:
            self._teensy_data['imu_yaw'] = value
            self.teensyImuYawChanged.emit(value)

    @Property(bool, notify=teensyYawEnabledChanged)
    def teensy_yaw_enabled(self):
        return self._teensy_data['yaw_enabled']
    
    @teensy_yaw_enabled.setter
    def teensy_yaw_enabled(self, value):
        if self._teensy_data['yaw_enabled'] != value:
            self._teensy_data['yaw_enabled'] = value
            self.teensyYawEnabledChanged.emit(value)

    @Property(str, notify=teensyYawCommandChanged)
    def teensy_yaw_command(self):
        return self._teensy_data['yaw_command']
    
    @teensy_yaw_command.setter
    def teensy_yaw_command(self, value):
        if self._teensy_data['yaw_command'] != value:
            self._teensy_data['yaw_command'] = value
            self.teensyYawCommandChanged.emit(value)

    @Property(str, notify=teensyYawPidPChanged)
    def teensy_yaw_pid_p(self):
        return self._teensy_data['yaw_pid_p']
    
    @teensy_yaw_pid_p.setter
    def teensy_yaw_pid_p(self, value):
        if self._teensy_data['yaw_pid_p'] != value:
            self._teensy_data['yaw_pid_p'] = value
            self.teensyYawPidPChanged.emit(value)

    @Property(str, notify=teensyYawPidIChanged)
    def teensy_yaw_pid_i(self):
        return self._teensy_data['yaw_pid_i']
    
    @teensy_yaw_pid_i.setter
    def teensy_yaw_pid_i(self, value):
        if self._teensy_data['yaw_pid_i'] != value:
            self._teensy_data['yaw_pid_i'] = value
            self.teensyYawPidIChanged.emit(value)

    @Property(str, notify=teensyYawPidDChanged)
    def teensy_yaw_pid_d(self):
        return self._teensy_data['yaw_pid_d']
    
    @teensy_yaw_pid_d.setter
    def teensy_yaw_pid_d(self, value):
        if self._teensy_data['yaw_pid_d'] != value:
            self._teensy_data['yaw_pid_d'] = value
            self.teensyYawPidDChanged.emit(value)

    @Property(str, notify=teensyYawPWMChanged)
    def teensy_yaw_pwm(self):
        return self._teensy_data['yaw_pwm']
    
    @teensy_yaw_pwm.setter
    def teensy_yaw_pwm(self, value):
        if self._teensy_data['yaw_pwm'] != value:
            self._teensy_data['yaw_pwm'] = value
            self.teensyYawPWMChanged.emit(value)

#############################################
### Video Streaming
#############################################

class ImageProvider(QQuickImageProvider):
    def __init__(self, width: int, height: int):
        super().__init__(QQuickImageProvider.Image)
        self._width = width
        self._height = height
        self._format = QImage.Format_RGB888
        self.image = QImage(self._width, self._height, self._format)
        self._lock = threading.Lock()

    def update_image(self, new_image: QImage):
        with self._lock:
            self.image = new_image.copy()

    def requestImage(self, id: str, size, requestedSize) -> QImage:
        with self._lock:
            return self.image

class VideoStream:
    def __init__(self, port: int):
        Gst.init(None)
        self.pipeline = Gst.parse_launch(
            f"udpsrc port={port} caps=\"application/x-rtp, media=(string)video, "
            f"clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" "
            f"! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
        )
        self.sink = self.pipeline.get_by_name('sink')
        self.sink.set_property('emit-signals', True)
        
    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        
    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def connect_new_sample_callback(self, callback: Callable):
        self.sink.connect('new-sample', callback)

#############################################
### Motor Control
#############################################

class MotorControllerBase:
    def __init__(self):
        self._enabled = False
        self._status = {}
        self._last_command_time = 0
        self._watchdog_timeout = 1.0

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._check_watchdog()

    def _check_watchdog(self) -> bool:
        return time.time() - self._last_command_time < self._watchdog_timeout

class WinchController(MotorControllerBase):
    def __init__(self, node: Node, max_speed: float):
        super().__init__()
        self._node = node
        self._max_speed = max_speed
        self._setup_publishers()
        self._status_callbacks = []
        self._status = {}

    def _setup_publishers(self):
        self._speed_pub = self._node.create_publisher(Float64, 'winch/cmd_speed', 1)
        self._enable_pub = self._node.create_publisher(Bool, 'winch/enable', 1)

    def command_speed(self, speed: float) -> bool:
        safe_speed = self._apply_safety_limits(speed)
        msg = Float64()
        msg.data = safe_speed
        self._speed_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def _apply_safety_limits(self, speed: float) -> float:
        return max(min(speed, self._max_speed), -self._max_speed)

    def update_status(self, msg: WinchStatus):
        self._status = {
            'cable_length': f"{msg.cable_length:.2f}",
            'cable_speed': f"{msg.cable_speed:.2f}",
            'winch_torque': f"{msg.winch_torque:.2f}",
            'motor_temperature': f"{msg.motor_temperature:.1f}",
            'motor_voltage': f"{msg.motor_voltage:.1f}",
            'motor_brake': msg.motor_brake,
            'available': msg.available
        }
        for callback in self._status_callbacks:
            callback(self._status)

    def get_status(self) -> Dict:
        return self._status
    
#############################################
### Teensy Monitor
#############################################

class TeensyMonitor:
    def __init__(self, node: Node):
        self._node = node
        self._status = {}

    def _status_callback(self, msg: TeensyStatus):
        try:
            # Convert milliseconds to hours, minutes, seconds
            total_seconds = int(msg.runtime / 1000)  # Convert ms to seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            formatted_runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            self._status = {
                'top_rail_position': f"{msg.top_rail_position:.2f}",
                'top_rail_speed': f"{msg.top_rail_speed:.2f}",
                'top_rail_current': f"{msg.top_rail_current:.2f}",
                'arm_rail_position': f"{msg.arm_rail_position:.2f}",
                'arm_rail_speed': f"{msg.arm_rail_speed:.2f}",
                'arm_rail_current': f"{msg.arm_rail_current:.2f}",
                'voltage': f"{msg.voltage:.2f}",
                'temperature': f"{msg.temperature:.1f}",
                'current': f"{msg.current:.2f}",
                'run_time': formatted_runtime,
                'loop_time': f"{msg.looptime:.2f}",
                'loop_time_counter': f"{msg.looptime_counter:.2f}",
                'left_prop_position': f"{msg.left_prop_position:.2f}",
                'left_prop_pwm': f"{msg.left_prop_pwm:.2f}",
                'right_prop_position': f"{msg.right_prop_position:.2f}",
                'right_prop_pwm': f"{msg.right_prop_pwm:.2f}",
                'imu_acc_x': f"{msg.linear_acceleration.x:.2f}",
                'imu_acc_y': f"{msg.linear_acceleration.y:.2f}",
                'imu_acc_z': f"{msg.linear_acceleration.z:.2f}",
                'imu_angular_acc_x': f"{msg.angular_velocity.x:.2f}",
                'imu_angular_acc_y': f"{msg.angular_velocity.y:.2f}",
                'imu_angular_acc_z': f"{msg.angular_velocity.z:.2f}",
                'imu_pitch': msg.orientation.x,
                'imu_roll': msg.orientation.y,
                'imu_yaw': msg.orientation.z,
                'yaw_enabled': msg.yaw_enabled,
                'yaw_command': f"{msg.yaw_command:.2f}",
                'yaw_pid_p': f"{msg.yaw_pid_p:.2f}",
                'yaw_pid_i': f"{msg.yaw_pid_i:.2f}",
                'yaw_pid_d': f"{msg.yaw_pid_d:.2f}",
                'yaw_pwm': f"{msg.yaw_pwm:.2f}"
            }
        except Exception as e:
            print(f"Error processing Teensy status: {e}")

    def get_status(self) -> Dict:
        return self._status
    

#############################################
### Input Handling
#############################################

class InputDevice(Enum):
    STEAM_DECK = auto()
    KEYBOARD = auto()
    GAMEPAD = auto()

class InputManager:
    def __init__(self):
        self._handlers = {}
        self._active_device = None
        self._callbacks = {}

    def register_device(self, device: InputDevice, handler: Any):
        self._handlers[device] = handler

    def set_active_device(self, device: InputDevice):
        if device not in self._handlers:
            raise ValueError(f"Device {device} not registered")
        self._active_device = device

    def register_callback(self, event_type: str, callback: Callable):
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

class SteamDeckHandler:
    def __init__(self, deadzone: float, smoothing_factor: float = 0.1):
        self._deadzone = deadzone
        self._smoothing_factor = max(0.0, min(1.0, smoothing_factor))  # Clamp between 0 and 1
        self._input_state = {}
        self._callbacks = {}
        self._prev_stick_values = {
            'left_stick': {'x': 0.0, 'y': 0.0},
            'right_stick': {'x': 0.0, 'y': 0.0}
        }

    def process_input(self, msg: SteamDeckInput):
        new_state = {
            'left_stick': self._process_stick(msg.left_stick_x, msg.left_stick_y, 'left_stick'),
            'right_stick': self._process_stick(msg.right_stick_x, msg.right_stick_y, 'right_stick'),
            'triggers': {
                'left': msg.left_trigger,
                'right': msg.right_trigger
            },
            'dpad': {
                'up': msg.dpad_up,
                'down': msg.dpad_down,
                'left': msg.dpad_left,
                'right': msg.dpad_right
            },
            'buttons': {
                'a': msg.a,
                'b': msg.b,
                'x': msg.x,
                'y': msg.y,
                'l1': msg.l1,
                'r1': msg.r1,
                'menu': msg.menu
            },
            'imu': {
                'pitch': msg.imu_pitch,
                'roll': msg.imu_roll,
                'yaw': msg.imu_yaw
            }
        }
        
        self._input_state = new_state

    def _process_stick(self, x: float, y: float, stick_id: str) -> Dict[str, float]:
        # Normalize inputs to -1.0 to 1.0 range
        x = x / 32768.0
        y = y / 32768.0
        
        # Calculate magnitude and direction
        magnitude = math.sqrt(x*x + y*y)
        if magnitude < self._deadzone:
            self._prev_stick_values[stick_id] = {'x': 0.0, 'y': 0.0}
            return {'x': 0.0, 'y': 0.0}
        
        # Calculate normalized direction
        if magnitude > 0:
            normalized_x = x / magnitude
            normalized_y = y / magnitude
        else:
            normalized_x = 0
            normalized_y = 0
        
        # Apply deadzone scaling
        scaled_magnitude = self._scale_deadzone(magnitude)
        
        # Apply the scaled magnitude back to the normalized direction
        processed_x = normalized_x * scaled_magnitude
        processed_y = normalized_y * scaled_magnitude
        
        # Apply smoothing
        smoothed_x = self._apply_smoothing(processed_x, self._prev_stick_values[stick_id]['x'])
        smoothed_y = self._apply_smoothing(processed_y, self._prev_stick_values[stick_id]['y'])
        
        # Store current values for next frame
        self._prev_stick_values[stick_id] = {'x': smoothed_x, 'y': smoothed_y}
        
        return {
            'x': smoothed_x * 32768,
            'y': smoothed_y * 32768
        }

    def _scale_deadzone(self, magnitude: float) -> float:
        """
        Scales the input magnitude accounting for deadzone.
        Returns a value between 0 and 1.
        """
        if magnitude < self._deadzone:
            return 0.0
        
        # Rescale the input from [deadzone, 1.0] to [0.0, 1.0]
        scaled = (magnitude - self._deadzone) / (1.0 - self._deadzone)
        return min(scaled, 1.0)  # Clamp to maximum of 1.0

    def _apply_smoothing(self, current: float, previous: float) -> float:
        """
        Applies exponential smoothing to the input values.
        smoothing_factor of 1.0 means no smoothing, 0.0 means maximum smoothing.
        """
        return current * self._smoothing_factor + previous * (1.0 - self._smoothing_factor)

    def _detect_changes(self, new_state: Dict) -> Dict[str, Any]:
        changes = {}
        for key in new_state:
            if key not in self._input_state or new_state[key] != self._input_state[key]:
                changes[key] = new_state[key]
        return changes
    
    def get_current_state(self) -> Dict:
        """Get current input state"""
        return self._input_state

    def has_new_input(self) -> bool:
        """Check if there are new inputs to process"""
        return bool(self._detect_changes(self._input_state))

#############################################
### ROS Integration
#############################################

class RosThread(QThread):
    error_occurred = Signal(str)
    node_started = Signal()
    node_stopped = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self._running = False
        self._shutdown_requested = False

    def run(self):
        try:
            self._running = True
            self.node_started.emit()
            
            while not self._shutdown_requested:
                if not rclpy.ok():
                    raise RuntimeError("ROS context is not valid")
                rclpy.spin_once(self.node, timeout_sec=0.1)
                
            self._cleanup()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._running = False
            self.node_stopped.emit()

    def request_shutdown(self):
        self._shutdown_requested = True

    def _cleanup(self):
        if self.node:
            self.node.destroy_node()

#############################################
### Main Controller
#############################################

class RobotController(Node, QObject):
    frame_ready = Signal()
    new_scan_data = Signal(list, float, float, float, float)
    status_updated = Signal()

    def __init__(self, config: RobotConfig):
        Node.__init__(self, 'robot_controller')
        QObject.__init__(self)
        
        # Initialize components
        self.config = config
        self.image_provider = ImageProvider(config.video_width, config.video_height)
        self.video_stream = VideoStream(config.video_port)
        self.winch_controller = WinchController(self, config.max_winch_speed)
        self.teensyMonitor = TeensyMonitor(self)
        
        self.input_manager = InputManager()
        self.steam_deck = SteamDeckHandler(config.joystick_deadzone)
        self.input_manager.register_device(InputDevice.STEAM_DECK, self.steam_deck)

        self.ui_data_model = UIDataModel()
        self.status_updated.connect(self._update_ui)
        
        # Setup ROS subscribers and publishers
        self._setup_subscribers()
        self._setup_publishers()
        
        # Start video stream
        self.video_stream.connect_new_sample_callback(self.on_new_video_frame)
        self.video_stream.start()

    def _update_ui(self):
        """Update UI elements with latest data"""
        # Update Winch UI
        winch_status = self.winch_controller.get_status()
        self.ui_data_model.winch_length = winch_status.get('cable_length', '0.00')
        self.ui_data_model.winch_speed = winch_status.get('cable_speed', '0.00')
        self.ui_data_model.winch_current = winch_status.get('winch_torque', '0.00')
        self.ui_data_model.winch_available = winch_status.get('available', False)
        self.ui_data_model.winch_torque = winch_status.get('winch_torque', '0.00')
        self.ui_data_model.winch_temperature = winch_status.get('motor_temperature', '0.00')
        self.ui_data_model.winch_voltage = winch_status.get('motor_voltage', '0.00')
        self.ui_data_model.winch_brake = winch_status.get('motor_brake', True)

        # Update Steam Deck Controls
        input_state = self.steam_deck.get_current_state()
        self.ui_data_model.left_joystick_x = input_state.get('left_stick', {}).get('x', 0)
        self.ui_data_model.left_joystick_y = input_state.get('left_stick', {}).get('y', 0)
        self.ui_data_model.right_joystick_x = input_state.get('right_stick', {}).get('x', 0)
        self.ui_data_model.right_joystick_y = input_state.get('right_stick', {}).get('y', 0)
        self.ui_data_model.left_trigger = input_state.get('triggers', {}).get('left', 0)
        self.ui_data_model.right_trigger = input_state.get('triggers', {}).get('right', 0)
        self.ui_data_model.dpad_up = input_state.get('dpad', {}).get('up', False)
        self.ui_data_model.dpad_down = input_state.get('dpad', {}).get('down', False)
        self.ui_data_model.dpad_left = input_state.get('dpad', {}).get('left', False)
        self.ui_data_model.dpad_right = input_state.get('dpad', {}).get('right', False)
        self.ui_data_model.button_a = input_state.get('buttons', {}).get('a', False)
        self.ui_data_model.button_b = input_state.get('buttons', {}).get('b', False)
        self.ui_data_model.button_x = input_state.get('buttons', {}).get('x', False)
        self.ui_data_model.button_y = input_state.get('buttons', {}).get('y', False)
        self.ui_data_model.button_l1 = input_state.get('buttons', {}).get('l1', False)
        self.ui_data_model.button_r1 = input_state.get('buttons', {}).get('r1', False)
        self.ui_data_model.button_menu = input_state.get('buttons', {}).get('menu', False)
        self.ui_data_model.imu_pitch = input_state.get('imu', {}).get('pitch', 0)
        self.ui_data_model.imu_roll = input_state.get('imu', {}).get('roll', 0)
        self.ui_data_model.imu_yaw = input_state.get('imu', {}).get('yaw', 0)

        self.ui_data_model.display_message = self.ui_data_model.display_message

        teensy_status = self.teensyMonitor.get_status()
        self.ui_data_model.top_rail_position = teensy_status.get('top_rail_position', '0.00')
        self.ui_data_model.top_rail_speed = teensy_status.get('top_rail_speed', '0.00')
        self.ui_data_model.top_rail_current = teensy_status.get('top_rail_current', '0.00')
        self.ui_data_model.arm_rail_position = teensy_status.get('arm_rail_position', '0.00')
        self.ui_data_model.arm_rail_speed = teensy_status.get('arm_rail_speed', '0.00')
        self.ui_data_model.arm_rail_current = teensy_status.get('arm_rail_current', '0.00')
        self.ui_data_model.teensy_voltage = teensy_status.get('voltage', '0.00')
        self.ui_data_model.teensy_temperature = teensy_status.get('temperature', '0.00')
        self.ui_data_model.teensy_current = teensy_status.get('current', '0.00')
        self.ui_data_model.teensy_run_time = teensy_status.get('run_time', '0.00')
        self.ui_data_model.teensy_loop_time = teensy_status.get('loop_time', '0.00')
        self.ui_data_model.teensy_loop_time_counter = teensy_status.get('loop_time_counter', '0.00')
        self.ui_data_model.left_prop_position = teensy_status.get('left_prop_position', '0.00')
        self.ui_data_model.left_prop_pwm = teensy_status.get('left_prop_pwm', '0.00')
        self.ui_data_model.right_prop_position = teensy_status.get('right_prop_position', '0.00')
        self.ui_data_model.right_prop_pwm = teensy_status.get('right_prop_pwm', '0.00')
        self.ui_data_model.teensy_imu_acc_x = teensy_status.get('imu_acc_x', '0.00')
        self.ui_data_model.teensy_imu_acc_y = teensy_status.get('imu_acc_y', '0.00')
        self.ui_data_model.teensy_imu_acc_z = teensy_status.get('imu_acc_z', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_x = teensy_status.get('imu_angular_acc_x', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_y = teensy_status.get('imu_angular_acc_y', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_z = teensy_status.get('imu_angular_acc_z', '0.00')
        self.ui_data_model.teensy_imu_pitch = round(float(teensy_status.get('imu_pitch', '0.00')), 2)
        self.ui_data_model.teensy_imu_roll = round(float(teensy_status.get('imu_roll', '0.00')), 2)
        self.ui_data_model.teensy_imu_yaw = round(float(teensy_status.get('imu_yaw', '0.00')), 2)
        self.ui_data_model.teensy_yaw_enabled = teensy_status.get('yaw_enabled', False)
        self.ui_data_model.teensy_yaw_command = teensy_status.get('yaw_command', '0.00')
        self.ui_data_model.teensy_yaw_pid_p = teensy_status.get('yaw_pid_p', '0.00')
        self.ui_data_model.teensy_yaw_pid_i = teensy_status.get('yaw_pid_i', '0.00')
        self.ui_data_model.teensy_yaw_pid_d = teensy_status.get('yaw_pid_d', '0.00')
        self.ui_data_model.teensy_yaw_pwm = teensy_status.get('yaw_pwm', '0.00')


        # Process control inputs
        self._process_control_input(input_state)

    def display_message(self, message: str):
        self.ui_data_model.display_message = message
        
    def _process_control_input(self, input_state: Dict):
        """Process control inputs and update UI accordingly"""
        # Process joystick inputs
        if self.ui_data_model.left_joystick_control == "EF arm":
            command_speed = input_state['left_stick']['y'] * 1000 / 32768
            msg = Float32(data=command_speed)
            self.ef_move_arm_rail_speed_pub.publish(msg)
            self.display_message(f"Sending EF Arm Rail Speed: {command_speed:.2f}")
        elif self.ui_data_model.left_joystick_control == "EF prop joint":
            command_angle = input_state['left_stick']['x'] * 60.0 / 32768.0
            print(f"Command Angle: {command_angle}")
            left_msg = Float32(data=command_angle)
            right_msg = Float32(data=-command_angle)
            self.prop_left_joint_pub.publish(right_msg)
            self.prop_right_joint_pub.publish(right_msg)
            # self.display_message(f"Sending EF Prop Speed: {command_speed:.2f}, Angle: {command_angle:.2f}")
        elif self.ui_data_model.left_joystick_control == "EF spray trigger":
            command_value = 1000 + input_state['left_stick']['y'] * 1000 / 32768
            if command_value < 1000:
                return
            command_value = int(command_value)
            msg = Int32(data=command_value)
            self.ef_spray_trigger_pub.publish(msg)
                

        if self.ui_data_model.right_joystick_control == "Winch Speed":
            if self.ui_data_model.winch_available and self.winch_controller.get_status().get('available', False):
                command_speed = input_state['right_stick']['y'] * self.config.max_winch_speed / 32768
                self.winch_controller.command_speed(command_speed)
                self.display_message(f"Sending Winch Speed: {command_speed:.2f}")
            else:
                self.display_message("Winch not available")
        elif self.ui_data_model.right_joystick_control == "EF top rail":
                command_speed = input_state['right_stick']['y'] * 1000 / 32768
                msg = Float32(data=command_speed)
                self.ef_move_top_rail_speed_pub.publish(msg)
                self.display_message(f"Sending EF Top Rail Speed: {command_speed:.2f}")
        elif self.ui_data_model.right_joystick_control == "EF prop pwm":
                command_speed = input_state['right_stick']['y'] * 600 / 32768
                if command_speed < 0:
                    return
                command_speed = int(command_speed) + 1000
                msg = Int32(data=command_speed)
                self.prop_left_pwm_pub.publish(msg)
                self.prop_right_pwm_pub.publish(msg)
        elif self.ui_data_model.right_joystick_control == "EF spray gimbal":
                command_speed = int(input_state['right_stick']['y'] * 100 / 32768)
                msg = Int32(data=command_speed)
                self.ef_spray_gimbal_speed_pub.publish(msg)
                self.display_message(f"Sending EF Spray Gimbal Speed: {command_speed}")
        


    def _setup_subscribers(self):
        self.create_subscription(
            WinchStatus,
            'winch/status',
            self.winch_controller.update_status,
            1
        )
        
        self.create_subscription(
            SteamDeckInput,
            'steam_deck/input',
            self.steam_deck.process_input,
            1
        )
        
        self.create_subscription(
            LaserScan,
            'scan',
            self._on_lidar_scan,
            1
        )

        self.create_subscription(
            TeensyStatus,
            'teensy/status',
            self.teensyMonitor._status_callback,
            1
        )

    def _setup_publishers(self):
        self.winch_enable_pub = self.create_publisher(Bool, 'winch/enable', 1)
        self.winch_move_speed_pub = self.create_publisher(Float64, 'winch/cmd_speed', 1)
        self.ef_move_top_rail_speed_pub = self.create_publisher(Float32, 'teensy/top_rail/speed/cmd', 1)
        self.ef_move_arm_rail_speed_pub = self.create_publisher(Float32, 'teensy/arm_rail/speed/cmd', 1)
        self.prop_left_pwm_pub = self.create_publisher(Int32, 'teensy/prop/left/pwm/cmd', 1)
        self.prop_right_pwm_pub = self.create_publisher(Int32, 'teensy/prop/right/pwm/cmd', 1)
        self.prop_left_joint_pub = self.create_publisher(Float32, 'teensy/prop/left/joint/cmd', 1)
        self.prop_right_joint_pub = self.create_publisher(Float32, 'teensy/prop/right/joint/cmd', 1)
        self.teensy_relay_pub = self.create_publisher(Bool, 'teensy/relay/cmd', 1)
        self.teensy_enable_pub = self.create_publisher(Bool, 'teensy/enable/cmd', 1)
        self.ef_spray_trigger_pub = self.create_publisher(Int32, 'teensy/spray_gun/trigger/cmd', 1)
        self.ef_spray_gimbal_speed_pub = self.create_publisher(Int32, 'teensy/spray_gun/gimbal/speed/cmd', 1)
        self.ef_yaw_control_pub = self.create_publisher(TeensyYaw, 'teensy/yaw/control/cmd', 1)

    def _on_steam_deck_input(self, msg: SteamDeckInput):
        changes = self.steam_deck.process_input(msg)
        print(f"Steam Deck Input: {changes}")
        self.status_updated.emit()

    def _on_lidar_scan(self, msg: LaserScan):
        self.new_scan_data.emit(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment,
            msg.range_min,
            msg.range_max
        )

    def on_new_video_frame(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        structure = caps.get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')
        
        _, map_info = buffer.map(Gst.MapFlags.READ)
        
        image = QImage(
            map_info.data, 
            width, 
            height, 
            width * 3, 
            QImage.Format_RGB888
        )
        
        self.image_provider.update_image(image)
        buffer.unmap(map_info)
        self.frame_ready.emit()
        
        return Gst.FlowReturn.OK
    
    #############################################
    ### UI Control Methods
    #############################################

    @Slot(bool)
    def setTeensyEnabled(self, enabled: bool):
        """Enable/disable Teensy control"""
        self.ui_data_model.teensy_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.teensy_enable_pub.publish(msg)
        self.get_logger().info(f'Teensy {"enabled" if enabled else "disabled"}')

    @Slot(bool)
    def setWinchEnabled(self, enabled: bool):
        """Enable/disable winch control"""
        self.ui_data_model.winch_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.winch_enable_pub.publish(msg)
        self.get_logger().info(f'Winch {"enabled" if enabled else "disabled"}')

    @Slot(bool)
    def setTeensyRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self.ui_data_model.teensy_relay_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.teensy_relay_pub.publish(msg)
        self.get_logger().info(f'Teensy relay {"enabled" if enabled else "disabled"}')

    @Slot(str)
    def setLeftJoystickControl(self, control: str):
        """Set left joystick control mode"""
        self.ui_data_model.left_joystick_control = control
        self.get_logger().info(f'Left joystick control set to: {control}')

    @Slot(str)
    def setRightJoystickControl(self, control: str):
        """Set right joystick control mode"""
        self.ui_data_model.right_joystick_control = control
        self.get_logger().info(f'Right joystick control set to: {control}')
        self.display_message(f'Right joystick control set to: {control}')

    @Slot(bool, float, float, float, float, int)
    def setYawControl(self, enabled: bool, target: float, p: float, i: float, d: float, pwm: int):
        """Set yaw control parameters and enable state"""
        msg = TeensyYaw()
        msg.yaw_enabled = enabled
        msg.yaw_command = target  # Use current yaw as target
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        msg.yaw_pwm = pwm
        self.ef_yaw_control_pub.publish(msg)
        self.display_message(f'Yaw control {"enabled" if enabled else "disabled"} with Target: {target} P:{p} I:{i} D:{d} PWM:{pwm}')

    @Slot()
    def terminateNodes(self):
        """Terminate all ROS nodes"""
        try:
            home_dir = os.path.expanduser("~")
            script_path = os.path.join(home_dir, "stop_all_nodes.bash")
            subprocess.run(["bash", script_path])
            self.get_logger().info('Terminated all nodes')
        except subprocess.CalledProcessError as e:
            self.get_logger().error(f'Error terminating nodes: {e}')

    @Slot(bool)
    def toggleSwitchChanged(self, checked: bool):
        """Handle toggle switch state change"""
        self.get_logger().info(f'Toggle switch changed to: {checked}')
        # Add specific toggle switch handling logic here

    def cleanup(self):
        self.video_stream.stop()

#############################################
### Main Application
#############################################

def main():
    # Initialize ROS
    rclpy.init()
    
    # Load configuration
    config = ConfigLoader.load_config('robot_config.yaml')
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create robot controller
    controller = RobotController(config)
    
    # Start ROS thread
    ros_thread = RosThread(controller)
    ros_thread.start()
    
    # Setup QML engine
    engine = QQmlApplicationEngine()
    engine.addImageProvider("live", controller.image_provider)
    
    # Load QML interface
    qml_path = os.path.join(os.path.dirname(__file__), 'qml', 'MainWindow.qml')
    engine.load(QUrl.fromLocalFile(qml_path))
    
    # Set context properties
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty("uiData", controller.ui_data_model)
    
    # Start status update timer
    status_timer = QTimer()
    status_timer.timeout.connect(controller.status_updated.emit)
    status_timer.start(int(1000 / config.update_rate))
    
    # Run application
    try:
        sys.exit(app.exec())
    finally:
        controller.cleanup()
        ros_thread.request_shutdown()
        ros_thread.wait()
        rclpy.shutdown()

if __name__ == '__main__':
    main()