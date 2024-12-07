import rclpy
from rclpy.node import Node
from towngas_interfaces.msg import SteamDeckInput
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
import hid
import struct
from dataclasses import dataclass
import time
import threading

@dataclass
class SteamInputState:
    # Binary buttons with edge detection
    a: bool = False
    a_pressed: bool = False
    b: bool = False
    b_pressed: bool = False
    x: bool = False 
    x_pressed: bool = False
    y: bool = False
    y_pressed: bool = False
    l1: bool = False
    l1_pressed: bool = False
    r1: bool = False
    r1_pressed: bool = False
    l2_click: bool = False
    l2_click_pressed: bool = False
    r2_click: bool = False
    r2_click_pressed: bool = False
    l5: bool = False
    l5_pressed: bool = False
    menu: bool = False
    menu_pressed: bool = False
    steam: bool = False
    steam_pressed: bool = False
    quick_access: bool = False
    quick_access_pressed: bool = False
    dpad_up: bool = False
    dpad_up_pressed: bool = False
    dpad_down: bool = False
    dpad_down_pressed: bool = False
    dpad_left: bool = False
    dpad_left_pressed: bool = False
    dpad_right: bool = False
    dpad_right_pressed: bool = False
    l3: bool = False
    l3_pressed: bool = False
    r5: bool = False
    r5_pressed: bool = False
    right_touchpad_touch: bool = False
    right_touchpad_touch_pressed: bool = False
    left_touchpad_touch: bool = False
    left_touchpad_touch_pressed: bool = False
    
    # Analog inputs
    imu_pitch: float = 0.0
    imu_roll: float = 0.0
    imu_yaw: float = 0.0
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0

class SteamDeckNode(Node):
    def __init__(self):
        super().__init__('steam_deck_node')

        # Configure QoS profile for better performance
        steam_input_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST
        )
        
        # Create publisher with QoS profile
        self.publisher = self.create_publisher(
            SteamDeckInput, 
            'steam_deck/input', 
            1
        )
        
        # Initialize Steam Deck connection
        VALVE_VID = 0x28DE
        STEAM_DECK_PID = 0x1205
        
        # Find Steam Deck device
        device_info = None
        for dev in hid.enumerate(VALVE_VID, STEAM_DECK_PID):
            if dev.get('interface_number') == 2:
                device_info = dev
                break
        
        if not device_info:
            self.get_logger().error('Steam Deck interface 2 not found!')
            raise RuntimeError('Steam Deck not found')
        
        # Initialize device and states
        self.device = hid.Device(path=device_info['path'])
        self.device.nonblocking = 1
        self._lock = threading.Lock()
        self._prev_state = SteamInputState()
        self._current_state = SteamInputState()
        
        # Configure and start read thread
        self._stop_thread = False
        self._read_thread = threading.Thread(target=self._read_loop)
        self._read_thread.daemon = True
        self._read_thread.start()

    def _process_button_edges(self):
        """Process button edge detection"""
        buttons = [
            'a', 'b', 'x', 'y', 'l1', 'r1', 'l2_click', 'r2_click', 
            'l5', 'menu', 'steam', 'quick_access', 'dpad_up', 'dpad_down',
            'dpad_left', 'dpad_right', 'l3', 'r5', 'right_touchpad_touch',
            'left_touchpad_touch'
        ]
        
        for btn in buttons:
            current_val = getattr(self._current_state, btn)
            prev_val = getattr(self._prev_state, btn)
            setattr(self._current_state, f'{btn}_pressed', current_val and not prev_val)

    def _process_input(self, data):
        """Process input data and publish message"""
        if len(data) < 64:
            return
            
        # Process byte 8 (first button byte)
        button_byte1 = data[8]
        self._current_state.r2_click = bool(button_byte1 & (1 << 0))
        self._current_state.l2_click = bool(button_byte1 & (1 << 1))
        self._current_state.r1 = bool(button_byte1 & (1 << 2))
        self._current_state.l1 = bool(button_byte1 & (1 << 3))
        self._current_state.y = bool(button_byte1 & (1 << 4))
        self._current_state.b = bool(button_byte1 & (1 << 5))
        self._current_state.x = bool(button_byte1 & (1 << 6))
        self._current_state.a = bool(button_byte1 & (1 << 7))
        
        # Process byte 9 (second button byte)
        button_byte2 = data[9]
        self._current_state.dpad_up = bool(button_byte2 & (1 << 0))
        self._current_state.dpad_right = bool(button_byte2 & (1 << 1))
        self._current_state.dpad_left = bool(button_byte2 & (1 << 2))
        self._current_state.dpad_down = bool(button_byte2 & (1 << 3))
        self._current_state.quick_access = bool(button_byte2 & (1 << 4))
        self._current_state.steam = bool(button_byte2 & (1 << 5))
        self._current_state.menu = bool(button_byte2 & (1 << 6))
        self._current_state.l5 = bool(button_byte2 & (1 << 7))
        
        # Process byte 10 (third button byte)
        button_byte3 = data[10]
        self._current_state.r5 = bool(button_byte3 & (1 << 0))
        self._current_state.left_touchpad_touch = bool(button_byte3 & (1 << 3))
        self._current_state.right_touchpad_touch = bool(button_byte3 & (1 << 4))
        self._current_state.l3 = bool(button_byte3 & (1 << 6))
        
        # Process analog inputs
        self._current_state.imu_pitch = struct.unpack('<h', bytes([data[38], data[39]]))[0]
        self._current_state.imu_roll = struct.unpack('<h', bytes([data[40], data[41]]))[0]
        self._current_state.imu_yaw = struct.unpack('<h', bytes([data[42], data[43]]))[0]
        self._current_state.left_trigger = struct.unpack('<h', bytes([data[44], data[45]]))[0]
        self._current_state.right_trigger = struct.unpack('<h', bytes([data[46], data[47]]))[0]
        self._current_state.left_stick_x = struct.unpack('<h', bytes([data[48], data[49]]))[0]
        self._current_state.left_stick_y = struct.unpack('<h', bytes([data[50], data[51]]))[0]
        self._current_state.right_stick_x = struct.unpack('<h', bytes([data[52], data[53]]))[0]
        self._current_state.right_stick_y = struct.unpack('<h', bytes([data[54], data[55]]))[0]
        
        # Process edge detection
        self._process_button_edges()
        
        # Create and publish message
        msg = SteamDeckInput()
        for field in self._current_state.__dataclass_fields__:
            setattr(msg, field, getattr(self._current_state, field))
        
        self.publisher.publish(msg)
        
        # Update previous state
        self._prev_state = SteamInputState()
        for field in self._current_state.__dataclass_fields__:
            setattr(self._prev_state, field, getattr(self._current_state, field))

    def _read_loop(self):
        """Main read loop with optimized CPU usage"""
        while not self._stop_thread:
            try:
                data = self.device.read(64)
                if data:
                    with self._lock:
                        self._process_input(data)
                else:
                    # Sleep when no data is available
                    time.sleep(0.001)
            except Exception as e:
                self.get_logger().error(f'Error reading Steam Deck: {e}')
                # Longer sleep on errors
                time.sleep(0.01)

    def __del__(self):
        """Cleanup when object is deleted"""
        self._stop_thread = True
        if hasattr(self, '_read_thread'):
            self._read_thread.join()

def main():
    rclpy.init()
    node = SteamDeckNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()