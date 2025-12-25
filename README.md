# Paint Controller

A comprehensive ROS 2-based control system for robotic painting operations with a modern Qt/QML user interface. This package provides real-time robot control, video streaming, workflow automation, and hardware integration through an intuitive graphical interface.

> **Note:** The C++ version of this project has been discontinued. This documentation focuses on the actively maintained **Python version**.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [Workflow System](#workflow-system)
- [Hardware Integration](#hardware-integration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Documentation](#documentation)
- [License](#license)

## Overview

Paint Controller is a sophisticated control system designed for robotic painting applications. It integrates multiple hardware components (winches, wheels, sensors, cameras) with a responsive GUI built using PySide6 and QML. The system supports automated workflows, real-time monitoring, emergency safety features, and Steam Deck controller input.

### Key Components

- **ROS 2 Integration**: Full ROS 2 Humble+ support for robot communication
- **Qt/QML GUI**: Modern, responsive user interface with PySide6
- **Hardware Controllers**: Support for winches, wheels, Teensy boards, LiDAR, and more
- **Video Streaming**: Multi-camera support with GStreamer backend
- **Workflow Automation**: YAML-based workflow system for automated operations
- **Steam Deck Input**: Native support for Steam Deck controller with haptic feedback
- **Safety Features**: Emergency stop, heartbeat monitoring, warning system

## Features

### Core Features

- **Multi-Hardware Control**
  - Winch control with position feedback
  - Wheel/locomotion control
  - Teensy microcontroller integration
  - LiDAR sensor integration
  - Wind monitoring system

- **Real-time Monitoring**
  - System health monitoring (CPU, memory, disk, network)
  - Heartbeat monitoring for connected devices
  - 3D point cloud visualization (VTK)
  - Live video streaming from multiple cameras

- **User Interface**
  - Modern Qt6/QML-based GUI
  - Customizable overlays and widgets
  - Real-time status displays
  - Interactive control panels

- **Workflow Automation**
  - YAML-based workflow definitions
  - Time-sequenced action execution
  - Support for parallel and sequential operations
  - Built-in actions for common tasks

- **Input Control**
  - Steam Deck controller support with full button/joystick mapping
  - Emergency stop functionality
  - Configurable control modes (Base/EF)
  - Dead zone configuration

- **Safety & Reliability**
  - Emergency stop button with visual/audio feedback
  - Heartbeat monitoring system
  - Warning and alert management
  - Graceful error handling

## System Architecture

The Paint Controller follows a modular architecture organized into specialized packages:

```
paint_controller/
├── controllers/     # Hardware-specific controllers
│   ├── lidar.py           # LiDAR sensor interface
│   ├── wheel.py           # Wheel/locomotion control
│   ├── winch.py           # Winch control system
│   ├── teensy.py          # Teensy board interface
│   ├── wind_monitor.py    # Wind sensor monitoring
│   ├── system_monitor.py  # System resource monitoring
│   └── ssh.py             # SSH connection management
├── handlers/        # Event and input handlers
│   ├── steam_deck.py      # Steam Deck controller
│   ├── emergency.py       # Emergency stop handler
│   ├── heartbeat.py       # Heartbeat monitoring
│   ├── input.py           # General input handling
│   ├── control_processor.py  # Control signal processing
│   └── warnings.py        # Warning management
├── services/        # Service modules
│   ├── video_stream.py    # Video streaming service
│   ├── screen_recorder.py # Screen recording
│   ├── workflow_legacy.py # Legacy workflow system
│   └── workflow/          # Modern workflow system
│       ├── workflow_runner.py
│       ├── workflow_executor.py
│       ├── scheduler.py
│       ├── actions.py
│       └── hardware.py
├── core/            # Core application
│   ├── application.py     # Main application & ROS node
│   └── settings.py        # Settings management
├── ui/              # UI controllers
│   └── overlay.py         # Overlay management
├── widgets/         # Custom Qt widgets
│   └── vtk_pointcloud.py  # VTK point cloud visualization
├── models/          # Data models
│   └── action_config.py   # Action configuration
├── qml/             # QML UI files
│   ├── components/        # Reusable UI components
│   ├── pages/             # Main application pages
│   ├── overlays/          # Overlay definitions
│   └── widgets/           # Custom widgets
└── resource/        # Resources
    └── workflows/         # YAML workflow definitions
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Installation

### System Requirements

- **OS**: Ubuntu 22.04 or later (recommended)
- **ROS**: ROS 2 Humble or later
- **Python**: 3.10+
- **Qt**: Qt 6 (via PySide6)

### Dependencies

#### System Packages

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    libhidapi-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    pkg-config \
    python3-pip
```

#### Python Dependencies

```bash
# Install Python packages
pip3 install \
    PySide6 \
    pyyaml \
    hid \
    vtk \
    numpy \
    matplotlib
```

#### ROS 2 Dependencies

This package requires the custom `paint_interfaces` package:

```bash
# Navigate to your ROS 2 workspace
cd ~/ros2_workspace/src

# Clone paint_interfaces
git clone https://github.com/hychowah/paint_interfaces.git

# Build the interface package
cd ~/ros2_workspace
colcon build --packages-select paint_interfaces

# Source the workspace
source install/setup.bash
```

### Installing Paint Controller

```bash
# Clone the repository
cd ~/ros2_workspace/src
git clone https://github.com/hychowah/paint_controller.git

# Install Python package in development mode
cd paint_controller
pip3 install -e .

# Build the ROS 2 package
cd ~/ros2_workspace
colcon build --packages-select paint_controller_ros2

# Source the workspace
source install/setup.bash
```

### Setting Up Permissions

For Steam Deck controller support, configure udev rules:

```bash
# Create udev rules
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<EOF
# Steam Deck HID
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Quick Start

### Running the Application

The Paint Controller can be run in multiple ways:

#### Method 1: Using ROS 2 Run (Recommended)

```bash
# Source your ROS 2 workspace
source ~/ros2_workspace/install/setup.bash

# Run the paint controller
ros2 run paint_controller_ros2 paint_controller
```

#### Method 2: As a Python Module

```bash
# From the repository root
python3 -m paint_controller
```

#### Method 3: Using Entry Point

```bash
# After pip installation
paint_controller
```

### First Launch

On first launch, the application will:

1. Initialize ROS 2 node
2. Load configuration files
3. Initialize hardware controllers
4. Start video streams (if configured)
5. Display the main GUI

### Basic Controls

- **Menu Button**: Access main control menu
- **L4/R4 Buttons**: Switch between joystick control modes
- **Steam Button (Hold)**: Emergency stop
- **Joysticks**: Robot movement control (mode-dependent)

## Usage

### Control Modes

The Paint Controller supports two primary control modes:

#### Base Control Mode
Controls the robot's base movement (wheels/locomotion).

#### End Effector (EF) Control Mode
Controls the end effector position and orientation.

**Switching Modes**: Press the designated mode switch button on the Steam Deck controller.

### Video Streaming

The application supports multiple camera streams:

```python
# Configure in your settings or config file
camera_streams = [
    {
        "name": "Front Camera",
        "url": "rtsp://camera-ip:554/stream",
        "enabled": True
    },
    # Add more cameras as needed
]
```

### Running Workflows

Workflows automate complex sequences of operations:

```bash
# Load and run a workflow from the GUI
# Or programmatically:
workflow_runner.load_workflow("path/to/workflow.yaml")
workflow_runner.start()
```

See [WORKFLOWS.md](WORKFLOWS.md) for detailed workflow documentation.

### System Monitoring

The system monitor displays:
- CPU usage
- Memory usage
- Disk usage
- Network status
- Connected hardware status

### Emergency Stop

**Immediate Stop**: Hold the Steam button on the controller.

The emergency stop will:
1. Halt all robot motion
2. Display emergency overlay
3. Sound alert (if configured)
4. Log the event

**Recovery**: Follow on-screen instructions to reset and resume operations.

## Configuration

### Configuration Files

Configuration files are located in the `config/` directory:

- `ssh_config.json`: SSH connection settings

### Application Settings

Settings are managed through the `SettingsManager` class and can be configured via:

1. **GUI Settings Panel**: Runtime configuration
2. **Configuration Files**: Persistent settings
3. **Environment Variables**: System-level overrides

### Common Configuration Tasks

#### Configure SSH Connections

Edit `config/ssh_config.json`:

```json
{
    "connections": [
        {
            "name": "Robot PC",
            "host": "192.168.1.100",
            "port": 22,
            "username": "robot",
            "launch_commands": [
                "ros2 launch robot_bringup robot.launch.py"
            ]
        }
    ]
}
```

#### Adjust Control Sensitivity

Modify control parameters in the settings:

```python
# Dead zone for joysticks (0.0 - 1.0)
joystick_dead_zone = 0.15

# Speed multipliers
base_speed_multiplier = 1.0
ef_speed_multiplier = 0.5
```

## Workflow System

The Paint Controller includes a powerful YAML-based workflow system for automating operations.

### Example Workflow

```yaml
name: ascend
description: Move winch to top position
actions:
  - id: Ascend_to_top
    name: winch_move
    type: winch_absolute
    params:
      length: 5000
      speed: 150
    wait_for_completion: true
```

### Available Action Types

- `winch_absolute`: Move winch to absolute position
- `winch_relative`: Move winch relative to current position
- `wheel_move`: Control wheel movement
- `wait`: Wait for specified duration
- `parallel`: Execute multiple actions simultaneously

See [WORKFLOWS.md](WORKFLOWS.md) for complete workflow documentation.

## Hardware Integration

### Supported Hardware

- **Winch Systems**: Position control with feedback
- **Wheel Controllers**: Multi-wheel locomotion
- **Teensy Microcontrollers**: Real-time I/O
- **LiDAR Sensors**: Distance and angle measurement
- **Wind Sensors**: Environmental monitoring
- **Cameras**: GStreamer-compatible video sources
- **Steam Deck Controller**: Primary input device

### Adding New Hardware

To integrate new hardware:

1. Create a controller in `controllers/` directory
2. Inherit from `QObject` for Qt integration
3. Implement ROS 2 publishers/subscribers
4. Register with the main application
5. Update QML UI as needed

Example controller structure:

```python
from PySide6.QtCore import QObject, Signal, Property
from rclpy.node import Node

class MyController(QObject):
    status_changed = Signal()
    
    def __init__(self, robot_controller: Node):
        super().__init__()
        self._robot_controller = robot_controller
        self._setup_ros_interfaces()
    
    def _setup_ros_interfaces(self):
        # Create publishers, subscribers, etc.
        pass
```

## Troubleshooting

### Common Issues

#### Steam Deck Not Detected

**Symptoms**: Controller input not working, device not found error.

**Solutions**:
1. Check USB connection
2. Verify udev rules are installed (see Installation)
3. Ensure Steam Deck is in desktop mode
4. Check device permissions:
   ```bash
   ls -l /dev/hidraw*
   ```
5. Try running with elevated permissions (testing only):
   ```bash
   sudo paint_controller
   ```

#### Video Stream Not Loading

**Symptoms**: Black screen or "No Signal" message.

**Solutions**:
1. Verify camera URL and network connectivity
2. Check GStreamer plugins are installed
3. Test stream with external player:
   ```bash
   gst-launch-1.0 playbin uri=rtsp://your-camera-url
   ```
4. Check firewall settings

#### Qt/GUI Issues

**Symptoms**: Application crashes on startup, rendering issues.

**Solutions**:
1. Force X11 backend (already done in code):
   ```bash
   export QT_QPA_PLATFORM=xcb
   ```
2. Update Qt/PySide6:
   ```bash
   pip3 install --upgrade PySide6
   ```
3. Check system theme compatibility (use light themes)

#### ROS 2 Connection Issues

**Symptoms**: No communication with robot, topics not found.

**Solutions**:
1. Verify ROS 2 environment is sourced:
   ```bash
   source /opt/ros/humble/setup.bash
   source ~/ros2_workspace/install/setup.bash
   ```
2. Check ROS 2 domain ID matches:
   ```bash
   echo $ROS_DOMAIN_ID
   ```
3. List available topics:
   ```bash
   ros2 topic list
   ```
4. Verify network connectivity between machines

#### Build Errors

**Symptoms**: Compilation fails, missing dependencies.

**Solutions**:
1. Clean build:
   ```bash
   cd ~/ros2_workspace
   rm -rf build/ install/ log/
   colcon build --packages-select paint_controller_ros2
   ```
2. Verify all dependencies are installed
3. Check Python version compatibility (3.10+)

### Getting Help

- Check the [API Reference](API_REFERENCE.md) for detailed class documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
- Open an issue on GitHub with detailed error logs

## Development

### Development Setup

```bash
# Install in editable mode
pip3 install -e .

# Install development dependencies
pip3 install pytest black flake8
```

### Code Structure

- Follow PEP 8 style guidelines
- Use type hints for function parameters and returns
- Document classes and functions with docstrings
- Keep modules focused and single-purpose

### Testing

```bash
# Run tests (if available)
pytest

# Run with coverage
pytest --cov=paint_controller
```

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Test your changes thoroughly
5. Submit a pull request

## Documentation

Additional documentation:

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detailed system architecture and design
- **[API_REFERENCE.md](API_REFERENCE.md)**: Complete API documentation
- **[WORKFLOWS.md](WORKFLOWS.md)**: Workflow system guide
- **[README_OLD.md](README_OLD.md)**: Previous README with C++ information

## License

Copyright 2025 Paint Controller Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

---

**Maintainer**: c3spray_deck (hychowah@gmail.com)

**Version**: 0.1.0

**Status**: Active Development (Python Version)

> **Note**: The C++ version of this project is no longer maintained. All new development focuses on the Python implementation.
