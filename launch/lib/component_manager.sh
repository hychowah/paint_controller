#!/bin/bash

# Component management functions

# Manage EF components
manage_ef_components() {
    if ! check_tmux_session "$MAIN_SESSION_NAME"; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    log_info "Managing EF components"
    show_ef_component_menu
}

# Manage Base components
manage_base_components() {
    if ! check_tmux_session "$MAIN_SESSION_NAME"; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    log_info "Managing Base components"
    show_base_component_menu
}

# Manage Controller components
manage_controller_components() {
    if ! check_tmux_session "$MAIN_SESSION_NAME"; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    log_info "Managing Controller components"
    show_controller_component_menu
}

# Restart a specific component
restart_component() {
    local system="$1"     # "ef" or "base"
    local component="$2"  # component name
    
    if ! check_tmux_session "$MAIN_SESSION_NAME"; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return 1
    fi
    
    log_info "Restarting $system component: $component"
    
    # Get component details
    local command=""
    local display_name=""
    local window=""
    
    if [[ "$system" == "ef" ]]; then
        command="${EF_RESTART_COMMANDS[$component]}"
        display_name="${EF_DISPLAY_NAMES[$component]}"
        window="0"
    elif [[ "$system" == "base" ]]; then
        command="${BASE_RESTART_COMMANDS[$component]}"
        display_name="${BASE_DISPLAY_NAMES[$component]}"
        window="1"
    else
        dialog --title "Error" --msgbox "Invalid system: $system" 5 40
        return 1
    fi
    
    if [[ -z "$command" ]]; then
        dialog --title "Error" --msgbox "Component '$component' not found." 5 40
        return 1
    fi
    
    # Restart the component with progress
    local steps=(
        "Stopping $display_name..."
        "Preparing to restart $display_name..."
        "Restarting $display_name..."
        "$display_name restarted successfully!"
    )
    
    show_progress_with_steps "Restarting Component" "${steps[@]}" &
    local progress_pid=$!
    
    # Perform the restart
    perform_component_restart "$window" "$component" "$command" "$display_name"
    
    kill $progress_pid 2>/dev/null
    dialog --title "Component Restarted" --msgbox "$display_name has been restarted successfully." 6 50
    
    log_info "Component $component restarted successfully"
    return 0
}

# Perform the actual component restart
perform_component_restart() {
    local window="$1"
    local component="$2"
    local command="$3"
    local display_name="$4"
    
    # Send Ctrl+C to stop the component
    tmux send-keys -t "$MAIN_SESSION_NAME:$window" C-c
    sleep "$COMPONENT_RESTART_DELAY"
    
    # Clear screen and set up colors
    tmux send-keys -t "$MAIN_SESSION_NAME:$window" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:$window" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    
    # Show restart message
    tmux send-keys -t "$MAIN_SESSION_NAME:$window" 'echo -e "${YELLOW}Restarting component: '"$component"'${RESET}"' C-m
    
    # Execute the appropriate command
    if [[ $command == *.bash ]]; then
        # Execute bash script
        tmux send-keys -t "$MAIN_SESSION_NAME:$window" "./$command" C-m
    elif [[ $command == *launch.py ]]; then
        # Launch ROS2 node
        tmux send-keys -t "$MAIN_SESSION_NAME:$window" "ros2 launch $command" C-m
    else
        # Execute Python script or other command
        tmux send-keys -t "$MAIN_SESSION_NAME:$window" "$command" C-m
    fi
}

show_controller_component_menu() {
    

    while true; do
        local choice=$(dialog --title "Manage Controller Components" \
            --menu "Select a component to restart:" 10 60 4 \
            "controller" "Main Paint Controller" \
            "recorder" "Data Recorder" \
            "chrono" "Time Synchronization" \
            "back" "Back to Component Menu" \
            3>&1 1>&2 2>&3)

        dialog --title "Debug" --msgbox "User selected choice: $choice" 6 50
        restart_controller_component "$choice"
        
        if [[ $choice == "back" ]] || [[ $? -ne 0 ]]; then
            break
        fi
        
    done
}

# Restart controller components
restart_controller_component() {
    local component="$1"
    
    dialog --title "Debug" --msgbox "Function called with component: $component" 6 50 
    
    case $component in
        controller)
            restart_paint_controller
            ;;
        recorder)
            restart_data_recorder
            ;;
        chrono)
            restart_time_sync
            ;;
        *)
            dialog --title "Error" --msgbox "Unknown controller component: $component" 5 50
            return 1
            ;;
    esac
}

