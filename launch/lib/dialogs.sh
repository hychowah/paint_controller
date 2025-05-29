#!/bin/bash

# Dialog functions for user interface

# Global variables for menu choices
MENU_CHOICE=""

show_welcome() {
    dialog --title "Welcome" --msgbox "C3SPRAY PAINT SYSTEM CONTROL CENTER\n\nWelcome to the paint system management interface." 10 60
}

show_main_menu() {
    # Read current connectivity status
    read_connectivity_status
    
    MENU_CHOICE=$(dialog --clear --title "C3SPRAY PAINT SYSTEM CONTROL CENTER" \
        --menu "\nSystem Status:\n• Complete System: $MAIN_STATUS\n• EF System: $EF_STATUS\n• Base System: $BASE_STATUS\n\nDevice Connectivity (Live - Auto Updates):\n• $EF_DEVICE_NAME ($EF_IP): $EF_CONNECTIVITY_STATUS\n• $BASE_DEVICE_NAME ($BASE_IP): $BASE_CONNECTIVITY_STATUS\n• Last Update: $LAST_UPDATE\n\nSelect an option:" 22 75 10 \
        "1" "Start Complete System" \
        "2" "Launch Subsystem" \
        "3" "Attach to Running System" \
        "4" "Manage System Components" \
        "5" "Stop System" \
        "6" "Check System Status" \
        "7" "Check Remote Sessions" \
        "8" "Settings" \
        "9" "Help" \
        "10" "Exit" \
        3>&1 1>&2 2>&3)
    
    # If dialog timed out (exit code 1), clear choice to refresh menu
    if [[ $? -eq 1 ]]; then
        MENU_CHOICE=""
    fi
}
show_subsystem_menu() {
    while true; do
        local choice=$(dialog --title "Launch Subsystem" \
            --menu "Select a subsystem to launch directly:" 11 60 3 \
            "1" "Launch EF System Only" \
            "2" "Launch Base System Only" \
            "3" "Back to Main Menu" \
            3>&1 1>&2 2>&3)
        
        case $choice in
            1) launch_ef_script ;;
            2) launch_base_script ;;
            3|"") break ;;
        esac
    done
}

show_component_menu() {
    while true; do
        local choice=$(dialog --title "Component Management" \
            --menu "Select a system to manage:" 12 60 4 \
            "1" "EF Components" \
            "2" "Base Robot Components" \
            "3" "Controller Components" \
            "4" "Back to Main Menu" \
            3>&1 1>&2 2>&3)
        
        case $choice in
            1) manage_ef_components ;;
            2) manage_base_components ;;
            3) manage_controller_components ;;
            4|"") break ;;
        esac
    done
}

show_ef_component_menu() {
    while true; do
        local choice=$(dialog --title "Manage Paint Tool Components" \
            --menu "Select a component to restart:" 12 60 5 \
            "teensy" "Teensy Controller" \
            "lidar" "Lidar Sensor" \
            "camera" "Camera System" \
            "sync" "Robot Action Synchronizer" \
            "back" "Back to Component Menu" \
            3>&1 1>&2 2>&3)
        
        if [[ $choice == "back" ]] || [[ $? -ne 0 ]]; then
            break
        fi
        
        restart_component "ef" "$choice"
    done
}

show_base_component_menu() {
    while true; do
        local choice=$(dialog --title "Manage Base Robot Components" \
            --menu "Select a component to restart:" 12 60 5 \
            "wheel" "Wheel Control System" \
            "winch" "Winch Control System" \
            "camera" "Camera System" \
            "sync" "Robot Action Synchronizer" \
            "back" "Back to Component Menu" \
            3>&1 1>&2 2>&3)
        
        if [[ $choice == "back" ]] || [[ $? -ne 0 ]]; then
            break
        fi
        
        restart_component "base" "$choice"
    done
}


change_ros_bag_interval() {
    local new_interval
    new_interval=$(dialog --title "ROS Bag Interval" --inputbox "Enter new interval in minutes:" 8 50 "$ROS_BAG_INTERVAL" 3>&1 1>&2 2>&3)
    
    if [[ $? -eq 0 ]] && validate_number "$new_interval"; then
        update_config "ROS_BAG_INTERVAL" "$new_interval"
        dialog --title "Settings Updated" --msgbox "ROS Bag interval updated to $new_interval minutes.\n\nNote: This will apply to new recording sessions." 8 60
    elif [[ $? -eq 0 ]]; then
        dialog --title "Invalid Input" --msgbox "Please enter a valid number." 5 40
    fi
}

