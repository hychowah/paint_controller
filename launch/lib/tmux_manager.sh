#!/bin/bash

# Tmux session management functions

# Global status variables
MAIN_RUNNING=0
EF_RUNNING=0
BASE_RUNNING=0
MAIN_STATUS="[ ]"
EF_STATUS="[ ]"
BASE_STATUS="[ ]"

# Check if tmux session exists
check_tmux_session() {
    local session="$1"
    tmux has-session -t "$session" 2>/dev/null
    return $?
}

# Update system status variables
update_system_status() {
    check_tmux_session "$MAIN_SESSION_NAME" && MAIN_RUNNING=1 || MAIN_RUNNING=0
    check_tmux_session "$EF_SESSION_NAME" && EF_RUNNING=1 || EF_RUNNING=0
    check_tmux_session "$BASE_SESSION_NAME" && BASE_RUNNING=1 || BASE_RUNNING=0
    
    [[ $MAIN_RUNNING -eq 1 ]] && MAIN_STATUS="[✓]" || MAIN_STATUS="[ ]"
    [[ $EF_RUNNING -eq 1 ]] && EF_STATUS="[✓]" || EF_STATUS="[ ]"
    [[ $BASE_RUNNING -eq 1 ]] && BASE_STATUS="[✓]" || BASE_STATUS="[ ]"
    
    log_debug "System status updated - Main: $MAIN_RUNNING, EF: $EF_RUNNING, Base: $BASE_RUNNING"
}

# Gracefully terminate tmux session
terminate_session() {
    local session="$1"
    
    if check_tmux_session "$session"; then
        log_info "Terminating tmux session: $session"
        
        # Try to gracefully stop processes first
        tmux list-panes -a -t "$session" -F '#{session_name}:#{window_index}.#{pane_index}' | while read pane; do
            tmux send-keys -t "$pane" C-c
            sleep 0.5
        done
        
        sleep 1
        tmux kill-session -t "$session"
        
        # Verify session is terminated
        if ! check_tmux_session "$session"; then
            log_info "Session $session terminated successfully"
            return 0
        else
            log_warning "Failed to terminate session $session"
            return 1
        fi
    else
        log_warning "Session $session does not exist"
        return 1
    fi
}

