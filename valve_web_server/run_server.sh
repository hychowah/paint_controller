#!/bin/bash
# Valve Web Server Startup Script

set -e

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source ROS 2 setup BEFORE creating venv
echo "Setting up ROS 2 environment..."
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
else
    echo "ERROR: ROS 2 humble setup not found at /opt/ros/humble/setup.bash"
    exit 1
fi

# Source workspace setup if available
if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
    source $HOME/ros2_ws/install/setup.bash
else
    echo "WARNING: ROS 2 workspace not found at $HOME/ros2_ws/install/setup.bash"
    echo "Make sure to build your workspace with: colcon build"
fi

# Set ROS_DOMAIN_ID to match your system
# Check if ROS_DOMAIN_ID is already set, otherwise use 2
if [ -z "$ROS_DOMAIN_ID" ]; then
    export ROS_DOMAIN_ID=2
    echo "Setting ROS_DOMAIN_ID to 2"
fi
echo "Using ROS_DOMAIN_ID=$ROS_DOMAIN_ID"

# Create Python virtual environment if it doesn't exist
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Preserve ROS_DOMAIN_ID before sourcing ROS
ROS_DOMAIN_ID_BACKUP=$ROS_DOMAIN_ID

# Reinstall ROS 2 Python paths after venv activation
# This ensures rclpy is available in the venv
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
fi

if [ -f "$HOME/ros2_ws/install/setup.bash" ]; then
    source $HOME/ros2_ws/install/setup.bash
fi

# Restore and ensure ROS_DOMAIN_ID
if [ -z "$ROS_DOMAIN_ID_BACKUP" ]; then
    export ROS_DOMAIN_ID=2
else
    export ROS_DOMAIN_ID=$ROS_DOMAIN_ID_BACKUP
fi

# Install requirements (excluding ROS packages)
echo "Installing Python dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"

# Run the server
echo ""
echo "=========================================="
echo "Valve Web Server Starting"
echo "=========================================="
echo "Server:         http://0.0.0.0:5000"
echo "ROS Topic:      teensy/valve/turn/cmd"
echo "Message Type:   std_msgs/Float32"
echo "=========================================="
echo ""
echo "Access from iPhone:"
echo "  Get your IP: hostname -I"
echo "  Then open: http://<your-ip>:5000"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

cd "$SCRIPT_DIR"
python3 app/valve_server.py
