#!/bin/bash

# Utility functions for the paint system

# Logging functions
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_PATH"
}

log_warning() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" | tee -a "$LOG_PATH"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_PATH"
}

log_debug() {
    if [[ "$LOG_LEVEL" == "DEBUG" ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] DEBUG: $1" | tee -a "$LOG_PATH"
    fi
}

# Check if required dependencies are installed
check_dependencies() {
    local deps=("dialog" "tmux" "ssh" "ping")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Missing dependencies: ${missing[*]}"
        echo "Please install them using:"
        echo "sudo apt-get install ${missing[*]}"
        exit 1
    fi
    
    log_info "All dependencies are available"
}

# Progress bar function
show_progress() {
    local title="$1"
    local message="$2"
    local steps="${3:-10}"
    
    for i in $(seq 0 $((100/steps)) 100); do
        echo $i
        sleep $PROGRESS_DELAY
    done | dialog --title "$title" --gauge "$message" 10 $DIALOG_WIDTH 0
}

# Validation functions
validate_ip() {
    local ip="$1"
    local regex="^([0-9]{1,3}\.){3}[0-9]{1,3}$"
    
    if [[ $ip =~ $regex ]]; then
        return 0
    else
        return 1
    fi
}

validate_number() {
    local num="$1"
    local regex="^[0-9]+$"
    
    if [[ $num =~ $regex ]] && [[ $num -gt 0 ]]; then
        return 0
    else
        return 1
    fi
}

validate_path() {
    local path="$1"
    local expanded_path
    
    # Expand tilde and environment variables
    expanded_path=$(eval echo "$path")
    
    if [[ -d "$expanded_path" ]]; then
        return 0
    else
        return 1
    fi
}

# System information functions
get_disk_usage() {
    df -h ~ | awk 'NR==2 {print $5}'
}

get_available_space() {
    df -h ~ | awk 'NR==2 {print $4}'
}

get_memory_usage() {
    free -h | awk 'NR==2{printf "%.1f%%", $3/$2*100}'
}

get_cpu_usage() {
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
}

# Time functions
get_timestamp() {
    date +"%Y%m%d_%H%M%S"
}

get_human_timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Color definitions for terminal output
setup_colors() {
    export RED=$(tput setaf 1)
    export GREEN=$(tput setaf 2)
    export YELLOW=$(tput setaf 3)
    export BLUE=$(tput setaf 4)
    export MAGENTA=$(tput setaf 5)
    export CYAN=$(tput setaf 6)
    export WHITE=$(tput setaf 7)
    export BOLD=$(tput bold)
    export RESET=$(tput sgr0)
}

# Cleanup function
cleanup_and_exit() {
    log_info "Paint system control panel exiting"
    
    # Clean up temporary files
    rm -f /tmp/paint_system_help.txt
    rm -f /tmp/paint_connectivity_status
    
    clear
    exit 0
}

# Error handling
handle_error() {
    local error_code="$1"
    local error_message="$2"
    
    log_error "Error $error_code: $error_message"
    
    dialog --title "Error" --msgbox "An error occurred:\n\n$error_message\n\nError Code: $error_code" 10 60
}

# Create help file
create_help_file() {
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

SYSTEM STATUS INDICATORS:
- [✓] System is running
- [ ] System is not running
- Connected ✓ Device is reachable
- Not Connected ✗ Device is not reachable

=================================================================
EOL
}