change_ros_bag_path() {
    local new_path
    new_path=$(dialog --title "ROS Bag Path" --inputbox "Enter new path for ROS Bag files:" 8 60 "$ROS_BAG_PATH" 3>&1 1>&2 2>&3)
    
    if [[ $? -eq 0 ]] && [[ -n "$new_path" ]]; then
        if validate_path "$new_path"; then
            update_config "ROS_BAG_PATH" "$new_path"
            dialog --title "Settings Updated" --msgbox "ROS Bag path updated to $new_path.\n\nNote: This will apply to new recording sessions." 8 60
        else
            dialog --title "Invalid Path" --msgbox "The specified path does not exist." 6 40
        fi
    fi
}

change_log_level() {
    local choice
    choice=$(dialog --title "Log Level" --radiolist "Select log level:" 10 50 3 \
        "INFO" "Information messages" on \
        "DEBUG" "Debug messages" off \
        "ERROR" "Error messages only" off \
        3>&1 1>&2 2>&3)
    
    if [[ $? -eq 0 ]] && [[ -n "$choice" ]]; then
        update_config "LOG_LEVEL" "$choice"
        dialog --title "Settings Updated" --msgbox "Log level updated to $choice." 6 40
    fi
}

show_simplified_stop_menu() {
    local choice=$(dialog --title "Stop System" --menu "Select which system to stop:" 12 60 3 \
        "1" "Stop All (Remote $EF_DEVICE_NAME + Remote $BASE_DEVICE_NAME + Local)" \
        "2" "Stop $EF_DEVICE_NAME (Remote session only)" \
        "3" "Stop $BASE_DEVICE_NAME (Remote session only)" \
        3>&1 1>&2 2>&3)
    
    if [[ $? -ne 0 ]] || [[ -z "$choice" ]]; then
        return
    fi
    
    # Confirm the action
    local confirm_message=""
    case $choice in
        1) confirm_message="This will stop:\n• Remote $EF_DEVICE_NAME tmux session '$REMOTE_EF_SESSION_NAME'\n• Remote $BASE_DEVICE_NAME tmux session '$REMOTE_BASE_SESSION_NAME'\n• Local tmux session '$MAIN_SESSION_NAME' (if exists)\n\nProceed?" ;;
        2) confirm_message="This will stop:\n• Remote $EF_DEVICE_NAME tmux session '$REMOTE_EF_SESSION_NAME' on $EF_SSH_TARGET\n\nProceed?" ;;
        3) confirm_message="This will stop:\n• Remote $BASE_DEVICE_NAME tmux session '$REMOTE_BASE_SESSION_NAME' on $BASE_SSH_TARGET\n\nProceed?" ;;
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

show_settings_menu() {
    while true; do
        local choice=$(dialog --title "Settings" --menu "Configure system settings:" 15 70 6 \
            "1" "Change ROS Bag Interval (current: ${ROS_BAG_INTERVAL}m)" \
            "2" "Change ROS Bag Path (current: $ROS_BAG_PATH)" \
            "3" "Change Log Level (current: $LOG_LEVEL)" \
            "4" "Configure EF Device (current: $EF_SSH_TARGET)" \
            "5" "Configure Base Device (current: $BASE_SSH_TARGET)" \
            "6" "Back to Main Menu" \
            3>&1 1>&2 2>&3)
        
        case $choice in
            1) change_ros_bag_interval ;;
            2) change_ros_bag_path ;;
            3) change_log_level ;;
            4) configure_ef_device ;;
            5) configure_base_device ;;
            6|"") break ;;
        esac
    done
}

configure_ef_device() {
    local new_target
    new_target=$(dialog --title "Configure EF Device" --inputbox "Enter EF SSH target (format: username@ip):" 8 60 "$EF_SSH_TARGET" 3>&1 1>&2 2>&3)
    
    if [[ $? -eq 0 ]] && [[ -n "$new_target" ]]; then
        if [[ $new_target =~ .+@.+ ]]; then
            update_config "EF_SSH_TARGET" "$new_target"
            # Extract IP from SSH target for ping tests
            local new_ip=$(echo "$new_target" | cut -d'@' -f2)
            update_config "EF_IP" "$new_ip"
            dialog --title "Settings Updated" --msgbox "EF device configuration updated to: $new_target" 6 60
        else
            dialog --title "Invalid Format" --msgbox "Please use format: username@ip\nExample: ef@192.168.1.100" 7 50
        fi
    fi
}

