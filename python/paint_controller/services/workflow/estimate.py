"""Single source of truth for workflow action duration estimates.

Compile and scheduler both call :func:`estimate_duration_s` so action-type
duration math is not re-implemented in parallel tables.
"""

from __future__ import annotations

from typing import Any

from .action_schema import EstimateMode, get_action_type


def estimate_duration_ms(
    action_type: str | None,
    params: dict[str, Any] | None,
    *,
    hardware: Any | None = None,
    explicit_estimated_duration_ms: float | int | None = None,
) -> float:
    """Return estimated duration in milliseconds."""
    return estimate_duration_s(
        action_type,
        params,
        hardware=hardware,
        explicit_estimated_duration_ms=explicit_estimated_duration_ms,
    ) * 1000.0


def estimate_duration_s(
    action_type: str | None,
    params: dict[str, Any] | None,
    *,
    hardware: Any | None = None,
    explicit_estimated_duration_ms: float | int | None = None,
) -> float:
    """Return estimated duration in seconds for schedule/compile.

    Prefer an explicit stamp (action dict ``estimated_duration`` in ms) when
    provided. Otherwise use the action type's :class:`EstimateSpec`.
    """
    if explicit_estimated_duration_ms is not None:
        try:
            return max(float(explicit_estimated_duration_ms), 0.0) / 1000.0
        except (TypeError, ValueError):
            pass

    params = dict(params or {})
    action = get_action_type(action_type)
    if action is None:
        return 1.0

    spec = action.metadata.estimate
    mode = spec.mode

    if mode == EstimateMode.FIXED_MS:
        return max(spec.fixed_ms, 0) / 1000.0

    if mode == EstimateMode.DURATION_MS_PARAM:
        key = spec.primary_param or "duration_ms"
        try:
            return max(float(params.get(key, 0) or 0), 0.0) / 1000.0
        except (TypeError, ValueError):
            return 0.0

    if mode == EstimateMode.ABS_PARAM_OVER_SPEED:
        primary = abs(_as_float(params.get(spec.primary_param or "length", 0)))
        speed = max(_as_float(params.get(spec.speed_param or "speed", spec.default_speed)), 1e-6)
        # Optional hardware correction for absolute winch targets
        if spec.use_hardware_delta and hardware is not None:
            primary = _hardware_adjusted_distance(hardware, params, primary, spec)
        return primary / speed

    if mode == EstimateMode.SIGNED_PARAM_OVER_SPEED:
        primary = abs(_as_float(params.get(spec.primary_param or "length", 0)))
        speed = max(_as_float(params.get(spec.speed_param or "speed", spec.default_speed)), 1e-6)
        return primary / speed

    return max(spec.fixed_ms, 0) / 1000.0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _hardware_adjusted_distance(hardware: Any, params: dict[str, Any], fallback: float, spec: Any) -> float:
    """If winch cable length is available, use |target - current| for absolute moves."""
    distance_explicit = params.get("distance")
    if distance_explicit is not None:
        try:
            d = float(distance_explicit)
            if d > 0:
                return abs(d)
        except (TypeError, ValueError):
            pass

    target = _as_float(params.get(spec.primary_param or "length", 0))
    winch = getattr(hardware, "winch", None)
    if winch is None:
        return abs(target)
    try:
        current = float(winch.get_cable_length())
        return abs(target - current)
    except Exception:
        return abs(target)
