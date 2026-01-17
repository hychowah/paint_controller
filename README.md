# Paint Controller

A ROS 2 node with PySide6 UI for controlling the robot.

## Features

- **Adaptive Multi-Screen Support** - Real-time display detection and management
  - Automatically detects connected/disconnected displays
  - Switch between displays in Settings
  - Supports extended and duplicate display modes
  - See [Multi-Screen Support Documentation](docs/MULTI_SCREEN_SUPPORT.md) for details

## Prerequisites

- Ubuntu 22.04/24.04
- ROS 2 (Humble or Jazzy)
- Python 3.10+

### System Dependencies

```bash
sudo apt update
sudo apt install -y \
    python3-venv \
    python3-pip \
    libhidapi-dev \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev
```

### Steam Deck Permissions (if using Steam Deck controller)

```bash
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<EOF
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Installation

### 1. Clone the Repository

```bash
cd ~/ros2_ws/src
git clone https://github.com/hychowah/paint_controller.git paint_controller_ros2
```

### 2. Clone Dependencies

```bash
cd ~/ros2_ws/src
git clone https://github.com/hychowah/paint_interfaces.git
```

### 3. Build ROS 2 Packages

```bash
cd ~/ros2_ws
colcon build --packages-select paint_interfaces paint_controller_ros2
source install/setup.bash
```

### 4. Create Virtual Environment

```bash
cd ~/ros2_ws/src/paint_controller_ros2
python3 -m venv python/paint_controller/venv
source python/paint_controller/venv/bin/activate
pip install --upgrade pip
pip install -r python/paint_controller/requirements.txt
pip install -e .
```

### 5. Create Launcher Script

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/paint_controller << 'EOF'
#!/bin/bash
SCRIPT_DIR="/home/$USER/ros2_ws/src/paint_controller_ros2"
VENV_DIR="${SCRIPT_DIR}/python/paint_controller/venv"
source /opt/ros/jazzy/setup.bash 2>/dev/null || source /opt/ros/humble/setup.bash 2>/dev/null
source ~/ros2_ws/install/setup.bash 2>/dev/null
source "${VENV_DIR}/bin/activate"
cd "${SCRIPT_DIR}/python"
python -m paint_controller "$@"
EOF
chmod +x ~/.local/bin/paint_controller
```

Make sure `~/.local/bin` is in your PATH (add to `~/.bashrc` if needed):
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Running the Application

### Option 1: Using the Launcher (Recommended)

```bash
paint_controller
```

### Option 2: Manual Run

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
source ~/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/activate
cd ~/ros2_ws/src/paint_controller_ros2/python
python -m paint_controller
```

## Troubleshooting

### Qt Platform Plugin Error
If you see `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`:
```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

### Module Not Found Error
Make sure you installed the package in editable mode:
```bash
cd ~/ros2_ws/src/paint_controller_ros2
source python/paint_controller/venv/bin/activate
pip install -e .
```

### Steam Deck Not Detected
1. Ensure Steam Deck is in desktop mode
2. Check USB connection
3. Verify udev rules are configured (see Prerequisites)
