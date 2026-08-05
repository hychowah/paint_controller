"""Level C P0: DeviceNotifier Protocol and SignalDeviceNotifier contracts."""

from __future__ import annotations

from paint_controller.ports import DeviceNotifier
from paint_controller.ports.notifier import NullDeviceNotifier, RecordingDeviceNotifier


def test_recording_notifier_records_names_in_order() -> None:
    rec = RecordingDeviceNotifier()
    rec.notify("distance_changed")
    rec.notify("angle_changed")
    rec.notify("distance_changed")
    assert rec.names == ["distance_changed", "angle_changed", "distance_changed"]


def test_null_notifier_is_noop() -> None:
    NullDeviceNotifier().notify("anything")


def test_recording_and_null_satisfy_device_notifier_protocol() -> None:
    assert isinstance(RecordingDeviceNotifier(), DeviceNotifier)
    assert isinstance(NullDeviceNotifier(), DeviceNotifier)


def test_device_notifier_importable_from_ports_package() -> None:
    # Must not pull controllers (circular-import hazard).
    assert DeviceNotifier is not None
    assert callable(DeviceNotifier.notify)


def test_signal_device_notifier_emits_named_signal(qt_core_app) -> None:
    from PySide6.QtCore import QObject, Signal

    from paint_controller.core.device_notifier import SignalDeviceNotifier

    class _Shell(QObject):
        distance_changed = Signal()

    shell = _Shell()
    hits: list[str] = []
    shell.distance_changed.connect(lambda: hits.append("distance_changed"))

    notifier = SignalDeviceNotifier(shell)
    assert isinstance(notifier, DeviceNotifier)
    notifier.notify("distance_changed")
    assert hits == ["distance_changed"]


def test_signal_device_notifier_missing_signal_is_fail_loud(qt_core_app) -> None:
    from PySide6.QtCore import QObject

    from paint_controller.core.device_notifier import SignalDeviceNotifier

    shell = QObject()
    notifier = SignalDeviceNotifier(shell)
    try:
        notifier.notify("distance_changed")
    except AttributeError as exc:
        assert "distance_changed" in str(exc)
        assert "QObject" in str(exc) or "missing" in str(exc).lower()
    else:
        raise AssertionError("expected AttributeError for missing signal")


def test_signal_device_notifier_rejects_none_owner(qt_core_app) -> None:
    from paint_controller.core.device_notifier import SignalDeviceNotifier

    try:
        SignalDeviceNotifier(None)  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("expected TypeError for None owner")
