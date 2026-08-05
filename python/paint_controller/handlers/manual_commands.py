"""Python-owned manual command boundary for the system-control overlay.

TD-052: form catalog (labels, units, placeholders, param lists) lives here with
coerce + dispatch so QML only renders a generic form.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.handlers.demo_sequence import run_demo_action
from paint_controller.ports.teensy import SupportsTeensyWorkflowBody
from paint_controller.ports.winch import SupportsWinchMotion

ParamType = Literal["number", "dropdown"]


class SupportsManualTeensyCommands(SupportsTeensyWorkflowBody, Protocol):
    """Teensy surface used by system-control manual commands (incl. tap helpers)."""

    def startTapFreq(self, power: float, period: float) -> None: ...

    def tapOnce(self, power: float) -> None: ...


@dataclass(frozen=True)
class _ParameterSpec:
    name: str
    coerce: Callable[[str], object]
    type: ParamType = "number"
    unit: str = ""
    placeholder: str = ""
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class _CommandSpec:
    id: str
    label: str
    description: str
    parameters: tuple[_ParameterSpec, ...]
    executor: Callable[[dict[str, object]], bool | None]
    supported: bool = True


class ManualCommandHandler(QObject):
    """Own manual command catalog, validation, coercion, and dispatch for QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: SupportsManualTeensyCommands,
        winch: SupportsWinchMotion | None,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._winch = winch
        self._logger = logger
        # Single registry: stable id + form metadata + coerce + executor (TD-052).
        # "Move to Position" is intentionally omitted (unsupported phantom not in catalog).
        self._command_specs: dict[str, _CommandSpec] = {
            "spray_gun_angle": _CommandSpec(
                id="spray_gun_angle",
                label="Set Spray Gun Angle",
                description="Configure spray gun angle",
                parameters=(
                    _ParameterSpec("Angle", self._to_float, unit="degrees", placeholder="0.0"),
                    _ParameterSpec("Speed", self._to_float, unit="degrees/s", placeholder="1.0"),
                ),
                executor=self._execute_set_spray_gun_angle,
            ),
            "demo": _CommandSpec(
                id="demo",
                label="Demo",
                description="Run demo action",
                parameters=(
                    _ParameterSpec("Gimbal Angle", self._to_float, unit="degrees", placeholder="0.0"),
                    _ParameterSpec("Gimbal Speed", self._to_float, unit="degrees/s", placeholder="1.0"),
                    _ParameterSpec("Cable Length", self._to_float, unit="m", placeholder="1.0"),
                    _ParameterSpec("Cable Speed", self._to_float, unit="m/s", placeholder="0.5"),
                    _ParameterSpec("Force Y", self._to_float, unit="N", placeholder="0.0"),
                ),
                executor=self._execute_demo,
            ),
            "winch_control": _CommandSpec(
                id="winch_control",
                label="Winch Control",
                description="Control winch movement",
                parameters=(
                    _ParameterSpec("Distance", self._to_int, unit="mm", placeholder="0"),
                    _ParameterSpec("Speed", self._to_int, unit="mm/s", placeholder="500"),
                    _ParameterSpec("Acceleration", self._to_int, unit="RPM/s", placeholder="30"),
                ),
                executor=self._execute_winch_control,
            ),
            "frequency_tap": _CommandSpec(
                id="frequency_tap",
                label="Frequency Tap",
                description="Start Frequency Tap",
                parameters=(
                    _ParameterSpec("Power", self._to_float, unit="%", placeholder="1.0"),
                    _ParameterSpec("Period", self._to_float, unit="s", placeholder="1.0"),
                ),
                executor=self._execute_frequency_tap,
            ),
            "tap_once": _CommandSpec(
                id="tap_once",
                label="Tap Once",
                description="Tap once",
                parameters=(_ParameterSpec("Power", self._to_float, unit="%", placeholder="1.0"),),
                executor=self._execute_tap_once,
            ),
            "extend_arm": _CommandSpec(
                id="extend_arm",
                label="Extend Arm",
                description="Extend the robotic arm",
                parameters=(_ParameterSpec("Length", self._to_int, unit="mm", placeholder="1.0"),),
                executor=self._execute_extend_arm,
            ),
        }
        # English labels → ids for one-release compat (executeCommand accepts either).
        self._command_aliases: dict[str, str] = {
            spec.label: command_id for command_id, spec in self._command_specs.items()
        }
        self._catalog_cache: list[dict[str, Any]] = self._build_catalog()

    def _build_catalog(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for command_id, spec in self._command_specs.items():
            rows.append(
                {
                    "id": command_id,
                    "label": spec.label,
                    "description": spec.description,
                    "supported": spec.supported,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "unit": p.unit,
                            "placeholder": p.placeholder,
                            "options": list(p.options),
                        }
                        for p in spec.parameters
                    ],
                }
            )
        return rows

    @Property("QVariantList", constant=True)
    def commandCatalog(self) -> list[dict[str, Any]]:
        """Form catalog for CommandTab (id, label, description, supported, parameters)."""
        return list(self._catalog_cache)

    def _resolve_command_id(self, command_name: str) -> str | None:
        if command_name in self._command_specs:
            spec = self._command_specs[command_name]
            return command_name if spec.supported else None
        alias_id = self._command_aliases.get(command_name)
        if alias_id is None:
            return None
        return alias_id if self._command_specs[alias_id].supported else None

    @Slot(str, result=bool)
    def isCommandSupported(self, command_name: str) -> bool:
        return self._resolve_command_id(command_name) is not None

    @Slot(str, "QVariantMap", result=bool)
    def executeCommand(self, command_name: str, raw_parameters: Any) -> bool:
        command_id = self._resolve_command_id(command_name)
        if command_id is None:
            return self._fail(f"Command '{command_name}' is not available yet")

        try:
            parameters = self._coerce_parameters(command_id, raw_parameters)
        except ValueError as exc:
            return self._fail(str(exc))

        display_name = self._command_specs[command_id].label
        result = self._command_specs[command_id].executor(parameters)
        if result is False:
            return self._fail(f"Command '{display_name}' was rejected by the backend")

        message = f"Command sent: {display_name}"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _coerce_parameters(self, command_name: str, raw_parameters: Any) -> dict[str, object]:
        command_spec = self._command_specs[command_name]
        if raw_parameters is None:
            parameter_map: dict[str, Any] = {}
        elif isinstance(raw_parameters, dict):
            parameter_map = raw_parameters
        else:
            try:
                parameter_map = dict(raw_parameters)
            except Exception as exc:
                raise ValueError(f"Invalid parameter payload for '{command_name}'") from exc

        coerced: dict[str, object] = {}
        for spec in command_spec.parameters:
            raw_value = parameter_map.get(spec.name)
            if raw_value is None or str(raw_value).strip() == "":
                raise ValueError(f"Missing parameter: {spec.name}")

            try:
                coerced[spec.name] = spec.coerce(str(raw_value))
            except ValueError as exc:
                raise ValueError(f"Invalid value for {spec.name}: {raw_value}") from exc

        return coerced

    @staticmethod
    def _to_float(value: str) -> float:
        return float(value)

    @staticmethod
    def _to_int(value: str) -> int:
        return int(float(value))

    @staticmethod
    def _as_float(value: object) -> float:
        return float(str(value))

    @staticmethod
    def _as_int(value: object) -> int:
        return int(float(str(value)))

    def _execute_set_spray_gun_angle(self, parameters: dict[str, object]) -> None:
        self._teensy.setSprayGunPitchAngle(self._as_float(parameters["Angle"]), self._as_float(parameters["Speed"]))

    def _execute_demo(self, parameters: dict[str, object]) -> None:
        # TD-055: multi-device demo lives in application demo_sequence, not on Teensy.
        run_demo_action(
            self._teensy,
            self._winch,
            pitch_angle=self._as_float(parameters["Gimbal Angle"]),
            pitch_speed=self._as_float(parameters["Gimbal Speed"]),
            cable_length=self._as_float(parameters["Cable Length"]),
            cable_speed=self._as_float(parameters["Cable Speed"]),
            force_y=self._as_float(parameters["Force Y"]),
        )

    def _execute_winch_control(self, parameters: dict[str, object]) -> bool | None:
        if self._winch is None:
            return False
        # TD-055.6: single port verb — no dual getattr fallback.
        result = self._winch.move_increment_with_accel(
            self._as_int(parameters["Distance"]),
            self._as_int(parameters["Speed"]),
            self._as_int(parameters["Acceleration"]),
        )
        return result if isinstance(result, bool) or result is None else bool(result)

    def _execute_frequency_tap(self, parameters: dict[str, object]) -> None:
        self._teensy.startTapFreq(self._as_float(parameters["Power"]), self._as_float(parameters["Period"]))

    def _execute_tap_once(self, parameters: dict[str, object]) -> None:
        self._teensy.tapOnce(self._as_float(parameters["Power"]))

    def _execute_extend_arm(self, parameters: dict[str, object]) -> None:
        self._teensy.extendArm(self._as_int(parameters["Length"]))

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False