# Start complete paint system
start_complete_system() {
    log_info "Starting complete paint system"
    
    dialog --title "Starting Paint System" --infobox "Preparing to start the complete paint system..." 5 60
    sleep 1
    
    # Check existing session and ask to terminate if needed
    if check_tmux_session "$MAIN_SESSION_NAME"; then
        dialog --title "Session Exists" --yesno "A paint system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [[ $? -eq 0 ]]; then
            show_progress_with_steps "Cleaning Up" "Terminating existing sessions..." "Previous sessions closed."
            terminate_session "$MAIN_SESSION_NAME"
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    # Check connectivity to both systems FIRST
    local ef_online=1
    local base_online=1
    
    (
        echo "20"; echo "XXX"; echo "Checking EF device connectivity..."; echo "XXX"
        if ping -c 1 -W 2 "$EF_IP" > /dev/null 2>&1; then
            ef_online=0
        fi
        
        echo "60"; echo "XXX"; echo "Checking Base device connectivity..."; echo "XXX"
        if ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1; then
            base_online=0
        fi
        
        echo "100"; echo "XXX"; echo "Connectivity check completed."; echo "XXX"
        sleep 1
    ) | dialog --title "Checking Connectivity" --gauge "Testing device connections..." 8 60 0
    
    # Re-check outside the progress dialog for decision making
    ping -c 1 -W 2 "$EF_IP" > /dev/null 2>&1
    ef_online=$?
    
    ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1
    base_online=$?
    
    # Show connectivity results and ask user if both are not connected
    if [[ $ef_online -ne 0 ]] && [[ $base_online -ne 0 ]]; then
        # Both devices are offline
        dialog --title "Connection Issues" --yesno "Both devices are not reachable:\n\n• EF Device ($EF_IP): Not Connected ✗\n• Base Device ($BASE_IP): Not Connected ✗\n\nThe paint system may not function properly without device connections.\n\nDo you want to continue anyway?" 12 70
        if [[ $? -ne 0 ]]; then
            dialog --title "Operation Cancelled" --msgbox "Paint system startup cancelled due to connectivity issues." 6 60
            return
        fi
    elif [[ $ef_online -ne 0 ]]; then
        # Only EF is offline
        dialog --title "Connection Issues" --yesno "EF device is not reachable:\n\n• EF Device ($EF_IP): Not Connected ✗\n• Base Device ($BASE_IP): Connected ✓\n\nThe paint system may have limited functionality without EF connection.\n\nDo you want to continue anyway?" 11 70
        if [[ $? -ne 0 ]]; then
            dialog --title "Operation Cancelled" --msgbox "Paint system startup cancelled due to EF connectivity issues." 6 60
            return
        fi
    elif [[ $base_online -ne 0 ]]; then
        # Only Base is offline
        dialog --title "Connection Issues" --yesno "Base device is not reachable:\n\n• EF Device ($EF_IP): Connected ✓\n• Base Device ($BASE_IP): Not Connected ✗\n\nThe paint system may have limited functionality without Base connection.\n\nDo you want to continue anyway?" 11 70
        if [[ $? -ne 0 ]]; then
            dialog --title "Operation Cancelled" --msgbox "Paint system startup cancelled due to Base connectivity issues." 6 60
            return
        fi
    else
        # Both devices are online
        dialog --title "Connectivity Check" --msgbox "Device connectivity verified:\n\n• EF Device ($EF_IP): Connected ✓\n• Base Device ($BASE_IP): Connected ✓\n\nProceeding with paint system startup..." 10 60
    fi
    
    # Start the system with progress indicator
    local steps=(
        "Creating tmux session..."
        "Setting up Paint Tool window..."
        "Setting up Base Robot window..."
        "Setting up Control Center..."
        "Setting up data recording..."
        "Configuring help system..."
        "System started successfully!"
    )
    
    show_progress_with_steps "Starting System" "${steps[@]}" &
    local progress_pid=$!
    
    # Create the actual system
    create_main_tmux_session
    
    # Kill progress dialog
    kill $progress_pid 2>/dev/null
    
    # Show final status with connectivity info
    local status_msg="The paint system has been started successfully!\n\nDevice Status:\n"
    if [[ $ef_online -eq 0 ]]; then
        status_msg="${status_msg}• EF Device: Connected ✓\n"
    else
        status_msg="${status_msg}• EF Device: Not Connected ✗\n"
    fi
    
    if [[ $base_online -eq 0 ]]; then
        status_msg="${status_msg}• Base Device: Connected ✓\n"
    else
        status_msg="${status_msg}• Base Device: Not Connected ✗\n"
    fi
    
    status_msg="${status_msg}\nYou can now:\n• Click 'Attach to System' to view and control it\n• Click 'Main Menu' to return to the menu\n• Use 'tmux attach -t $MAIN_SESSION_NAME' in a terminal"
    
    dialog --title "System Started" --msgbox "$status_msg" 16 70
    
    log_info "Complete paint system started successfully"
}

# Create the main tmux session
create_main_tmux_session() {
    log_info "Creating main tmux session: $MAIN_SESSION_NAME"
    
    # Create the tmux session and enable mouse
    tmux new-session -d -s "$MAIN_SESSION_NAME" -n "🎨 Paint Tool"
    tmux set -g mouse on
    
    # Setup colors for all panes
    setup_colors
    
    # First window - EF system
    setup_ef_window
    
    # Second window - Base system
    setup_base_window
    
    # Third window - Controller with split panes
    setup_controller_window
    
    # Create help file and setup help commands
    create_help_file
    setup_help_commands
    
    # Select first window
    tmux select-window -t "$MAIN_SESSION_NAME:0"
    
    log_info "Main tmux session created successfully"
}

