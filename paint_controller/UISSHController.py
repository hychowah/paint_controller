from PySide6.QtCore import QObject, Slot
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
    def __init__(self, robot_controller, parent=None):
        super().__init__(parent)
        self.robot_controller = robot_controller

        # Store config paths instead of content
        config_dir = os.path.join(os.getcwd(), "config")
        self.ssh_path = os.path.join(config_dir, "ssh_config.json")
        self.bash_path = os.path.join(config_dir, "bash_config.json")

    def _load_json_file(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[UISSHController] Failed to load JSON config from {path}: {e}")
            return {}

    def _load_ssh_config(self, path):
        ssh_config = self._load_json_file(path)
        return {
            name: SSHLauncher(**info)
            for name, info in ssh_config.items()
        }

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
