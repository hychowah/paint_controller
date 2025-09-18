#!/bin/bash

# Steam Deck Test Program Wrapper
# This script runs the Steam Deck handler test program with proper library setup

cd /home/c3spray_deck/ros2_ws
source install/setup.bash

echo "Starting Steam Deck Controller Test..."
echo "Make sure your Steam Deck is connected via USB and in desktop mode."
echo "You may need to run this with sudo if permissions are required."
echo ""

# Run with pthread library preload to avoid snap conflicts
LD_PRELOAD=/lib/x86_64-linux-gnu/libpthread.so.0 ./install/paint_controller_ros2/lib/paint_controller_ros2/steam_deck_test
