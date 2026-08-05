"""Level C P1: pure LidarHal + shell bridge/notify contracts."""

from __future__ import annotations

import ast
import threading
from pathlib import Path

from paint_controller.controllers.lidar import LidarDistanceSnapshot, LidarHal
from paint_controller.ports.notifier import RecordingDeviceNotifier


_CONTROLLERS = Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "controllers"


def test_lidar_py_has_no_pyside6_import() -> None:
    source = (_CONTROLLERS / "lidar.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("PySide6"), alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("PySide6"), node.module


def test_lidar_hal_notifies_on_set(fake_node) -> None:
    rec = RecordingDeviceNotifier()
    hal = LidarHal(fake_node, notifier=rec)
    hal.set_distance(1.5)
    hal.set_angle(-0.25)
    hal.set_distance(1.5)  # no-op same value
    assert rec.names == ["distance_changed", "angle_changed"]
    assert hal.distance == 1.5
    assert hal.angle == -0.25


def test_lidar_hal_apply_snapshots(fake_node) -> None:
    rec = RecordingDeviceNotifier()
    hal = LidarHal(fake_node, notifier=rec)
    hal.apply_distance(LidarDistanceSnapshot(distance=3.0))
    assert hal.distance == 3.0
    assert rec.names == ["distance_changed"]


def test_lidar_shell_bridge_parented_to_shell_applies_on_main(qt_core_app, fake_node) -> None:
    from paint_controller.controllers.lidar_shell import LidarController

    main_tid = threading.get_ident()
    shell = LidarController(fake_node)
    assert shell._distance_bridge.parent() is shell
    assert shell._angle_bridge.parent() is shell

    apply_tids: list[int] = []
    hits: list[str] = []
    shell.distance_changed.connect(lambda: (hits.append("distance"), apply_tids.append(threading.get_ident())))

    errors: list[BaseException] = []

    def worker() -> None:
        try:
            for i in range(1, 6):
                shell._distance_bridge.post(LidarDistanceSnapshot(distance=float(i)))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="lidar-shell-post-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []
    assert hits == []

    qt_core_app.processEvents()

    assert shell.distance == 5.0
    assert hits == ["distance"]
    assert apply_tids == [main_tid]


def test_lidar_status_reads_shell_and_notifies(qt_core_app, fake_node) -> None:
    from paint_controller.controllers.lidar_shell import LidarController
    from paint_controller.models.lidar_status import LidarStatus

    shell = LidarController(fake_node)
    status = LidarStatus(shell)
    emitted: list[str] = []
    status.distanceChanged.connect(lambda: emitted.append("distance"))
    status.angleChanged.connect(lambda: emitted.append("angle"))

    shell.set_distance(2.0)
    shell.set_angle(0.5)
    assert status.distance == 2.0
    assert status.angle == 0.5
    assert emitted == ["distance", "angle"]
