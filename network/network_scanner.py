import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import netifaces
import ipaddress
import json
import subprocess
import re
import time
from datetime import datetime
import socket
import platform
import asyncio
import random

class NetworkScannerNode(Node):
    def __init__(self):
        super().__init__('network_scanner')
        
        # Declare test_mode parameter
        self.declare_parameter('test_mode', False)
        self.test_mode = self.get_parameter('test_mode').value
        
        # Create publishers
        self.base_publisher = self.create_publisher(String, 'connection/base/ip', 10)
        self.end_effector_publisher = self.create_publisher(String, 'connection/ef/ip', 10)
        self.base_signal_publisher = self.create_publisher(String, 'connection/base/signal', 10)
        self.ee_signal_publisher = self.create_publisher(String, 'connection/ef/signal', 10)
        
        # Set scanning interval (in seconds)
        self.scan_interval = 8
        
        # Load device configuration
        self.devices = self.load_devices()
        
        # Cache for MAC addresses
        self.mac_cache = {}
        
        # Create timer for periodic scanning
        self.timer = self.create_timer(self.scan_interval, self.scan_callback)
        
        self.get_logger().info(f'Network Scanner Node started (test_mode: {self.test_mode})')

    def generate_random_ip(self):
        """Generate a random IP address in the format 192.168.1.X"""
        return f"192.168.10.{random.randint(2, 254)}"

    def load_devices(self):
        try:
            with open('devices.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            self.get_logger().error("devices.json not found!")
            return None
        except json.JSONDecodeError:
            self.get_logger().error("Error reading devices.json - invalid JSON format!")
            return None

    def get_signal_strength(self, interface='wlo1'):
        try:
            if platform.system() == 'Linux':
                # Using iwconfig instead of iw (usually doesn't require sudo)
                cmd = f"iwconfig {interface}"
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                match = re.search(r'Signal level=(-\d+)', result.stdout)
                if match:
                    return int(match.group(1))
            elif platform.system() == 'Darwin':  # macOS
                cmd = f"/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                match = re.search(r'agrCtlRSSI: (-\d+)', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception as e:
            self.get_logger().debug(f"Signal strength error: {e}")
        return None

    def get_current_network(self):
        try:
            gateways = netifaces.gateways()
            if 'default' in gateways and netifaces.AF_INET in gateways['default']:
                default_interface = gateways['default'][netifaces.AF_INET][1]
            else:
                for interface in netifaces.interfaces():
                    if interface != 'lo':
                        default_interface = interface
                        break
            
            interface_details = netifaces.ifaddresses(default_interface)
            if netifaces.AF_INET in interface_details:
                ip_info = interface_details[netifaces.AF_INET][0]
                ip = ip_info['addr']
                netmask = ip_info['netmask']
                network = ipaddress.IPv4Network(f'{ip}/{netmask}', strict=False)
                return str(network), default_interface
        except Exception as e:
            self.get_logger().error(f"Network detection error: {e}")
        return None, None

    async def check_host(self, ip):
        """Check if a host is up using TCP connection to common ports."""
        common_ports = [22, 80, 443, 8080]  # Add other common ports if needed
        for port in common_ports:
            try:
                # Set a short timeout for the connection attempt
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=0.5
                )
                writer.close()
                await writer.wait_closed()
                return True
            except:
                continue
        return False

    def get_mac_from_arp(self, ip):
        """Get MAC address from ARP cache (no sudo required)."""
        if ip in self.mac_cache:
            return self.mac_cache[ip]

        try:
            if platform.system() == "Linux":
                cmd = ["arp", "-n", ip]
            elif platform.system() == "Darwin":  # macOS
                cmd = ["arp", ip]
            else:
                return None

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                mac_matches = re.findall(r'([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})', result.stdout)
                if mac_matches:
                    mac = mac_matches[0].lower()
                    self.mac_cache[ip] = mac
                    return mac
        except Exception as e:
            self.get_logger().debug(f"Error getting MAC: {e}")
        return None

    async def scan_network(self, target_mac):
        network_range, interface = self.get_current_network()
        if not network_range:
            return None, None

        try:
            network = ipaddress.IPv4Network(network_range)
            target_mac = target_mac.lower()

            # Scan all IPs in the network
            tasks = []
            for ip in network.hosts():
                ip_str = str(ip)
                tasks.append(self.check_host(ip_str))

            # Wait for all scans to complete
            results = await asyncio.gather(*tasks)

            # Check MAC addresses of responding hosts
            for ip, is_up in zip(network.hosts(), results):
                if is_up:
                    mac = self.get_mac_from_arp(str(ip))
                    if mac and mac == target_mac:
                        signal = self.get_signal_strength(interface)
                        return str(ip), signal

        except Exception as e:
            self.get_logger().error(f"Scan error: {e}")
        
        return None, None

    async def scan_system(self, system_config):
        if self.test_mode:
            # In test mode, randomly decide if device is found (80% chance)
            if random.random() < 0.8:
                return {
                    'device': system_config['primary']['name'],
                    'mac': system_config['primary']['mac'],
                    'ip': self.generate_random_ip(),
                    'signal': random.randint(-70, -30),  # Random signal strength between -70 and -30 dBm
                    'type': 'primary'
                }
            # 20% chance to fall back to secondary device
            elif random.random() < 0.5:
                return {
                    'device': system_config['fallback']['name'],
                    'mac': system_config['fallback']['mac'],
                    'ip': self.generate_random_ip(),
                    'signal': random.randint(-80, -40),  # Slightly worse signal for fallback
                    'type': 'fallback'
                }
            return None
        # Try primary device first
        ip, signal = await self.scan_network(system_config['primary']['mac'])
        if ip:
            return {
                'device': system_config['primary']['name'],
                'mac': system_config['primary']['mac'],
                'ip': ip,
                'signal': signal,
                'type': 'primary'
            }
        
        # If primary not found, try fallback
        ip, signal = await self.scan_network(system_config['fallback']['mac'])
        if ip:
            return {
                'device': system_config['fallback']['name'],
                'mac': system_config['fallback']['mac'],
                'ip': ip,
                'signal': signal,
                'type': 'fallback'
            }
        
        return None

    def scan_callback(self):
        if not self.devices:
            return

        async def async_scan():
            # Scan base system
            base_result = await self.scan_system(self.devices['base_system'])
            if base_result:
                msg = String()
                msg.data = base_result['ip']
                self.base_publisher.publish(msg)
                self.get_logger().info(f"Base System: {base_result['ip']} via {base_result['type']}")
            else:
                self.get_logger().warn("Base System: Not Found")
                msg = String()
                msg.data = 'Not Found'
                self.base_publisher.publish(msg)

            # Scan end effector system
            ee_result = await self.scan_system(self.devices['end_effector_system'])
            if ee_result:
                msg = String()
                msg.data = ee_result['ip']
                self.end_effector_publisher.publish(msg)
                self.get_logger().info(f"End Effector: {ee_result['ip']} via {ee_result['type']}")
            else:
                self.get_logger().warn("End Effector: Not Found")
                msg = String()
                msg.data = 'Not Found'
                self.end_effector_publisher.publish(msg)

        # Run the async scan in the event loop
        asyncio.run(async_scan())

def main(args=None):
    rclpy.init(args=args)
    network_scanner = NetworkScannerNode()
    
    try:
        rclpy.spin(network_scanner)
    except KeyboardInterrupt:
        pass
    finally:
        network_scanner.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()