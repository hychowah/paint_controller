"""ROS pub/sub integration tests for paint_controller.controllers.winch.

Runs the real rclpy path in a **subprocess** so a poisoned process-global
rclpy context from earlier suite tests cannot abort the parent pytest process.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

rclpy = pytest.importorskip("rclpy")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYTHON = sys.executable


def test_speed_command_reaches_real_ros_subscriber(qt_app) -> None:
    """Winch speed command is received by a real ROS subscription (subprocess)."""
    script = textwrap.dedent(
        """
        import importlib
        import time
        import uuid

        import rclpy
        from rclpy.node import Node
        from std_msgs.msg import Float64

        def main() -> int:
            if not rclpy.ok():
                rclpy.init()
            controller_node = Node(f"winch_controller_test_pub_{uuid.uuid4().hex}")
            subscriber_node = Node(f"winch_controller_test_sub_{uuid.uuid4().hex}")
            WinchController = importlib.import_module(
                "paint_controller.controllers.winch_shell"
            ).WinchController
            controller = WinchController(controller_node)
            controller.set_available(True)
            received = []

            subscription = subscriber_node.create_subscription(
                Float64,
                "winch/move/speed/mmps/cmd",
                lambda message: received.append(message.data),
                10,
            )
            try:
                assert controller.command_speed_mmps(125.0) is True
                deadline = time.monotonic() + 1.0
                while not received and time.monotonic() < deadline:
                    rclpy.spin_once(controller_node, timeout_sec=0.05)
                    rclpy.spin_once(subscriber_node, timeout_sec=0.05)
                assert received == [125.0], received
            finally:
                controller.cleanup()
                subscriber_node.destroy_subscription(subscription)
                controller_node.destroy_node()
                subscriber_node.destroy_node()
                if rclpy.ok():
                    rclpy.shutdown()
            return 0

        raise SystemExit(main())
        """
    )
    env = os.environ.copy()
    # Ensure package import resolves to this workspace tree.
    py_path = str(_REPO_ROOT / "python")
    env["PYTHONPATH"] = py_path + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["QT_QPA_PLATFORM"] = "offscreen"
    proc = subprocess.run(
        [_PYTHON, "-c", script],
        cwd=str(_REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, (
        f"subprocess failed rc={proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