configure_base_device() {
    local new_target
    new_target=$(dialog --title "Configure Base Device" --inputbox "Enter Base SSH target (format: username@ip):" 8 60 "$BASE_SSH_TARGET" 3>&1 1>&2 2>&3)
    
    if [[ $? -eq 0 ]] && [[ -n "$new_target" ]]; then
        if [[ $new_target =~ .+@.+ ]]; then
            update_config "BASE_SSH_TARGET" "$new_target"
            # Extract IP from SSH target for ping tests
            local new_ip=$(echo "$new_target" | cut -d'@' -f2)
            update_config "BASE_IP" "$new_ip"
            dialog --title "Settings Updated" --msgbox "Base device configuration updated to: $new_target" 6 60
        else
            dialog --title "Invalid Format" --msgbox "Please use format: username@ip\nExample: user@192.168.1.200" 7 50
        fi
    fi
}

show_system_status() {
    # Get system information
    local disk_space=$(get_disk_usage)
    local disk_avail=$(get_available_space)
    local memory_usage=$(get_memory_usage)
    
    # Check connectivity
    check_device "$EF_IP" "EF" >/dev/null 2>&1
    local ef_online=$?
    check_device "$BASE_IP" "Base Robot" >/dev/null 2>&1
    local base_online=$?
    
    # Prepare status messages
    local ef_status="Not Connected ✗"
    [[ $ef_online -eq 0 ]] && ef_status="Connected ✓"
    
    local base_status="Not Connected ✗"
    [[ $base_online -eq 0 ]] && base_status="Connected ✓"
    
    local system_status="Not Running ✗"
    [[ $MAIN_RUNNING -eq 1 ]] && system_status="Running ✓"
    
    # Get component status
    local ef_components_status=""
    local base_components_status=""
    local controller_status=""
    
    if [[ $MAIN_RUNNING -eq 1 ]]; then
        ef_components_status="\n• Paint Tool: Running"
        base_components_status="\n• Base Robot: Running"
        controller_status="\n• Controller: Running"
        
        if tmux list-panes -t "$MAIN_SESSION_NAME:2.1" &>/dev/null; then
            controller_status="$controller_status\n• Data Recording: Active"
        else
            controller_status="$controller_status\n• Data Recording: Not active"
        fi
    else
        [[ $EF_RUNNING -eq 1 ]] && ef_components_status="\n• Paint Tool: Running Standalone"
        [[ $BASE_RUNNING -eq 1 ]] && base_components_status="\n• Base Robot: Running Standalone"
    fi
    
    dialog --title "System Status" --msgbox "\
    
DEVICE CONNECTIVITY:
- EF: $ef_status
- Base Robot: $base_status

SYSTEM STATUS:
- Main Paint System: $system_status$ef_components_status$base_components_status$controller_status

RESOURCES:
- Disk Space Used: $disk_space
- Available Space: $disk_avail
- Memory Usage: $memory_usage

Last Updated: $(get_human_timestamp)

Press OK to return to the main menu." 20 70
}

show_help() {
    dialog --title "Paint System Help" --msgbox "\
C3SPRAY PAINT SYSTEM CONTROL CENTER

This application helps you manage the C3Spray Paint System.

MAIN FUNCTIONS:

• Start System - Starts the complete paint system including:
  - Paint Tool (End Effector)
  - Base Robot
  - Main Controller
  - Data Recording (auto-saves every $ROS_BAG_INTERVAL minutes)
  - Time Synchronization Monitor

• Launch Subsystem - Launch either EF or Base system independently

• Attach to System - View and control running systems

• Manage Components - Restart individual system components:
  - Paint Tool Components (Teensy, Lidar, Camera, Sync)
  - Base Robot Components (Wheel, Winch, Camera, Sync)
  - Controller Components (Main Controller, Data Recorder, Time Sync)

• Stop System - Safely shut down all components

• Check Status - Verify connectivity and system status

• Settings - Configure system parameters

WHEN VIEWING THE SYSTEM:
- Use Ctrl+B then d to detach and return to this menu
- Use Ctrl+B then 0-2 to switch between main screens
- Click directly on panes to select them
- Use mouse wheel to scroll text in panes

LOG FILES:
- System logs are stored in: $LOG_PATH
- ROS bag files are stored in: $ROS_BAG_PATH

Press OK to return to the main menu." 26 76
}

confirm_exit() {
    dialog --title "Confirm Exit" --yesno "Are you sure you want to exit?\n\nNote: Any running systems will continue to run." 8 50
    return $?
}

show_progress_with_steps() {
    local title="$1"
    local steps=("${@:2}")
    local total_steps=${#steps[@]}
    local current_step=0
    
    for step in "${steps[@]}"; do
        current_step=$((current_step + 1))
        local percentage=$((current_step * 100 / total_steps))
        
        echo $percentage
        echo "XXX"
        echo "$step"
        echo "XXX"
        sleep 1
    done | dialog --title "$title" --gauge "Processing..." 8 60 0
}