# Setup EF window
setup_ef_window() {
    log_debug "Setting up EF window"
    
    tmux send-keys -t "$MAIN_SESSION_NAME:0" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" 'echo -e "${BLUE}${BOLD}PAINT TOOL CONTROL PANEL${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" 'echo -e "\n${YELLOW}• Connecting to Paint Tool...\n${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" "ssh $EF_SSH_TARGET" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" 'echo -e "\n${GREEN}• Starting Paint Tool systems...${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:0" "./start_ef.bash" C-m
}

# Setup Base window
setup_base_window() {
    log_debug "Setting up Base window"
    
    tmux new-window -t "$MAIN_SESSION_NAME:1" -n "🤖 Base Robot"
    tmux send-keys -t "$MAIN_SESSION_NAME:1" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" 'echo -e "${BLUE}${BOLD}BASE ROBOT CONTROL PANEL${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" 'echo -e "\n${YELLOW}• Connecting to Base Robot...\n${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" "ssh $BASE_SSH_TARGET" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" 'echo -e "\n${GREEN}• Starting Base Robot systems...${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:1" "./start_base.bash" C-m
}

# Setup Controller window with split panes
setup_controller_window() {
    log_debug "Setting up Controller window"
    
    # Third window - Controller with split panes
    tmux new-window -t "$MAIN_SESSION_NAME:2" -n "🎛️ Control Center"
    
    # Main controller pane
    setup_main_controller_pane
    
    # Data recording pane
    setup_data_recording_pane
    
    # Time synchronization pane
    setup_time_sync_pane
    
    # Adjust layout and name panes
    tmux select-layout -t "$MAIN_SESSION_NAME:2" tiled
    tmux select-pane -t "$MAIN_SESSION_NAME:2.0" -T "Paint Controller"
    tmux select-pane -t "$MAIN_SESSION_NAME:2.1" -T "Data Recorder"
    tmux select-pane -t "$MAIN_SESSION_NAME:2.2" -T "Time Monitor"
}

# Setup main controller pane
setup_main_controller_pane() {
    tmux send-keys -t "$MAIN_SESSION_NAME:2" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2" 'echo -e "${BLUE}${BOLD}MAIN PAINT CONTROLLER${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2" 'echo -e "\n${YELLOW}• Starting central control system...\n${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2" "cd $ROS2_WORKSPACE/$PAINT_CONTROLLER_PATH" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2" "python3 paint_controller.py" C-m
}

# Setup data recording pane
setup_data_recording_pane() {
    tmux split-window -v -t "$MAIN_SESSION_NAME:2"
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "${BLUE}${BOLD}DATA RECORDER (AUTO-SAVE)${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n• Recording will automatically save every '$ROS_BAG_INTERVAL' minutes"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "cd $ROS_BAG_PATH" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n${YELLOW}• Starting in 10 seconds...${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "for i in {10..1}; do echo -ne \"Starting in \$i seconds...\r\"; sleep 1; done" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n${GREEN}• Beginning data recording...${RESET}"' C-m
    
    # Setup the recording loop
    setup_recording_loop
}

# Setup recording loop
setup_recording_loop() {
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "while true; do" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "  TIMESTAMP=\$(date +\"%Y%m%d_%H%M%S\")" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" '  echo -e "\n${GREEN}• [Recording \$TIMESTAMP] Started new '$ROS_BAG_INTERVAL'-minute session${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "  timeout ${ROS_BAG_INTERVAL}m ros2 bag record -a -o ${ROS_BAG_PATH}/rosbag2_\$TIMESTAMP" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" '  echo -e "${BLUE}• [Recording \$TIMESTAMP] Saved successfully${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" '  echo -e "${YELLOW}• Preparing next recording in 5 seconds...${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "  sleep 5" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "done" C-m
}

# Setup time synchronization pane
setup_time_sync_pane() {
    tmux split-window -h -t "$MAIN_SESSION_NAME:2.1"
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "${BLUE}${BOLD}TIME SYNCHRONIZATION MONITOR${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "\n• Checking system time synchronization status..."' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "\n${YELLOW}• Note: This may ask for your password${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" "sudo chronyc clients" C-m
}

# Setup help commands in all panes
setup_help_commands() {
    for pane in $(tmux list-panes -a -t "$MAIN_SESSION_NAME" -F '#{session_name}:#{window_index}.#{pane_index}'); do
        tmux send-keys -t "$pane" 'function help() { clear && cat /tmp/paint_system_help.txt; }; alias help=help' C-m
    done
    
    # Set up help key binding
    tmux bind-key -T root -t "$MAIN_SESSION_NAME" ? run-shell "cat /tmp/paint_system_help.txt | less"
}

# Launch EF script directly
launch_ef_script() {
    log_info "Launching EF script directly"
    
    # Check if session already exists
    if check_tmux_session "$EF_SESSION_NAME"; then
        dialog --title "Session Exists" --yesno "An EF system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [[ $? -eq 0 ]]; then
            show_progress_with_steps "Cleaning Up" "Terminating existing EF session..." "Previous session terminated."
            terminate_session "$EF_SESSION_NAME"
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    local steps=(
        "Connecting to EF..."
        "EF is online. Starting script..."
        "Launching start_ef.bash..."
        "EF system started!"
    )
    
    show_progress_with_steps "Starting EF System" "${steps[@]}" &
    local progress_pid=$!
    
    # Check connectivity
    ping -c 1 -W 2 "$EF_IP" > /dev/null 2>&1
    local ef_online=$?
    
    if [[ $ef_online -ne 0 ]]; then
        kill $progress_pid 2>/dev/null
        dialog --title "Warning" --msgbox "EF is not reachable. Continuing anyway..." 6 50
    fi
    
    # Launch the script
    ssh $EF_SSH_TARGET './start_ef.bash' >/dev/null 2>&1 &
    
    kill $progress_pid 2>/dev/null
    dialog --title "EF System Started" --msgbox "The EF system has been started.\n\nNote: This runs independently of the main control panel." 7 60
    
    log_info "EF script launched successfully"
}

# Launch Base script directly
launch_base_script() {
    log_info "Launching Base script directly"
    
    # Check if session already exists
    if check_tmux_session "$BASE_SESSION_NAME"; then
        dialog --title "Session Exists" --yesno "A Base system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [[ $? -eq 0 ]]; then
            show_progress_with_steps "Cleaning Up" "Terminating existing Base session..." "Previous session terminated."
            terminate_session "$BASE_SESSION_NAME"
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    local steps=(
        "Connecting to Base..."
        "Base is online. Starting script..."
        "Launching start_base.bash..."
        "Base system started!"
    )
    
    show_progress_with_steps "Starting Base System" "${steps[@]}" &
    local progress_pid=$!
    
    # Check connectivity
    ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1
    local base_online=$?
    
    if [[ $base_online -ne 0 ]]; then
        kill $progress_pid 2>/dev/null
        dialog --title "Warning" --msgbox "Base is not reachable. Continuing anyway..." 6 50
    fi
    
    # Launch the script
    ssh $BASE_SSH_TARGET './start_base.bash' >/dev/null 2>&1 &
    
    kill $progress_pid 2>/dev/null
    dialog --title "Base System Started" --msgbox "The Base system has been started.\n\nNote: This runs independently of the main control panel." 7 60
    
    log_info "Base script launched successfully"
}

# Attach to running system
attach_to_system() {
    log_info "Attempting to attach to running system"
    
    # Check which sessions are available
    update_system_status
    
    # If no sessions are running, show error
    if [[ $MAIN_RUNNING -eq 0 ]] && [[ $EF_RUNNING -eq 0 ]] && [[ $BASE_RUNNING -eq 0 ]]; then
        dialog --title "Error" --msgbox "No paint system sessions are currently running.\n\nPlease start a system first." 8 50
        return
    fi
    
    # If only one session is running, attach to it directly
    if [[ $MAIN_RUNNING -eq 1 ]] && [[ $EF_RUNNING -eq 0 ]] && [[ $BASE_RUNNING -eq 0 ]]; then
        attach_to_session "$MAIN_SESSION_NAME" "main paint system"
    elif [[ $MAIN_RUNNING -eq 0 ]] && [[ $EF_RUNNING -eq 1 ]] && [[ $BASE_RUNNING -eq 0 ]]; then
        attach_to_session "$EF_SESSION_NAME" "EF system"
    elif [[ $MAIN_RUNNING -eq 0 ]] && [[ $EF_RUNNING -eq 0 ]] && [[ $BASE_RUNNING -eq 1 ]]; then
        attach_to_session "$BASE_SESSION_NAME" "Base system"
    else
        # Multiple sessions running, let user choose
        show_session_selection_menu
    fi
}

# Attach to specific session
attach_to_session() {
    local session="$1"
    local description="$2"
    
    dialog --title "Attaching to System" --infobox "Attaching to the $description...\n\nTo return to this menu, press Ctrl+B then d" 7 50
    sleep 2
    clear
    tmux attach-session -t "$session"
    clear
    
    log_info "Attached to session: $session"
}

# Show session selection menu
show_session_selection_menu() {
    local options=""
    [[ $MAIN_RUNNING -eq 1 ]] && options="$options 1 \"Complete Paint System\" on"
    [[ $EF_RUNNING -eq 1 ]] && options="$options 2 \"EF System Only\" off"
    [[ $BASE_RUNNING -eq 1 ]] && options="$options 3 \"Base System Only\" off"
    
    local session=$(dialog --title "Attach to System" --radiolist "Multiple systems are running.\nSelect which system to attach to:" 12 60 3 $options 3>&1 1>&2 2>&3)
    
    case $session in
        1) attach_to_session "$MAIN_SESSION_NAME" "main paint system" ;;
        2) attach_to_session "$EF_SESSION_NAME" "EF system" ;;
        3) attach_to_session "$BASE_SESSION_NAME" "Base system" ;;
    esac
}

# Stop system with simplified menu
stop_system() {
    log_info "Opening stop system menu"
    
    # Show simplified stop menu with 3 options
    show_simplified_stop_menu
}

# Show simplified stop system menu
show_simplified_stop_menu() {
    local choice=$(dialog --title "Stop System" --menu "Select which system to stop:" 12 60 3 \
        "1" "Stop All (Remote EF + Remote Base + Local)" \
        "2" "Stop EF (Remote EF session only)" \
        "3" "Stop Base (Remote Base session only)" \
        3>&1 1>&2 2>&3)
    
    if [[ $? -ne 0 ]] || [[ -z "$choice" ]]; then
        return
    fi
    
    # Confirm the action
    local confirm_message=""
    case $choice in
        1) confirm_message="This will stop:\n• Remote EF tmux session '$REMOTE_EF_SESSION_NAME'\n• Remote Base tmux session '$REMOTE_BASE_SESSION_NAME'\n• Local tmux session '$MAIN_SESSION_NAME' (if exists)\n\nProceed?" ;;
        2) confirm_message="This will stop:\n• Remote EF tmux session '$REMOTE_EF_SESSION_NAME' on EF device\n\nProceed?" ;;
        3) confirm_message="This will stop:\n• Remote Base tmux session '$REMOTE_BASE_SESSION_NAME' on Base device\n\nProceed?" ;;
    esac
    
    dialog --title "Confirm Stop" --yesno "$confirm_message" 12 70
    if [[ $? -ne 0 ]]; then
        return
    fi
    
    # Execute the stop operation
    case $choice in
        1) stop_all_systems ;;
        2) stop_ef_only ;;
        3) stop_base_only ;;
    esac
}

# Stop all systems (EF + Base + Local)
stop_all_systems() {
    log_info "Stopping all systems (EF + Base + Local)"
    
    local steps=(
        "Checking remote EF session..."
        "Stopping remote EF system..."
        "Checking remote Base session..."
        "Stopping remote Base system..."
        "Checking local paint system..."
        "Stopping local paint system..."
        "All systems stopped successfully!"
    )
    
    show_progress_with_steps "Stopping All Systems" "${steps[@]}" &
    local progress_pid=$!
    
    # Stop remote EF system
    stop_remote_ef_system
    sleep 1
    
    # Stop remote Base system
    stop_remote_base_system
    sleep 1
    
    # Stop local main system if it exists
    if check_tmux_session "$MAIN_SESSION_NAME"; then
        log_info "Found local session '$MAIN_SESSION_NAME', terminating..."
        terminate_session "$MAIN_SESSION_NAME"
    else
        log_info "Local session '$MAIN_SESSION_NAME' not found"
    fi
    
    kill $progress_pid 2>/dev/null
    
    dialog --title "All Systems Stopped" --msgbox "All systems have been stopped:\n\n✓ Remote EF system\n✓ Remote Base system\n✓ Local paint system (if running)\n\nAll tmux sessions have been terminated." 12 60
    
    log_info "All systems stopped successfully"
}

# Stop EF only
stop_ef_only() {
    log_info "Stopping EF system only"
    
    local steps=(
        "Connecting to EF device..."
        "Checking for EF tmux session..."
        "Stopping EF system..."
        "EF system stopped successfully!"
    )
    
    show_progress_with_steps "Stopping EF System" "${steps[@]}" &
    local progress_pid=$!
    
    # Stop remote EF system
    stop_remote_ef_system
    
    kill $progress_pid 2>/dev/null
    
    dialog --title "EF System Stopped" --msgbox "EF system has been stopped:\n\n✓ Remote EF tmux session '$REMOTE_EF_SESSION_NAME' terminated\n\nThe EF device is now free of running tmux sessions." 10 60
    
    log_info "EF system stopped successfully"
}

# Stop Base only
stop_base_only() {
    log_info "Stopping $BASE_DEVICE_NAME system only"
    
    # Ask for confirmation before SSH
    dialog --title "Confirm SSH Connection" --yesno "This will connect to the $BASE_DEVICE_NAME device via SSH to stop tmux sessions.\n\nDevice: $BASE_DEVICE_NAME\nSSH Target: $BASE_SSH_TARGET\nSession to stop: '$REMOTE_BASE_SESSION_NAME'\n\nProceed with SSH connection?" 12 70
    if [[ $? -ne 0 ]]; then
        dialog --title "Operation Cancelled" --msgbox "$BASE_DEVICE_NAME stop operation cancelled by user." 5 50
        return 1
    fi
    
    # Do ALL checks inside one progress dialog
    (
        echo "10"; echo "XXX"; echo "Checking $BASE_DEVICE_NAME device connectivity..."; echo "XXX"
        
        # Check if Base is reachable
        if ! ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1; then
            echo "100"; echo "XXX"; echo "$BASE_DEVICE_NAME device is not reachable!"; echo "XXX"
            sleep 2
            exit 1  # Signal failure
        fi
        
        echo "30"; echo "XXX"; echo "$BASE_DEVICE_NAME device is reachable. Connecting via SSH..."; echo "XXX"
        
        # Check if tmux session exists
        if ssh -o BatchMode=yes -o ConnectTimeout=10 "$BASE_SSH_TARGET" "tmux has-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null" 2>/dev/null; then
            echo "50"; echo "XXX"; echo "Found tmux session '$REMOTE_BASE_SESSION_NAME'. Stopping processes..."; echo "XXX"
            
            # Stop processes gracefully
            ssh -o BatchMode=yes -o ConnectTimeout=10 "$BASE_SSH_TARGET" "
                tmux list-panes -a -t $REMOTE_BASE_SESSION_NAME -F '#{session_name}:#{window_index}.#{pane_index}' 2>/dev/null | while read pane; do
                    tmux send-keys -t \$pane C-c 2>/dev/null || true
                    sleep 0.5
                done
                sleep 2
            " 2>/dev/null
            
            echo "80"; echo "XXX"; echo "Killing tmux session..."; echo "XXX"
            
            # Kill the session
            ssh -o BatchMode=yes -o ConnectTimeout=10 "$BASE_SSH_TARGET" "
                tmux kill-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null || true
            " 2>/dev/null
            
            echo "100"; echo "XXX"; echo "$BASE_DEVICE_NAME tmux session terminated successfully!"; echo "XXX"
            exit 0  # Signal success
        else
            echo "100"; echo "XXX"; echo "No tmux session '$REMOTE_BASE_SESSION_NAME' found."; echo "XXX"
            exit 2  # Signal session not found
        fi
    ) | dialog --title "Stopping $BASE_DEVICE_NAME System" --gauge "Checking connectivity..." 8 60 0
    
    # Check the exit code from the subshell
    local result=$?
    
    case $result in
        0)  # Success
            dialog --title "$BASE_DEVICE_NAME System Stopped" --msgbox "$BASE_DEVICE_NAME system has been stopped:\n\n✓ Remote tmux session '$REMOTE_BASE_SESSION_NAME' terminated\n\nThe $BASE_DEVICE_NAME device is now free of running tmux sessions." 10 60
            log_info "$BASE_DEVICE_NAME system stopped successfully"
            ;;
        1)  # Connection failed
            dialog --title "Connection Error" --msgbox "$BASE_DEVICE_NAME device ($BASE_IP) is not reachable.\n\nPlease check:\n• Network connectivity\n• Device is powered on\n• IP address is correct" 10 50
            log_warning "$BASE_DEVICE_NAME device is not reachable"
            ;;
        2)  # Session not found
            dialog --title "Session Not Found" --msgbox "$BASE_DEVICE_NAME tmux session '$REMOTE_BASE_SESSION_NAME' not found.\n\nPossible reasons:\n• Session already stopped\n• Session never started" 9 60
            log_info "Remote $BASE_DEVICE_NAME session not found"
            ;;
    esac
}

