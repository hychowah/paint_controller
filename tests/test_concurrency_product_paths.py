"""Product-path concurrency contracts (auditor must-haves beyond pure mailbox tests).

Covers:
- SafetyCoordinator + real RosCommandBus + live continuous enqueue via bound WheelController
- ControlProcessor honors continuous_motion_allowed latch after halt
- WindMonitor residual fence (not on TD-056 bridge)
"""

from __future__ import annotations

import importlib
import threading

from paint_controller.core.ros_io import RosCommandBus
from paint_controller.handlers.safety_coordinator import SafetyCoordinator
from paint_controller.utils.constants import HeartbeatStatus
from tests.fakes import FakeEsp32Valve, FakeLogger, FakeStateStore, FakeTeensy


def _wheel_cls():
    return importlib.import_module("paint_controller.controllers.wheel_shell").WheelController


def _control_processor_cls():
    return importlib.import_module("paint_controller.handlers.control_processor").ControlProcessor


def test_halt_with_bus_and_live_wheel_continuous_enqueue(qt_app, fake_node) -> None:
    """Product halt path: live teleop workers + SafetyCoordinator + command bus.

    Asserts:
    - continuous_motion_allowed latches False
    - pending continuous scrubbed (invalidate)
    - wheel emergency_stop enqueues continuous zero (still continuous kind)
    - after halt, ControlProcessor must not re-command wheel while latched
    """
    from tests.fakes import FakeHeartbeatHandler, FakeOverlay, FakeWinch

    bus = RosCommandBus()
    wheel = _wheel_cls()(fake_node, command_bus=bus)
    speed_pub = fake_node.publishers[0]
    state = FakeStateStore()
    coordinator = SafetyCoordinator(
        winch=FakeWinch(),
        teensy=FakeTeensy(),
        wheel=wheel,
        esp32_valve=FakeEsp32Valve(),
        state_store=state,
        logger=FakeLogger(),
        command_bus=bus,
    )

    errors: list[BaseException] = []
    stop = threading.Event()
    start = threading.Barrier(3)  # 2 workers + main

    def teleop_worker(n: int) -> None:
        try:
            start.wait(timeout=5.0)
            while not stop.is_set():
                # Direct device command path (as teleop would when latch open).
                wheel.command_speed(100 + n, -(50 + n))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=teleop_worker, args=(t,), name=f"teleop-{t}") for t in range(2)]
    for t in threads:
        t.start()

    start.wait(timeout=5.0)

    # Product halt while workers still live.
    coordinator.halt_all_effectors("e-stop product path")
    assert coordinator.continuous_motion_allowed is False
    assert state.controller_heartbeat_state == HeartbeatStatus.ERROR.value
    # Continuous pending scrubbed at halt; emergency_stop may re-enqueue continuous zero.
    oneshot_n, cont_n = bus.pending_counts()
    assert oneshot_n == 0
    assert cont_n <= 1

    stop.set()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()
    assert errors == []

    # Final scrub of any post-halt worker continuous, then re-assert halt zero.
    bus.invalidate_continuous()
    wheel.emergency_stop()
    assert bus.pump() >= 1
    assert speed_pub.published_messages, "halt zero should raw-publish after pump"
    last = speed_pub.published_messages[-1]
    assert last.left_rpm == 0
    assert last.right_rpm == 0

    # Teleop facade must not re-command while latched.
    class _CmdWheel:
        def __init__(self) -> None:
            self.calls: list[tuple[int, int]] = []

        def command_speed(self, left: int, right: int) -> bool:
            self.calls.append((left, right))
            return True

        def command_left_wheel_speed(self, speed: float) -> bool:
            return self.command_speed(int(speed), 0)

        def command_right_wheel_speed(self, speed: float) -> bool:
            return self.command_speed(0, int(speed))

        def command_position(self, *args, **kwargs) -> bool:
            return True

    cmd_wheel = _CmdWheel()
    overlay = FakeOverlay(left="Track Control Left", right="None")
    cp = _control_processor_cls()(
        wheel=cmd_wheel,
        winch=FakeWinch(),
        teensy=FakeTeensy(),
        esp32_valve=FakeEsp32Valve(),
        selection_model=overlay,
        heartbeat_handler=FakeHeartbeatHandler(),
        settings_manager=None,
        state_store=state,
        safety_coordinator=coordinator,
    )
    cp.process_input(
        {
            "left_stick": {"y": 20000, "x": 0},
            "right_stick": {"y": 0, "x": 0},
            "triggers": {"left": 0, "right": 0},
        }
    )
    assert cmd_wheel.calls == [], "latched continuous teleop must not re-command wheel"


def test_wind_monitor_residual_mutates_on_calling_thread(qt_app, fake_node) -> None:
    """RESIDUAL fence: WindMonitor is not on RosTelemetryBridge (TD-056).

    Unlike wheel/winch/teensy, ROS callbacks mutate fields and emit on the
    *calling* thread. This test documents that residual so Level C / "all
    ROS→Qt marshaled" claims cannot silently assume wind is covered.

    When Wind is migrated to RosTelemetryBridge, invert this test to the
    deferred-apply pattern used by ``test_status_callback_from_worker_thread_*``.
    """
    import threading

    from std_msgs.msg import Float32

    WindMonitor = importlib.import_module("paint_controller.controllers.wind_monitor").WindMonitor
    monitor = WindMonitor(fake_node)
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            msg = Float32()
            msg.data = 12.5
            monitor._speed_callback(msg)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="wind-residual-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []

    # Residual behavior: mutation already visible without processEvents.
    assert monitor.windSpeed == 12.5
    # processEvents is not required for the residual path (contrast device affinity tests).
    qt_app.processEvents()
    assert monitor.windSpeed == 12.5
