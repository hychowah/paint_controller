from PySide6.QtCore import QObject, Slot, Signal, QTimer, Property, QRunnable, QThreadPool
import os
import json
import paramiko
import threading
import socket
import time

class SSHLauncher:
    def __init__(self, hostname, username, password=None, key_path=None, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.port = port

    def run_script(self, command, callback=None):
        def _execute():
            print(f"[SSHLauncher] Connecting to {self.username}@{self.hostname}:{self.port}")
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.key_path:
                    print(f"[SSHLauncher] Using private key: {self.key_path}")
                    key = paramiko.RSAKey.from_private_key_file(self.key_path)
                    client.connect(self.hostname, port=self.port, username=self.username, pkey=key)
                else:
                    print("[SSHLauncher] Using password authentication")
                    client.connect(self.hostname, port=self.port, username=self.username, password=self.password)

                print(f"[SSHLauncher] Executing command:\n{command}")
                stdin, stdout, stderr = client.exec_command(command)
                out = stdout.read().decode()
                err = stderr.read().decode()
                print(f"[SSHLauncher] STDOUT:\n{out}")
                print(f"[UISSHController] STDERR:\n{err}")

                client.close()
                if callback:
                    callback(out, err)
            except Exception as e:
                print(f"[SSHLauncher] Exception: {e}")
                if callback:
                    callback("", str(e))

        threading.Thread(target=_execute).start()

class AvailabilityCheckRunnable(QRunnable):
    def __init__(self, device_name, hostname, port, timeout, callback):
        super().__init__()
        self.device_name = device_name
        self.hostname = hostname
        self.port = port
        self.timeout = timeout
        self.callback = callback

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            start_time = time.time()
            result = sock.connect_ex((self.hostname, self.port))
            sock.close()

            is_available = result == 0
            elapsed = time.time() - start_time
            message = f"Device {self.device_name} checked at {time.strftime('%H:%M:%S')}: {'Available' if is_available else 'Unavailable'}"
            if not is_available:
                message += f" (errno: {result})"

            self.callback(self.device_name, is_available, message, elapsed)

        except Exception as e:
            self.callback(self.device_name, False, f"{self.device_name} check failed: {str(e)}", 0)

class UISSHController(QObject):
    # Signals for QML
    configUpdated = Signal(str, str)  # Signal when config is updated
    deviceAvailable = Signal(str, bool, str)  # device_name, is_available, message
    deviceAvailabilityChanged = Signal()

    def __init__(self, robot_controller, parent=None):
        super().__init__(parent)
        self.robot_controller = robot_controller
        self.thread_pool = QThreadPool.globalInstance()
        self._deviceAvailability = {}  # Backing store for device_availability property: {device_name: bool}

        # Store config paths
        config_dir = os.path.join(os.getcwd(), "config")
        self.ssh_path = os.path.join(config_dir, "ssh_config.json")
        self.bash_path = os.path.join(config_dir, "bash_config.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)

        # Dictionary to store timers for each device
        self.availability_timers = {}

        # Start availability checks for all devices in ssh_config.json
        self._start_all_availability_checks()

    def _load_json_file(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[UISSHController] Failed to load JSON config from {path}: {e}")
            return {}

    def _save_json_file(self, path, data):
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"[UISSHController] Failed to save JSON config to {path}: {e}")
            return False

    def _load_ssh_config(self, path):
        ssh_config = self._load_json_file(path)
        return {
            name: SSHLauncher(**info)
            for name, info in ssh_config.items()
        }

    def _check_device_availability(self, device_name: str, hostname: str, port: int = 22, timeout: float = 0.5):
        def handle_result(name, is_available, message, elapsed):
            previous = self._deviceAvailability.get(name)
            self._deviceAvailability[name] = is_available
            if previous != is_available:
                self.deviceAvailabilityChanged.emit()
            self.deviceAvailable.emit(name, is_available, message)
            print(f"[UISSHController] {message} (check took {elapsed:.3f}s)")

        runnable = AvailabilityCheckRunnable(device_name, hostname, port, timeout, handle_result)
        self.thread_pool.start(runnable)

    def _start_all_availability_checks(self):
        """Start periodic availability checks for all devices in ssh_config.json."""
        ssh_config = self._load_json_file(self.ssh_path)
        for index, (device_name, device_config) in enumerate(ssh_config.items()):
            if not device_config or not device_config.get("hostname"):
                self.deviceAvailable.emit(device_name, False, f"Invalid configuration for {device_name}")
                print(f"[UISSHController] Cannot start check for {device_name}: Invalid config")
                continue
            
            hostname = device_config["hostname"]
            port = int(device_config.get("port", 22))
            
            if device_name in self.availability_timers:
                print(f"[UISSHController] Availability check already running for {device_name}")
                continue
            
            timer = QTimer(self)
            timer.timeout.connect(lambda name=device_name, host=hostname, p=port: self._check_device_availability(name, host, p))
            timer.start(1000 + index * 200)  # Stagger checks by 200ms per device
            self.availability_timers[device_name] = timer

    def _stop_all_availability_checks(self):
        """Stop all periodic availability checks and clear timers."""
        for device_name, timer in list(self.availability_timers.items()):
            timer.stop()
            timer.deleteLater()
            print(f"[UISSHController] Stopped availability check for {device_name}")
        self.availability_timers.clear()

    def _get_deviceAvailability(self):
        return self._deviceAvailability

    deviceAvailability = Property('QVariantMap', _get_deviceAvailability, notify=deviceAvailabilityChanged)

    @Slot(str, result=str)
    def get_device_config(self, device_name: str):
        """Get the current configuration for a device as JSON string"""
        ssh_config = self._load_json_file(self.ssh_path)
        device_config = ssh_config.get(device_name, {})
        
        ui_config = {
            "ip": device_config.get("hostname", ""),
            "port": str(device_config.get("port", 22)),
            "username": device_config.get("username", ""),
            "key_path": device_config.get("key_path", "")
        }
        
        return json.dumps(ui_config)

    @Slot(str, str, str, str, str)
    def update_device_config(self, device_name: str, ip: str, port: str, username: str, key_path: str):
        """Update device configuration and save to JSON file"""
        try:
            # Load existing config
            ssh_config = self._load_json_file(self.ssh_path)

            print(f"[UISSHController] Updating config for {device_name} with IP: {ip}, Port: {port}, Username: {username}, Key Path: {key_path}")
            
            # Update the device config
            if device_name not in ssh_config:
                ssh_config[device_name] = {}
            
            ssh_config[device_name]["hostname"] = ip
            ssh_config[device_name]["port"] = int(port) if port else 22
            ssh_config[device_name]["username"] = username
            
            # Only set key_path if provided
            if key_path.strip():
                ssh_config[device_name]["key_path"] = key_path
            elif "key_path" in ssh_config[device_name]:
                # Remove key_path if empty string provided
                del ssh_config[device_name]["key_path"]
            
            # Save updated config
            if self._save_json_file(self.ssh_path, ssh_config):
                print(f"[UISSHController] Updated config for {device_name}")
                self.configUpdated.emit(device_name, "Configuration updated successfully")
                
                # Show success popup
                self.robot_controller.show_popup(
                    title="Configuration Updated",
                    message=f"{device_name} settings have been saved successfully",
                    popup_type="success"
                )

                if device_name in self.availability_timers:
                    self.availability_timers[device_name].stop()
                    self.availability_timers[device_name].deleteLater()
                    del self.availability_timers[device_name]

                # Read updated config
                hostname = ip
                port_num = int(port) if port else 22

                # Restart timer with updated config
                timer = QTimer(self)
                timer.timeout.connect(lambda name=device_name, host=hostname, p=port_num: self._check_device_availability(name, host, p))
                timer.start(1000)  # Optional: make interval configurable
                self.availability_timers[device_name] = timer
                return True
            else:
                self.robot_controller.show_popup(
                    title="Configuration Error",
                    message=f"Failed to save {device_name} settings",
                    popup_type="error"
                )
                return False
                
        except Exception as e:
            print(f"[UISSHController] Error updating config for {device_name}: {e}")
            self.robot_controller.show_popup(
                title="Configuration Error", 
                message=f"Error updating {device_name}: {str(e)}",
                popup_type="error"
            )
            return False

    @Slot(str, str, str)
    def handle_device_command(self, device_name: str, service_name: str, action: str):
        remote_hosts = self._load_ssh_config(self.ssh_path)
        command_map = self._load_json_file(self.bash_path)

        self.robot_controller.show_popup(
            title="Device Command",
            message=f"Handling {action.upper()} for {service_name} on {device_name}",
            popup_type="info"
        )

        launcher = remote_hosts.get(device_name)
        if not launcher:
            print(f"[UISSHController] ERROR: Unknown device '{device_name}'")
            return

        service_commands = command_map.get(device_name, {}).get(service_name)
        if not service_commands:
            print(f"[UISSHController] ERROR: '{service_name}' not defined on device '{device_name}'")
            return

        command = service_commands.get(action)
        if not command:
            print(f"[UISSHController] ERROR: No '{action}' command for {service_name} on {device_name}")
            return

        def callback(stdout, stderr):
            self.robot_controller.show_popup(
                title="Device Command",
                message=f"Command executed on {device_name}:\n{command}",
                popup_type="info"
            )
            if stderr:
                print(f"[{device_name}] STDERR:\n{stderr.strip()}")
            else:
                print(f"[{device_name}] STDOUT:\n{stdout.strip() or 'Done.'}")

        launcher.run_script(command, callback)