import nmap
import argparse
import logging
from datetime import datetime
import socket
import sys
from typing import List, Dict

class NetworkScanner:
    def __init__(self, network_range: str):
        """Initialize NetworkScanner with network range and setup logging"""
        self.network_range = network_range
        self.nm = nmap.PortScanner()
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging to file and console"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'network_scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def validate_network_range(self) -> bool:
        """Validate if the network range is properly formatted"""
        try:
            # Split the range into base and range parts
            base = self.network_range.split('.')[0:3]
            if len(base) != 3:
                return False
            
            # Validate each octet
            for octet in base:
                if not (0 <= int(octet) <= 255):
                    return False
            
            return True
        except Exception as e:
            logging.error(f"Invalid network range: {str(e)}")
            return False
    
    def scan_network(self) -> Dict:
        """Perform network scan and return results"""
        if not self.validate_network_range():
            raise ValueError("Invalid network range provided")
        
        logging.info(f"Starting scan of network range: {self.network_range}")
        try:
            # Perform the scan
            self.nm.scan(hosts=self.network_range, arguments='-sP')
            
            # Process results
            results = {}
            for host in self.nm.all_hosts():
                try:
                    hostname = socket.gethostbyaddr(host)[0]
                except socket.herror:
                    hostname = "Unknown"
                
                results[host] = {
                    'hostname': hostname,
                    'state': self.nm[host].state(),
                }
            
            return results
        
        except Exception as e:
            logging.error(f"Scan failed: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Network Scanner Tool')
    parser.add_argument('network_range', help='Network range to scan (e.g., 192.168.1.0/24)')
    parser.add_argument('--output', help='Output file for results', default=None)
    args = parser.parse_args()
    
    try:
        scanner = NetworkScanner(args.network_range)
        results = scanner.scan_network()
        
        # Print results
        print("\nScan Results:")
        print("-" * 60)
        for ip, data in results.items():
            print(f"IP: {ip}")
            print(f"Hostname: {data['hostname']}")
            print(f"State: {data['state']}")
            print("-" * 60)
        
        # Save to file if specified
        if args.output:
            with open(args.output, 'w') as f:
                for ip, data in results.items():
                    f.write(f"IP: {ip}\n")
                    f.write(f"Hostname: {data['hostname']}\n")
                    f.write(f"State: {data['state']}\n")
                    f.write("-" * 60 + "\n")
            
            print(f"\nResults saved to {args.output}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()