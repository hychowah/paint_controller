from PySide6.QtCore import QObject, Slot, Signal, QTimer, Property, QRunnable, QThreadPool
import logging
import os
import json
import tempfile
import paramiko
import threading
import subprocess
import time
import platform

logger = logging.getLogger(__name__)


def _fsync_parent_directory(path: str) -> None:
    if not hasattr(os, "O_DIRECTORY"):
        return

    directory_fd = os.open(os.path.dirname(path), os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_json(path: str, data, *, indent: int) -> None:
    temp_path = None
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=f".{os.path.basename(path)}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = handle.name
            json.dump(data, handle, indent=indent)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, path)
        _fsync_parent_directory(path)
    except Exception:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

class SSHLauncher:
    def __init__(self, hostname, username, password=None, key_path=None, port=22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.key_path = os.path.expanduser(key_path) if key_path else None
        self.port = port

    def run_script(self, command, callback=None):
        def _execute():
            logger.info("Connecting to %s@%s:%s", self.username, self.hostname, self.port)
            client = None
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                if self.key_path:
                    logger.info("Using private key: %s", self.key_path)
                    key = paramiko.RSAKey.from_private_key_file(self.key_path)
                    client.connect(
                        self.hostname,
                        port=self.port,
                        username=self.username,
                        pkey=key,
                        timeout=5,
                        banner_timeout=5,
                        auth_timeout=5,
                    )
                else:
                    logger.info("Using password authentication")
                    client.connect(
                        self.hostname,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        timeout=5,
                        banner_timeout=5,
                        auth_timeout=5,
                    )

                logger.info("Executing command:\n%s", command)
                stdin, stdout, stderr = client.exec_command(command)
                out = stdout.read().decode()
                err = stderr.read().decode()
                logger.info("STDOUT:\n%s", out)
                logger.info("STDERR:\n%s", err)

                if callback:
                    callback(out, err)
            except Exception as e:
                logger.error("SSH exception: %s", e)
                if callback:
                    callback("", str(e))
            finally:
                if client is not None:
                    client.close()

        thread = threading.Thread(target=_execute, daemon=True)
        thread.start()
        return thread

class AvailabilityCheckRunnable(QRunnable):
    def __init__(self, device_name, hostname, timeout, callback):
        super().__init__()
        self.device_name = device_name
        self.hostname = hostname
        self.timeout = timeout
        self.callback = callback

    def run(self):
        try:
            # Determine ping command based on OS
            param = "-n" if platform.system().lower() == "windows" else "-c"
            
            # Run ping command with timeout
            cmd = ["ping", param, "1", "-W", str(int(self.timeout * 1000)), self.hostname]
            result = subprocess.run(cmd, capture_output=True, timeout=self.timeout + 1)
            
            is_available = result.returncode == 0
            
            # Extract ping time from output
            ping_time = None
            if is_available:
                output = result.stdout.decode()
                # Try to extract ping time (format varies by OS, looking for "time=X.XXms" or "time < X.XXms")
                import re
                match = re.search(r'time[<=\s]+([0-9.]+)\s*ms', output, re.IGNORECASE)
                if match:
                    try:
                        ping_time = float(match.group(1))
                    except ValueError:
                        ping_time = None
            
            message = f"Device {self.device_name} checked at {time.strftime('%H:%M:%S')}: {'Available' if is_available else 'Unavailable'}"
            if is_available and ping_time is not None:
                message += f" ({ping_time:.2f}ms)"

            self.callback(self.device_name, is_available, message, ping_time if ping_time is not None else 0)

        except Exception as e:
            self.callback(self.device_name, False, f"{self.device_name} check failed: {str(e)}", 0)

class UISSHController(QObject):
    # Signals for QML
    configUpdated = Signal(str, str)  # Signal when config is updated
    deviceAvailable = Signal(str, bool, str)  # device_name, is_available, message
    devicePingTime = Signal(str, float)  # device_name, ping_time_ms
    deviceAvailabilityChanged = Signal()
    availabilityResultReady = Signal(str, bool, str, float)
    commandResultReady = Signal(str, str, str, str)

    def __init__(self, show_popup_fn=None, parent=None):
        super().__init__(parent)
        self._show_popup_fn = show_popup_fn
        self.thread_pool = QThreadPool.globalInstance()
        self._deviceAvailability = {}  # Backing store for device_availability property: {device_name: bool}
        self._devicePingTimes = {}  # Backing store for ping times: {device_name: float}
        self._is_cleaning_up = False  # Flag to prevent signal emission during cleanup
        self._command_threads = []
        self.availabilityResultReady.connect(self._handle_availability_result)
        self.commandResultReady.connect(self._handle_command_result)

        # Store config paths - resolve to absolute path
        config_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config"))
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
            logger.error("Failed to load JSON config from %s: %s", path, e)
            return {}

    def _save_json_file(self, path, data):
        try:
            _atomic_write_json(path, data, indent=4)
            return True
        except Exception as e:
            logger.error("Failed to save JSON config to %s: %s", path, e)
            return False

    def _prune_command_threads(self):
        self._command_threads = [thread for thread in self._command_threads if thread.is_alive()]

    def _load_ssh_config(self, path):
        ssh_config = self._load_json_file(path)
        return {
            name: SSHLauncher(**info)
            for name, info in ssh_config.items()
        }

    @Slot(str, bool, str, float)
    def _handle_availability_result(self, device_name: str, is_available: bool, message: str, ping_time: float):
        if self._is_cleaning_up:
            return

        self._deviceAvailability[device_name] = is_available
        self._devicePingTimes[device_name] = ping_time
        self.deviceAvailabilityChanged.emit()
        self.deviceAvailable.emit(device_name, is_available, message)
        self.devicePingTime.emit(device_name, ping_time)

    @Slot(str, str, str, str)
    def _handle_command_result(self, device_name: str, command: str, stdout: str, stderr: str):
        if self._show_popup_fn:
            self._show_popup_fn(
                title="Device Command",
                message=f"Command executed on {device_name}:\n{command}",
                popup_type="info"
            )
        if stderr:
            logger.warning("[%s] STDERR:\n%s", device_name, stderr.strip())
        else:
            logger.info("[%s] STDOUT:\n%s", device_name, stdout.strip() or 'Done.')

    def _check_device_availability(self, device_name: str, hostname: str, port: int = 22, timeout: float = 0.5):
        def handle_result(name, is_available, message, ping_time):
            # Skip if cleanup is in progress - object may be deleted
            if self._is_cleaning_up:
                return

            try:
                self.availabilityResultReady.emit(name, is_available, message, ping_time)
            except RuntimeError as e:
                if "already deleted" in str(e):
                    logger.debug("Object being destroyed, skipping signal emission for %s", name)
                else:
                    raise

        runnable = AvailabilityCheckRunnable(device_name, hostname, timeout, handle_result)
        self.thread_pool.start(runnable)

    def _start_all_availability_checks(self):
        """Start periodic availability checks for all devices in ssh_config.json."""
        ssh_config = self._load_json_file(self.ssh_path)
        for index, (device_name, device_config) in enumerate(ssh_config.items()):
            if not device_config or not device_config.get("hostname"):
                self.deviceAvailable.emit(device_name, False, f"Invalid configuration for {device_name}")
                logger.warning("Cannot start check for %s: Invalid config", device_name)
                continue
            
            hostname = device_config["hostname"]
            
            if device_name in self.availability_timers:
                logger.info("Availability check already running for %s", device_name)
                continue
            
            timer = QTimer(self)
            timer.timeout.connect(lambda name=device_name, host=hostname: self._check_device_availability(name, host))
            timer.start(1000 + index * 200)  # Stagger checks by 200ms per device
            self.availability_timers[device_name] = timer

    def _stop_all_availability_checks(self):
        """Stop all periodic availability checks and clear timers."""
        for device_name, timer in list(self.availability_timers.items()):
            timer.stop()
            timer.deleteLater()
            logger.info("Stopped availability check for %s", device_name)
        self.availability_timers.clear()

    def _get_deviceAvailability(self):
        return self._deviceAvailability

    deviceAvailability = Property('QVariantMap', _get_deviceAvailability, notify=deviceAvailabilityChanged)

    def _get_devicePingTimes(self):
        return self._devicePingTimes

    devicePingTimes = Property('QVariantMap', _get_devicePingTimes, notify=deviceAvailabilityChanged)

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

            logger.info("Updating config for %s with IP: %s, Port: %s, Username: %s, Key Path: %s", device_name, ip, port, username, key_path)
            
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
                logger.info("Updated config for %s", device_name)
                self.configUpdated.emit(device_name, "Configuration updated successfully")
                
                # Show success popup
                if self._show_popup_fn:
                    self._show_popup_fn(
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

                # Restart timer with updated config
                timer = QTimer(self)
                timer.timeout.connect(lambda name=device_name, host=hostname: self._check_device_availability(name, host))
                timer.start(1000)  # Optional: make interval configurable
                self.availability_timers[device_name] = timer
                return True
            else:
                if self._show_popup_fn:
                    self._show_popup_fn(
                        title="Configuration Error",
                        message=f"Failed to save {device_name} settings",
                        popup_type="error"
                    )
                return False
                
        except Exception as e:
            logger.error("Error updating config for %s: %s", device_name, e)
            if self._show_popup_fn:
                self._show_popup_fn(
                    title="Configuration Error", 
                    message=f"Error updating {device_name}: {str(e)}",
                    popup_type="error"
                )
            return False

    @Slot(str, str, str)
    def handle_device_command(self, device_name: str, service_name: str, action: str):
        remote_hosts = self._load_ssh_config(self.ssh_path)
        command_map = self._load_json_file(self.bash_path)

        if self._show_popup_fn:
            self._show_popup_fn(
                title="Device Command",
                message=f"Handling {action.upper()} for {service_name} on {device_name}",
                popup_type="info"
            )

        launcher = remote_hosts.get(device_name)
        if not launcher:
            logger.error("Unknown device '%s'", device_name)
            return

        service_commands = command_map.get(device_name, {}).get(service_name)
        if not service_commands:
            logger.error("'%s' not defined on device '%s'", service_name, device_name)
            return

        command = service_commands.get(action)
        if not command:
            logger.error("No '%s' command for %s on %s", action, service_name, device_name)
            return

        def callback(stdout, stderr):
            self.commandResultReady.emit(device_name, command, stdout, stderr)

        thread = launcher.run_script(command, callback)
        self._command_threads.append(thread)
        self._prune_command_threads()

    def cleanup(self):
        """Cleanup SSH controller resources"""
        self._is_cleaning_up = True
        self._stop_all_availability_checks()
        self._prune_command_threads()
        for thread in self._command_threads:
            thread.join(timeout=2)
        self._command_threads.clear()
        logger.info("Cleanup complete")