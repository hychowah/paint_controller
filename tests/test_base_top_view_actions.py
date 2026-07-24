"""Focused tests for the Python-owned base-top calibration action boundary."""

from __future__ import annotations

from paint_controller.models.base_top_view_actions import BaseTopViewActions
from tests.fakes import FakeLogger


class FakeBaseTopViewService:
    def __init__(self) -> None:
        self.zoom = 0.51
        self.offsetX = 0.026
        self.offsetY = 0.474
        self.cropEnabled = True
        self.cropWidthRatio = 0.9
        self.cropCenterX = 0.5
        self.k1 = -0.389
        self.k2 = 0.142
        self.k3 = 0.0
        self.k4 = 0.0
        self.save_calls = 0
        self.reset_calls = 0
        self.save_result = True

    def saveSettings(self) -> bool:
        self.save_calls += 1
        return self.save_result

    def resetToDefaults(self) -> None:
        self.reset_calls += 1


class FakeAdminActionGate:
    def __init__(self) -> None:
        self.results: dict[str, tuple[bool, str]] = {}
        self.calls: list[str] = []

    def set_result(self, action_key: str, allowed: bool, reason: str = "") -> None:
        self.results[action_key] = (allowed, reason)

    def check_action(self, action_key: str) -> tuple[bool, str]:
        self.calls.append(action_key)
        return self.results.get(action_key, (True, ""))


def _build_actions() -> tuple[BaseTopViewActions, FakeBaseTopViewService, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    service = FakeBaseTopViewService()
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = BaseTopViewActions(
        base_top_view_service=service,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, service, admin_action_gate, logger, results


def test_base_top_live_adjustments_and_actions_dispatch() -> None:
    actions, service, admin_action_gate, logger, results = _build_actions()

    assert actions.setZoom(0.75) is True
    assert actions.setOffsetX(0.11) is True
    assert actions.setOffsetY(0.22) is True
    assert actions.setCropEnabled(False) is True
    assert actions.setCropWidthRatio(0.8) is True
    assert actions.setCropCenterX(0.6) is True
    assert actions.setK1(-0.5) is True
    assert actions.setK2(0.25) is True
    assert actions.setK3(0.1) is True
    assert actions.setK4(0.05) is True
    assert actions.saveSettings() is True
    assert actions.resetToDefaults() is True

    assert service.zoom == 0.75
    assert service.offsetX == 0.11
    assert service.offsetY == 0.22
    assert service.cropEnabled is False
    assert service.cropWidthRatio == 0.8
    assert service.cropCenterX == 0.6
    assert service.k1 == -0.5
    assert service.k2 == 0.25
    assert service.k3 == 0.1
    assert service.k4 == 0.05
    assert service.save_calls == 1
    assert service.reset_calls == 1
    assert admin_action_gate.calls == [
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.save",
        "camera.base_top_view.reset",
    ]
    assert results[-1] == (True, "Base top view reset requested")
    assert logger.records[-1].message == "Base top view reset requested"


def test_base_top_gate_denial_blocks_live_adjustment() -> None:
    actions, service, admin_action_gate, logger, results = _build_actions()
    admin_action_gate.set_result(
        "camera.base_top_view.live_adjustments",
        False,
        "camera.base_top_view.live_adjustments requires the system to be idle",
    )

    assert actions.setZoom(0.92) is False

    assert service.zoom == 0.51
    assert results[-1] == (False, "camera.base_top_view.live_adjustments requires the system to be idle")
    assert logger.records[-1].message == "camera.base_top_view.live_adjustments requires the system to be idle"


def test_base_top_save_rejection_is_reported() -> None:
    actions, service, _gate, logger, results = _build_actions()
    service.save_result = False

    assert actions.saveSettings() is False

    assert service.save_calls == 1
    assert results[-1] == (False, "Base top view save was rejected by the backend")
    assert logger.records[-1].message == "Base top view save was rejected by the backend"
