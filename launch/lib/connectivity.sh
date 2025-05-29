#!/bin/bash

# Global variables for connectivity status
EF_CONNECTIVITY_STATUS="Unknown"
BASE_CONNECTIVITY_STATUS="Unknown"
CONNECTIVITY_MONITOR_PID=""

# Start background connectivity monitoring
start_connectivity_monitor() {
    log_info "Starting background connectivity monitor"
    
    # Create monitoring function that runs in background
    {
        while true; do
            # Check EF connectivity
            if ping -c 1 -W 1 $EF_IP > /dev/null 2>&1; then
                EF_CONNECTIVITY_STATUS="Connected ✓"
            else
                EF_CONNECTIVITY_STATUS="Offline ✗"
            fi
            
            # Check Base connectivity
            if ping -c 1 -W 1 "$BASE_IP" > /dev/null 2>&1; then
                BASE_CONNECTIVITY_STATUS="Connected ✓"
            else
                BASE_CONNECTIVITY_STATUS="Offline ✗"
            fi
            
            # Write status to temp file for main process to read
            echo "EF_STATUS=$EF_CONNECTIVITY_STATUS" > /tmp/paint_connectivity_status
            echo "BASE_STATUS=$BASE_CONNECTIVITY_STATUS" >> /tmp/paint_connectivity_status
            echo "LAST_UPDATE=$(date '+%H:%M:%S')" >> /tmp/paint_connectivity_status
            
            sleep 1
        done
    } &
    
    CONNECTIVITY_MONITOR_PID=$!
    log_info "Connectivity monitor started with PID: $CONNECTIVITY_MONITOR_PID"
}

# Stop background connectivity monitoring
stop_connectivity_monitor() {
    if [[ -n "$CONNECTIVITY_MONITOR_PID" ]]; then
        log_info "Stopping connectivity monitor (PID: $CONNECTIVITY_MONITOR_PID)"
        kill $CONNECTIVITY_MONITOR_PID 2>/dev/null
        wait $CONNECTIVITY_MONITOR_PID 2>/dev/null
        rm -f /tmp/paint_connectivity_status
    fi
}

# Read current connectivity status
read_connectivity_status() {
    if [[ -f /tmp/paint_connectivity_status ]]; then
        source /tmp/paint_connectivity_status
    else
        EF_STATUS="Unknown"
        BASE_STATUS="Unknown"
        LAST_UPDATE="--:--:--"
    fi
}