# Stop remote EF system
stop_remote_ef_system() {
    log_info "Stopping remote EF system"
    
    # Ask for confirmation before SSH
    dialog --title "Confirm SSH Connection" --yesno "This will connect to the EF device via SSH to stop tmux sessions.\n\nEF Device: $EF_SSH_TARGET\nSession to stop: '$REMOTE_EF_SESSION_NAME'\n\nProceed with SSH connection?" 10 60
    if [[ $? -ne 0 ]]; then
        dialog --title "Operation Cancelled" --msgbox "EF stop operation cancelled by user." 5 50
        return 1
    fi
    
    # Check if EF is reachable
    if ! ping -c 1 -W 2 "$EF_IP" > /dev/null 2>&1; then
        log_warning "EF device ($EF_IP) is not reachable"
        dialog --title "Connection Error" --msgbox "EF device ($EF_IP) is not reachable.\n\nPlease check network connectivity." 7 50
        return 1
    fi
    
    # Connect to EF and kill the tmux session
    if ssh -o BatchMode=yes -o ConnectTimeout=10 "$EF_SSH_TARGET" "tmux has-session -t $REMOTE_EF_SESSION_NAME 2>/dev/null" 2>/dev/null; then
        log_debug "Found remote EF session '$REMOTE_EF_SESSION_NAME', terminating..."
        
        # First try to gracefully stop processes
        ssh -o BatchMode=yes -o ConnectTimeout=10 "$EF_SSH_TARGET" "
            echo 'Stopping processes in tmux session $REMOTE_EF_SESSION_NAME...'
            tmux list-panes -a -t $REMOTE_EF_SESSION_NAME -F '#{session_name}:#{window_index}.#{pane_index}' 2>/dev/null | while read pane; do
                echo \"Sending Ctrl+C to pane: \$pane\"
                tmux send-keys -t \$pane C-c 2>/dev/null || true
                sleep 0.5
            done
            sleep 2
            echo 'Killing tmux session $REMOTE_EF_SESSION_NAME...'
            tmux kill-session -t $REMOTE_EF_SESSION_NAME 2>/dev/null || true
            echo 'EF tmux session terminated.'
        " 2>/dev/null
        
        log_info "Remote EF system stopped successfully"
    else
        log_info "Remote EF session '$REMOTE_EF_SESSION_NAME' not found (may already be stopped)"
        dialog --title "Session Not Found" --msgbox "EF tmux session '$REMOTE_EF_SESSION_NAME' not found.\n\nIt may already be stopped or never started." 7 60
    fi
}

