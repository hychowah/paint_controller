import evdev
from evdev import InputDevice, categorize, ecodes, list_devices

def list_input_devices():
    devices = [InputDevice(path) for path in list_devices()]
    return devices

def get_joystick_devices(devices):
    joysticks = []
    for device in devices:
        try:
            capabilities = device.capabilities()
            if ecodes.EV_ABS in capabilities and ecodes.EV_KEY in capabilities:
                joysticks.append(device)
        except OSError as e:
            print(f"Error accessing device {device.path}: {e}")
    return joysticks

def print_event(event):
    if event.type == ecodes.EV_ABS:
        print(f"Joystick moved: {ecodes.bytype[event.type][event.code]} = {event.value}")
    elif event.type == ecodes.EV_KEY:
        state = "pressed" if event.value == 1 else "released"
        print(f"Button {state}: {ecodes.bytype[event.type][event.code]}")

def is_significant_change(current_values, new_value, event_code, threshold):
    return abs(current_values.get(event_code, 0) - new_value) > threshold

# List and print all input devices
devices = list_input_devices()
print("Available input devices:")
for device in devices:
    print(f"{device.path}: {device.name}")

# Filter out joystick devices
joysticks = get_joystick_devices(devices)

if not joysticks:
    print("No joystick devices found.")
else:
    # Initialize dictionary to store the last axis values
    last_values = {}
    threshold = 500  # Set the threshold for significant change

    try:
        for joystick in joysticks:
            print(f"Reading events from {joystick.path} ({joystick.name})")
            for event in joystick.read_loop():
                if event.type in [ecodes.EV_ABS, ecodes.EV_KEY]:
                    if event.type == ecodes.EV_ABS and is_significant_change(last_values, event.value, event.code, threshold):
                        print_event(event)
                        last_values[event.code] = event.value
                    elif event.type == ecodes.EV_KEY:
                        print_event(event)
                        last_values[event.code] = event.value
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        for joystick in joysticks:
            joystick.close()
        print("Devices closed.")
