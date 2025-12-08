import hid
import time

def print_byte_bits(byte_num, data):
    """Print the binary representation of a specific byte"""
    if byte_num < len(data):
        byte = data[byte_num]
        bits = format(byte, '08b')  # Convert to 8-bit binary string
        print(f"Byte {byte_num:2d}: {bits} (0x{byte:02X})")

def print_all_bytes(data):
    """Print all 64 bytes of data"""
    byte_str = " ".join(f"{byte:03d}" for byte in data)
    print(f"Raw data ({len(data)} bytes): {byte_str}")

def main():

    # Steam Deck USB parameters
    VALVE_VID = 0x28DE
    STEAM_DECK_PID = 0x1205
    
    # Get user preference for display mode
    print("Choose display mode:")
    print("1: Monitor all 64 bytes") 
    print("2: Monitor specific byte(s)")
    choice = input("Enter your choice (1 or 2): ")
    
    byte_nums = []
    if choice == "2":
        while True:
            byte_input = input("Enter byte number(s) to monitor (0-63, comma-separated, or 'done' to finish): ")
            if byte_input.lower() == 'done':
                break
            try:
                for num in byte_input.split(','):
                    byte_num = int(num.strip())
                    if 0 <= byte_num <= 63:
                        byte_nums.append(byte_num)
                    else:
                        print(f"Skipping invalid byte number: {byte_num}")
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
        
        if not byte_nums:
            print("No valid byte numbers entered.")
            return
    
    # Find Steam Deck device
    device_info = None
    for dev in hid.enumerate(VALVE_VID, STEAM_DECK_PID):
        if dev.get('interface_number') == 2:
            device_info = dev
            break
    
    if not device_info:
        print('Steam Deck interface 2 not found!')
        return
    
    # Initialize device
    device = hid.device()
    device.open_path(device_info['path'])
    device.set_nonblocking(1)
    
    print("\nMonitoring Steam Deck data... Press Ctrl+C to stop")
    if choice == "2":
        print(f"Monitoring bytes: {sorted(byte_nums)}")
    print("Watch the bits change as you press buttons or move controls")
    
    try:
        prev_data = None
        while True:
            data = device.read(64)
            if data:
                if choice == "1":
                    print_all_bytes(data)
                else:
                    # Check if any monitored byte has changed
                    if prev_data is None:
                        changed = True
                    else:
                        changed = any(data[i] != prev_data[i] for i in byte_nums)
                    
                    if changed:
                        print("\n" + "="*40)
                        for byte_num in sorted(byte_nums):
                            print_byte_bits(byte_num, data)
                    
                    prev_data = bytes(data)
            else:
                time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        device.close()

if __name__ == '__main__':
    main()