# Restart paint controller
restart_paint_controller() {
    local steps=(
        "Stopping Paint Controller..."
        "Preparing to restart Paint Controller..."
        "Restarting Paint Controller..."
        "Paint Controller restarted successfully!"
    )
    
    show_progress_with_steps "Restarting Controller" "${steps[@]}" &
    local progress_pid=$!
    
    # Stop current controller
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" C-c
    sleep "$COMPONENT_RESTART_DELAY"
    
    # Clear and restart
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" 'echo -e "${BLUE}${BOLD}MAIN PAINT CONTROLLER${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" 'echo -e "\n${YELLOW}• Restarting central control system...\n${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" "cd $ROS2_WORKSPACE/$PAINT_CONTROLLER_PATH" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.0" "python3 paint_controller.py" C-m
    
    kill $progress_pid 2>/dev/null
    dialog --title "Component Restarted" --msgbox "Paint Controller has been restarted." 6 50
    
    log_info "Paint Controller restarted successfully"
}

# Restart data recorder
restart_data_recorder() {
    dialog --title "Confirm" --yesno "Restarting the Data Recorder will create a new recording session.\n\nProceed?" 8 60
    if [[ $? -ne 0 ]]; then
        return
    fi
    
    local steps=(
        "Stopping Data Recorder..."
        "Preparing new recording session..."
        "Starting Data Recorder..."
        "Data Recorder restarted successfully!"
    )
    
    show_progress_with_steps "Restarting Data Recorder" "${steps[@]}" &
    local progress_pid=$!
    
    # Stop current recorder
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" C-c
    sleep "$COMPONENT_RESTART_DELAY"
    
    # Clear and restart
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "${BLUE}${BOLD}DATA RECORDER (AUTO-SAVE)${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n• Recording will automatically save every '"$ROS_BAG_INTERVAL"' minutes"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "cd $ROS_BAG_PATH" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n${YELLOW}• Starting in 5 seconds...${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" "for i in {5..1}; do echo -ne \"Starting in \$i seconds...\r\"; sleep 1; done" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.1" 'echo -e "\n${GREEN}• Beginning data recording...${RESET}"' C-m
    
    # Setup recording loop
    setup_recording_loop
    
    kill $progress_pid 2>/dev/null
    dialog --title "Component Restarted" --msgbox "Data Recorder has been restarted." 6 50
    
    log_info "Data Recorder restarted successfully"
}

# Restart time synchronization
restart_time_sync() {
    local steps=(
        "Stopping Time Sync..."
        "Preparing to restart Time Sync..."
        "Restarting Time Sync..."
        "Time Sync restarted successfully!"
    )
    
    show_progress_with_steps "Restarting Time Sync" "${steps[@]}" &
    local progress_pid=$!
    
    # Stop current time sync
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" C-c
    sleep "$COMPONENT_RESTART_DELAY"
    
    # Clear and restart
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" "clear" C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "${BLUE}${BOLD}TIME SYNCHRONIZATION MONITOR${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "\n• Checking system time synchronization status..."' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" 'echo -e "\n${YELLOW}• Note: This may ask for your password${RESET}"' C-m
    tmux send-keys -t "$MAIN_SESSION_NAME:2.2" "sudo chronyc clients" C-m
    
    kill $progress_pid 2>/dev/null
    dialog --title "Component Restarted" --msgbox "Time Synchronization has been restarted." 6 50
    
    log_info "Time Synchronization restarted successfully"
}

# Get component status
get_component_status() {
    local system="$1"
    local component="$2"
    
    # This function would check if a specific component is running
    # For now, we'll return a generic status based on session existence
    if check_tmux_session "$MAIN_SESSION_NAME"; then
        echo "Running"
    else
        echo "Stopped"
    fi
}

# List all components
list_components() {
    local system="$1"
    
    if [[ "$system" == "ef" ]]; then
        for component in "${!EF_DISPLAY_NAMES[@]}"; do
            local status=$(get_component_status "ef" "$component")
            echo "$component: ${EF_DISPLAY_NAMES[$component]} - $status"
        done
    elif [[ "$system" == "base" ]]; then
        for component in "${!BASE_DISPLAY_NAMES[@]}"; do
            local status=$(get_component_status "base" "$component")
            echo "$component: ${BASE_DISPLAY_NAMES[$component]} - $status"
        done
    fi
}

# Validate component exists
validate_component() {
    local system="$1"
    local component="$2"
    
    if [[ "$system" == "ef" ]] && [[ -n "${EF_RESTART_COMMANDS[$component]}" ]]; then
        return 0
    elif [[ "$system" == "base" ]] && [[ -n "${BASE_RESTART_COMMANDS[$component]}" ]]; then
        return 0
    else
        return 1
    fi
}

# Batch restart components
batch_restart_components() {
    local system="$1"
    shift
    local components=("$@")
    
    if [[ ${#components[@]} -eq 0 ]]; then
        dialog --title "Error" --msgbox "No components specified for batch restart." 5 50
        return 1
    fi
    
    # Confirm batch restart
    local component_list=""
    for comp in "${components[@]}"; do
        if [[ "$system" == "ef" ]]; then
            component_list="$component_list\n• ${EF_DISPLAY_NAMES[$comp]}"
        else
            component_list="$component_list\n• ${BASE_DISPLAY_NAMES[$comp]}"
        fi
    done
    
    dialog --title "Confirm Batch Restart" --yesno "Restart the following components?$component_list" 12 60
    if [[ $? -ne 0 ]]; then
        return
    fi
    
    log_info "Starting batch restart of $system components: ${components[*]}"
    
    # Restart each component
    for component in "${components[@]}"; do
        if validate_component "$system" "$component"; then
            restart_component "$system" "$component"
            sleep 1  # Brief pause between restarts
        else
            log_warning "Invalid component for batch restart: $component"
        fi
    done
    
    dialog --title "Batch Restart Complete" --msgbox "All specified components have been restarted." 6 50
    log_info "Batch restart completed for $system components"
}