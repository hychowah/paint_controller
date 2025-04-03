#!/bin/bash
set -e

# ===== Configuration =====
NETWORK_SUBNET="192.168.101.0/24"  # Change to your network subnet
NTP_POOLS="pool.ntp.org"          # External time sources if local NTP servers are not available

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

# ===== Firewall Rules =====
echo "Configuring firewall..."
sudo ufw allow 123/udp
sudo ufw reload

# ===== Restart Service =====
sudo systemctl restart chrony
sudo chronyc makestep

echo "NTP Server setup complete!"
echo "Check status: chronyc tracking && chronyc sources" 
