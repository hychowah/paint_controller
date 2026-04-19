# Paint Controller

ROS 2 + PySide6/QML control application for the paint robot.

## Current Status

- Python runtime is the primary path; the old C++ UI path is retained only as reference and is no longer built.
- Runtime objects are exposed to QML through `setContextProperty()`. Do not use `qmlRegisterSingletonInstance()` in this repo.
- Local test suite currently passes at `42` tests using the project interpreter in `python/paint_controller/venv`.
- Active modernization status is tracked in `docs/plan/01_MASTER_PLAN.md`.

## Prerequisites

- Ubuntu 22.04 or 24.04
- ROS 2 Humble or Jazzy
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

### Steam Deck Permissions

If you use the Steam Deck controller directly over USB/HID, install the udev rules:

```bash
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<'EOF'
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Installation

### 1. Clone Repositories

```bash
cd ~/ros2_ws/src
git clone https://github.com/hychowah/paint_controller.git paint_controller_ros2
git clone https://github.com/hychowah/paint_interfaces.git
```

### 2. Build ROS Packages

```bash
cd ~/ros2_ws
colcon build --packages-select paint_interfaces paint_controller_ros2
source install/setup.bash
```

### 3. Create the Project Python Environment

```bash
cd ~/ros2_ws/src/paint_controller_ros2
python3 -m venv python/paint_controller/venv
source python/paint_controller/venv/bin/activate
pip install --upgrade pip
pip install -r python/paint_controller/requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### 4. Optional Launcher Script

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/paint_controller <<'EOF'
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

If needed:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Running the Application

### Recommended

```bash
paint_controller
```

### Manual Run

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
source ~/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/activate
cd ~/ros2_ws/src/paint_controller_ros2/python
python -m paint_controller
```

## Testing

Use the project-local interpreter, not an arbitrary workspace `.venv`.

### Run the Full Suite

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest -q
```

### Run a Focused File

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_winch.py -q
```

### Current Test Layers

- Pure logic: `tests/test_crc.py`, `tests/test_input_utils.py`, `tests/test_settings_schema.py`
- Harness validation: `tests/test_test_infrastructure.py`
- Component and handler behavior: `tests/test_emergency.py`, `tests/test_winch.py`
- Real ROS transport: `tests/test_winch_ros_integration.py`

## Repository Layout

- `python/paint_controller/` — Python application code
- `python/paint_controller/qml/` — QML UI
- `python/config/` — runtime configuration JSON
- `tests/` — pytest suite
- `docs/plan/` — modernization tracker and architecture docs
- `src/` — deprecated C++ reference path

## Documentation Map

- `docs/plan/01_MASTER_PLAN.md` — authoritative modernization tracker
- `docs/plan/02_ARCHITECTURE.md` — runtime architecture reference
- `docs/plan/03_QML_BINDINGS.md` — QML/Python binding inventory
- `DEVNOTES.md` — chronological development notes
- `KNOWLEDGE.md` — reusable Qt/Python/ROS gotchas

## Operational Notes

- Multi-screen behavior is managed by `ScreenManager` and the QML shell; the primary behavior is documented in `docs/plan/02_ARCHITECTURE.md`.
- The repository still contains reference C++ sources, but the build system is now a pure `ament_cmake` wrapper around the Python package.

## Troubleshooting

### Qt Platform Plugin Error

If you see `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`:

```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

### Editable Install Missing

```bash
cd ~/ros2_ws/src/paint_controller_ros2
source python/paint_controller/venv/bin/activate
pip install -e .
```

### Steam Deck Not Detected

1. Ensure the Steam Deck is in desktop mode.
2. Check the USB connection.
3. Verify the udev rules above are installed and reloaded.
