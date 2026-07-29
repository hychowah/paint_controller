"""Unit tests for RosTelemetryBridge (TD-056)."""

from __future__ import annotations

from dataclasses import dataclass

from paint_controller.core.ros_telemetry import ImmediateTelemetryBridge, RosTelemetryBridge


@dataclass(frozen=True, slots=True)
class _Snap:
    value: int


def test_post_does_not_apply_synchronously(qt_core_app) -> None:
    applied: list[int] = []
    bridge = RosTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(1))
    assert applied == []
    assert bridge.pending_snapshot() is not None
    assert bridge.is_scheduled is True


def test_process_events_delivers_latest_only(qt_core_app) -> None:
    applied: list[int] = []
    bridge = RosTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(1))
    bridge.post(_Snap(2))
    bridge.post(_Snap(3))
    qt_core_app.processEvents()
    # Last-wins: only latest POD is applied (single wake may deliver once).
    assert applied == [3]


def test_immediate_bridge_applies_on_post(qt_core_app) -> None:
    applied: list[int] = []
    bridge = ImmediateTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(9))
    assert applied == [9]
