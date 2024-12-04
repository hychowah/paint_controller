#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import  QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import  QQuickImageProvider


import sys
import os
import signal
import subprocess
import numpy as np
import rclpy
import random
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Float64, Bool
import time
from cv_bridge import CvBridge
from sensor_msgs.msg import LaserScan
from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp


class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(640, 480, QImage.Format_RGB888)

    def requestImage(self, id, size, requestedSize):
        return self.image

class PaintController(Node, QObject):
    frame_ready = Signal()
    new_scan_data = Signal(list, float, float, float, float)

    def __init__(self):
        Node.__init__(self, 'paint_controller')
        QObject.__init__(self)
        Gst.init(None)

        self.image_provider = ImageProvider()

        self.pipeline = Gst.parse_launch(
            "udpsrc port=5000 caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
        )
        self.sink = self.pipeline.get_by_name('sink')
        self.sink.set_property('emit-signals', True)
        self.sink.connect('new-sample', self.on_new_sample)

        self.pipeline.set_state(Gst.State.PLAYING)

        qos_profile = rclpy.qos.QoSProfile(
            reliability=rclpy.qos.QoSReliabilityPolicy.BEST_EFFORT,
            history=rclpy.qos.QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.br = CvBridge()

        self.lidar_sub = self.create_subscription(
            LaserScan,
            'scan',
            self.lidar_sub_callback,
            1)
        self.lidar_sub  # prevent unused variable warning
        
        """ WINCH RELATED TOPIC """
        self._winch_enabled = False
        self.winch_sub = self.create_subscription(
            WinchStatus,
            'winch/status',  # Match the publisher's topic name
            self.winch_sub_callback,
            1  
        )
        self.winch_sub  # prevent unused variable warning

        self.winch_move_speed_pub = self.create_publisher(
            Float64,
            'winch/cmd_speed',
            1
        )
        self.winch_enable_pub = self.create_publisher(
            Bool,
            'winch/enable',
            1
        )

        """ STEAM DECK INPUT RELATED TOPIC """
        steam_input_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST
        )
        self.steam_input_sub = self.create_subscription(
            SteamDeckInput,
            'steam_deck/input',
            self.steam_input_callback,
            steam_input_qos
        )
        self.steam_input_sub

        self.wheel_sub = self.create_subscription(
            WheelStatus,
            'wheel_motor_status',
            self.wheel_sub_callback,
            1)
        self.wheel_sub

        self.latest_scan = None

        self._left_wheel_speed = "0"
        self._right_wheel_speed = "0"
        self._left_wheel_current = "0"
        self._right_wheel_current = "0"
        self._wheel_available = False
        self.last_wheel_msg_time = time.time() - 2
        self.last_winch_msg_time = time.time() - 2

        self._left_joystick_control = "None"
        self._right_joystick_control = "None"

        self._winch_status = {}
        self._steam_input = {}

        self.scan_data = None

    def update_status(self):
        if time.time() - self.last_wheel_msg_time > 1:
            self.wheel_available = False
        else:
            self.wheel_available = True

        if time.time() - self.last_winch_msg_time > 1:
            self.winch_available = False
        else:
            self.winch_available = True

    #############################################
    ### Winch Motor Properties and Signals
    #############################################

    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(str)
    winchCurrentChanged = Signal(str)
    winchAvailableChanged = Signal(bool)
    winchTorqueChanged = Signal(str)
    winchTemperatureChanged = Signal(str)
    winchVoltageChanged = Signal(str)
    winchBrakeChanged = Signal(bool)
    winchEnabledChanged = Signal(bool)

    @Property(bool, notify=winchAvailableChanged)
    def winch_available(self):
        return self._winch_status.get('available', False)

    @winch_available.setter 
    def winch_available(self, value):
        if self._winch_status.get('available') != value:
            self._winch_status['available'] = value
            self.winchAvailableChanged.emit(value)

    @Property(str, notify=winchLengthChanged)
    def winch_length(self):
        return self._winch_status.get('cable_length', '0.00')

    @winch_length.setter
    def winch_length(self, value):
        if self._winch_status.get('cable_length') != value:
            self._winch_status['cable_length'] = value
            self.winchLengthChanged.emit(value)

    @Property(str, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_status.get('cable_speed', '0.00')

    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_status.get('cable_speed') != value:
            self._winch_status['cable_speed'] = value
            self.winchSpeedChanged.emit(value)

    @Property(str, notify=winchTorqueChanged)
    def winch_torque(self):
        return self._winch_status.get('winch_torque', '0.00')

    @winch_torque.setter
    def winch_torque(self, value):
        if self._winch_status.get('winch_torque') != value:
            self._winch_status['winch_torque'] = value
            self.winchTorqueChanged.emit(value)

    @Property(str, notify=winchTemperatureChanged)
    def winch_temperature(self):
        return self._winch_status.get('motor_temperature', '0.0')

    @winch_temperature.setter
    def winch_temperature(self, value):
        if self._winch_status.get('motor_temperature') != value:
            self._winch_status['motor_temperature'] = value
            self.winchTemperatureChanged.emit(value)

    @Property(str, notify=winchVoltageChanged)
    def winch_voltage(self):
        return self._winch_status.get('motor_voltage', '0.0')

    @winch_voltage.setter
    def winch_voltage(self, value):
        if self._winch_status.get('motor_voltage') != value:
            self._winch_status['motor_voltage'] = value
            self.winchVoltageChanged.emit(value)

    @Property(bool, notify=winchBrakeChanged)
    def winch_brake(self):
        return self._winch_status.get('motor_brake', False)

    @winch_brake.setter
    def winch_brake(self, value):
        if self._winch_status.get('motor_brake') != value:
            self._winch_status['motor_brake'] = value
            self.winchBrakeChanged.emit(value)

    def winch_sub_callback(self, msg):
        """Handle winch status messages"""
        try:
            # print(f"Received winch status message: {msg}")
            self._winch_status = {
                'cable_length': f"{msg.cable_length:.2f}",
                'cable_speed': f"{msg.cable_speed:.2f}",
                'winch_torque': f"{msg.winch_torque:.2f}",
                'motor_temperature': f"{msg.motor_temperature:.1f}",
                'motor_voltage': f"{msg.motor_voltage:.1f}",
                'motor_brake': msg.motor_brake,
                'available': msg.available
            }

            self.last_winch_msg_time = time.time()

            self.winchAvailableChanged.emit(self._winch_status['available'])
            self.winchLengthChanged.emit(self._winch_status['cable_length'])
            self.winchSpeedChanged.emit(self._winch_status['cable_speed'])
            self.winchTorqueChanged.emit(self._winch_status['winch_torque'])
            self.winchTemperatureChanged.emit(self._winch_status['motor_temperature'])
            self.winchVoltageChanged.emit(self._winch_status['motor_voltage'])
            self.winchBrakeChanged.emit(self._winch_status['motor_brake'])
        except Exception as e:
            self.get_logger().error(f'Error in winch status callback: {str(e)}')

    @Property(bool, notify=winchEnabledChanged)
    def winch_enabled(self):
        return self._winch_enabled

    @winch_enabled.setter
    def winch_enabled(self, value):
        if self._winch_enabled != value:
            self._winch_enabled = value
            self.winchEnabledChanged.emit(value)

    @Slot(bool)
    def setWinchEnabled(self, enabled):
        self.winch_enabled = enabled
        self.get_logger().info(f'Winch {"enabled" if enabled else "disabled"}')
        msg = Bool()
        msg.data = enabled
        self.winch_enable_pub.publish(msg)

    #############################################
    ### Wheel Motor Properties and Signals
    #############################################

    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    wheelAvailableChanged = Signal(bool)
    

    @Property(str, notify=leftSpeedChanged)
    def left_wheel_speed(self):
        return self._left_wheel_speed
    
    @left_wheel_speed.setter
    def left_wheel_speed(self, value):
        if self._left_wheel_speed != value:
            self._left_wheel_speed = value
            self.leftSpeedChanged.emit(value)

    @Property(str, notify=rightSpeedChanged)
    def right_wheel_speed(self):
        return self._right_wheel_speed
    
    @right_wheel_speed.setter
    def right_wheel_speed(self, value):
        if self._right_wheel_speed != value:
            self._right_wheel_speed = value
            self.rightSpeedChanged.emit(value)
    
    @Property(str, notify=leftCurrentChanged)
    def left_wheel_current(self):
        return self._left_wheel_current
    
    @left_wheel_current.setter
    def left_wheel_current(self, value):
        if self._left_wheel_current != value:
            self._left_wheel_current = value
            self.leftCurrentChanged.emit(value)

    @Property(str, notify=rightCurrentChanged)
    def right_wheel_current(self):
        return self._right_wheel_current
    
    @right_wheel_current.setter
    def right_wheel_current(self, value):
        if self._right_wheel_current != value:
            self._right_wheel_current = value
            self.rightCurrentChanged.emit(value)

    @Property(bool, notify=wheelAvailableChanged)  
    def wheel_available(self):
        return self._wheel_available
    
    @wheel_available.setter
    def wheel_available(self, value):
        if self._wheel_available != value:
            self._wheel_available = value
            self.wheelAvailableChanged.emit(value)

    def wheel_sub_callback(self, msg):
        self.left_wheel_speed = f"{msg.left_wheel_speed:.2f}"
        self.right_wheel_speed = f"{msg.right_wheel_speed:.2f}"
        self.left_wheel_current = f"{msg.left_wheel_current:.2f}"
        self.right_wheel_current = f"{msg.right_wheel_current:.2f}"
        self.last_msg_time = time.time()

    #############################################
    ### Steam Deck Input Properties and Signals
    #############################################

    leftStickXChanged = Signal(str)
    leftStickYChanged = Signal(str)
    rightStickXChanged = Signal(str)
    rightStickYChanged = Signal(str)
    leftTriggerChanged = Signal(str)
    rightTriggerChanged = Signal(str)
    aButtonPressedChanged = Signal(bool)
    bButtonPressedChanged = Signal(bool)
    xButtonPressedChanged = Signal(bool)
    yButtonPressedChanged = Signal(bool)
    l1ButtonPressedChanged = Signal(bool)
    r1ButtonPressedChanged = Signal(bool)
    menuButtonPressedChanged = Signal(bool)
    dpadUpPressedChanged = Signal(bool)
    dpadDownPressedChanged = Signal(bool)
    dpadLeftPressedChanged = Signal(bool)
    dpadRightPressedChanged = Signal(bool)
    SteamImuPitchChanged = Signal(str)
    SteamImuRollChanged = Signal(str)
    SteamImuYawChanged = Signal(str)

    @Property(str, notify=leftStickXChanged)
    def left_stick_x(self):
        return self._steam_input.get('left_stick_x', '0')
    
    @left_stick_x.setter
    def left_stick_x(self, value):
        if self._steam_input.get('left_stick_x') != value:
            self._steam_input['left_stick_x'] = value
            self.leftStickXChanged.emit(value)

    @Property(str, notify=leftStickYChanged)
    def left_stick_y(self):
        return self._steam_input.get('left_stick_y', '0')
    
    @left_stick_y.setter
    def left_stick_y(self, value):
        if self._steam_input.get('left_stick_y') != value:
            self._steam_input['left_stick_y'] = value
            self.leftStickYChanged.emit(value)

    @Property(str, notify=rightStickXChanged)
    def right_stick_x(self):
        return self._steam_input.get('right_stick_x', '0')
    
    @right_stick_x.setter
    def right_stick_x(self, value):
        if self._steam_input.get('right_stick_x') != value:
            self._steam_input['right_stick_x'] = value
            self.rightStickXChanged.emit(value)

    @Property(str, notify=rightStickYChanged)
    def right_stick_y(self):
        return self._steam_input.get('right_stick_y', '0')
    
    @right_stick_y.setter
    def right_stick_y(self, value):
        if self._steam_input.get('right_stick_y') != value:
            self._steam_input['right_stick_y'] = value
            self.rightStickYChanged.emit(value)

    # Trigger Properties
    @Property(str, notify=leftTriggerChanged)
    def left_trigger(self):
        return self._steam_input.get('left_trigger', '0')
    
    @left_trigger.setter
    def left_trigger(self, value):
        if self._steam_input.get('left_trigger') != value:
            self._steam_input['left_trigger'] = value
            self.leftTriggerChanged.emit(value)

    @Property(str, notify=rightTriggerChanged)
    def right_trigger(self):
        return self._steam_input.get('right_trigger', '0')
    
    @right_trigger.setter
    def right_trigger(self, value):
        if self._steam_input.get('right_trigger') != value:
            self._steam_input['right_trigger'] = value
            self.rightTriggerChanged.emit(value)

    # Button Properties
    @Property(bool, notify=aButtonPressedChanged)
    def a_pressed(self):
        return self._steam_input.get('a_pressed', False)
    
    @a_pressed.setter
    def a_pressed(self, value):
        if self._steam_input.get('a_pressed') != value:
            self._steam_input['a_pressed'] = value
            self.aButtonPressedChanged.emit(value)

    @Property(bool, notify=bButtonPressedChanged)
    def b_pressed(self):
        return self._steam_input.get('b_pressed', False)
    
    @b_pressed.setter
    def b_pressed(self, value):
        if self._steam_input.get('b_pressed') != value:
            self._steam_input['b_pressed'] = value
            self.bButtonPressedChanged.emit(value)

    @Property(bool, notify=xButtonPressedChanged)
    def x_pressed(self):
        return self._steam_input.get('x_pressed', False)
    
    @x_pressed.setter
    def x_pressed(self, value):
        if self._steam_input.get('x_pressed') != value:
            self._steam_input['x_pressed'] = value
            self.xButtonPressedChanged.emit(value)

    @Property(bool, notify=yButtonPressedChanged)
    def y_pressed(self):
        return self._steam_input.get('y_pressed', False)
    
    @y_pressed.setter
    def y_pressed(self, value):
        if self._steam_input.get('y_pressed') != value:
            self._steam_input['y_pressed'] = value
            self.yButtonPressedChanged.emit(value)

    @Property(bool, notify=l1ButtonPressedChanged)
    def l1_pressed(self):
        return self._steam_input.get('l1_pressed', False)
    
    @l1_pressed.setter
    def l1_pressed(self, value):
        if self._steam_input.get('l1_pressed') != value:
            self._steam_input['l1_pressed'] = value
            self.l1ButtonPressedChanged.emit(value)

    @Property(bool, notify=r1ButtonPressedChanged)
    def r1_pressed(self):
        return self._steam_input.get('r1_pressed', False)
    
    @r1_pressed.setter
    def r1_pressed(self, value):
        if self._steam_input.get('r1_pressed') != value:
            self._steam_input['r1_pressed'] = value
            self.r1ButtonPressedChanged.emit(value)

    @Property(bool, notify=menuButtonPressedChanged)
    def menu_pressed(self):
        return self._steam_input.get('menu_pressed', False)
    
    @menu_pressed.setter
    def menu_pressed(self, value):
        if self._steam_input.get('menu_pressed') != value:
            self._steam_input['menu_pressed'] = value
            self.menuButtonPressedChanged.emit(value)

    # D-Pad Properties
    @Property(bool, notify=dpadUpPressedChanged)
    def dpad_up_pressed(self):
        return self._steam_input.get('dpad_up_pressed', False)
    
    @dpad_up_pressed.setter
    def dpad_up_pressed(self, value):
        if self._steam_input.get('dpad_up_pressed') != value:
            self._steam_input['dpad_up_pressed'] = value
            self.dpadUpPressedChanged.emit(value)

    @Property(bool, notify=dpadDownPressedChanged)
    def dpad_down_pressed(self):
        return self._steam_input.get('dpad_down_pressed', False)
    
    @dpad_down_pressed.setter
    def dpad_down_pressed(self, value):
        if self._steam_input.get('dpad_down_pressed') != value:
            self._steam_input['dpad_down_pressed'] = value
            self.dpadDownPressedChanged.emit(value)

    @Property(bool, notify=dpadLeftPressedChanged)
    def dpad_left_pressed(self):
        return self._steam_input.get('dpad_left_pressed', False)
    
    @dpad_left_pressed.setter
    def dpad_left_pressed(self, value):
        if self._steam_input.get('dpad_left_pressed') != value:
            self._steam_input['dpad_left_pressed'] = value
            self.dpadLeftPressedChanged.emit(value)

    @Property(bool, notify=dpadRightPressedChanged)
    def dpad_right_pressed(self):
        return self._steam_input.get('dpad_right_pressed', False)
    
    @dpad_right_pressed.setter
    def dpad_right_pressed(self, value):
        if self._steam_input.get('dpad_right_pressed') != value:
            self._steam_input['dpad_right_pressed'] = value
            self.dpadRightPressedChanged.emit(value)

    # IMU Properties
    @Property(str, notify=SteamImuPitchChanged)
    def imu_pitch(self):
        return self._steam_input.get('imu_pitch', '0')
    
    @imu_pitch.setter
    def imu_pitch(self, value):
        if self._steam_input.get('imu_pitch') != value:
            self._steam_input['imu_pitch'] = value
            self.SteamImuPitchChanged.emit(value)

    @Property(str, notify=SteamImuRollChanged)
    def imu_roll(self):
        return self._steam_input.get('imu_roll', '0')
    
    @imu_roll.setter
    def imu_roll(self, value):
        if self._steam_input.get('imu_roll') != value:
            self._steam_input['imu_roll'] = value
            self.SteamImuRollChanged.emit(value)

    @Property(str, notify=SteamImuYawChanged)
    def imu_yaw(self):
        return self._steam_input.get('imu_yaw', '0')
    
    @imu_yaw.setter
    def imu_yaw(self, value):
        if self._steam_input.get('imu_yaw') != value:
            self._steam_input['imu_yaw'] = value
            self.SteamImuYawChanged.emit(value)

    def steam_input_callback(self, msg):
        """Handle Steam Deck input messages"""
        try:
            self._steam_input = {
                'left_stick_x': f"{msg.left_stick_x}",
                'left_stick_y': f"{msg.left_stick_y}",
                'right_stick_x': f"{msg.right_stick_x}",
                'right_stick_y': f"{msg.right_stick_y}",
                'left_trigger': f"{msg.left_trigger}",
                'right_trigger': f"{msg.right_trigger}",
                'a_pressed': msg.a,
                'b_pressed': msg.b,
                'x_pressed': msg.x,
                'y_pressed': msg.y,
                'l1_pressed': msg.l1,
                'r1_pressed': msg.r1,
                'menu_pressed': msg.menu,
                'dpad_up_pressed': msg.dpad_up,
                'dpad_down_pressed': msg.dpad_down,
                'dpad_left_pressed': msg.dpad_left,
                'dpad_right_pressed': msg.dpad_right,
                'imu_pitch': f"{msg.imu_pitch}",
                'imu_roll': f"{msg.imu_roll}",
                'imu_yaw': f"{msg.imu_yaw}"
            }

            # Emit all signals with their corresponding values
            self.leftStickXChanged.emit(self._steam_input['left_stick_x'])
            self.leftStickYChanged.emit(self._steam_input['left_stick_y'])
            self.rightStickXChanged.emit(self._steam_input['right_stick_x'])
            self.rightStickYChanged.emit(self._steam_input['right_stick_y'])
            self.leftTriggerChanged.emit(self._steam_input['left_trigger'])
            self.rightTriggerChanged.emit(self._steam_input['right_trigger'])
            self.aButtonPressedChanged.emit(self._steam_input['a_pressed'])
            self.bButtonPressedChanged.emit(self._steam_input['b_pressed'])
            self.xButtonPressedChanged.emit(self._steam_input['x_pressed'])
            self.yButtonPressedChanged.emit(self._steam_input['y_pressed'])
            self.l1ButtonPressedChanged.emit(self._steam_input['l1_pressed'])
            self.r1ButtonPressedChanged.emit(self._steam_input['r1_pressed'])
            self.menuButtonPressedChanged.emit(self._steam_input['menu_pressed'])
            self.dpadUpPressedChanged.emit(self._steam_input['dpad_up_pressed'])
            self.dpadDownPressedChanged.emit(self._steam_input['dpad_down_pressed'])
            self.dpadLeftPressedChanged.emit(self._steam_input['dpad_left_pressed'])
            self.dpadRightPressedChanged.emit(self._steam_input['dpad_right_pressed'])
            self.SteamImuPitchChanged.emit(self._steam_input['imu_pitch'])
            self.SteamImuRollChanged.emit(self._steam_input['imu_roll'])
            self.SteamImuYawChanged.emit(self._steam_input['imu_yaw'])

            self.update_joystick_control()

        except Exception as e:
            self.get_logger().error(f'Error in steam input callback: {str(e)}')

    #############################################
    ### Control Mapping Properties and Signals
    #############################################

    def update_joystick_control(self):
        'LEFT JOYSTICK CONTROL'
        # if self.left_joystick_control == "None":
        #     pass
        # elif self.left_joystick_control == "Winch Speed":
        #     command_speed = self.joystick_control_winch_speed(self._steam_input.get('left_stick_y', 0))
            
        #     #publish command speed
        #     msg = Float64()
        #     msg.data = command_speed
        #     self.winch_move_speed_pub.publish(msg)
        "RIGHT JOYSTICK CONTROL"
        if self.right_joystick_control == "None":
            pass
        elif self.right_joystick_control == "Winch Speed":
            if not self._winch_enabled:
                return
            command_speed = self.joystick_control_winch_speed(float(self._steam_input.get('right_stick_y', 0.0)))
            #publish command speed
            msg = Float64()
            # print(f"Command speed: {command_speed}")
            msg.data = float(command_speed)
            self.winch_move_speed_pub.publish(msg)

    def joystick_control_winch_speed(self, joystick_value):
        # check if winch is enabled
        if not self._winch_status.get('available', False):
            print("winch not avail")
            return 0
        
        # if not self._winch_status.get('motor_brake', False):
        #     print("winch brake locked")
        #     return 0
        
        # map y axis joystick value to winch speed (-32768 to 32767 -> -1000 to 1000)
        # dead zone is -1000 to 1000
        if (abs(joystick_value) < 1800):
            return 0
        return float(joystick_value / 32.768)
        

    leftJoystickControlChanged = Signal(str)
    rightJoystickControlChanged = Signal(str)

    @Property(str, notify=leftJoystickControlChanged)
    def left_joystick_control(self):
        return self._left_joystick_control

    @left_joystick_control.setter
    def left_joystick_control(self, value):
        if self._left_joystick_control != value:
            self._left_joystick_control = value
            self.leftJoystickControlChanged.emit(value)

    @Property(str, notify=rightJoystickControlChanged)
    def right_joystick_control(self):
        return self._right_joystick_control

    @right_joystick_control.setter
    def right_joystick_control(self, value):
        if self._right_joystick_control != value:
            self._right_joystick_control = value
            self.rightJoystickControlChanged.emit(value)

    @Slot(str)
    def setLeftJoystickControl(self, control):
        self.left_joystick_control = control
        # Add your control logic here based on the selection
        self.get_logger().info(f'Left joystick control set to: {control}')

    @Slot(str)
    def setRightJoystickControl(self, control):
        self.right_joystick_control = control
        # Add your control logic here based on the selection
        self.get_logger().info(f'Right joystick control set to: {control}')

                

    #############################################
    ### Other Properties and Signals
    #############################################
        
    @Slot(bool)
    def toggleSwitchChanged(self, checked):
        print(f"Toggle switch changed: {checked}")
        # Implement your function here that should be triggered by the toggle switch

    @Slot()
    def update_plot(self):
        if self.latest_scan is None:
            return

        ranges = list(self.latest_scan.ranges)
        self.new_scan_data.emit(
            ranges,
            self.latest_scan.angle_min,
            self.latest_scan.angle_increment,
            self.latest_scan.range_min,
            self.latest_scan.range_max
        )

    @Slot(np.ndarray)
    def update_frame(self, frame):
        print("Updating frame")
        self.video_output.update()

    @Slot()
    def terminateNodes(self):
        print("Terminating nodes")
        try:
            home_dir = os.path.expanduser("~")
            script_path = os.path.join(home_dir, "stop_all_nodes.bash")
            subprocess.run(["bash", script_path])
        except subprocess.CalledProcessError as e:
            print(f"Error running stop_all_nodes.bash: {e}")

    def on_new_sample(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        structure = caps.get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')
        
        _, map_info = buffer.map(Gst.MapFlags.READ)
        
        # Ensure the data is in the correct format (RGB)
        data = map_info.data
        
        # Create QImage directly from the buffer data
        image = QImage(data, width, height, width * 3, QImage.Format_RGB888)
        
        self.image_provider.image = image.copy()  # Create a deep copy of the image
        buffer.unmap(map_info)
        
        self.frame_ready.emit()
        
        return Gst.FlowReturn.OK

    def lidar_sub_callback(self, msg):
        self.latest_scan = msg


class RosThread(QThread):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def run(self):
        rclpy.spin(self.node)


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv) 

    paint_controller = PaintController()

    ros_thread = RosThread(paint_controller)
    ros_thread.start()

    engine = QQmlApplicationEngine()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    qml_path = os.path.join(current_dir, 'qml', 'MainWindow.qml')
    engine.addImageProvider("live", paint_controller.image_provider)
    
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("Failed to load QML file.")
        sys.exit(-1)

    root = engine.rootObjects()[0]
    print(f"Root object: {root}")

    stack_view = root.findChild(QObject, "stackView")
    if stack_view is None:
        print("Could not find stackView in QML")
        sys.exit(-1)

    print("Found stackView")

    page1 = stack_view.findChild(QObject, "page1Rect")
    if page1 is None:
        print("Could not find page1 in QML")
        sys.exit(-1)

    print("Found page1")

    engine.rootContext().setContextProperty("lidar_visualizer", paint_controller)
    engine.rootContext().setContextProperty("backend", paint_controller)
    engine.rootContext().setContextProperty("videoStreamer", paint_controller)

    status_timer = QTimer()
    status_timer.timeout.connect(paint_controller.update_status)
    status_timer.start(100)  # update every 100 ms

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