# Check device connectivity with progress dialog (existing function)
check_device() {
    local ip="$1"
    local name="$2"
    local show_dialog="${3:-true}"
    
    if [[ "$show_dialog" == "true" ]]; then
        (
            echo "10"; echo "XXX"; echo "Checking $name..."; echo "XXX"
            ping -c 1 -W "$PING_TIMEOUT" "$ip" > /dev/null 2>&1
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
    else
        # Silent check without dialog
        ping -c 1 -W "$PING_TIMEOUT" "$ip" > /dev/null 2>&1
        return $?
    fi
}

# Check connectivity to both systems
check_all_connectivity() {
    log_info "Checking connectivity to all systems"
    
    check_device "$EF_IP" "EF"
    EF_ONLINE=$?
    
    check_device "$BASE_IP" "Base Robot"
    BASE_ONLINE=$?
    
    # Log results
    if [[ $EF_ONLINE -eq 0 ]]; then
        log_info "EF system is online"
    else
        log_warning "EF system is offline"
    fi
    
    if [[ $BASE_ONLINE -eq 0 ]]; then
        log_info "Base Robot system is online"
    else
        log_warning "Base Robot system is offline"
    fi
    
    return $((EF_ONLINE + BASE_ONLINE))
}

# Handle connectivity issues with user options
handle_connectivity_issues() {
    local ef_online="$1"
    local base_online="$2"
    
    # If both systems are online, return success
    if [[ $ef_online -eq 0 ]] && [[ $base_online -eq 0 ]]; then
        return 0
    fi
    
    # Prepare offline device list
    local devices_offline=""
    [[ $ef_online -ne 0 ]] && devices_offline="$devices_offline\n• EF"
    [[ $base_online -ne 0 ]] && devices_offline="$devices_offline\n• Base Robot"
    
    # Show appropriate menu based on what's offline
    if [[ $ef_online -ne 0 ]] && [[ $base_online -ne 0 ]]; then
        # Both systems offline
        local choice=$(dialog --title "Connection Issues" --menu "Both systems are unreachable:$devices_offline\n\nWhat would you like to do?" 15 70 4 \
            "1" "Continue anyway (not recommended)" \
            "2" "Launch start_ef.bash directly on EF" \
            "3" "Launch start_base.bash directly on Base" \
            "4" "Cancel operation" \
            3>&1 1>&2 2>&3)
            
        case $choice in
            1) return 0 ;; # Continue anyway
            2) launch_ef_script; return 1 ;;
            3) launch_base_script; return 1 ;;
            4|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return 1 ;;
        esac
        
    elif [[ $ef_online -ne 0 ]]; then
        # Only EF is offline
        local choice=$(dialog --title "Connection Issues" --menu "EF is unreachable.\n\nWhat would you like to do?" 13 70 3 \
            "1" "Continue anyway (not recommended)" \
            "2" "Launch start_ef.bash directly on EF" \
            "3" "Cancel operation" \
            3>&1 1>&2 2>&3)
            
        case $choice in
            1) return 0 ;; # Continue anyway
            2) launch_ef_script; return 1 ;;
            3|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return 1 ;;
        esac
        
    elif [[ $base_online -ne 0 ]]; then
        # Only Base is offline
        local choice=$(dialog --title "Connection Issues" --menu "Base Robot is unreachable.\n\nWhat would you like to do?" 13 70 3 \
            "1" "Continue anyway (not recommended)" \
            "2" "Launch start_base.bash directly on Base" \
            "3" "Cancel operation" \
            3>&1 1>&2 2>&3)
            
        case $choice in
            1) return 0 ;; # Continue anyway
            2) launch_base_script; return 1 ;;
            3|"") dialog --title "Operation Cancelled" --msgbox "Operation cancelled by user." 5 40; return 1 ;;
        esac
    fi
    
    return 0
}

# Test SSH connectivity
test_ssh_connection() {
    local host="$1"
    local timeout="${2:-$SSH_TIMEOUT}"
    
    log_debug "Testing SSH connection to $host"
    
    if timeout "$timeout" ssh -o BatchMode=yes -o ConnectTimeout="$timeout" "$host" exit 2>/dev/null; then
        log_info "SSH connection to $host successful"
        return 0
    else
        log_warning "SSH connection to $host failed"
        return 1
    fi
}

# Get network interface information
get_network_info() {
    local interface=$(ip route | grep default | awk '{print $5}' | head -n1)
    local local_ip=$(ip route get 8.8.8.8 | awk '{print $7}' | head -n1)
    
    echo "Interface: $interface"
    echo "Local IP: $local_ip"
    
    log_debug "Network info - Interface: $interface, Local IP: $local_ip"
}

# Ping test with detailed results
detailed_ping_test() {
    local target="$1"
    local name="$2"
    local count="${3:-5}"
    
    log_info "Running detailed ping test to $name ($target)"
    
    local result=$(ping -c "$count" -W "$PING_TIMEOUT" "$target" 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        local avg_time=$(echo "$result" | tail -1 | awk -F'/' '{print $5}')
        local packet_loss=$(echo "$result" | grep "packet loss" | awk '{print $6}')
        
        dialog --title "Ping Test Results" --msgbox "Target: $name ($target)\nStatus: Connected ✓\nPacket Loss: $packet_loss\nAverage Response: ${avg_time}ms" 10 50
        log_info "Ping test to $name successful - Loss: $packet_loss, Avg: ${avg_time}ms"
    else
        dialog --title "Ping Test Results" --msgbox "Target: $name ($target)\nStatus: Failed ✗\nError: Connection timeout or unreachable" 8 50
        log_warning "Ping test to $name failed"
    fi
    
    return $exit_code
}