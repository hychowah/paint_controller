#!/bin/bash

# CONFIGURABLE VARIABLES
# ======================
EF_IP="192.168.10.102"          # EF system IP address
BASE_IP="192.168.10.173"        # Base system IP address
MAIN_SESSION_NAME="paint_system" # Name of the main tmux session
EF_SESSION_NAME="paint_ef_system"   # Name for EF system session
BASE_SESSION_NAME="paint_base_system" # Name for Base system session
ROS_BAG_INTERVAL=30             # Interval for ROS bag recording auto-save (minutes)
ROS_BAG_PATH="~/Documents"      # Path to store ROS bag files

# Component definitions
declare -A EF_COMPONENTS=(
    ["teensy"]="paint_end_effector/teensy_node.py"
    ["lidar"]="unitree_lidar_ros2 launch.py"
    ["camera"]="start_ef_cam.bash"
    ["sync"]="paint_interfaces/RobotActionSynchronizer.py --robot ef"
)

declare -A BASE_COMPONENTS=(
    ["wheel"]="paint_base/wheel_node.py"
    ["winch"]="paint_base/winch/python/winch_node.py"
    ["camera"]="start_base_cam.bash"
    ["sync"]="towngas_interfaces/RobotActionSynchronizer.py --robot base"
)

# Check if dialog is installed
if ! command -v dialog &> /dev/null; then
    echo "Dialog is required but not installed."
    echo "Please install it using: sudo apt-get install dialog"
    exit 1
fi

# Function to show progress
show_progress() {
    for i in $(seq 0 10 100); do
        echo $i
        sleep 0.1
    done | dialog --title "$1" --gauge "$2" 10 70 0
}

# Function to check connectivity
check_device() {
    local ip=$1
    local name=$2
    
    (
        echo "10"; echo "XXX"; echo "Checking $name..."; echo "XXX"
        ping -c 1 -W 2 $ip > /dev/null 2>&1
        local result=$?
        
        echo "50"; echo "XXX"; echo "Analyzing connection..."; echo "XXX"
        sleep 0.5
        
        echo "100"; echo "XXX"
        if [ $result -eq 0 ]; then
            echo "$name: Connected!"
        else
            echo "$name: Not connected!"
        fi
        echo "XXX"
        sleep 1
    ) | dialog --title "Connection Check" --gauge "Checking $name connection..." 8 60 0
    
    return $result
}

# Function to check if tmux session exists
check_tmux_session() {
    tmux has-session -t $1 2>/dev/null
    return $?
}

# Function to gracefully terminate tmux session
terminate_session() {
    local session=$1
    if check_tmux_session $session; then
        # Try to gracefully stop processes first
        tmux list-panes -a -t $session -F '#{session_name}:#{window_index}.#{pane_index}' | while read pane; do
            tmux send-keys -t $pane C-c
            sleep 0.5
        done
        sleep 1
        tmux kill-session -t $session
    fi
}

# Function to restart a specific component
restart_component() {
    local system=$1     # "ef" or "base"
    local component=$2  # component name
    local command=$3    # command to run
    local window=$4     # window/pane address
    
    if ! check_tmux_session $MAIN_SESSION_NAME; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return 1
    fi
    
    if [ "$system" == "ef" ]; then
        HOST="ef"
    else
        HOST="base"
    fi
    
    (
        echo "10"; echo "XXX"; echo "Stopping $component..."; echo "XXX"
        # Send Ctrl+C to stop the component
        tmux send-keys -t $MAIN_SESSION_NAME:$window C-c
        sleep 1.5
        
        echo "40"; echo "XXX"; echo "Preparing to restart $component..."; echo "XXX"
        # Clear screen and set up colors
        tmux send-keys -t $MAIN_SESSION_NAME:$window "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:$window 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        
        echo "70"; echo "XXX"; echo "Restarting $component..."; echo "XXX"
        # Restart the component with appropriate command
        tmux send-keys -t $MAIN_SESSION_NAME:$window 'echo -e "${YELLOW}Restarting component: '$component'${RESET}"' C-m
        
        if [[ $command == *.bash ]]; then
            # Execute bash script
            tmux send-keys -t $MAIN_SESSION_NAME:$window "./$command" C-m
        elif [[ $command == *launch.py ]]; then
            # Launch ROS2 node
            tmux send-keys -t $MAIN_SESSION_NAME:$window "ros2 launch $command" C-m
        else
            # Execute Python script
            tmux send-keys -t $MAIN_SESSION_NAME:$window "python3 $command" C-m
        fi
        
        echo "100"; echo "XXX"; echo "$component restarted successfully!"; echo "XXX"
        sleep 1
    ) | dialog --title "Restarting Component" --gauge "Restarting $component..." 8 60 0
    
    dialog --title "Component Restarted" --msgbox "$component has been restarted successfully." 6 50
    return 0
}

