from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from paint_controller.models.action_legality_model import ActionLegalityModel


class _FakeAdminActionGate(QObject):
    gate_state_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.evaluations: dict[str, dict] = {}

    def set_evaluation(self, action_key: str, evaluation: dict) -> None:
        self.evaluations[action_key] = dict(evaluation)

    def evaluate(self, action_key: str):
        return dict(
            self.evaluations.get(
                action_key,
                {
                    "actionKey": action_key,
                    "allowed": True,
                    "reason": "",
                    "title": action_key,
                    "legalStateClass": "status-admin",
                    "allowedHeartbeatStates": [1, 2],
                },
            )
        )


class _FakeCapabilityCatalog:
    def __init__(self) -> None:
        self.capabilities: dict[str, dict] = {}

    def set_capability(self, action_key: str, capability: dict) -> None:
        self.capabilities[action_key] = dict(capability)

    def getActionCapability(self, action_key: str):
        return dict(self.capabilities.get(action_key, {}))


def test_action_legality_model_combines_gate_and_capability_metadata(qt_app) -> None:
    gate = _FakeAdminActionGate()
    gate.set_evaluation(
        "wheel.reset_position",
        {
            "actionKey": "wheel.reset_position",
            "allowed": False,
            "reason": "Reset Wheel Position requires the system to be idle",
            "title": "Reset Wheel Position",
            "legalStateClass": "maintenance-preset",
            "allowedHeartbeatStates": [1],
        },
    )
    catalog = _FakeCapabilityCatalog()
    catalog.set_capability(
        "wheel.reset_position",
        {
            "surfaceKeys": ["overlay:systemcontrol:devices", "page:wheel"],
            "primarySurface": "overlay:systemcontrol:devices",
            "authority": "wheelActions.resetPosition",
            "capabilityClass": "direct-admin-action",
            "immediateRuntimeSideEffect": True,
        },
    )

    model = ActionLegalityModel(admin_action_gate=gate, capability_catalog=catalog)
    legality = model.getActionLegality("wheel.reset_position")

    assert legality["allowed"] is False
    assert legality["reason"] == "Reset Wheel Position requires the system to be idle"
    assert legality["title"] == "Reset Wheel Position"
    assert legality["surfaceKeys"] == ["overlay:systemcontrol:devices", "page:wheel"]
    assert legality["primarySurface"] == "overlay:systemcontrol:devices"
    assert legality["authority"] == "wheelActions.resetPosition"
    assert legality["capabilityClass"] == "direct-admin-action"
    assert legality["immediateRuntimeSideEffect"] is True


def test_action_legality_model_emits_change_when_gate_changes(qt_app) -> None:
    gate = _FakeAdminActionGate()
    model = ActionLegalityModel(admin_action_gate=gate)
    changed: list[bool] = []
    model.legalityChanged.connect(lambda: changed.append(True))

    gate.gate_state_changed.emit()

    assert changed == [True]


def test_action_legality_model_defaults_to_allowed_when_key_is_empty(qt_app) -> None:
    model = ActionLegalityModel(admin_action_gate=_FakeAdminActionGate())

    legality = model.getActionLegality("")

    assert legality["allowed"] is True
    assert legality["reason"] == ""
    assert legality["surfaceKeys"] == []