# Stop remote Base system (used by stop_all_systems)
stop_remote_base_system() {
    log_info "Stopping remote Base system (internal call)"
    
    # Check if Base is reachable
    if ! ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1; then
        log_warning "Base device ($BASE_IP) is not reachable"
        return 1
    fi
    
    # Connect to Base and kill the tmux session
    if ssh -o BatchMode=yes -o ConnectTimeout=10 "$BASE_SSH_TARGET" "tmux has-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null" 2>/dev/null; then
        log_debug "Found remote Base session '$REMOTE_BASE_SESSION_NAME', terminating..."
        
        # First try to gracefully stop processes
        ssh -o BatchMode=yes -o ConnectTimeout=10 "$BASE_SSH_TARGET" "
            tmux list-panes -a -t $REMOTE_BASE_SESSION_NAME -F '#{session_name}:#{window_index}.#{pane_index}' 2>/dev/null | while read pane; do
                tmux send-keys -t \$pane C-c 2>/dev/null || true
                sleep 0.5
            done
            sleep 2
            tmux kill-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null || true
        " 2>/dev/null
        
        log_info "Remote Base system stopped successfully"
    else
        log_info "Remote Base session '$REMOTE_BASE_SESSION_NAME' not found (may already be stopped)"
    fi
}


# Check remote tmux sessions
check_remote_sessions() {
    log_debug "Checking remote tmux sessions"
    
    # Check EF remote session
    EF_REMOTE_RUNNING=0
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$EF_SSH_TARGET" "tmux has-session -t $REMOTE_EF_SESSION_NAME 2>/dev/null" 2>/dev/null; then
        EF_REMOTE_RUNNING=1
        log_debug "EF remote session '$REMOTE_EF_SESSION_NAME' is running"
    fi
    
    # Check Base remote session
    BASE_REMOTE_RUNNING=0
    if ssh -o BatchMode=yes -o ConnectTimeout=5 "$BASE_SSH_TARGET" "tmux has-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null" 2>/dev/null; then
        BASE_REMOTE_RUNNING=1
        log_debug "Base remote session '$REMOTE_BASE_SESSION_NAME' is running"
    fi
}

