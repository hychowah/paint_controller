#!/bin/bash

# C3SPRAY Paint System Installation Script
# This script sets up the modular paint system control center

set -e  # Exit on any error

INSTALL_DIR="${1:-$HOME/paint-system}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "C3SPRAY Paint System Installation"
echo "======================================"
echo
echo "Installing to: $INSTALL_DIR"
echo

# Create directory structure
echo "Creating directory structure..."
mkdir -p "$INSTALL_DIR"/{config,lib,logs,backup}

# Copy files
echo "Copying system files..."

# Main script
cp "$SCRIPT_DIR/main.sh" "$INSTALL_DIR/" 2>/dev/null || echo "main.sh not found - you'll need to create it"

# Configuration files
cp "$SCRIPT_DIR/config/"* "$INSTALL_DIR/config/" 2>/dev/null || echo "Config files not found - using defaults"

# Library files
cp "$SCRIPT_DIR/lib/"* "$INSTALL_DIR/lib/" 2>/dev/null || echo "Library files not found - you'll need to create them"

# Make main script executable
chmod +x "$INSTALL_DIR/main.sh"

# Create default configuration if not exists
if [[ ! -f "$INSTALL_DIR/config/settings.conf" ]]; then
    echo "Creating default configuration..."
    cat > "$INSTALL_DIR/config/settings.conf" << 'EOF'
# C3SPRAY PAINT SYSTEM CONFIGURATION
# =================================

# NETWORK CONFIGURATION
EF_IP="192.168.10.102"
BASE_IP="192.168.10.173"

# TMUX SESSION NAMES
MAIN_SESSION_NAME="paint_system"
EF_SESSION_NAME="paint_ef_system"
BASE_SESSION_NAME="paint_base_system"

# DATA RECORDING SETTINGS
ROS_BAG_INTERVAL=30
ROS_BAG_PATH="~/Documents"

# SYSTEM PATHS
ROS2_WORKSPACE="~/ros2_ws"
PAINT_CONTROLLER_PATH="src/paint_controller_ros2/paint_controller"

# TIMEOUT SETTINGS
PING_TIMEOUT=2
SSH_TIMEOUT=10
COMPONENT_RESTART_DELAY=1.5

# UI SETTINGS
PROGRESS_DELAY=0.1
DIALOG_WIDTH=70
DIALOG_HEIGHT=20

# LOGGING
LOG_LEVEL="INFO"
LOG_PATH="/tmp/paint_system.log"
EOF
fi

# Create component configurations if they don't exist
if [[ ! -f "$INSTALL_DIR/config/ef_components.conf" ]]; then
    echo "Creating EF component configuration..."
    cat > "$INSTALL_DIR/config/ef_components.conf" << 'EOF'
# EF SYSTEM COMPONENT DEFINITIONS
# ===============================

# Component restart commands
declare -A EF_RESTART_COMMANDS=(
    ["teensy"]="python3 paint_end_effector/teensy_node.py"
    ["lidar"]="ros2 launch unitree_lidar_ros2 launch.py"
    ["camera"]="./start_ef_cam.bash"
    ["sync"]="python3 paint_interfaces/RobotActionSynchronizer.py --robot ef"
)

# Component display names
declare -A EF_DISPLAY_NAMES=(
    ["teensy"]="Teensy Controller"
    ["lidar"]="Lidar Sensor"
    ["camera"]="Camera System"
    ["sync"]="Robot Action Synchronizer"
)
EOF
fi

if [[ ! -f "$INSTALL_DIR/config/base_components.conf" ]]; then
    echo "Creating Base component configuration..."
    cat > "$INSTALL_DIR/config/base_components.conf" << 'EOF'
# BASE SYSTEM COMPONENT DEFINITIONS
# =================================

# Component restart commands
declare -A BASE_RESTART_COMMANDS=(
    ["wheel"]="python3 paint_base/wheel_node.py"
    ["winch"]="python3 paint_base/winch/python/winch_node.py"
    ["camera"]="./start_base_cam.bash"
    ["sync"]="python3 towngas_interfaces/RobotActionSynchronizer.py --robot base"
)

# Component display names
declare -A BASE_DISPLAY_NAMES=(
    ["wheel"]="Wheel Control System"
    ["winch"]="Winch Control System"
    ["camera"]="Camera System"
    ["sync"]="Robot Action Synchronizer"
)
EOF
fi

# Check and install dependencies
echo
echo "Checking dependencies..."
MISSING_DEPS=()

for dep in dialog tmux ssh ping; do
    if ! command -v "$dep" &> /dev/null; then
        MISSING_DEPS+=("$dep")
    fi
done

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo "Missing dependencies: ${MISSING_DEPS[*]}"
    echo
    echo "Please install them using:"
    echo "sudo apt-get update && sudo apt-get install ${MISSING_DEPS[*]}"
    echo
    echo "Then re-run this installer or run the paint system directly."
else
    echo "All dependencies are installed ✓"
fi

# Create desktop shortcut (optional)
if command -v desktop-file-install &> /dev/null; then
    echo
    read -p "Create desktop shortcut? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > "/tmp/paint-system.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=C3SPRAY Paint System
Comment=Paint System Control Center
Exec=gnome-terminal -- bash -c "cd '$INSTALL_DIR' && ./main.sh"
Icon=utilities-terminal
Terminal=false
Categories=Development;
EOF
        
        if desktop-file-install --dir="$HOME/.local/share/applications" "/tmp/paint-system.desktop" 2>/dev/null; then
            echo "Desktop shortcut created ✓"
        else
            echo "Failed to create desktop shortcut"
        fi
        rm -f "/tmp/paint-system.desktop"
    fi
fi

# Create bash alias (optional)
echo
read -p "Add 'paint-system' alias to ~/.bashrc? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if ! grep -q "alias paint-system=" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo "# C3SPRAY Paint System alias" >> "$HOME/.bashrc"
        echo "alias paint-system='cd \"$INSTALL_DIR\" && ./main.sh'" >> "$HOME/.bashrc"
        echo "Alias added to ~/.bashrc ✓"
        echo "Run 'source ~/.bashrc' or restart your terminal to use the 'paint-system' command"
    else
        echo "Alias already exists in ~/.bashrc"
    fi
fi

# Set up log rotation (optional)
if command -v logrotate &> /dev/null; then
    echo
    read -p "Set up log rotation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkdir -p "$HOME/.config/logrotate"
        cat > "$HOME/.config/logrotate/paint-system" << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
        echo "Log rotation configured ✓"
    fi
fi

echo
echo "======================================"
echo "Installation completed successfully!"
echo "======================================"
echo
echo "Installation directory: $INSTALL_DIR"
echo
echo "To start the paint system:"
echo "1. cd $INSTALL_DIR"
echo "2. ./main.sh"
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Or simply run: paint-system"
    echo
fi
echo "Configuration files are in: $INSTALL_DIR/config/"
echo "You can edit them to customize your system settings."
echo
echo "Logs will be stored in: $INSTALL_DIR/logs/"
echo
echo "For help and documentation, run the system and select 'Help' from the menu."

# Final dependency check message
if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo
    echo "⚠️  IMPORTANT: Install missing dependencies before running:"
    echo "sudo apt-get update && sudo apt-get install ${MISSING_DEPS[*]}"
fi

echo
echo "Enjoy using the C3SPRAY Paint System Control Center!"  