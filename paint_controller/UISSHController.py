from PySide6.QtCore import QObject, Slot
import os
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
    def __init__(self, parent=None):
        super().__init__(parent)

        # Step 1: Define remote hosts (per physical device)
        self.remote_hosts = {
            "BASE": SSHLauncher(hostname="192.168.1.106", username="c3-pc01", password="312213"),
            "END_EFFECTOR": SSHLauncher(hostname="192.168.1.133", username="sparyrobot", password="C3robotics"),
        }

        # Step 2: Define commands per service on each host
        self.command_map = {
            "BASE": {
                "Winch": {
                    "start": (
                        "bash -c 'source /opt/ros/jazzy/setup.bash && "
                        "source ~/ros2_ws/install/setup.bash && export ROS_DOMAIN_ID=2 && "
                        "cd ~/ros2_ws/src/paint_base/paint_base/winch/python/ && "
                        "python3 winch_node.py --nosensor --port /dev/ttyUSB0'"
                    ),
                    "stop": "pkill -f winch_node.py && echo 'winch_node.py killed.'"
                },
                "Camera": {
                    "start": "...",
                    "stop": "..."
                }
            },
            "END_EFFECTOR": {
                "Camera": {
                    "start": (
                        "bash -c 'source ~/ros2_ws/src/paint_end_effector/start_cam.bash'"
                    ),
                    "stop": "pkill -f gst-launch-1.0 && echo 'GStreamer process killed.'"
                },
                "Teensy": {
                    "start": (
                        "bash -c 'source /opt/ros/humble/setup.bash && "
                        "source ~/ros2_ws/install/setup.bash && export ROS_DOMAIN_ID=2 && "
                        "cd ~/ros2_ws/src/paint_base/paint_base/winch/python/ && "
                        "python3 winch_node.py --nosensor --port /dev/ttyUSB0'"
                    ),
                    "stop": "..."
                }
            }
        }

    @Slot(str, str, str)
    def handle_device_command(self, device_name: str, service_name: str, action: str):
        print(f"[UISSHController] Handling {action.upper()} for {service_name} on {device_name}")

        launcher = self.remote_hosts.get(device_name)
        if not launcher:
            print(f"[UISSHController] ERROR: Unknown device '{device_name}'")
            return

        service_commands = self.command_map.get(device_name, {}).get(service_name)
        if not service_commands:
            print(f"[UISSHController] ERROR: '{service_name}' not defined on device '{device_name}'")
            return

        command = service_commands.get(action)
        if not command:
            print(f"[UISSHController] ERROR: No '{action}' command for {service_name} on {device_name}")
            return

        def callback(stdout, stderr):
            print(f"[{device_name}] {service_name} {action.upper()} complete")
            if stderr:
                print(f"[{device_name}] STDERR:\n{stderr.strip()}")
            else:
                print(f"[{device_name}] STDOUT:\n{stdout.strip() or 'Done.'}")

        launcher.run_script(command, callback)
