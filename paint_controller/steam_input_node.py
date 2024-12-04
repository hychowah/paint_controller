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
    
    # Analog inputs (unchanged)
    imu_pitch: float = 0.0
    imu_roll: float = 0.0
    imu_yaw: float = 0.0
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0

class SteamDeckInputMsg:
    def __init__(self):
        self.state = SteamInputState()
        self._last_data = None
    
    def _decode_16bit(self, data: bytes, start_byte: int) -> int:
        return struct.unpack('<h', bytes([data[start_byte], data[start_byte + 1]]))[0]
    
    def _get_bit(self, byte: int, bit_position: int) -> bool:
        return bool(byte & (1 << (8 - bit_position)))
    
    def _check_edge(self, current: bool, previous: bool, pressed_attr: str):
        if current and not previous:
            setattr(self.state, pressed_attr, True)
        else:
            setattr(self.state, pressed_attr, False)

    def process_input(self, data: bytes) -> SteamInputState:
        if len(data) < 64:
            return self.state
            
        # Store previous button states
        prev_state = SteamInputState()
        for field in self.state.__dataclass_fields__:
            if not field.endswith('_pressed'):
                setattr(prev_state, field, getattr(self.state, field))
            
        # Process byte 8 (first button byte)
        button_byte1 = data[8]
        self.state.r2_click = self._get_bit(button_byte1, 1)
        self.state.l2_click = self._get_bit(button_byte1, 2)
        self.state.r1 = self._get_bit(button_byte1, 3)
        self.state.l1 = self._get_bit(button_byte1, 4)
        self.state.y = self._get_bit(button_byte1, 5)
        self.state.b = self._get_bit(button_byte1, 6)
        self.state.x = self._get_bit(button_byte1, 7)
        self.state.a = self._get_bit(button_byte1, 8)
        
        # Process byte 9 (second button byte)
        button_byte2 = data[9]
        self.state.dpad_up = self._get_bit(button_byte2, 1)
        self.state.dpad_right = self._get_bit(button_byte2, 2)
        self.state.dpad_left = self._get_bit(button_byte2, 3)
        self.state.dpad_down = self._get_bit(button_byte2, 4)
        self.state.quick_access = self._get_bit(button_byte2, 5)
        self.state.steam = self._get_bit(button_byte2, 6)
        self.state.menu = self._get_bit(button_byte2, 7)
        self.state.l5 = self._get_bit(button_byte2, 8)
        
        # Process byte 10 (third button byte)
        button_byte3 = data[10]
        self.state.r5 = self._get_bit(button_byte3, 1)
        self.state.left_touchpad_touch = self._get_bit(button_byte3, 4)
        self.state.right_touchpad_touch = self._get_bit(button_byte3, 5)
        self.state.l3 = self._get_bit(button_byte3, 7)
        
        # Detect edges for all buttons
        buttons = ['a', 'b', 'x', 'y', 'l1', 'r1', 'l2_click', 'r2_click', 
                  'l5', 'menu', 'steam', 'quick_access', 'dpad_up', 'dpad_down',
                  'dpad_left', 'dpad_right', 'l3', 'r5', 'right_touchpad_touch',
                  'left_touchpad_touch']
        
        for btn in buttons:
            self._check_edge(
                getattr(self.state, btn),
                getattr(prev_state, btn),
                f'{btn}_pressed'
            )
        
        # Process analog inputs (unchanged)
        self.state.imu_pitch = self._decode_16bit(data, 38)
        self.state.imu_roll = self._decode_16bit(data, 40)
        self.state.imu_yaw = self._decode_16bit(data, 42)
        self.state.left_trigger = self._decode_16bit(data, 44)
        self.state.right_trigger = self._decode_16bit(data, 46)
        self.state.left_stick_x = self._decode_16bit(data, 48)
        self.state.left_stick_y = self._decode_16bit(data, 50)
        self.state.right_stick_x = self._decode_16bit(data, 52)
        self.state.right_stick_y = self._decode_16bit(data, 54)
        
        return self.state
    
