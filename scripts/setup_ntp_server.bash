#!/bin/bash
set -e

# ===== Configuration =====
NTP_POOLS="pool.ntp.org"  # External time sources

# ===== Detect current network subnet =====
echo "Detecting current network subnet..."

# Get primary interface (excluding loopback)
PRIMARY_INTERFACE=$(ip -o -4 route show to default | awk '{print $5}' | head -n1)

if [ -z "$PRIMARY_INTERFACE" ]; then
    echo "Could not determine primary network interface."
    read -p "Enter network interface manually (e.g., eth0, wlan0): " MANUAL_INTERFACE
    
    if [ -z "$MANUAL_INTERFACE" ]; then
        echo "No interface provided. Exiting."
        exit 1
    fi
    
    PRIMARY_INTERFACE="$MANUAL_INTERFACE"
fi

echo "Using interface: $PRIMARY_INTERFACE"

# Get IP and netmask of the primary interface
IP_INFO=$(ip -o -4 addr show dev "$PRIMARY_INTERFACE" | awk '{print $4}')

if [ -z "$IP_INFO" ]; then
    echo "Could not determine IP information for interface $PRIMARY_INTERFACE."
    read -p "Enter network subnet manually (e.g., 192.168.1.0/24): " MANUAL_SUBNET
    
    if [ -z "$MANUAL_SUBNET" ]; then
        echo "No subnet provided. Exiting."
        exit 1
    fi
    
    NETWORK_SUBNET="$MANUAL_SUBNET"
else
    # Extract IP and CIDR
    IP_ADDR=$(echo "$IP_INFO" | cut -d/ -f1)
    CIDR=$(echo "$IP_INFO" | cut -d/ -f2)
    
    # Calculate the network address
    IFS=. read -r i1 i2 i3 i4 <<< "$IP_ADDR"
    
    # Convert netmask to network address
    if [ "$CIDR" -eq 24 ]; then
        NETWORK_SUBNET="$i1.$i2.$i3.0/24"
    elif [ "$CIDR" -eq 16 ]; then
        NETWORK_SUBNET="$i1.$i2.0.0/16"
    elif [ "$CIDR" -eq 8 ]; then
        NETWORK_SUBNET="$i1.0.0.0/8"
    else
        # For other subnet sizes, ask for manual confirmation
        SUGGESTED_SUBNET="$i1.$i2.$i3.0/24"
        echo "Detected subnet: $SUGGESTED_SUBNET (This might not be accurate)"
        read -p "Use this subnet? (Y/n): " CONFIRM
        
        if [[ "$CONFIRM" == [Nn]* ]]; then
            read -p "Enter network subnet manually: " MANUAL_SUBNET
            NETWORK_SUBNET="$MANUAL_SUBNET"
        else
            NETWORK_SUBNET="$SUGGESTED_SUBNET"
        fi
    fi
fi

echo "Using network subnet: $NETWORK_SUBNET"

# Check if chrony is installed
if ! command -v chronyc &> /dev/null; then
    echo "Chrony not found. Installing..."
    sudo apt update && sudo apt install -y chrony
fi

# ===== Configure Chrony =====
echo "Configuring NTP server..."
sudo bash -c "cat > /etc/chrony/chrony.conf << EOF
# Server Configuration
pool $NTP_POOLS iburst
allow $NETWORK_SUBNET
local stratum 10
makestep 1 3
keyfile /etc/chrony/chrony.keys
driftfile /var/lib/chrony/chrony.drift
logdir /var/log/chrony
maxupdateskew 100.0
hwclockfile /etc/adjtime
rtcsync
EOF"

# ===== Firewall Rules (Only if ufw is installed) =====
if command -v ufw &> /dev/null; then
    echo "Configuring firewall..."
    sudo ufw allow 123/udp
    sudo ufw reload
else
    echo "UFW firewall not found, skipping firewall configuration."
    echo "Note: Make sure port 123/udp is allowed in your firewall if you have one."
fi

# ===== Restart Service =====
sudo systemctl restart chrony
sudo chronyc makestep

echo "NTP Server setup complete!"
echo "Check status: chronyc tracking && chronyc sources"
echo "Your NTP server is configured to allow clients from: $NETWORK_SUBNET"