# Function to launch start_ef.bash directly
launch_ef_script() {
    # Check if session already exists
    if check_tmux_session $EF_SESSION_NAME; then
        dialog --title "Session Exists" --yesno "An EF system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [ $? -eq 0 ]; then
            (
                echo "30"; echo "XXX"; echo "Terminating existing EF session..."; echo "XXX"
                terminate_session $EF_SESSION_NAME
                echo "100"; echo "XXX"; echo "Previous session terminated."; echo "XXX"
                sleep 1
            ) | dialog --title "Cleaning Up" --gauge "Preparing system..." 8 60 0
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    (
        echo "20"; echo "XXX"; echo "Connecting to EF..."; echo "XXX"
        ping -c 1 -W 2 $EF_IP > /dev/null 2>&1
        EF_ONLINE=$?
        
        if [ $EF_ONLINE -ne 0 ]; then
            echo "100"; echo "XXX"; echo "Warning: EF is not reachable. Continuing anyway..."; echo "XXX"
            sleep 2
        else
            echo "50"; echo "XXX"; echo "EF is online. Starting script..."; echo "XXX"
            sleep 1
        fi
        
        echo "80"; echo "XXX"; echo "Launching start_ef.bash..."; echo "XXX"
        ssh ef './start_ef.bash' >/dev/null 2>&1 &
        
        echo "100"; echo "XXX"; echo "EF system started!"; echo "XXX"
        sleep 1
    ) | dialog --title "Starting EF System" --gauge "Launching EF system..." 8 60 0
    
    dialog --title "EF System Started" --msgbox "The EF system has been started.\n\nNote: This runs independently of the main control panel." 7 60
}

# Function to launch start_base.bash directly
launch_base_script() {
    # Check if session already exists
    if check_tmux_session $BASE_SESSION_NAME; then
        dialog --title "Session Exists" --yesno "A Base system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [ $? -eq 0 ]; then
            (
                echo "30"; echo "XXX"; echo "Terminating existing Base session..."; echo "XXX"
                terminate_session $BASE_SESSION_NAME
                echo "100"; echo "XXX"; echo "Previous session terminated."; echo "XXX"
                sleep 1
            ) | dialog --title "Cleaning Up" --gauge "Preparing system..." 8 60 0
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    (
        echo "20"; echo "XXX"; echo "Connecting to Base..."; echo "XXX"
        ping -c 1 -W 2 $BASE_IP > /dev/null 2>&1
        BASE_ONLINE=$?
        
        if [ $BASE_ONLINE -ne 0 ]; then
            echo "100"; echo "XXX"; echo "Warning: Base is not reachable. Continuing anyway..."; echo "XXX"
            sleep 2
        else
            echo "50"; echo "XXX"; echo "Base is online. Starting script..."; echo "XXX"
            sleep 1
        fi
        
        echo "80"; echo "XXX"; echo "Launching start_base.bash..."; echo "XXX"
        ssh base './start_base.bash' >/dev/null 2>&1 &
        
        echo "100"; echo "XXX"; echo "Base system started!"; echo "XXX"
        sleep 1
    ) | dialog --title "Starting Base System" --gauge "Launching Base system..." 8 60 0
    
    dialog --title "Base System Started" --msgbox "The Base system has been started.\n\nNote: This runs independently of the main control panel." 7 60
}

