"""Schema integrity tests for simple device status wrappers."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal

from paint_controller.models.lidar_status import LIDAR_STATUS_PROPERTY_NAMES, LIDAR_STATUS_SIGNAL_MAP, LidarStatus
from paint_controller.models.valve_status import VALVE_STATUS_PROPERTY_NAMES, VALVE_STATUS_SIGNAL_MAP, ValveStatus
from paint_controller.models.wheel_status import WHEEL_STATUS_PROPERTY_NAMES, WHEEL_STATUS_SIGNAL_MAP, WheelStatus
from paint_controller.models.winch_status import WINCH_STATUS_PROPERTY_NAMES, WINCH_STATUS_SIGNAL_MAP, WinchStatus

_SIMPLE_WRAPPERS = (WheelStatus, WinchStatus, ValveStatus, LidarStatus)

_SIGNAL_MAPS = {
    WheelStatus: WHEEL_STATUS_SIGNAL_MAP,
    WinchStatus: WINCH_STATUS_SIGNAL_MAP,
    ValveStatus: VALVE_STATUS_SIGNAL_MAP,
    LidarStatus: LIDAR_STATUS_SIGNAL_MAP,
}

_PROPERTY_NAMES = {
    WheelStatus: WHEEL_STATUS_PROPERTY_NAMES,
    WinchStatus: WINCH_STATUS_PROPERTY_NAMES,
    ValveStatus: VALVE_STATUS_PROPERTY_NAMES,
    LidarStatus: LIDAR_STATUS_PROPERTY_NAMES,
}


def _property_name_from_notify(notify_name: str) -> str:
    assert notify_name.endswith("Changed"), f"notify name must end with Changed: {notify_name}"
    prop = notify_name[: -len("Changed")]
    return prop[0].lower() + prop[1:]


def test_status_schema_entries_have_matching_signal_and_property() -> None:
    for cls in _SIMPLE_WRAPPERS:
        for producer, controller_attr, notify_name, py_type in cls._STATUS_SCHEMA:
            assert hasattr(cls, notify_name), f"{cls.__name__}: missing notify signal {notify_name}"
            signal = getattr(cls, notify_name)
            assert isinstance(signal, Signal), f"{cls.__name__}.{notify_name} is not a Signal"

            prop_name = _property_name_from_notify(notify_name)
            assert hasattr(cls, prop_name), f"{cls.__name__}: missing property {prop_name}"
            prop = getattr(cls, prop_name)
            assert isinstance(prop, Property), f"{cls.__name__}.{prop_name} is not a Property"


def test_status_schema_signal_map_matches_schema() -> None:
    for cls in _SIMPLE_WRAPPERS:
        signal_map = _SIGNAL_MAPS[cls]

        map_producers = {producer for producer, _ in signal_map}
        schema_producers = {producer for producer, _, _, _ in cls._STATUS_SCHEMA}
        assert map_producers == schema_producers, f"{cls.__name__}: signal map and schema producers differ"

        map_notifies = {notify for _, notify in signal_map}
        schema_notifies = {notify for _, _, notify, _ in cls._STATUS_SCHEMA}
        assert map_notifies == schema_notifies, f"{cls.__name__}: signal map and schema notify names differ"


def test_status_schema_property_names_match_schema() -> None:
    for cls in _SIMPLE_WRAPPERS:
        property_names = _PROPERTY_NAMES[cls]

        expected = {_property_name_from_notify(notify) for _, _, notify, _ in cls._STATUS_SCHEMA}
        assert set(property_names) == expected, f"{cls.__name__}: property names constant does not match schema"
