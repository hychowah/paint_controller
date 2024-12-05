from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread

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
            'brake': False,
            'enabled': False
        }
        
        self._wheel_data = {
            'left_speed': '0.00',
            'right_speed': '0.00',
            'left_current': '0.00',
            'right_current': '0.00',
            'available': False
        }

        self.winch_enabled = False
        
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
            }
        }

    def winch_enable(self):
        return self._winch_data.get('brake', False)

    # Winch Properties
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

    # Similar properties for other winch attributes...
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
