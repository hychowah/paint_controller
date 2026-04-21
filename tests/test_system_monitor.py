"""Tests for paint_controller.controllers.system_monitor."""

from __future__ import annotations

import importlib

from PySide6.QtCore import QThread
from PySide6.QtTest import QTest


def _system_monitor_class():
    return importlib.import_module("paint_controller.controllers.system_monitor").SystemMonitor


def test_start_monitoring_runs_in_worker_thread(qt_app):
    monitor = _system_monitor_class()()
    worker = monitor.worker
    calls = []

    assert worker.update_timer.parent() is worker

    def fake_update() -> None:
        calls.append(QThread.currentThread() is worker.thread())

    worker._update_system_metrics = fake_update

    try:
        monitor.start_monitoring(5000)
        assert calls == []

        for _ in range(20):
            if calls:
                break
            QTest.qWait(10)

        assert calls == [True]
    finally:
        monitor.cleanup()