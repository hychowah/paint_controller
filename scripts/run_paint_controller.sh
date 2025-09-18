#!/bin/bash

# Set up environment for paint controller
export LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0

# Run the paint controller
ros2 run paint_controller_ros2 paint_controller_cpp "$@"
