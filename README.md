# Paint Controller

A ROS 2 node with PySide6 UI for controlling the robot.

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

## Features

### Multi-Screen Display Support

The application now supports adaptive multi-screen display with real-time detection:

- **Automatic Detection**: Detects connected displays automatically
- **Real-Time Monitoring**: Updates when monitors are plugged/unplugged
- **Test Interface**: Dedicated UI for testing multi-screen functionality
- **Extended Display**: Can utilize external monitors for extended workspace

#### Using Multi-Screen Support

1. Launch the application normally
2. Navigate to **Settings** → **Display Settings**
3. Click **"Multi-Screen Test"** to open the test window
4. Connect/disconnect external monitors to see real-time updates

For detailed documentation, see [docs/MULTISCREEN_SUPPORT.md](docs/MULTISCREEN_SUPPORT.md)

#### Testing Multi-Screen (Standalone)

```bash
cd python/paint_controller/scripts
python3 test_multiscreen.py
```

This runs a standalone test that monitors screen changes without the full application.

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

## Development

### Architecture (Phase 1 - New)

The application now uses a modern architecture with dependency injection and separation of concerns:

- **ServiceContainer** (`python/paint_controller/core/service_container.py`) - Dependency injection container
- **ROSManager** (`python/paint_controller/core/ros_manager.py`) - ROS2 lifecycle management
- **QtManager** (`python/paint_controller/core/qt_manager.py`) - Qt/QML lifecycle management
- **PaintControllerApplication** (`python/paint_controller/core/app.py`) - Main application class
- **ViewModels** (`python/paint_controller/viewmodels/`) - MVVM pattern for UI separation

The new architecture uses `main_new()` by default. To use the legacy implementation:
```bash
USE_OLD_MAIN=1 paint_controller
```

### Testing

#### Install Test Dependencies

```bash
cd ~/ros2_ws/src/paint_controller_ros2
source python/paint_controller/venv/bin/activate
pip install -r python/paint_controller/requirements-dev.txt
```

#### Run Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run with coverage
pytest tests/ --cov=paint_controller --cov-report=html

# Run specific test file
pytest tests/unit/test_service_container.py -v
```

#### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions
- `tests/conftest.py` - Shared pytest fixtures

### Migration to New Architecture

The new architecture is backward compatible. The old `main()` function still works, but the new `PaintControllerApplication` class is recommended for new development.

Key improvements:
- Better testability through dependency injection
- Clear separation of concerns (ROS, Qt, Application logic)
- Easier to extend and maintain
- Example ViewModel pattern for UI components

Future phases will continue extracting services from `RobotController` and adding more ViewModels.
