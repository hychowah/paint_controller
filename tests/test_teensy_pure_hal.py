"""Level C P4: pure TeensyHal + shell timer/settings/bridge contracts."""

from __future__ import annotations

import threading

from paint_controller.controllers.teensy import TeensyHal
from paint_controller.ports.notifier import RecordingDeviceNotifier


def test_teensy_hal_notifies_status(fake_node) -> None:
    rec = RecordingDeviceNotifier()
    hal = TeensyHal(fake_node, notifier=rec)
    hal.setRelayEnabled(True)
    assert "status_changed" in rec.names
    assert any(n == "status_changed" for n in rec.names)


def test_teensy_shell_bridge_and_thrust_timer(qt_app, fake_node) -> None:
    from paint_controller.controllers.teensy_shell import TeensyController

    shell = TeensyController(fake_node)
    assert shell._telemetry.parent() is shell
    assert shell._thrust_ramp_timer.isActive()
    assert shell._watchdog is not None
    assert shell._watchdog.parent() is shell

    hits: list[object] = []
    shell.status_changed.connect(lambda s: hits.append(s))
    main_tid = threading.get_ident()
    tids: list[int] = []

    def on_status(_s):
        tids.append(threading.get_ident())

    shell.status_changed.connect(on_status)

    def worker() -> None:
        shell._telemetry.post({"available": True, "voltage": 22.0, "recv_mono": 1.0})

    t = threading.Thread(target=worker)
    t.start()
    t.join(5)
    qt_app.processEvents()
    assert shell.get_status_value("voltage") == 22.0
    assert tids == [main_tid]
    shell.cleanup()
    assert not shell._thrust_ramp_timer.isActive()


def test_teensy_settings_inject_on_shell(qt_app, fake_node) -> None:
    from PySide6.QtCore import QObject, Signal

    from paint_controller.controllers.teensy_shell import TeensyController

    class FakeSettings(QObject):
        thrust_force_changed = Signal(float)
        thrust_ramp_rate_changed = Signal(float)

        def get(self, key, default=None):
            if key == "thrust_force":
                return 0.5
            if key == "thrust_ramp_rate":
                return 2.0
            return default

    settings = FakeSettings()
    shell = TeensyController(fake_node, settings_manager=settings)
    assert shell.thrust_force == 0.5
    assert shell._thrust_ramp_rate == 2.0
    settings.thrust_force_changed.emit(0.8)
    assert abs(shell.thrust_force - 0.8) < 1e-6
    settings.thrust_ramp_rate_changed.emit(3.0)
    assert shell._thrust_ramp_rate == 3.0
    shell.cleanup()