class SteamDeckNode(Node):
    def __init__(self):
        super().__init__('steam_deck_node')

        steam_input_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST
        )
        self.publisher = self.create_publisher(SteamDeckInput, 'steam_deck/input', 1)
        self.timer = self.create_timer(0.02, self.timer_callback)  # 100Hz

        
        
        # Initialize Steam Deck
        VALVE_VID = 0x28DE
        STEAM_DECK_PID = 0x1205
        
        device_info = None
        for dev in hid.enumerate(VALVE_VID, STEAM_DECK_PID):
            if dev.get('interface_number') == 2:
                device_info = dev
                break
        
        if not device_info:
            self.get_logger().error('Steam Deck interface 2 not found!')
            raise RuntimeError('Steam Deck not found')
            
        self.device = hid.Device(path=device_info['path'])
        self.device.nonblocking = 1
        self.input_handler = SteamDeckInputMsg()
        self._lock = threading.Lock()
        self._latest_data = None
        self._prev_state = SteamInputState()
        
        # Start read thread
        self._stop_thread = False
        self._read_thread = threading.Thread(target=self._read_loop)
        self._read_thread.daemon = True
        self._read_thread.start()

    def _read_loop(self):
        while not self._stop_thread:
            try:
                data = self.device.read(64)
                if data:
                    with self._lock:
                        self._latest_data = data
            except Exception as e:
                self.get_logger().error(f'Error reading Steam Deck: {e}')
                time.sleep(0.001)

    def timer_callback(self):
        with self._lock:
            if self._latest_data:
                data = self._latest_data
                current_state = SteamInputState()
                
                # Process byte 8 (first button byte)
                button_byte1 = data[8]
                current_state.r2_click = bool(button_byte1 & (1 << 0))
                current_state.l2_click = bool(button_byte1 & (1 << 1))
                current_state.r1 = bool(button_byte1 & (1 << 2))
                current_state.l1 = bool(button_byte1 & (1 << 3))
                current_state.y = bool(button_byte1 & (1 << 4))
                current_state.b = bool(button_byte1 & (1 << 5))
                current_state.x = bool(button_byte1 & (1 << 6))
                current_state.a = bool(button_byte1 & (1 << 7))
                
                # Process byte 9 (second button byte)
                button_byte2 = data[9]
                current_state.dpad_up = bool(button_byte2 & (1 << 0))
                current_state.dpad_right = bool(button_byte2 & (1 << 1))
                current_state.dpad_left = bool(button_byte2 & (1 << 2))
                current_state.dpad_down = bool(button_byte2 & (1 << 3))
                current_state.quick_access = bool(button_byte2 & (1 << 4))
                current_state.steam = bool(button_byte2 & (1 << 5))
                current_state.menu = bool(button_byte2 & (1 << 6))
                current_state.l5 = bool(button_byte2 & (1 << 7))
                
                # Process byte 10 (third button byte)
                button_byte3 = data[10]
                current_state.r5 = bool(button_byte3 & (1 << 71))
                current_state.left_touchpad_touch = bool(button_byte3 & (1 << 3))
                current_state.right_touchpad_touch = bool(button_byte3 & (1 << 4))
                current_state.l3 = bool(button_byte3 & (1 << 6))
                
                # Process analog inputs
                current_state.imu_pitch = struct.unpack('<h', bytes([data[38], data[39]]))[0]
                current_state.imu_roll = struct.unpack('<h', bytes([data[40], data[41]]))[0]
                current_state.imu_yaw = struct.unpack('<h', bytes([data[42], data[43]]))[0]
                current_state.left_trigger = struct.unpack('<h', bytes([data[44], data[45]]))[0]
                current_state.right_trigger = struct.unpack('<h', bytes([data[46], data[47]]))[0]
                current_state.left_stick_x = struct.unpack('<h', bytes([data[48], data[49]]))[0]
                current_state.left_stick_y = struct.unpack('<h', bytes([data[50], data[51]]))[0]
                current_state.right_stick_x = struct.unpack('<h', bytes([data[52], data[53]]))[0]
                current_state.right_stick_y = struct.unpack('<h', bytes([data[54], data[55]]))[0]
                
                # Edge detection
                buttons = ['a', 'b', 'x', 'y', 'l1', 'r1', 'l2_click', 'r2_click', 
                        'l5', 'menu', 'steam', 'quick_access', 'dpad_up', 'dpad_down',
                        'dpad_left', 'dpad_right', 'l3', 'r5', 'right_touchpad_touch',
                        'left_touchpad_touch']
                
                for btn in buttons:
                    if getattr(current_state, btn) and not getattr(self._prev_state, btn):
                        setattr(current_state, f'{btn}_pressed', True)
                    else:
                        setattr(current_state, f'{btn}_pressed', False)
                        
                # Update previous state
                self._prev_state = current_state
                
                # Create and publish message
                msg = SteamDeckInput()
                for field in current_state.__dataclass_fields__:
                    setattr(msg, field, getattr(current_state, field))
                    
                self.publisher.publish(msg)

    def __del__(self):
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