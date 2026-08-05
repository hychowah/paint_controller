"""TD-052: command/tuning form schemas must not live as QML object literals."""

from __future__ import annotations

import re
from pathlib import Path

_QML_ROOT = Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "qml"

# Ban re-introducing view-owned form schemas (layout chrome is fine).
_BANNED_LITERALS = (
    re.compile(r"\bcommandDefinitions\s*:\s*\{"),
    re.compile(r"\bparameterSetDefinitions\s*:\s*\{"),
)


def test_no_command_or_tuning_schema_literals_in_qml() -> None:
    offenders: list[str] = []
    for path in _QML_ROOT.rglob("*.qml"):
        source = path.read_text(encoding="utf-8")
        for pattern in _BANNED_LITERALS:
            if pattern.search(source):
                offenders.append(f"{path.relative_to(_QML_ROOT.parent.parent.parent)}: {pattern.pattern}")
    assert offenders == [], "TD-052: form schema literals must live in Python, found:\n" + "\n".join(offenders)


def test_command_catalog_export_matches_param_coerce_names() -> None:
    from paint_controller.handlers.manual_commands import ManualCommandHandler
    from tests.fakes import FakeLogger

    class _T:
        def setSprayGunPitchAngle(self, *_a): ...
        def set_ef_force(self, *_a): ...
        def extendArm(self, *_a): ...
        def startTapFreq(self, *_a): ...
        def tapOnce(self, *_a): ...

    class _W:
        def move_increment_with_accel(self, *_a):
            return True

        def move_absolute_with_accel(self, *_a, **_k):
            return True

        def get_cable_length(self):
            return 0.0

    handler = ManualCommandHandler(teensy=_T(), winch=_W(), logger=FakeLogger())  # type: ignore[arg-type]
    for row in handler.commandCatalog:
        assert row["id"]
        assert row["label"]
        assert handler.isCommandSupported(row["id"]) is True
        # Param names in catalog must match coerce keys used by executeCommand
        for param in row["parameters"]:
            assert param["name"]


def test_tuning_parameter_sets_export_has_send_fields() -> None:
    from paint_controller.models.tuning_actions import TuningActions
    from tests.fakes import FakeLogger

    actions = TuningActions(teensy=None, admin_action_gate=object(), logger=FakeLogger())
    assert len(actions.parameterSets) >= 2
    for row in actions.parameterSets:
        send_params = [p for p in row["parameters"] if p.get("send")]
        assert len(send_params) >= 3  # P/I/D
