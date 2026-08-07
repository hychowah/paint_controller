# Paint Controller

ROS 2 + PySide6/QML control application for the paint robot.

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

`paint_controller` is installed by `pip install -e .`. The launcher script above is only an optional convenience wrapper when you do not want to activate the project venv manually.

### Manual Run

```bash
source /opt/ros/jazzy/setup.bash 2>/dev/null || source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
source ~/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/activate
cd ~/ros2_ws/src/paint_controller_ros2/python
python -m paint_controller
```

## Testing

Use the project-local interpreter, not an arbitrary workspace `.venv`.

### Common Validation Commands

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m ruff check .
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m ruff format --check .
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pyright
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests -q
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py -q
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py -q
cd ~/ros2_ws && colcon build --packages-select paint_interfaces paint_controller_ros2
```

### Run the Full Suite

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests -q
```

Note: If `QT_QPA_PLATFORM` is set to `xcb` in your shell environment, `conftest.py` force-overrides it to `offscreen`. The full suite should run without aborting.

### Run a Focused File

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_winch.py -q
```

Useful focused handoff bands:

```bash
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_startup_smoke_shell.py tests/test_startup_smoke_home.py tests/test_qml_imports.py -q
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_startup_smoke_workflow_editor.py tests/test_qml_imports.py -q
/home/$USER/ros2_ws/src/paint_controller_ros2/python/paint_controller/venv/bin/python -m pytest tests/test_app_runtime_runtime.py tests/test_controller_factory_runtime.py -q
```

### Current Test Layers

- **Pure logic and schema**
  - `tests/test_crc.py` — CRC8 algorithm behavior
  - `tests/test_input_utils.py` — Deadzone and double-press input logic
  - `tests/test_settings_schema.py` — Settings schema integrity and signal-pair coverage
  - `tests/test_teleop_modes.py` — Teleop mode catalog invariants and dispatch
  - `tests/test_layer_responsibility_depth.py` — TD-055 layer-depth / port-policy structural checks

- **Harness validation and static regressions**
  - `tests/test_test_infrastructure.py` — Fake ROS/Qt harness primitives
  - `tests/test_qml_imports.py` — Heavyweight QML import usage regression

- **Core runtime state, settings, shell, and overlay**
  - `tests/test_state_store.py` — StateStore property emissions
  - `tests/test_settings_runtime.py` — SettingsManager load/save/gating behavior
  - `tests/test_capability_catalog.py` — Capability catalog metadata and surface mapping
  - `tests/test_shell_state.py` — Single/dual-screen shell state policy
  - `tests/test_shell_router.py` — Route registry and navigation
  - `tests/test_overlay_host_policy.py` — Overlay host matrix and fullscreen policy

- **AppRuntime lifecycle and signal wiring**
  - `tests/test_app_runtime_runtime.py` — AppRuntime bundle creation, context properties, shutdown order
  - `tests/test_signal_wiring.py` — Qt signal interconnection and timer startup

- **Controller factory, admin gate, and action legality**
  - `tests/test_controller_factory_runtime.py` — Controller dependency graph and cleanup order
  - `tests/test_admin_action_gate.py` — Heartbeat gating and enforcement flag behavior
  - `tests/test_action_legality_model.py` — Gate + capability metadata merge

- **QML bridge and context composition**
  - `tests/test_qt_bridge.py` — Popup/fullscreen signal bridge
  - `tests/test_qml_context_composer.py` — QML context-property composition
  - `tests/test_notify_contracts.py` — QML NOTIFY signal contracts for status models

- **Joystick selection, overlay, and input handling**
  - `tests/test_joystick_selection.py` — Joystick selection model
  - `tests/test_overlay_controller.py` — Overlay menu controller
  - `tests/test_input_handler.py` — Menu delegation and thrust toggle
  - `tests/test_exit_hold.py` — Switch hold-to-exit progress, cancel, quit

- **Device controllers and ROS I/O**
  - `tests/test_ros_node.py` — PaintRosNode heartbeat, cleanup, and command-bus pump
  - `tests/test_ros_io.py` — RosCommandBus traffic ordering and invalidation
  - `tests/test_ros_telemetry.py` — Deferred telemetry bridge scheduling
  - `tests/test_winch.py` — WinchController commands, clamping, and status
  - `tests/test_wheel.py` — WheelController commands and availability
  - `tests/test_teensy.py` — TeensyController status, relay, and thrust ramping
  - `tests/test_esp32_valve.py` — ESP32 valve UDP/ROS gateway
  - `tests/test_ssh.py` — SSH launcher and controller cleanup
  - `tests/test_system_monitor.py` — Worker-thread system monitor

- **Safety, heartbeat, and emergency**
  - `tests/test_safety_coordinator.py` — Halt-all effectors and safety latch
  - `tests/test_safety_integration.py` — Heartbeat loss flows through safety coordinator
  - `tests/test_heartbeat.py` — UIHeartbeatHandler online/loss/recovery
  - `tests/test_emergency.py` — Steam emergency button hold and dispatch

- **Teleop control dispatch**
  - `tests/test_control_processor.py` — Joystick-to-hardware command mapping and safety latches

- **Manual action boundaries**
  - `tests/test_manual_command_handler.py` — Python-owned manual command handler
  - `tests/test_winch_motion_handler.py` — Winch action facade
  - `tests/test_wheel_actions.py` — Wheel action facade
  - `tests/test_teensy_actions.py` — Teensy toggle action facade
  - `tests/test_tuning_actions.py` — Tuning PID action facade
  - `tests/test_system_actions.py` — Clear-errors action facade
  - `tests/test_recording_actions.py` — Recording toggle action facade
  - `tests/test_base_top_view_actions.py` — Base-top calibration action facade
  - `tests/test_device_power_actions.py` — Power/home toggle absorption into action facades

- **Workflow engine and editor**
  - `tests/test_workflow_scheduler.py` — Action registry and scheduler
  - `tests/test_workflow_executor.py` — WorkFlowExecutor state machine
  - `tests/test_workflow_runner.py` — QML-facing workflow runner
  - `tests/test_workflow_editor.py` — Editor session (document mutations, save/load)
  - `tests/test_workflow_document.py` — v2 document / migrate / compile
  - `tests/test_workflow_estimate.py` — Shared duration estimate SOT
  - `tests/test_workflow_completion.py` — Wait-done completion policies
  - `tests/test_workflow_action_schema_integrity.py` — ActionType registry integrity

- **Video, base-top view, and runtime services**
  - `tests/test_base_top_view_service.py` — Base-top worker-thread cleanup and map ownership
  - `tests/test_services_runtime.py` — ScreenManager and base-top transformer
  - `tests/test_video_stream.py` — CameraStream / ImageProvider cleanup

- **Steam Deck input**
  - `tests/test_steam_deck_hid.py` — HID report parsing
  - `tests/test_steam_deck_handler.py` — SteamDeckHandler cleanup and button-hold behavior

- **Startup smoke by QML surface**
  - `tests/test_startup_smoke.py` — Feature and page surfaces
  - `tests/test_startup_smoke_home.py` — Home page surface
  - `tests/test_startup_smoke_shell.py` — Shell and navigation surface
  - `tests/test_startup_smoke_workflow_editor.py` — Workflow editor surface

- **Real ROS transport**
  - `tests/test_winch_ros_integration.py` — Winch pub/sub over live ROS

## Repository Layout

- `python/paint_controller/` — Python application code
- `python/paint_controller/qml/` — QML UI
- `python/config/` — runtime configuration JSON
- `tests/` — pytest suite
- Historical C++ sources have been removed from the live repo; no `src/` runtime path remains

## Operational Notes

- Multi-screen behavior is managed by `ScreenManager` and the QML shell.
- The build system is now a pure `ament_cmake` wrapper around the Python package; no live C++ UI/runtime path remains in the repo.
- In fullscreen video, the left/right `ControlInfoPanel` tiles are touch targets: tapping one shows a pressed highlight and opens the joystick control menu; tapping a menu item briefly highlights it before selecting and committing that mode; tapping outside the menu dismisses it. Long mode names (e.g., `"Track Control Right"`) are shown as compact labels in the panel while the full names remain in the menu. Physical L4/R4 and D-pad navigation continue to work as before.

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
