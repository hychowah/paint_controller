from PySide6.QtCore import QObject, Slot, Signal
import os
import json
import paramiko
import threading

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
                print(f"[SSHLauncher] STDERR:\n{err}")

                client.close()
                if callback:
                    callback(out, err)
            except Exception as e:
                print(f"[SSHLauncher] Exception: {e}")
                if callback:
                    callback("", str(e))

        threading.Thread(target=_execute).start()


class UISSHController(QObject):
    # Signals for QML
    configUpdated = Signal(str, str)  # Signal when config is updated
    
    def __init__(self, robot_controller, parent=None):
        super().__init__(parent)
        self.robot_controller = robot_controller

        # Store config paths instead of content
        config_dir = os.path.join(os.getcwd(), "config")
        self.ssh_path = os.path.join(config_dir, "ssh_config.json")
        self.bash_path = os.path.join(config_dir, "bash_config.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)

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

    @Slot(str, result=str)
    def get_device_config(self, device_name: str):
        """Get the current configuration for a device as JSON string"""
        ssh_config = self._load_json_file(self.ssh_path)
        device_config = ssh_config.get(device_name, {})
        
        # Return relevant fields for the UI
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
        # Reload configs on every command
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