# Check all remote sessions status
check_all_remote_sessions() {
    local ef_status="Unknown"
    local base_status="Unknown"
    local ef_details=""
    local base_details=""
    
    # Check EF
    if ping -c 1 -W 2 "$EF_IP" > /dev/null 2>&1; then
        if ssh -o BatchMode=yes -o ConnectTimeout=5 "$EF_SSH_TARGET" "tmux has-session -t $REMOTE_EF_SESSION_NAME 2>/dev/null" 2>/dev/null; then
            ef_status="Running ✓"
            ef_details="Session '$REMOTE_EF_SESSION_NAME' is active"
        else
            ef_status="Not Running"
            ef_details="No tmux session found"
        fi
    else
        ef_status="Not Reachable ✗"
        ef_details="Device is offline or unreachable"
    fi
    
    # Check Base
    if ping -c 1 -W 2 "$BASE_IP" > /dev/null 2>&1; then
        if ssh -o BatchMode=yes -o ConnectTimeout=5 "$BASE_SSH_TARGET" "tmux has-session -t $REMOTE_BASE_SESSION_NAME 2>/dev/null" 2>/dev/null; then
            base_status="Running ✓"
            base_details="Session '$REMOTE_BASE_SESSION_NAME' is active"
        else
            base_status="Not Running"
            base_details="No tmux session found"
        fi
    else
        base_status="Not Reachable ✗"
        base_details="Device is offline or unreachable"
    fi
    
    # Check local session
    local local_status="Not Running"
    if check_tmux_session "$MAIN_SESSION_NAME"; then
        local_status="Running ✓"
    fi
    
    dialog --title "Remote Sessions Status" --msgbox "System Status Overview:\n\nEF Device ($EF_IP):\n• Status: $ef_status\n• Details: $ef_details\n\nBase Device ($BASE_IP):\n• Status: $base_status\n• Details: $base_details\n\nLocal Paint System:\n• Session '$MAIN_SESSION_NAME': $local_status\n\nUse 'Stop System' menu to terminate sessions." 18 70
}