# Function to start complete paint system
start_complete_system() {
    dialog --title "Starting Paint System" --infobox "Preparing to start the complete paint system..." 5 60
    sleep 1
    
    # Check existing session and ask to terminate if needed
    if check_tmux_session $MAIN_SESSION_NAME; then
        dialog --title "Session Exists" --yesno "A paint system session is already running.\n\nDo you want to terminate it first?" 8 60
        if [ $? -eq 0 ]; then
            (
                echo "30"; echo "XXX"; echo "Terminating existing sessions..."; echo "XXX"
                terminate_session $MAIN_SESSION_NAME
                echo "100"; echo "XXX"; echo "Previous sessions closed."; echo "XXX"
                sleep 1
            ) | dialog --title "Cleaning Up" --gauge "Preparing system..." 8 60 0
        else
            dialog --title "Operation Cancelled" --msgbox "Launch cancelled to avoid conflicts with existing session." 6 60
            return
        fi
    fi
    
    # Check connectivity to both systems
    check_device $EF_IP "(EF)"
    EF_ONLINE=$?
    
    check_device $BASE_IP "Base Robot"
    BASE_ONLINE=$?
    
    # Handle connection failures with options
    CONNECTIVITY_ISSUE=0
    EF_LAUNCH_DIRECT=0
    BASE_LAUNCH_DIRECT=0
    
    if [ $EF_ONLINE -ne 0 ] || [ $BASE_ONLINE -ne 0 ]; then
        DEVICES_OFFLINE=""
        [ $EF_ONLINE -ne 0 ] && DEVICES_OFFLINE="$DEVICES_OFFLINE\n• EF"
        [ $BASE_ONLINE -ne 0 ] && DEVICES_OFFLINE="$DEVICES_OFFLINE\n• Base Robot"
        
        # Create a more advanced menu for handling connection issues
        if [ $EF_ONLINE -ne 0 ] && [ $BASE_ONLINE -ne 0 ]; then
            # Both systems offline
            CONNECTIVITY_CHOICE=$(dialog --title "Connection Issues" --menu "Both systems are unreachable:$DEVICES_OFFLINE\n\nWhat would you like to do?" 15 70 4 \
                "1" "Continue anyway (not recommended)" \
                "2" "Launch start_ef.bash directly on EF" \
                "3" "Launch start_base.bash directly on Base" \
                "4" "Cancel operation" \
                3>&1 1>&2 2>&3)
                
            case $CONNECTIVITY_CHOICE in
                1) CONNECTIVITY_ISSUE=0 ;; # Continue anyway
                2) EF_LAUNCH_DIRECT=1; CONNECTIVITY_ISSUE=1 ;;
                3) BASE_LAUNCH_DIRECT=1; CONNECTIVITY_ISSUE=1 ;;
                4|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return ;;
            esac
            
        elif [ $EF_ONLINE -ne 0 ]; then
            # Only EF is offline
            CONNECTIVITY_CHOICE=$(dialog --title "Connection Issues" --menu "EF is unreachable.\n\nWhat would you like to do?" 13 70 3 \
                "1" "Continue anyway (not recommended)" \
                "2" "Launch start_ef.bash directly on EF" \
                "3" "Cancel operation" \
                3>&1 1>&2 2>&3)
                
            case $CONNECTIVITY_CHOICE in
                1) CONNECTIVITY_ISSUE=0 ;; # Continue anyway
                2) EF_LAUNCH_DIRECT=1; CONNECTIVITY_ISSUE=1 ;;
                3|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return ;;
            esac
            
        elif [ $BASE_ONLINE -ne 0 ]; then
            # Only Base is offline
            CONNECTIVITY_CHOICE=$(dialog --title "Connection Issues" --menu "Base Robot is unreachable.\n\nWhat would you like to do?" 13 70 3 \
                "1" "Continue anyway (not recommended)" \
                "2" "Launch start_base.bash directly on Base" \
                "3" "Cancel operation" \
                3>&1 1>&2 2>&3)
                
            case $CONNECTIVITY_CHOICE in
                1) CONNECTIVITY_ISSUE=0 ;; # Continue anyway
                2) BASE_LAUNCH_DIRECT=1; CONNECTIVITY_ISSUE=1 ;;
                3|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return ;;
            esac
        fi
    fi
    
    # Handle direct script launches if selected
    if [ $EF_LAUNCH_DIRECT -eq 1 ]; then
        launch_ef_script
    fi
    
    if [ $BASE_LAUNCH_DIRECT -eq 1 ]; then
        launch_base_script
    fi
    
    # If we're only doing direct launches, return after they're done
    if [ $CONNECTIVITY_ISSUE -eq 1 ]; then
        return
    fi
    
    # Start the system in background and show progress
    (
        echo "10"; echo "XXX"; echo "Creating tmux session..."; echo "XXX"
        
        # Create the tmux session and enable mouse
        tmux new-session -d -s $MAIN_SESSION_NAME -n "🎨 Paint Tool"
        tmux set -g mouse on
        
        echo "20"; echo "XXX"; echo "Setting up Paint Tool window..."; echo "XXX"
        # First window - EF system
        tmux send-keys -t $MAIN_SESSION_NAME:0 "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 'echo -e "${BLUE}${BOLD}PAINT TOOL CONTROL PANEL${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 'echo -e "\n${YELLOW}• Connecting to Paint Tool...\n${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 "ssh ef" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 'echo -e "\n${GREEN}• Starting Paint Tool systems...${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:0 "./start_ef.bash" C-m
        sleep 1
        
        echo "40"; echo "XXX"; echo "Setting up Base Robot window..."; echo "XXX"
        # Second window - Base system
        tmux new-window -t $MAIN_SESSION_NAME:1 -n "🤖 Base Robot"
        tmux send-keys -t $MAIN_SESSION_NAME:1 "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 'echo -e "${BLUE}${BOLD}BASE ROBOT CONTROL PANEL${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 'echo -e "\n${YELLOW}• Connecting to Base Robot...\n${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 "ssh base" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 'echo -e "\n${GREEN}• Starting Base Robot systems...${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:1 "./start_base.bash" C-m
        sleep 1
        
        echo "60"; echo "XXX"; echo "Setting up Control Center..."; echo "XXX"
        # Third window - Controller with split panes
        tmux new-window -t $MAIN_SESSION_NAME:2 -n "🎛️ Control Center"
        
        # Main controller pane
        tmux send-keys -t $MAIN_SESSION_NAME:2 "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2 'echo -e "${BLUE}${BOLD}MAIN PAINT CONTROLLER${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2 'echo -e "\n${YELLOW}• Starting central control system...\n${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2 "cd ~/ros2_ws/src/paint_controller_ros2/paint_controller/" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2 "python3 paint_controller.py" C-m
        sleep 1
        
        echo "80"; echo "XXX"; echo "Setting up data recording..."; echo "XXX"
        # Split for ROS2 bag recording with auto-termination
        tmux split-window -v -t $MAIN_SESSION_NAME:2
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "${BLUE}${BOLD}DATA RECORDER (AUTO-SAVE)${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n• Recording will automatically save every '$ROS_BAG_INTERVAL' minutes"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "cd $ROS_BAG_PATH" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n${YELLOW}• Starting in 10 seconds...${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "for i in {10..1}; do echo -ne \"Starting in \$i seconds...\r\"; sleep 1; done" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n${GREEN}• Beginning data recording...${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "while true; do" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  TIMESTAMP=\$(date +\"%Y%m%d_%H%M%S\")" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "\n${GREEN}• [Recording \$TIMESTAMP] Started new '$ROS_BAG_INTERVAL'-minute session${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  timeout ${ROS_BAG_INTERVAL}m ros2 bag record -a -o ${ROS_BAG_PATH}/rosbag2_\$TIMESTAMP" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "${BLUE}• [Recording \$TIMESTAMP] Saved successfully${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "${YELLOW}• Preparing next recording in 5 seconds...${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  sleep 5" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.1 "done" C-m
        
        # Split for time synchronization
        tmux split-window -h -t $MAIN_SESSION_NAME:2.1
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 "clear" C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 'echo -e "${BLUE}${BOLD}TIME SYNCHRONIZATION MONITOR${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 'echo -e "\n• Checking system time synchronization status..."' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 'echo -e "\n${YELLOW}• Note: This may ask for your password${RESET}"' C-m
        tmux send-keys -t $MAIN_SESSION_NAME:2.2 "sudo chronyc clients" C-m
        
        # Adjust layout to be more balanced
        tmux select-layout -t $MAIN_SESSION_NAME:2 tiled
        
        # Name the panes
        tmux select-pane -t $MAIN_SESSION_NAME:2.0 -T "Paint Controller"
        tmux select-pane -t $MAIN_SESSION_NAME:2.1 -T "Data Recorder"
        tmux select-pane -t $MAIN_SESSION_NAME:2.2 -T "Time Monitor"
        
        # Create help file
        cat > /tmp/paint_system_help.txt << EOL
==================== PAINT SYSTEM QUICK HELP ====================

HOW TO NAVIGATE:
- Click directly on the panel you want to interact with
- Use the tabs at the bottom to switch between main screens
- Use the mouse wheel to scroll text in any panel

KEYBOARD SHORTCUTS:
- Press Ctrl+B then 0 → Paint Tool Screen
- Press Ctrl+B then 1 → Base Robot Screen
- Press Ctrl+B then 2 → Control Center
- Press Ctrl+B then ? → Show this help again
- Press Ctrl+B then d → Detach (minimize) without closing

TO SHOW THIS HELP AGAIN:
- Type "help" in any panel and press Enter
- Or press Ctrl+B then ?

TO RECONNECT LATER:
- Run "tmux attach -t $MAIN_SESSION_NAME" in a terminal
- Or use this control panel to attach

=================================================================
EOL
        
        # Set up help command in each pane
        for pane in $(tmux list-panes -a -t $MAIN_SESSION_NAME -F '#{session_name}:#{window_index}.#{pane_index}'); do
            tmux send-keys -t $pane 'function help() { clear && cat /tmp/paint_system_help.txt; }; alias help=help' C-m
        done
        
        # Set up help key binding
        tmux bind-key -t $MAIN_SESSION_NAME ? run-shell "cat /tmp/paint_system_help.txt | less"
        
        # Select first window
        tmux select-window -t $MAIN_SESSION_NAME:0
        
        echo "100"; echo "XXX"; echo "System started successfully!"; echo "XXX"
        sleep 1
    ) | dialog --title "Starting System" --gauge "Starting the paint system..." 8 70 0
    
    dialog --title "System Started" --msgbox "The paint system has been started successfully!\n\nYou can now:\n• Click 'Attach to System' to view and control it\n• Click 'Main Menu' to return to the menu\n• Use 'tmux attach -t $MAIN_SESSION_NAME' in a terminal to view it later" 12 70
}

# Function to attach to a running system
attach_to_system() {
    # Check which sessions are available
    MAIN_RUNNING=0
    EF_RUNNING=0
    BASE_RUNNING=0
    
    check_tmux_session $MAIN_SESSION_NAME && MAIN_RUNNING=1
    check_tmux_session $EF_SESSION_NAME && EF_RUNNING=1
    check_tmux_session $BASE_SESSION_NAME && BASE_RUNNING=1
    
    # If no sessions are running, show error
    if [ $MAIN_RUNNING -eq 0 ] && [ $EF_RUNNING -eq 0 ] && [ $BASE_RUNNING -eq 0 ]; then
        dialog --title "Error" --msgbox "No paint system sessions are currently running.\n\nPlease start a system first." 8 50
        return
    fi
    
    # If only one session is running, attach to it directly
    if [ $MAIN_RUNNING -eq 1 ] && [ $EF_RUNNING -eq 0 ] && [ $BASE_RUNNING -eq 0 ]; then
        dialog --title "Attaching to System" --infobox "Attaching to the main paint system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
        sleep 2
        clear
        tmux attach-session -t $MAIN_SESSION_NAME
        clear
        return
    elif [ $MAIN_RUNNING -eq 0 ] && [ $EF_RUNNING -eq 1 ] && [ $BASE_RUNNING -eq 0 ]; then
        dialog --title "Attaching to System" --infobox "Attaching to the EF system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
        sleep 2
        clear
        tmux attach-session -t $EF_SESSION_NAME
        clear
        return
    elif [ $MAIN_RUNNING -eq 0 ] && [ $EF_RUNNING -eq 0 ] && [ $BASE_RUNNING -eq 1 ]; then
        dialog --title "Attaching to System" --infobox "Attaching to the Base system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
        sleep 2
        clear
        tmux attach-session -t $BASE_SESSION_NAME
        clear
        return
    fi
    
    # If multiple sessions are running, let user choose
    OPTIONS=""
    [ $MAIN_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 1 \"Complete Paint System\" on"
    [ $EF_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 2 \"EF System Only\" off"
    [ $BASE_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 3 \"Base System Only\" off"
    
    SESSION=$(dialog --title "Attach to System" --radiolist "Multiple systems are running.\nSelect which system to attach to:" 12 60 3 $OPTIONS 3>&1 1>&2 2>&3)
    
    case $SESSION in
        1)
            dialog --title "Attaching to System" --infobox "Attaching to the main paint system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
            sleep 2
            clear
            tmux attach-session -t $MAIN_SESSION_NAME
            clear
            ;;
        2)
            dialog --title "Attaching to System" --infobox "Attaching to the EF system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
            sleep 2
            clear
            tmux attach-session -t $EF_SESSION_NAME
            clear
            ;;
        3)
            dialog --title "Attaching to System" --infobox "Attaching to the Base system...\n\nTo return to this menu, press Ctrl+B then d" 7 50
            sleep 2
            clear
            tmux attach-session -t $BASE_SESSION_NAME
            clear
            ;;
    esac
}

# Function to stop the system (continued)
stop_system() {
    # Check which sessions are running
    MAIN_RUNNING=0
    EF_RUNNING=0
    BASE_RUNNING=0
    
    check_tmux_session $MAIN_SESSION_NAME && MAIN_RUNNING=1
    check_tmux_session $EF_SESSION_NAME && EF_RUNNING=1
    check_tmux_session $BASE_SESSION_NAME && BASE_RUNNING=1
    
    # If no sessions are running, show error
    if [ $MAIN_RUNNING -eq 0 ] && [ $EF_RUNNING -eq 0 ] && [ $BASE_RUNNING -eq 0 ]; then
        dialog --title "Error" --msgbox "No paint system sessions are currently running." 5 50
        return
    fi
    
    # Let user choose which systems to stop
    OPTIONS=""
    [ $MAIN_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 1 \"Complete Paint System\" on"
    [ $EF_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 2 \"EF System Only\" off"
    [ $BASE_RUNNING -eq 1 ] && OPTIONS="$OPTIONS 3 \"Base System Only\" off"
    
    SESSIONS=$(dialog --title "Stop System" --checklist "Select which systems to stop:" 12 60 3 $OPTIONS 3>&1 1>&2 2>&3)
    
    if [ $? -ne 0 ] || [ -z "$SESSIONS" ]; then
        return
    fi
    
    # Confirm before stopping
    dialog --title "Confirm" --yesno "Are you sure you want to stop the selected systems?" 7 50
    if [ $? -ne 0 ]; then
        return
    fi
    
    (
        echo "10"; echo "XXX"; echo "Preparing to stop systems..."; echo "XXX"
        sleep 1
        
        for SESSION in $SESSIONS; do
            case $SESSION in
                1)
                    echo "40"; echo "XXX"; echo "Stopping complete paint system..."; echo "XXX"
                    terminate_session $MAIN_SESSION_NAME
                    sleep 1
                    ;;
                2)
                    echo "60"; echo "XXX"; echo "Stopping EF system..."; echo "XXX"
                    terminate_session $EF_SESSION_NAME
                    sleep 1
                    ;;
                3)
                    echo "80"; echo "XXX"; echo "Stopping Base system..."; echo "XXX"
                    terminate_session $BASE_SESSION_NAME
                    sleep 1
                    ;;
            esac
        done
        
        echo "100"; echo "XXX"; echo "Systems stopped successfully!"; echo "XXX"
        sleep 1
    ) | dialog --title "Stopping Systems" --gauge "Stopping selected systems..." 8 60 0
    
    dialog --title "Systems Stopped" --msgbox "The selected systems have been stopped successfully." 5 60
}

# Function to manage EF components
manage_ef_components() {
    if ! check_tmux_session $MAIN_SESSION_NAME; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    while true; do
        COMPONENT=$(dialog --title "Manage Paint Tool Components" \
                        --menu "Select a component to restart:" 12 60 5 \
                        "teensy" "Teensy Controller" \
                        "lidar" "Lidar Sensor" \
                        "camera" "Camera System" \
                        "sync" "Robot Action Synchronizer" \
                        "back" "Back to Main Menu" \
                        3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$COMPONENT" == "back" ]; then
            break
        fi
        
        # Get component command
        COMMAND=${EF_COMPONENTS[$COMPONENT]}
        
        if [ -z "$COMMAND" ]; then
            dialog --title "Error" --msgbox "Component not found." 5 40
            continue
        fi
        
        # In a real system, each component would have a specific pane in the tmux session
        # For this example, we'll use the EF window (0)
        restart_component "ef" "$COMPONENT" "$COMMAND" "0"
    done
}

# Function to manage Base components
manage_base_components() {
    if ! check_tmux_session $MAIN_SESSION_NAME; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    while true; do
        COMPONENT=$(dialog --title "Manage Base Robot Components" \
                        --menu "Select a component to restart:" 12 60 5 \
                        "wheel" "Wheel Control System" \
                        "winch" "Winch Control System" \
                        "camera" "Camera System" \
                        "sync" "Robot Action Synchronizer" \
                        "back" "Back to Main Menu" \
                        3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$COMPONENT" == "back" ]; then
            break
        fi
        
        # Get component command
        COMMAND=${BASE_COMPONENTS[$COMPONENT]}
        
        if [ -z "$COMMAND" ]; then
            dialog --title "Error" --msgbox "Component not found." 5 40
            continue
        fi
        
        # In a real system, each component would have a specific pane in the tmux session
        # For this example, we'll use the Base window (1)
        restart_component "base" "$COMPONENT" "$COMMAND" "1"
    done
}

# Function to manage Controller components
manage_controller_components() {
    if ! check_tmux_session $MAIN_SESSION_NAME; then
        dialog --title "Error" --msgbox "Paint system is not running. Please start it first." 6 50
        return
    fi
    
    while true; do
        COMPONENT=$(dialog --title "Manage Controller Components" \
                        --menu "Select a component to restart:" 10 60 4 \
                        "controller" "Main Paint Controller" \
                        "recorder" "Data Recorder" \
                        "chrono" "Time Synchronization" \
                        "back" "Back to Main Menu" \
                        3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$COMPONENT" == "back" ]; then
            break
        fi
        
        case $COMPONENT in
            controller)
                restart_component "local" "Paint Controller" "~/ros2_ws/src/paint_controller_ros2/paint_controller/paint_controller.py" "2.0"
                ;;
            recorder)
                dialog --title "Confirm" --yesno "Restarting the Data Recorder will create a new recording session.\n\nProceed?" 8 60
                if [ $? -eq 0 ]; then
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 C-c
                    sleep 1
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "clear" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 'BLUE=$(tput setaf 4); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3); RED=$(tput setaf 1); RESET=$(tput sgr0); BOLD=$(tput bold)' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "${BLUE}${BOLD}DATA RECORDER (AUTO-SAVE)${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n• Recording will automatically save every '$ROS_BAG_INTERVAL' minutes"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "cd $ROS_BAG_PATH" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n${YELLOW}• Starting in 5 seconds...${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "for i in {5..1}; do echo -ne \"Starting in \$i seconds...\r\"; sleep 1; done" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 'echo -e "\n${GREEN}• Beginning data recording...${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "while true; do" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  TIMESTAMP=\$(date +\"%Y%m%d_%H%M%S\")" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "\n${GREEN}• [Recording \$TIMESTAMP] Started new '$ROS_BAG_INTERVAL'-minute session${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  timeout ${ROS_BAG_INTERVAL}m ros2 bag record -a -o ${ROS_BAG_PATH}/rosbag2_\$TIMESTAMP" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "${BLUE}• [Recording \$TIMESTAMP] Saved successfully${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 '  echo -e "${YELLOW}• Preparing next recording in 5 seconds...${RESET}"' C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "  sleep 5" C-m
                    tmux send-keys -t $MAIN_SESSION_NAME:2.1 "done" C-m
                    dialog --title "Component Restarted" --msgbox "Data Recorder has been restarted." 6 50
                fi
                ;;
            chrono)
                restart_component "local" "Time Synchronization" "sudo chronyc clients" "2.2"
                ;;
        esac
    done
}

# Function to show subsystem launch menu
launch_subsystem_menu() {
    while true; do
        SUBSYSTEM=$(dialog --title "Launch Subsystem" \
                        --menu "Select a subsystem to launch directly:" 11 60 3 \
                        "1" "Launch EF System Only" \
                        "2" "Launch Base System Only" \
                        "3" "Back to Main Menu" \
                        3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$SUBSYSTEM" == "3" ]; then
            break
        fi
        
        case $SUBSYSTEM in
            1) launch_ef_script ;;
            2) launch_base_script ;;
        esac
    done
}

# Function to check system status
check_system_status() {
    # Check connectivity
    check_device $EF_IP "EF"
    EF_ONLINE=$?
    
    check_device $BASE_IP "Base Robot"
    BASE_ONLINE=$?
    
    # Check if systems are running
    MAIN_RUNNING=0
    EF_RUNNING=0
    BASE_RUNNING=0
    
    check_tmux_session $MAIN_SESSION_NAME && MAIN_RUNNING=1
    check_tmux_session $EF_SESSION_NAME && EF_RUNNING=1
    check_tmux_session $BASE_SESSION_NAME && BASE_RUNNING=1
    
    # Get components status if system is running
    EF_COMPONENTS_STATUS=""
    BASE_COMPONENTS_STATUS=""
    CONTROLLER_STATUS=""
    
    if [ $MAIN_RUNNING -eq 1 ]; then
        # Check if we can get window list (will succeed if session exists)
        if tmux list-windows -t $MAIN_SESSION_NAME &>/dev/null; then
            EF_COMPONENTS_STATUS="\n• Paint Tool: Running"
            BASE_COMPONENTS_STATUS="\n• Base Robot: Running"
            CONTROLLER_STATUS="\n• Controller: Running"
            
            # Check ROS2 bag recording
            if tmux list-panes -t $MAIN_SESSION_NAME:2.1 &>/dev/null; then
                CONTROLLER_STATUS="$CONTROLLER_STATUS\n• Data Recording: Active"
            else
                CONTROLLER_STATUS="$CONTROLLER_STATUS\n• Data Recording: Not active"
            fi
        fi
    else
        if [ $EF_RUNNING -eq 1 ]; then
            EF_COMPONENTS_STATUS="\n• Paint Tool: Running Standalone"
        fi
        
        if [ $BASE_RUNNING -eq 1 ]; then
            BASE_COMPONENTS_STATUS="\n• Base Robot: Running Standalone"
        fi
    fi
    
    # Check disk space
    DISK_SPACE=$(df -h ~ | awk 'NR==2 {print $5}')
    DISK_AVAIL=$(df -h ~ | awk 'NR==2 {print $4}')
    
    # Prepare status messages
    EF_STATUS="Not Connected ✗"
    [ $EF_ONLINE -eq 0 ] && EF_STATUS="Connected ✓"
    
    BASE_STATUS="Not Connected ✗"
    [ $BASE_ONLINE -eq 0 ] && BASE_STATUS="Connected ✓"
    
    SYSTEM_STATUS="Not Running ✗"
    [ $MAIN_RUNNING -eq 1 ] && SYSTEM_STATUS="Running ✓"
    
    # Display status
    dialog --title "System Status" --msgbox "\
DEVICE CONNECTIVITY:
- EF: $EF_STATUS
- Base Robot: $BASE_STATUS

SYSTEM STATUS:
- Main Paint System: $SYSTEM_STATUS$EF_COMPONENTS_STATUS$BASE_COMPONENTS_STATUS$CONTROLLER_STATUS

RESOURCES:
- Disk Space Used: $DISK_SPACE
- Available Space: $DISK_AVAIL

Press OK to return to the main menu." 18 70
}

# Function to show help
show_help() {
    dialog --title "Paint System Help" --msgbox "\
C3SPRAY PAINT SYSTEM CONTROL CENTER

This application helps you manage the C3Spray Paint System with buggy controls.


MAIN FUNCTIONS (not sure if any of these work):

- Start System - Starts the complete paint system including:
  - Paint Tool (End Effector)
  - Base Robot
  - Main Controller
  - Data Recording (auto-saves every $ROS_BAG_INTERVAL minutes)
  - Time Synchronization Monitor

- Launch Subsystem - Launch either EF or Base system independently

- Attach to System - View and control running systems

- Manage Components - Restart individual system components:
  - Paint Tool Components (Teensy, Lidar, Camera, Sync)
  - Base Robot Components (Wheel, Winch, Camera, Sync)
  - Controller Components (Main Controller, Data Recorder, Time Sync)

- Stop System - Safely shut down all components

- Check Status - Verify connectivity and system status

- Settings - Configure system parameters

WHEN VIEWING THE SYSTEM:
- Use Ctrl+B then d to detach and return to this menu
- Use Ctrl+B then 0-2 to switch between main screens
- Click directly on panes to select them
- Use mouse wheel to scroll text in panes

Press OK to return to the main menu." 26 76
}

# Function to show settings menu
show_settings() {
    while true; do
        SETTING=$(dialog --title "Settings" --menu "Configure system settings:" 12 60 3 \
                "1" "Change ROS Bag Interval (current: ${ROS_BAG_INTERVAL}m)" \
                "2" "Change ROS Bag Path (current: $ROS_BAG_PATH)" \
                "3" "Back to Main Menu" \
                3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$SETTING" == "3" ]; then
            break
        fi
        
        case $SETTING in
            1)
                NEW_INTERVAL=$(dialog --title "ROS Bag Interval" --inputbox "Enter new interval in minutes:" 8 50 "$ROS_BAG_INTERVAL" 3>&1 1>&2 2>&3)
                if [ $? -eq 0 ] && [[ $NEW_INTERVAL =~ ^[0-9]+$ ]]; then
                    ROS_BAG_INTERVAL=$NEW_INTERVAL
                    dialog --title "Settings Updated" --msgbox "ROS Bag interval updated to $ROS_BAG_INTERVAL minutes.\n\nNote: This will apply to new recording sessions." 8 60
                elif [ $? -eq 0 ]; then
                    dialog --title "Invalid Input" --msgbox "Please enter a valid number." 5 40
                fi
                ;;
            2)
                NEW_PATH=$(dialog --title "ROS Bag Path" --inputbox "Enter new path for ROS Bag files:" 8 60 "$ROS_BAG_PATH" 3>&1 1>&2 2>&3)
                if [ $? -eq 0 ] && [ ! -z "$NEW_PATH" ]; then
                    if [ -d "$(eval echo $NEW_PATH)" ]; then
                        ROS_BAG_PATH=$NEW_PATH
                        dialog --title "Settings Updated" --msgbox "ROS Bag path updated to $ROS_BAG_PATH.\n\nNote: This will apply to new recording sessions." 8 60
                    else
                        dialog --title "Invalid Path" --msgbox "The specified path does not exist." 6 40
                    fi
                fi
                ;;
        esac
    done
}

# Function to show component management menu
manage_components() {
    while true; do
        CHOICE=$(dialog --title "Component Management" \
                    --menu "Select a system to manage:" 12 60 4 \
                    "1" "EF Components" \
                    "2" "Base Robot Components" \
                    "3" "Controller Components" \
                    "4" "Back to Main Menu" \
                    3>&1 1>&2 2>&3)
        
        if [ $? -ne 0 ] || [ "$CHOICE" == "4" ]; then
            break
        fi
        
        case $CHOICE in
            1) manage_ef_components ;;
            2) manage_base_components ;;
            3) manage_controller_components ;;
        esac
    done
}

# Display welcome screen
dialog --title "Welcome" --msgbox "C3 paint" 10 60

# Main menu loop
while true; do
    # Check if systems are running
    MAIN_RUNNING=0
    EF_RUNNING=0
    BASE_RUNNING=0
    
    check_tmux_session $MAIN_SESSION_NAME && MAIN_RUNNING=1
    check_tmux_session $EF_SESSION_NAME && EF_RUNNING=1
    check_tmux_session $BASE_SESSION_NAME && BASE_RUNNING=1
    
    # Prepare status indicators
    MAIN_STATUS=""
    EF_STATUS=""
    BASE_STATUS=""
    
    [ $MAIN_RUNNING -eq 1 ] && MAIN_STATUS="[✓]" || MAIN_STATUS="[ ]"
    [ $EF_RUNNING -eq 1 ] && EF_STATUS="[✓]" || EF_STATUS="[ ]"
    [ $BASE_RUNNING -eq 1 ] && BASE_STATUS="[✓]" || BASE_STATUS="[ ]"
    
    # Show main menu with status indicators
    CHOICE=$(dialog --clear --title "C3SPRAY PAINT SYSTEM CONTROL CENTER" \
            --menu "\nSystem Status:\n• Complete System: $MAIN_STATUS\n• EF System: $EF_STATUS\n• Base System: $BASE_STATUS\n\nSelect an option:" 18 60 9 \
            "1" "Start Complete System" \
            "2" "Launch Subsystem" \
            "3" "Attach to Running System" \
            "4" "Manage System Components" \
            "5" "Stop System" \
            "6" "Check System Status" \
            "7" "Settings" \
            "8" "Help" \
            "9" "Exit" \
            3>&1 1>&2 2>&3)
    
    # Handle menu choice
    case $CHOICE in
        1) # Start System
            start_complete_system
            ;;
        2) # Launch Subsystem
            launch_subsystem_menu
            ;;
        3) # Attach to System
            attach_to_system
            ;;
        4) # Manage Components
            manage_components
            ;;
        5) # Stop System
            stop_system
            ;;
        6) # Check Status
            check_system_status
            ;;
        7) # Settings
            show_settings
            ;;
        8) # Help
            show_help
            ;;
        9|"") # Exit or Cancel
            dialog --title "Confirm Exit" --yesno "Are you sure you want to exit?\n\nNote: Any running systems will continue to run." 8 50
            if [ $? -eq 0 ]; then
                clear
                exit 0
            fi
            ;;
    esac
done