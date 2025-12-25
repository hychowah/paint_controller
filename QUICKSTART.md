# Paint Controller Quick Start Guide

Get up and running with Paint Controller in minutes! This guide provides the fastest path to running the application.

## Prerequisites

Before starting, ensure you have:
- Ubuntu 22.04 or later
- ROS 2 Humble installed and sourced
- Python 3.10 or later
- Approximately 2GB of free disk space

## Quick Installation

### 1. Install System Dependencies (5 minutes)

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y \
    libhidapi-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    pkg-config \
    python3-pip \
    git
```

### 2. Set Up ROS 2 Workspace (3 minutes)

```bash
# Create workspace if it doesn't exist
mkdir -p ~/ros2_workspace/src
cd ~/ros2_workspace/src

# Clone paint_interfaces dependency
git clone https://github.com/hychowah/paint_interfaces.git

# Clone paint_controller
git clone https://github.com/hychowah/paint_controller.git

# Go to workspace root
cd ~/ros2_workspace

# Build packages
colcon build --packages-select paint_interfaces paint_controller_ros2

# Source the workspace
source install/setup.bash
```

### 3. Install Python Dependencies (2 minutes)

```bash
cd ~/ros2_workspace/src/paint_controller

# Install Python packages
pip3 install -r requirements.txt

# Install in development mode
pip3 install -e .
```

### 4. Set Up Steam Deck Permissions (Optional, 1 minute)

Only needed if you plan to use a Steam Deck controller:

```bash
sudo tee /etc/udev/rules.d/99-steam-deck.rules <<EOF
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="28de", ATTRS{idProduct}=="1205", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

## First Run

### Launch the Application

```bash
# Source ROS 2 and workspace
source /opt/ros/humble/setup.bash
source ~/ros2_workspace/install/setup.bash

# Run paint controller
python3 -m paint_controller

# Or use ROS 2 run
ros2 run paint_controller_ros2 paint_controller
```

### What to Expect

On first launch, you'll see:

1. **Console Output**: ROS 2 initialization messages
2. **GUI Window**: Main application window with control panels
3. **Status Bar**: Shows connection status of hardware components

The application may show warnings if hardware components are not connected - this is normal for first-time setup.

## Basic Usage

### Main Interface

The application window has several sections:

```
┌─────────────────────────────────────┐
│         Navigation Bar               │
├─────────────────────────────────────┤
│                                     │
│         Main Content Area           │
│    (Pages: Home, Control, etc.)     │
│                                     │
├─────────────────────────────────────┤
│         Status Bar                   │
└─────────────────────────────────────┘
```

### Navigation

- **Home**: Overview and quick status
- **Control**: Manual control interface
- **Monitoring**: System and hardware monitoring
- **Workflows**: Automated workflow execution
- **Settings**: Application configuration

### Testing Without Hardware

You can test the application without physical hardware:

