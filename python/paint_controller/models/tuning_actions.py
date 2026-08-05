"""Python-owned, feature-root action boundary for tuning controls.

TD-052: parameter-set form catalog lives here with gated send; QML renders
generic forms and reads live values via status property keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.action_schema import ActionSchema, schema_map
from paint_controller.models.gated_action_mixin import GatedActionMixin

ACTION_SCHEMAS = schema_map(
    ActionSchema(
        ActionKey.TUNING_SHORT_YAW_PID,
        "Short Yaw PID",
        "tuning-calibration",
        "tuningActions.setShortYawPid",
    ),
    ActionSchema(
        ActionKey.TUNING_LONG_YAW_PID,
        "Long Yaw PID",
        "tuning-calibration",
        "tuningActions.setLongYawPid",
    ),
)


@dataclass(frozen=True)
class _TuningParamField:
    name: str
    status_key: str  # TeensyStatus QML property name (camelCase)
    status_backend_key: str  # controller get_status_value snake_case key
    unit: str = ""
    step_percent: float = 5.0
    send: bool = True  # False for display-only fields (e.g. Target)


@dataclass(frozen=True)
class _TuningParameterSet:
    id: str
    label: str
    description: str
    chart_series: str
    action_key: ActionKey
    current_status_key: str
    target_status_key: str
    parameters: tuple[_TuningParamField, ...]
    # Short and Long share yawPid* telemetry today (product quirk — do not invent separate keys).


# Form catalog SOT (TD-052). Target is display-only; only P/I/D are sent.
_PARAMETER_SETS: tuple[_TuningParameterSet, ...] = (
    _TuningParameterSet(
        id="short_yaw_pid",
        label="Short Yaw PID",
        description="Tune yaw axis PID parameters",
        chart_series="yaw",
        action_key=ActionKey.TUNING_SHORT_YAW_PID,
        current_status_key="imuYaw",
        target_status_key="yawCommand",
        parameters=(
            _TuningParamField("P Value", "yawPidP", "yaw_pid_p", step_percent=5.0, send=True),
            _TuningParamField("I Value", "yawPidI", "yaw_pid_i", step_percent=5.0, send=True),
            _TuningParamField("D Value", "yawPidD", "yaw_pid_d", step_percent=5.0, send=True),
            _TuningParamField(
                "Target",
                "yawCommand",
                "yaw_command",
                unit="degrees",
                step_percent=10.0,
                send=False,
            ),
        ),
    ),
    _TuningParameterSet(
        id="long_yaw_pid",
        label="Long Yaw PID",
        description="Tune long yaw axis PID parameters",
        chart_series="yaw",
        action_key=ActionKey.TUNING_LONG_YAW_PID,
        current_status_key="imuYaw",
        target_status_key="yawCommand",
        parameters=(
            _TuningParamField("P Value", "yawPidP", "yaw_pid_p", step_percent=5.0, send=True),
            _TuningParamField("I Value", "yawPidI", "yaw_pid_i", step_percent=5.0, send=True),
            _TuningParamField("D Value", "yawPidD", "yaw_pid_d", step_percent=5.0, send=True),
            _TuningParamField(
                "Target",
                "yawCommand",
                "yaw_command",
                unit="degrees",
                step_percent=10.0,
                send=False,
            ),
        ),
    ),
)


class SupportsTuningTeensy(Protocol):
    def setShortParams(self, p_value: float, i_value: float, d_value: float) -> object: ...

    def setLongParams(self, p_value: float, i_value: float, d_value: float) -> object: ...


class TuningActions(QObject, GatedActionMixin):
    """Own page-level tuning requests initiated from QML.

    TD-055.7: typed invoke — no string method-name dispatch.
    TD-052: parameterSets catalog + sendParameterSet for generic QML forms.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: SupportsTuningTeensy | None,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._admin_action_gate = admin_action_gate
        self._logger = logger
        self._sets_by_id = {s.id: s for s in _PARAMETER_SETS}
        self._sets_by_label = {s.label: s for s in _PARAMETER_SETS}
        self._catalog_cache = self._build_catalog()

    def _build_catalog(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for s in _PARAMETER_SETS:
            rows.append(
                {
                    "id": s.id,
                    "label": s.label,
                    "description": s.description,
                    "chartSeries": s.chart_series,
                    "actionKey": s.action_key.value,
                    "currentStatusKey": s.current_status_key,
                    "targetStatusKey": s.target_status_key,
                    "parameters": [
                        {
                            "name": p.name,
                            "statusKey": p.status_key,
                            "unit": p.unit,
                            "stepPercent": p.step_percent,
                            "send": p.send,
                            "type": "number",
                        }
                        for p in s.parameters
                    ],
                }
            )
        return rows

    @Property("QVariantList", constant=True)
    def parameterSets(self) -> list[dict[str, Any]]:
        """Form catalog for PageTuning (id, label, status keys, parameters)."""
        return list(self._catalog_cache)

    def _resolve_set(self, set_id_or_label: str) -> _TuningParameterSet | None:
        return self._sets_by_id.get(set_id_or_label) or self._sets_by_label.get(set_id_or_label)

    def _live_backend_value(self, backend_key: str, default: float = 0.0) -> float:
        teensy = self._teensy
        if teensy is None:
            return default
        getter = getattr(teensy, "get_status_value", None)
        if callable(getter):
            try:
                value = getter(backend_key)
            except Exception:
                return default
            if value is None:
                return default
            try:
                return float(str(value))
            except (TypeError, ValueError):
                return default
        return default

    @Slot(str, "QVariantMap", result=bool)
    def sendParameterSet(self, set_id: str, raw_parameters: Any) -> bool:
        """Send a parameter set by id/label; fill missing send fields from live status."""
        set_spec = self._resolve_set(set_id)
        if set_spec is None:
            return self._fail(f"Unknown tuning parameter set: {set_id}")

        if raw_parameters is None:
            parameter_map: dict[str, Any] = {}
        elif isinstance(raw_parameters, dict):
            parameter_map = raw_parameters
        else:
            try:
                parameter_map = dict(raw_parameters)
            except Exception:
                return self._fail(f"Invalid parameter payload for {set_id}")

        resolved: dict[str, float] = {}
        for field in set_spec.parameters:
            if not field.send:
                continue
            raw = parameter_map.get(field.name)
            if raw is None or (isinstance(raw, str) and str(raw).strip() == ""):
                resolved[field.name] = self._live_backend_value(field.status_backend_key)
            else:
                try:
                    resolved[field.name] = float(str(raw))
                except (TypeError, ValueError):
                    return self._fail(f"Invalid value for {field.name}: {raw}")

        p_val = resolved.get("P Value", 0.0)
        i_val = resolved.get("I Value", 0.0)
        d_val = resolved.get("D Value", 0.0)

        if set_spec.action_key is ActionKey.TUNING_SHORT_YAW_PID:
            return self.setShortYawPid(p_val, i_val, d_val)
        if set_spec.action_key is ActionKey.TUNING_LONG_YAW_PID:
            return self.setLongYawPid(p_val, i_val, d_val)
        return self._fail(f"No send path for parameter set {set_spec.id}")

    @Slot(float, float, float, result=bool)
    def setShortYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run_gated(
            action_key=ActionKey.TUNING_SHORT_YAW_PID,
            name="Short yaw PID",
            controller=self._teensy,
            invoke=lambda t: t.setShortParams(p_value, i_value, d_value),
        )

    @Slot(float, float, float, result=bool)
    def setLongYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run_gated(
            action_key=ActionKey.TUNING_LONG_YAW_PID,
            name="Long yaw PID",
            controller=self._teensy,
            invoke=lambda t: t.setLongParams(p_value, i_value, d_value),
        )
