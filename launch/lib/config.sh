#!/bin/bash

# Configuration loader and management

init_config() {
    local config_file="$SCRIPT_DIR/config/settings.conf"
    local ef_config="$SCRIPT_DIR/config/ef_components.conf"
    local base_config="$SCRIPT_DIR/config/base_components.conf"
    
    # Load main configuration
    if [[ -f "$config_file" ]]; then
        source "$config_file"
        log_info "Configuration loaded from $config_file"
    else
        log_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    # Load component configurations
    if [[ -f "$ef_config" ]]; then
        source "$ef_config"
        log_info "EF components loaded from $ef_config"
    else
        log_warning "EF component config not found: $ef_config"
    fi
    
    if [[ -f "$base_config" ]]; then
        source "$base_config"
        log_info "Base components loaded from $base_config"
    else
        log_warning "Base component config not found: $base_config"
    fi
    
    # Validate required variables
    validate_config
}

validate_config() {
    local required_vars=(
        "EF_DEVICE_NAME" "EF_IP" "EF_SSH_TARGET"
        "BASE_DEVICE_NAME" "BASE_IP" "BASE_SSH_TARGET"
        "MAIN_SESSION_NAME" "EF_SESSION_NAME" "BASE_SESSION_NAME"
        "REMOTE_EF_SESSION_NAME" "REMOTE_BASE_SESSION_NAME"
        "ROS_BAG_INTERVAL" "ROS_BAG_PATH"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "Required configuration variable '$var' is not set"
            exit 1
        fi
    done
    
    # Validate SSH target format (should contain @)
    if [[ ! "$EF_SSH_TARGET" =~ .+@.+ ]]; then
        log_error "EF_SSH_TARGET must be in format 'username@ip' (current: $EF_SSH_TARGET)"
        exit 1
    fi
    
    if [[ ! "$BASE_SSH_TARGET" =~ .+@.+ ]]; then
        log_error "BASE_SSH_TARGET must be in format 'username@ip' (current: $BASE_SSH_TARGET)"
        exit 1
    fi
    
    log_info "Configuration validation passed"
    log_info "EF Device: $EF_DEVICE_NAME ($EF_SSH_TARGET)"
    log_info "Base Device: $BASE_DEVICE_NAME ($BASE_SSH_TARGET)"
}

update_config() {
    local key="$1"
    local value="$2"
    local config_file="$SCRIPT_DIR/config/settings.conf"
    
    # Update the configuration file
    if grep -q "^$key=" "$config_file"; then
        sed -i "s/^$key=.*/$key=\"$value\"/" "$config_file"
    else
        echo "$key=\"$value\"" >> "$config_file"
    fi
    
    # Update the current session
    declare -g "$key"="$value"
    
    log_info "Configuration updated: $key=$value"
}

get_config() {
    local key="$1"
    echo "${!key}"
}

save_user_settings() {
    local settings_file="$SCRIPT_DIR/config/user_settings.conf"
    
    cat > "$settings_file" << EOF
# User customized settings
# Last updated: $(date)

ROS_BAG_INTERVAL="$ROS_BAG_INTERVAL"
ROS_BAG_PATH="$ROS_BAG_PATH"
LOG_LEVEL="$LOG_LEVEL"
EOF

    log_info "User settings saved to $settings_file"
}