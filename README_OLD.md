# Paint Controller (Old Documentation)

> **⚠️ NOTICE: This documentation is outdated and refers to the discontinued C++ version.**
> 
> **For current Python version documentation, see [README.md](README.md)**

The `Paint Controller` is a ROS 2 node designed to provide a user interface for controlling the robot

---

**The content below is preserved for historical reference only. The C++ version is no longer maintained.**

---

## Dependencies

### System Requirements
This package requires the following system libraries and dependencies:

#### Required Packages
```bash
# Install required system packages
sudo apt update
sudo apt install -y \
    libhidapi-dev \
    libqt5quick5 \
    libqt5qml5 \
    libqt5widgets5 \
    libqt5core5a \
    qtdeclarative5-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    pkg-config
```

#### Library Dependencies
- **hidapi**: For Steam Deck controller HID communication
- **Qt5**: For GUI framework (Core, Widgets, Quick, Qml)
- **GStreamer**: For video streaming capabilities
- **ROS 2**: Humble or later

#### C++ Steam Deck Handler
The C++ implementation includes a Steam Deck handler that provides:
- Real-time button and joystick input reading
- IMU (accelerometer/gyroscope) data access
- Trigger and analog input processing
- Thread-safe input state management
- Qt signal integration for GUI updates

To test the Steam Deck handler independently:
```bash
# Build the package
cd ~/ros2_workspace
colcon build --packages-select paint_controller_ros2

# Run the Steam Deck test program
source install/setup.bash
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ./install/paint_controller_ros2/lib/paint_controller_ros2/steam_deck_test
```


### Setting Up Permissions
Before running the `Paint Controller`, configure permissions for the Steam Deck device to ensure proper access. Run the following commands to set permissions permanently:

```bash
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<EOF
# Steam Deck HID
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Cloning and Building paint_interfaces
The `Paint Controller` depends on the `paint_interfaces` package. Follow these steps to clone and build it:

1. Navigate to your ROS 2 workspace's `src` directory:
   ```bash
   cd ~/ros2_workspace/src
   ```

2. Clone the `paint_interfaces` repository:
   ```bash
   git clone https://github.com/hychowah/paint_interfaces.git
   ```

3. Build the `paint_interfaces` package:
   ```bash
   cd ~/ros2_workspace
   colcon build --packages-select paint_interfaces
   ```

4. Source the workspace:
   ```bash
   source ~/ros2_workspace/install/setup.bash
   ```

## Building the Package

### C++ Implementation
To build the C++ version of the Paint Controller:

```bash
cd ~/ros2_workspace
colcon build --packages-select paint_controller_ros2
source install/setup.bash
```

### Running the Applications

#### C++ Paint Controller
```bash
# Run with pthread library preload to avoid snap conflicts
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ros2 run paint_controller_ros2 paint_controller_cpp
```

#### Python Paint Controller (Legacy)
```bash
python paint_controller.py
```

#### Steam Deck Test Program
```bash
# Test Steam Deck controller functionality independently
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ./install/paint_controller_ros2/lib/paint_controller_ros2/steam_deck_test
```
   
## Steam Input Node
The Steam Input Node is deprecated. Button detection has been integrated directly into the `Paint Controller`, eliminating the need for a separate input node.

## Troubleshooting

### Library Conflicts
If you encounter library conflicts or undefined symbol errors, use the `LD_PRELOAD` workaround:
```bash
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 <command>
```

### Steam Deck Not Detected
1. Ensure the Steam Deck is connected via USB
2. Make sure it's in desktop mode (not gaming mode)
3. Check that udev rules are properly configured (see Setting Up Permissions section)
4. Try running with sudo if permission issues persist:
   ```bash
   sudo LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ./install/paint_controller_ros2/lib/paint_controller_ros2/steam_deck_test
   ```

### Build Issues
If you encounter build errors:
1. Ensure all dependencies are installed (see Dependencies section)
2. Clean and rebuild:
   ```bash
   rm -rf build/ install/ log/
   colcon build --packages-select paint_controller_ros2
   ```

# pthread Library Issue

## Problem
The application requires `LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0` to run properly due to conflicts between system pthread library and snap-installed libraries.

## Solution
Use the following alias (already added to ~/.bashrc):

```bash
alias run-paint-controller="LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ros2 run paint_controller_ros2 paint_controller_cpp"
```

## Usage
```bash
run-paint-controller
```

Instead of:
```bash
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ros2 run paint_controller_ros2 paint_controller_cpp
```


### Qt/GUI Issues
- Use a light system theme for better text visibility
- Ensure Qt5 development packages are properly installed
- Check that the QML files are in the correct location

## Control
Control Menu Button

![menu_button](https://github.com/user-attachments/assets/1cb5f0d9-d7fa-4900-858a-e7bf89f65758)
![Screenshot from 2025-04-30 00-27-14](https://github.com/user-attachments/assets/4a8c3dcd-b281-4cb0-9894-9078ca2e8596)

Joystick Control Selection R4 & L4

![Steam-Deck-OLED-rear webp](https://github.com/user-attachments/assets/6945287c-9d6d-4ba9-81ca-25c86aa887ac)
![Screenshot from 2025-04-30 00-30-23](https://github.com/user-attachments/assets/a5875e38-b665-4c3f-8f43-fbde514861e6)

To switch between Base control mode and EF control mode, press

![image](https://github.com/user-attachments/assets/65a007fc-0d73-40dd-ac61-aee627a318ce)

![image](https://github.com/user-attachments/assets/60012148-6ef2-4e8b-af41-008ad38814be)

To trigger emgenecy stop, press and hold "STEAM" button

![image](https://github.com/user-attachments/assets/f6739bd4-c247-4a22-9948-f8e7ee077a1b)

![image](https://github.com/user-attachments/assets/0c59fd84-ded4-4825-8854-19854437fef9)

