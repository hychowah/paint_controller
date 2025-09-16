#!/bin/bash

# Paint Controller C++ Launcher Script
# This script resolves the pthread library conflict and runs the paint controller

# Set up environment
source /opt/ros/humble/setup.bash
source /home/c3spray_deck/ros2_ws/install/setup.bash

# Override the problematic pthread library from snap
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0

# Run the paint controller with proper environment
exec ros2 run paint_controller_ros2 paint_controller_cpp "$@"
