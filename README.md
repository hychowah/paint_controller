# Paint Controller

ROS 2 + PySide6/QML control application for the paint robot.

## Current Status

- This repository is currently in a **refactor-first** phase. The intent is to improve architecture, safety, shutdown/threading behavior, tests, and typing gates before resuming net-new feature development.
- `TD-001` Stage 1 is complete: verified-dead QML was removed, false shared-component folders were flattened, constructor-driven QML surfaces were hardened with `required` / `readonly`, offscreen startup/import smoke coverage was expanded, and warn-only `qmllint` CI is in place.
- `TD-031` is complete: the shell now uses an explicit page registry, `systemcontrol` and fullscreen video have dedicated feature roots under `qml/features/`, and canonical theme ownership lives under `qml/theme/CommonStyle.qml` with compatibility shims left at the old paths.
- The architecture control plane is intentionally split: `docs/plan/00_ARCHITECTURE_PROGRESS.md` is the only live execution board, and `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` is durable architecture rationale plus historical context.
- Stage 1A through Stage 1E, Stage 2, Stage 3A, Stage 3B1, Stage 4, Stage 4.5, Workstream A, Workstream B, Workstream C, and Workstream D are complete for the targeted families. Workstream E then landed bounded system-control services, bounded video runtime, shared status models, shell/connectivity contracts, page-level wheel and winch detail retirement, teensy/valve detail retirement, lidar/monitor telemetry retirement, fullscreen overlay telemetry retirement, and the remaining PageHome preview/frame-refresh retirement behind explicit `videoRuntime` ownership.
- Recent runtime hardening also repaired the tracked fullscreen overlay warning classes and restored clean full-suite teardown after the SSH-controller cleanup fix.
- The current next recommended implementation path is settings cleanup, followed by bounded `app_runtime.py` and handler decomposition only where those slices preserve the current ownership boundaries and still materially reduce ambient reads.
- Python runtime is the only live application path in this repository; the old C++ UI path has been removed from the tree.
- Runtime objects are exposed to QML through `setContextProperty()`. Do not use `qmlRegisterSingletonInstance()` in this repo.
- Latest verified local validation on 2026-07-23 is green at `269 passed` via `python/paint_controller/venv/bin/python -m pytest tests -q`.
- Most recent focused validation is green at `10 passed` for `tests/test_startup_smoke_home.py`, `tests/test_startup_smoke_shell.py`, and `tests/test_qml_imports.py`, with the workflow-editor import follow-up green at `2 passed` for `tests/test_startup_smoke_workflow_editor.py` and `tests/test_qml_imports.py`.
- For authority and session-start order: use `INDEX.md` first, prefer `DEVNOTES.md` for the latest verified runtime state, use `docs/plan/00_ARCHITECTURE_PROGRESS.md` for live next-step guidance, and use `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for durable rationale.

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

`paint_controller` is installed by `pip install -e .`. The launcher script below is only an optional convenience wrapper when you do not want to activate the project venv manually.

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

- Pure logic and schema: `tests/test_crc.py`, `tests/test_input_utils.py`, `tests/test_settings_schema.py`
- Harness validation: `tests/test_test_infrastructure.py`
- Core runtime state and persistence: `tests/test_state_store.py`, `tests/test_settings_runtime.py`
- Direct AppRuntime seams and shutdown behavior: `tests/test_app_runtime_runtime.py`
- Controller-factory wiring and admin gate behavior: `tests/test_controller_factory_runtime.py`
- Startup smoke by surface: `tests/test_startup_smoke.py`, `tests/test_startup_smoke_shell.py`, `tests/test_startup_smoke_home.py`, `tests/test_startup_smoke_workflow_editor.py`
- Manual command boundary: `tests/test_manual_command_handler.py`
- Safety-critical command dispatch: `tests/test_control_processor.py`
- Qt signal bridge: `tests/test_qt_bridge.py`
- Component and handler behavior: `tests/test_emergency.py`, `tests/test_input_handler.py`, `tests/test_steam_deck_hid.py`, `tests/test_winch.py`, `tests/test_ssh.py`
- Safety convergence wiring: `tests/test_safety_integration.py`
- Real ROS transport: `tests/test_winch_ros_integration.py`

## Repository Layout

- `python/paint_controller/` — Python application code
- `python/paint_controller/qml/` — QML UI
- `python/config/` — runtime configuration JSON
- `tests/` — pytest suite
- `docs/plan/` — live architecture board plus durable architecture guide
- Historical C++ sources have been removed from the live repo; no `src/` runtime path remains

## Documentation Map

- `INDEX.md` — start here in a fresh LLM or handoff session; repo authority order and doc navigation
- `docs/plan/00_ARCHITECTURE_PROGRESS.md` — current roadmap status, completed slices, next recommended slice
- `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` — durable architecture rationale, anti-goals, and historical completion context
- `DEVNOTES.md` — chronological development notes
- `KNOWLEDGE.md` — reusable Qt/Python/ROS gotchas

## Operational Notes

- Multi-screen behavior is managed by `ScreenManager` and the QML shell; use `docs/plan/00_ARCHITECTURE_PROGRESS.md` for the live next slice and `docs/plan/01_PYTHON_QT_ARCHITECTURE_DEBT_PLAN.md` for durable architecture rationale.
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
