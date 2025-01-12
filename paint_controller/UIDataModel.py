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

class UIDataModel(QObject):
    # Motor Status Signals
    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(int)
    winchCurrentChanged = Signal(int)
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
    wheelEnabledChanged = Signal(bool)
    
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
    buttonL4Changed = Signal(bool)
    buttonR4Changed = Signal(bool)
    buttonMenuChanged = Signal(bool)
    buttonQuickAccessChanged = Signal(bool)
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

    teensyAvailableChanged = Signal(bool)
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

    windSpeedChanged = Signal(float)
    windDirectionChanged = Signal(float)

    efIpChanged = Signal(str)
    efSignalStrengthChanged = Signal(int)
    baseIpChanged = Signal(str)
    baseSignalStrengthChanged = Signal(int)

    
    def __init__(self):
        super().__init__()
        self._winch_data = {
            'length': '0.00',
            'speed': 0,
            'current': 0,
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
            'available': False,
            'enabled': False
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
                'l4': False,
                'r4': False,
                'menu': False,
                'quick_access': False
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
        self._teensy_available = False
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

        self._wind_data = {
            'speed': '0.00',
            'direction': '0.00'
        }

        self._network_data = {
            'ef_ip': "",
            'ef_signal_strength': 0,
            'base_ip': "",
            'base_signal_strength': 0
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

    @Property(int, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_data['speed']
    
    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_data['speed'] != value:
            self._winch_data['speed'] = value
            self.winchSpeedChanged.emit(value)
    
    @Property(int, notify=winchCurrentChanged)
    def winch_current(self):
        return self._winch_data['current']
    
    @winch_current.setter
    def winch_current(self, value):
        if self._winch_data['current'] != value:
            self._winch_data['current'] = value
            self.winchCurrentChanged.emit(value)
    
    @Property(int, notify=winchTorqueChanged)
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

    @Property(str, notify=rightSpeedChanged)
    def right_wheel_speed(self):
        return self._wheel_data['right_speed']
    
    @right_wheel_speed.setter
    def right_wheel_speed(self, value):
        if self._wheel_data['right_speed'] != value:
            self._wheel_data['right_speed'] = value
            self.rightSpeedChanged.emit(value)

    @Property(str, notify=leftCurrentChanged)
    def left_wheel_current(self):
        return self._wheel_data['left_current']
    
    @left_wheel_current.setter
    def left_wheel_current(self, value):
        if self._wheel_data['left_current'] != value:
            self._wheel_data['left_current'] = value
            self.leftCurrentChanged.emit(value)

    @Property(str, notify=rightCurrentChanged)
    def right_wheel_current(self):
        return self._wheel_data['right_current']
    
    @right_wheel_current.setter
    def right_wheel_current(self, value):
        if self._wheel_data['right_current'] != value:
            self._wheel_data['right_current'] = value
            self.rightCurrentChanged.emit(value)

    @Property(bool, notify=wheelAvailableChanged)
    def wheel_available(self):
        return self._wheel_data['available']
    
    @wheel_available.setter
    def wheel_available(self, value):
        if self._wheel_data['available'] != value:
            self._wheel_data['available'] = value
            self.wheelAvailableChanged.emit(value)

    @Property(bool, notify=wheelEnabledChanged)
    def wheel_enabled(self):
        return self._wheel_data['enabled']
    
    @wheel_enabled.setter
    def wheel_enabled(self, value):
        if self._wheel_data['enabled'] != value:
            self._wheel_data['enabled'] = value
            self.wheelEnabledChanged.emit(value)

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

    @Property(bool, notify=buttonL4Changed)
    def button_l4(self):
        return self._input_state['buttons']['l4']
    
    @button_l4.setter
    def button_l4(self, value):
        if self._input_state['buttons']['l4'] != value:
            self._input_state['buttons']['l4'] = value
            self.buttonL4Changed.emit(value)

    @Property(bool, notify=buttonR4Changed)
    def button_r4(self):
        return self._input_state['buttons']['r4']

    @Property(bool, notify=buttonMenuChanged)
    def button_menu(self):
        return self._input_state['buttons']['menu']
    
    @button_menu.setter
    def button_menu(self, value):
        if self._input_state['buttons']['menu'] != value:
            self._input_state['buttons']['menu'] = value
            self.buttonMenuChanged.emit(value)

    @Property(bool, notify=buttonQuickAccessChanged)
    def button_quick_access(self):
        return self._input_state['buttons']['quick_access']
    
    @button_quick_access.setter
    def button_quick_access(self, value):
        if self._input_state['buttons']['quick_access'] != value:
            self._input_state['buttons']['quick_access'] = value
            self.buttonQuickAccessChanged.emit(value)

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

    @Property(bool, notify=teensyAvailableChanged)
    def teensy_available(self):
        return self._teensy_available
    
    @teensy_available.setter
    def teensy_available(self, value):
        if self._teensy_available != value:
            self._teensy_available = value
            self.teensyAvailableChanged.emit(value)

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

    # Wind Properties
    @Property(float, notify=windSpeedChanged)
    def wind_speed(self):
        return self._wind_data['speed']
    
    @wind_speed.setter
    def wind_speed(self, value):
        if self._wind_data['speed'] != value:
            self._wind_data['speed'] = value
            self.windSpeedChanged.emit(value)

    @Property(float, notify=windDirectionChanged)
    def wind_direction(self):
        return self._wind_data['direction']
    
    @wind_direction.setter
    def wind_direction(self, value):
        if self._wind_data['direction'] != value:
            self._wind_data['direction'] = value
            self.windDirectionChanged.emit(value)


    # Network Properties

    @Property(str, notify=efIpChanged)
    def ef_ip(self):
        return self._network_data['ef_ip']
    
    @ef_ip.setter
    def ef_ip(self, value):
        if self._network_data['ef_ip'] != value:
            self._network_data['ef_ip'] = value
            self.efIpChanged.emit(value)

    @Property(int, notify=efSignalStrengthChanged)
    def ef_signal_strength(self):
        return self._network_data['ef_signal_strength']
    
    @ef_signal_strength.setter
    def ef_signal_strength(self, value):
        if self._network_data['ef_signal_strength'] != value:
            self._network_data['ef_signal_strength'] = value
            self.efSignalStrengthChanged.emit(value)

    @Property(str, notify=baseIpChanged)
    def base_ip(self):
        return self._network_data['base_ip']
    
    @base_ip.setter
    def base_ip(self, value):
        if self._network_data['base_ip'] != value:
            self._network_data['base_ip'] = value
            self.baseIpChanged.emit(value)

    @Property(int, notify=baseSignalStrengthChanged)
    def base_signal_strength(self):
        return self._network_data['base_signal_strength']
    
    @base_signal_strength.setter
    def base_signal_strength(self, value):
        if self._network_data['base_signal_strength'] != value:
            self._network_data['base_signal_strength'] = value
            self.baseSignalStrengthChanged.emit(value)