#!/bin/bash

# Get script directory for relative imports
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source all required modules
source "$SCRIPT_DIR/lib/config.sh"
source "$SCRIPT_DIR/lib/utils.sh"
source "$SCRIPT_DIR/lib/dialogs.sh"
source "$SCRIPT_DIR/lib/connectivity.sh"
source "$SCRIPT_DIR/lib/tmux_manager.sh"
source "$SCRIPT_DIR/lib/component_manager.sh"


# Initialize configuration
init_config

# Check dependencies
check_dependencies

# Start background connectivity monitoring
start_connectivity_monitor
echo "DEBUG: Connectivity monitor started with PID: $CONNECTIVITY_MONITOR_PID" >&2

# Display welcome screen
show_welcome

# Main menu loop
while true; do
    # Update system status
    update_system_status
    
    # Show main menu (will auto-refresh every 2 seconds)
    show_main_menu
    
    # Handle menu choice (empty choice means timeout - just refresh)
    if [[ -n "$MENU_CHOICE" ]]; then
        case $MENU_CHOICE in
            1) start_complete_system ;;
            2) show_subsystem_menu ;;
            3) attach_to_system ;;
            4) show_component_menu ;;
            5) stop_system ;;
            6) show_system_status ;;
            7) check_all_remote_sessions ;;
            8) show_settings_menu ;;
            9) show_help ;;
            10) 
                if confirm_exit; then
                    stop_connectivity_monitor
                    cleanup_and_exit
                fi
                ;;
        esac
    fi
    # If MENU_CHOICE is empty (timeout), loop continues and refreshes menu automatically
done