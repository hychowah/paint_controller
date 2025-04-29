#!/bin/bash

# Function to check if session exists
session_exists() {
    tmux has-session -t paint_controller_system 2>/dev/null
}

# Check if we're in a tmux session
if [ -z "$TMUX" ]; then
    # Check if paint_system session exists
    if session_exists; then
        echo "Session 'paint_system' exists. Attaching..."
        tmux attach-session -t paint_controller_system
    else
        # Start a new tmux session
        echo "Creating new paint_system session..."
        tmux new-session -d -s paint_controller_system
        tmux rename-window 'paint_control'

        tmux set -g mouse onv

        # Split the window into 5 panes
        tmux split-window -v -p 80
        tmux split-window -h -p 50
        tmux select-pane -t 0
        tmux split-window -h -p 50
        tmux select-pane -t 2
        tmux split-window -v -p 50
        tmux select-pane -t 4
        tmux split-window -v -p 50

        # Start camera in pane 0
        tmux select-pane -t 0

        # Start main program
        tmux select-pane -t 1
        tmux send-keys 'python3 paint_controller/paint_controller.py' C-m

        # Start ros2 bag recording 
        tmux select-pane -t 2
        tmux send-keys "echo 'Waiting 5 seconds for nodes to initialize...' && sleep 5 && timestamp=\$(date '+%Y-%m-%d-%H-%M-%S') && ros2 bag record -o ~/Documents/rosbag_\$timestamp -a" C-m

        # check if client is running
        tmux select-pane -t 3
        tmux send-keys 'sudo chronyc clients' C-m

        # 
        tmux select-pane -t 4

        tmux select-pane -t 5

        # Attach to the new session
        tmux attach-session -t paint_controller_system
    fi
else
    echo "Already in a tmux session. Please exit current session first."
    exit 1
fi