1. **Launch** the application as shown above
2. **Explore** the UI and different pages
3. **Monitor** system resources in the Monitoring page
4. **Load** a sample workflow (won't execute without hardware)
5. **Configure** settings in the Settings page

## Next Steps

### Connect Hardware

To connect actual hardware:

1. **Review** your hardware's ROS 2 topics
2. **Configure** topic names in the code if needed
3. **Connect** hardware and verify ROS 2 communication
4. **Test** individual controllers before full operation

### Run a Workflow

Try running a sample workflow:

```bash
# The workflow files are in resource/workflows/
# Example: ascend.yaml

# From the GUI:
# 1. Go to Workflows page
# 2. Click "Load Workflow"
# 3. Select "resource/workflows/ascend.yaml"
# 4. Click "Start"
```

### Configure Settings

Customize the application:

1. Open Settings page
2. Adjust control parameters:
   - Joystick dead zone
   - Speed multipliers
   - Control modes
3. Configure camera streams
4. Set up SSH connections

## Common First-Run Issues

### Issue: "No module named 'paint_controller'"

**Solution**: Install the package in development mode:
```bash
cd ~/ros2_workspace/src/paint_controller
pip3 install -e .
```

### Issue: "ModuleNotFoundError: No module named 'rclpy'"

**Solution**: Source your ROS 2 installation:
```bash
source /opt/ros/humble/setup.bash
source ~/ros2_workspace/install/setup.bash
```

### Issue: GUI doesn't appear or crashes

**Solution**: Ensure X11 backend is used:
```bash
export QT_QPA_PLATFORM=xcb
python3 -m paint_controller
```

### Issue: "Steam Deck not detected"

**Solution**: 
1. Verify USB connection
2. Check udev rules are installed (see step 4 above)
3. Try reconnecting the controller
4. Check device appears in `/dev/hidraw*`:
   ```bash
   ls -l /dev/hidraw*
   ```

### Issue: Video streams not loading

**Solution**:
1. Verify camera URL is correct
2. Test with gst-launch:
   ```bash
   gst-launch-1.0 playbin uri=rtsp://your-camera-url
   ```
3. Check network connectivity
4. Ensure GStreamer plugins are installed

## Essential Commands

### Starting the Application

```bash
# Standard way (after sourcing ROS 2)
python3 -m paint_controller

# Using ROS 2 run
ros2 run paint_controller_ros2 paint_controller

# With specific log level
python3 -m paint_controller --ros-args --log-level debug
```

### Checking ROS 2 Topics

```bash
# List all topics
ros2 topic list

# Echo a topic
ros2 topic echo /winch/state

# Get topic info
ros2 topic info /cmd_vel
```

### Monitoring System

```bash
# Check ROS 2 nodes
ros2 node list

# Check node info
ros2 node info /paint_controller

# Check running services
ros2 service list
```

## Quick Reference: Controls

### Keyboard Shortcuts (if implemented)

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit application |
| `F11` | Toggle fullscreen |
| `Esc` | Close overlay/modal |

### Steam Deck Controls

| Button | Action |
|--------|--------|
| Menu Button | Open main menu |
| L4/R4 | Switch joystick modes |
| Steam (Hold) | Emergency stop |
| Joysticks | Robot control (mode-dependent) |
| Triggers | Speed control |

## Configuration Files

Key configuration files:

```
paint_controller/
├── config/
│   └── ssh_config.json        # SSH connections
├── resource/
│   └── workflows/              # Workflow YAML files
└── python/paint_controller/
    └── qml/                    # UI configuration
```

## Useful Aliases

Add these to your `~/.bashrc` for convenience:

```bash
# Alias for sourcing workspace
alias source-paint='source /opt/ros/humble/setup.bash && source ~/ros2_workspace/install/setup.bash'

# Alias for running paint controller
alias run-paint='source-paint && python3 -m paint_controller'

# Alias for rebuilding
alias build-paint='cd ~/ros2_workspace && colcon build --packages-select paint_controller_ros2 && source install/setup.bash'
```

After adding, reload your bashrc:
```bash
source ~/.bashrc
```

Then you can simply run:
```bash
run-paint
```

## Learning Resources

### Documentation

- **[README.md](README.md)**: Complete feature overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System design and structure
- **[WORKFLOWS.md](WORKFLOWS.md)**: Creating and running workflows
- **[API_REFERENCE.md](API_REFERENCE.md)**: Complete API documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: How to contribute

### Example Workflows

Check out example workflows in `resource/workflows/`:

- `ascend.yaml`: Simple winch movement
- `descend_a_roll.yaml`: Complete painting sequence

### Code Examples

Look at existing controllers for examples:

```bash
# Simple controller example
cat python/paint_controller/controllers/lidar.py

# Complex controller with multiple features
cat python/paint_controller/controllers/winch.py

# Handler with input processing
cat python/paint_controller/handlers/steam_deck.py
```

## Tips for Success

### 1. Start Small
Begin with simple operations:
- Monitor system resources
- Test individual controllers
- Run simple workflows

### 2. Use Logging
Enable debug logging to understand what's happening:
```bash
python3 -m paint_controller --ros-args --log-level debug
```

### 3. Test Incrementally
- Test one component at a time
- Verify ROS 2 communication separately
- Use small test workflows

### 4. Check Connections
Before running:
- Verify ROS 2 is sourced
- Check hardware is powered and connected
- Verify network connectivity for cameras

### 5. Read the Logs
Console output provides valuable information:
- Initialization messages
- Connection status
- Error details

## Getting Help

If you encounter issues:

1. **Check documentation**: Most common issues are covered
2. **Search issues**: Someone may have encountered the same problem
3. **Check logs**: Error messages often indicate the problem
4. **Ask for help**: Open an issue on GitHub with:
   - Clear description
   - Steps to reproduce
   - Error messages/logs
   - System information

## What's Next?

Now that you have Paint Controller running:

1. **Explore the UI**: Navigate through different pages
2. **Connect hardware**: Set up your actual robot components
3. **Create workflows**: Automate your painting operations
4. **Customize**: Adjust settings to your needs
5. **Contribute**: Help improve the project!

## Quick Command Summary

```bash
# Installation
sudo apt install libhidapi-dev libgstreamer1.0-dev ...
pip3 install -r requirements.txt
pip3 install -e .

# Building
cd ~/ros2_workspace
colcon build --packages-select paint_interfaces paint_controller_ros2

# Running
source /opt/ros/humble/setup.bash
source ~/ros2_workspace/install/setup.bash
python3 -m paint_controller

# Monitoring
ros2 topic list
ros2 node list
ros2 topic echo /winch/state
```

---

**Time to first run**: ~15 minutes (including all installation steps)

**Minimum functional setup**: ~10 minutes (skip optional components)

**Full setup with hardware**: ~30 minutes (including hardware configuration)

---

Happy painting! 🎨🤖

For detailed information, see the [full README](README.md).
