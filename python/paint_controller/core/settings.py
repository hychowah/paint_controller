"""
SettingsManager - Centralized settings management with file persistence

This module provides a centralized location for application parameters that were
previously scattered across multiple controller classes. Settings are persisted
to ~/ros2_ws/src/paint_controller_ros2/python/config/settings.json and can be modified at runtime.
"""

import os
import json
import logging
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from PySide6.QtCore import QObject, Signal, Slot, Property

logger = logging.getLogger(__name__)


def _fsync_parent_directory(path: Path) -> None:
    """Best-effort directory fsync so the rename is durable after power loss."""
    if not hasattr(os, "O_DIRECTORY"):
        return

    directory_fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_write_json(path: Path, payload: Dict[str, Any], *, indent: int) -> None:
    """Write JSON atomically so a failed write cannot corrupt the last good file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(payload, handle, indent=indent)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(temp_path, path)
        _fsync_parent_directory(path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

# Settings schema — defines metadata for all settings (default, min, max, type, etc.)
_SETTINGS_SCHEMA: Dict[str, Dict[str, Any]] = {
    "winch_max_speed_mmps": {
        "default": 200.0,
        "min": 0.0,
        "max": 400.0,
        "type": "float",
        "requires_restart": False,
        "description": "Maximum winch speed limit (mm/s)"
    },
    "track_max_speed": {
        "default": 500.0,
        "min": 5.0,
        "max": 500.0,
        "type": "float",
        "requires_restart": False,
        "description": "Maximum track/wheel speed"
    },
    "track_min_speed": {
        "default": 50.0,
        "min": 0.0,
        "max": 50.0,
        "type": "float",
        "requires_restart": False,
        "description": "Minimum track speed to overcome friction"
    },
    "thrust_force": {
        "default": -1.0,
        "min": -1.5,
        "max": 1.5,
        "type": "float",
        "requires_restart": False,
        "description": "Thrust force for vertical movement"
    },
    "thrust_ramp_rate": {
        "default": 1.0,
        "min": 0.1,
        "max": 10.0,
        "type": "float",
        "requires_restart": False,
        "description": "Thrust force ramp rate (thrust/second)"
    },
    "valve_turn_max": {
        "default": 6.0,
        "min": 0.0,
        "max": 10.0,
        "type": "float",
        "requires_restart": False,
        "description": "Maximum valve turn value"
    },
    "arm_retract_length": {
        "default": 250,
        "min": 0,
        "max": 1000,
        "type": "int",
        "requires_restart": False,
        "description": "Arm retracted position preset"
    },
    "arm_extend_length": {
        "default": 800,
        "min": 0,
        "max": 1500,
        "type": "int",
        "requires_restart": False,
        "description": "Arm extended position preset"
    },
    "wheel_travel_max": {
        "default": 500.0,
        "min": 100.0,
        "max": 1000.0,
        "type": "float",
        "requires_restart": False,
        "description": "Maximum wheel travel distance (mm)"
    },
    "wheel_travel_rate": {
        "default": 100.0,
        "min": 10.0,
        "max": 500.0,
        "type": "float",
        "requires_restart": False,
        "description": "Wheel travel adjustment rate (mm/sec)"
    },
    "wheel_travel_rpm": {
        "default": 300,
        "min": 50,
        "max": 600,
        "type": "int",
        "requires_restart": False,
        "description": "Fixed RPM for wheel travel commands"
    },
    "emergency_hold_duration_s": {
        "default": 1.0,
        "min": 0.2,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Hold duration required to trigger emergency stop (seconds)"
    },
    "ui_section_states": {
        "default": {},
        "type": "dict",
        "requires_restart": False,
        "description": "Collapsed/expanded state of UI sections"
    },
    "base_top_view_zoom": {
        "default": 0.51,
        "min": 0.1,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view zoom factor"
    },
    "base_top_view_offset_x": {
        "default": 0.026,
        "min": -1.0,
        "max": 1.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view horizontal offset"
    },
    "base_top_view_offset_y": {
        "default": 0.474,
        "min": -1.0,
        "max": 1.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view vertical offset"
    },
    "base_top_view_crop_enabled": {
        "default": True,
        "type": "bool",
        "requires_restart": False,
        "description": "Enable base top view cropping"
    },
    "base_top_view_crop_width_ratio": {
        "default": 0.9,
        "min": 0.1,
        "max": 1.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view crop width ratio"
    },
    "base_top_view_crop_center_x": {
        "default": 0.5,
        "min": 0.0,
        "max": 1.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view crop center X position"
    },
    "base_top_view_k1": {
        "default": -0.389,
        "min": -2.0,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view fisheye distortion coefficient k1"
    },
    "base_top_view_k2": {
        "default": 0.142,
        "min": -2.0,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view fisheye distortion coefficient k2"
    },
    "base_top_view_k3": {
        "default": 0.0,
        "min": -2.0,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view fisheye distortion coefficient k3"
    },
    "base_top_view_k4": {
        "default": 0.0,
        "min": -2.0,
        "max": 2.0,
        "type": "float",
        "requires_restart": False,
        "description": "Base top view fisheye distortion coefficient k4"
    },
    "base_top_view_src_points": {
        "default": [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]],
        "type": "list",
        "requires_restart": False,
        "description": "Base top view source trapezoid points (normalized coordinates)"
    }
}

_SIGNAL_TYPES = {"float": float, "int": int, "bool": bool, "list": object}
_PROPERTY_TYPES = {"float": float, "int": int, "bool": bool, "list": "QVariantList"}


def _make_setting_pair(key):
    """Create a (Signal, Property) pair for a setting key from the schema."""
    schema = _SETTINGS_SCHEMA[key]
    sig_type = _SIGNAL_TYPES[schema["type"]]
    prop_type = _PROPERTY_TYPES[schema["type"]]
    default = schema["default"]

    signal = Signal(sig_type)

    def getter(self):
        return self.get(key, default)

    def setter(self, value):
        self.set(key, value)

    return signal, Property(prop_type, getter, setter, notify=signal)


class SettingsManager(QObject):
    """
    Centralized settings manager with file persistence and QML integration.
    
    Settings are stored in ~/ros2_ws/src/paint_controller_ros2/python/config/settings.json
    Each setting has metadata including: value, default, min, max, type, requires_restart, description
    """
    
    _settings_schema = _SETTINGS_SCHEMA

    # Setting signals and properties (auto-generated from schema via _make_setting_pair)
    winch_max_speed_mmps_changed, winch_max_speed_mmps = _make_setting_pair("winch_max_speed_mmps")
    track_max_speed_changed, track_max_speed = _make_setting_pair("track_max_speed")
    track_min_speed_changed, track_min_speed = _make_setting_pair("track_min_speed")
    thrust_force_changed, thrust_force = _make_setting_pair("thrust_force")
    thrust_ramp_rate_changed, thrust_ramp_rate = _make_setting_pair("thrust_ramp_rate")
    valve_turn_max_changed, valve_turn_max = _make_setting_pair("valve_turn_max")
    arm_retract_length_changed, arm_retract_length = _make_setting_pair("arm_retract_length")
    arm_extend_length_changed, arm_extend_length = _make_setting_pair("arm_extend_length")
    wheel_travel_max_changed, wheel_travel_max = _make_setting_pair("wheel_travel_max")
    wheel_travel_rate_changed, wheel_travel_rate = _make_setting_pair("wheel_travel_rate")
    wheel_travel_rpm_changed, wheel_travel_rpm = _make_setting_pair("wheel_travel_rpm")
    emergency_hold_duration_s_changed, emergency_hold_duration_s = _make_setting_pair("emergency_hold_duration_s")
    base_top_view_zoom_changed, base_top_view_zoom = _make_setting_pair("base_top_view_zoom")
    base_top_view_offset_x_changed, base_top_view_offset_x = _make_setting_pair("base_top_view_offset_x")
    base_top_view_offset_y_changed, base_top_view_offset_y = _make_setting_pair("base_top_view_offset_y")
    base_top_view_crop_enabled_changed, base_top_view_crop_enabled = _make_setting_pair("base_top_view_crop_enabled")
    base_top_view_crop_width_ratio_changed, base_top_view_crop_width_ratio = _make_setting_pair("base_top_view_crop_width_ratio")
    base_top_view_crop_center_x_changed, base_top_view_crop_center_x = _make_setting_pair("base_top_view_crop_center_x")
    base_top_view_k1_changed, base_top_view_k1 = _make_setting_pair("base_top_view_k1")
    base_top_view_k2_changed, base_top_view_k2 = _make_setting_pair("base_top_view_k2")
    base_top_view_k3_changed, base_top_view_k3 = _make_setting_pair("base_top_view_k3")
    base_top_view_k4_changed, base_top_view_k4 = _make_setting_pair("base_top_view_k4")
    base_top_view_src_points_changed, base_top_view_src_points = _make_setting_pair("base_top_view_src_points")

    # Generic signals
    setting_changed = Signal(str, object)
    operation_result = Signal(bool, str)
    setting_saved = Signal(str, object, str)
    
    def __init__(self, parent=None, show_popup_fn=None):
        super().__init__(parent)
        self._show_popup_fn = show_popup_fn
        self._values: Dict[str, Any] = {}
        self._values_lock = threading.Lock()

        package_dir = Path(__file__).parent.parent.parent
        self._config_dir = package_dir / "config"
        self._config_file = self._config_dir / "settings.json"
        self.load()
    
    def _get_config_path(self) -> Path:
        """Get the configuration file path, creating directory if needed"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        return self._config_file
    
    def load(self) -> bool:
        """
        Load settings from file. If file doesn't exist, use defaults.
        
        Returns:
            bool: True if loaded successfully, False if using defaults
        """
        # Initialize with defaults first
        with self._values_lock:
            for key, schema in self._settings_schema.items():
                self._values[key] = schema["default"]
        
        config_path = self._get_config_path()
        
        if not config_path.exists():
            logger.info("No config file found, using defaults")
            return False
        
        try:
            with open(config_path, 'r') as f:
                saved_values = json.load(f)
            
            # Merge saved values with defaults (validate each)
            with self._values_lock:
                for key, value in saved_values.items():
                    if key in self._settings_schema:
                        validated = self._validate_value(key, value)
                        if validated is not None:
                            self._values[key] = validated
            
            logger.info("Loaded settings from %s", config_path)
            return True
            
        except json.JSONDecodeError as e:
            logger.error("Error parsing config file: %s", e)
            return False
        except Exception as e:
            logger.error("Error loading config: %s", e)
            return False
    
    def _validate_value(self, key: str, value: Any) -> Optional[Any]:
        """
        Validate and convert a value according to its schema.
        
        Args:
            key: Setting key
            value: Value to validate
            
        Returns:
            Validated and typed value, or None if invalid
        """
        if key not in self._settings_schema:
            return None
        
        schema = self._settings_schema[key]
        
        try:
            # Type conversion
            if schema["type"] == "float":
                typed_value = float(value)
            elif schema["type"] == "int":
                typed_value = int(value)
            elif schema["type"] == "bool":
                typed_value = bool(value)
                return typed_value  # Bool doesn't have min/max
            elif schema["type"] == "dict":
                # Dict type doesn't need conversion, just validate it's a dict
                if isinstance(value, dict):
                    return value
                else:
                    return None
            elif schema["type"] == "list":
                # List type doesn't need conversion, just validate it's a list
                if isinstance(value, list):
                    return value
                else:
                    return None
            else:
                typed_value = value
            
            # Clamp to min/max range
            min_val = schema.get("min", float('-inf'))
            max_val = schema.get("max", float('inf'))
            typed_value = max(min_val, min(max_val, typed_value))
            
            return typed_value
            
        except (ValueError, TypeError) as e:
            logger.warning("Validation error for %s: %s", key, e)
            return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default if key doesn't exist
        """
        with self._values_lock:
            return self._values.get(key, default)
    
    def set(self, key: str, value: Any) -> Tuple[bool, str]:
        """
        Set a setting value (in memory only, does not save to file).
        
        Args:
            key: Setting key
            value: New value
            
        Returns:
            Tuple of (success, message)
        """
        if key not in self._settings_schema:
            return (False, f"Unknown setting: {key}")
        
        validated = self._validate_value(key, value)
        if validated is None:
            return (False, f"Invalid value for {key}: {value}")
        
        with self._values_lock:
            old_value = self._values.get(key)
            self._values[key] = validated
        
        # Emit signals OUTSIDE lock to prevent deadlock
        self._emit_setting_signal(key, validated)
        self.setting_changed.emit(key, validated)
        
        return (True, f"Setting {key} updated to {validated}")
    
    def _emit_setting_signal(self, key: str, value: Any):
        """Emit the specific signal for a setting change"""
        signal = getattr(self, f"{key}_changed", None)
        if signal is not None:
            signal.emit(value)
    
    @Slot(str, result=bool)
    def saveSetting(self, key: str) -> bool:
        """
        Save a single setting to file (QML callable).
        
        Args:
            key: Setting key to save
            
        Returns:
            bool: True if successful
        """
        success, message = self.save_setting(key)
        self.operation_result.emit(success, message)
        
        # Show popup notification if save was successful
        if success and key in self._settings_schema:
            value = self._values.get(key)
            description = self._settings_schema[key].get("description", key)
            self.setting_saved.emit(key, value, description)
            
            # Show popup
            if self._show_popup_fn:
                popup_message = f"{description}: {value}"
                self._show_popup_fn("Setting Saved", popup_message, "info", 2000)
        
        return success
    
    def save_setting(self, key: str) -> Tuple[bool, str]:
        """
        Save a single setting to the config file.
        
        Args:
            key: Setting key to save
            
        Returns:
            Tuple of (success, message)
        """
        if key not in self._settings_schema:
            return (False, f"Unknown setting: {key}")
        
        return self.save_all()
    
    def save_all(self) -> Tuple[bool, str]:
        """
        Save all current settings to file.
        
        Returns:
            Tuple of (success, message)
        """
        config_path = self._get_config_path()
        
        try:
            with self._values_lock:
                values_snapshot = self._values.copy()

            _atomic_write_json(config_path, values_snapshot, indent=2)
            
            logger.info("Saved settings to %s", config_path)
            return (True, "Settings saved successfully")
            
        except Exception as e:
            error_msg = f"Failed to save settings: {e}"
            logger.error("%s", error_msg)
            return (False, error_msg)

    def apply_value(self, key: str, value: Any) -> Tuple[bool, str]:
        """Set a value in memory and persist it without UI-specific popup behavior."""
        success, message = self.set(key, value)
        if not success:
            return (False, message)
        return self.save_all()
    
    @Slot(str, result=bool)
    def resetSetting(self, key: str) -> bool:
        """
        Reset a single setting to its default value (QML callable).
        
        Args:
            key: Setting key to reset
            
        Returns:
            bool: True if successful
        """
        success, message = self.reset_setting(key)
        self.operation_result.emit(success, message)
        return success
    
    def reset_setting(self, key: str) -> Tuple[bool, str]:
        """
        Reset a single setting to its default value.
        
        Args:
            key: Setting key to reset
            
        Returns:
            Tuple of (success, message)
        """
        if key not in self._settings_schema:
            return (False, f"Unknown setting: {key}")
        
        default_value = self._settings_schema[key]["default"]
        with self._values_lock:
            self._values[key] = default_value
        
        # Emit signals outside lock
        self._emit_setting_signal(key, default_value)
        self.setting_changed.emit(key, default_value)
        
        # Save to file
        return self.save_all()
    
    def reset_to_defaults(self) -> Tuple[bool, str]:
        """
        Reset all settings to their default values.
        
        Returns:
            Tuple of (success, message)
        """
        defaults = {}
        with self._values_lock:
            for key, schema in self._settings_schema.items():
                self._values[key] = schema["default"]
                defaults[key] = schema["default"]
        
        # Emit signals outside lock
        for key, value in defaults.items():
            self._emit_setting_signal(key, value)
            self.setting_changed.emit(key, value)
        
        return self.save_all()
    
    def get_schema(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a setting (includes min, max, default, etc.)
        
        Args:
            key: Setting key
            
        Returns:
            Schema dict or None if key doesn't exist
        """
        return self._settings_schema.get(key)
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all setting schemas"""
        return self._settings_schema.copy()
    
    # =====================================================
    # QML Slots for setting values with key
    # =====================================================
    
    @Slot(str, float, result=bool)
    def setFloat(self, key: str, value: float) -> bool:
        """Set a float setting value from QML"""
        success, _ = self.set(key, value)
        return success
    
    @Slot(str, int, result=bool)
    def setInt(self, key: str, value: int) -> bool:
        """Set an int setting value from QML"""
        success, _ = self.set(key, value)
        return success

    @Slot(str, float, result=bool)
    def applyFloat(self, key: str, value: float) -> bool:
        """Set and persist a float setting value from QML without popup notification."""
        success, message = self.apply_value(key, value)
        self.operation_result.emit(success, message)
        return success

    @Slot(str, int, result=bool)
    def applyInt(self, key: str, value: int) -> bool:
        """Set and persist an int setting value from QML without popup notification."""
        success, message = self.apply_value(key, value)
        self.operation_result.emit(success, message)
        return success

    @Slot(str, bool, result=bool)
    def applyBool(self, key: str, value: bool) -> bool:
        """Set and persist a bool setting value from QML without popup notification."""
        success, message = self.apply_value(key, value)
        self.operation_result.emit(success, message)
        return success
    
    @Slot(str, result=float)
    def getFloat(self, key: str) -> float:
        """Get a float setting value from QML"""
        return float(self.get(key) or 0.0)
    
    @Slot(str, result=int)
    def getInt(self, key: str) -> int:
        """Get an int setting value from QML"""
        return int(self.get(key) or 0)
    
    @Slot(str, result=float)
    def getMin(self, key: str) -> float:
        """Get the minimum value for a setting from QML"""
        schema = self.get_schema(key)
        return float(schema.get("min", 0)) if schema else 0.0
    
    @Slot(str, result=float)
    def getMax(self, key: str) -> float:
        """Get the maximum value for a setting from QML"""
        schema = self.get_schema(key)
        return float(schema.get("max", 100)) if schema else 100.0
    
    @Slot(str, result=float)
    def getDefault(self, key: str) -> float:
        """Get the default value for a setting from QML"""
        schema = self.get_schema(key)
        return float(schema.get("default", 0)) if schema else 0.0
    
    @Slot(str, result=str)
    def getDescription(self, key: str) -> str:
        """Get the description for a setting from QML"""
        schema = self.get_schema(key)
        return schema.get("description", "") if schema else ""

    @Slot(str, result=str)
    def getRouteSummary(self, route_key: str) -> str:
        """Return the current subtitle text for a settings route summary card."""
        if route_key == "winch":
            return f"Max speed: {self.getFloat('winch_max_speed_mmps'):.1f} mm/s"
        if route_key == "wheels":
            return (
                f"Track max: {self.getFloat('track_max_speed'):.1f}, "
                f"travel max: {self.getFloat('wheel_travel_max'):.0f} mm"
            )
        if route_key == "camera":
            return (
                f"Base-top zoom: {self.getFloat('base_top_view_zoom'):.2f}; "
                "full calibration remains overlay-primary"
            )
        if route_key == "arm":
            return (
                f"Retract: {self.getInt('arm_retract_length')} mm, "
                f"extend: {self.getInt('arm_extend_length')} mm"
            )
        return ""

    @Slot(result=str)
    def getCameraCalibrationSummary(self) -> str:
        """Return the current camera calibration summary shown on the settings route."""
        crop_state = "enabled" if bool(self.get("base_top_view_crop_enabled", False)) else "disabled"
        return (
            f"Saved zoom {self.getFloat('base_top_view_zoom'):.2f}, "
            f"crop {crop_state}. Full calibration remains overlay-primary."
        )
    
    @Slot(str, result=bool)
    def requiresRestart(self, key: str) -> bool:
        """Check if a setting requires restart from QML"""
        schema = self.get_schema(key)
        return schema.get("requires_restart", False) if schema else False
    
    # =====================================================
    # UI Section State Persistence (for collapsible sections)
    # =====================================================
    
    @Slot(str, bool)
    def setSectionExpanded(self, sectionId: str, expanded: bool):
        """Save the expanded state of a UI section (QML callable)"""
        with self._values_lock:
            states = self._values.get("ui_section_states", {})
            if not isinstance(states, dict):
                states = {}
            states[sectionId] = expanded
            self._values["ui_section_states"] = states
        self.save_all()
    
    @Slot(str, result=bool)
    def getSectionExpanded(self, sectionId: str) -> bool:
        """Get the expanded state of a UI section (QML callable). Returns True by default."""
        with self._values_lock:
            states = self._values.get("ui_section_states", {})
            if not isinstance(states, dict):
                return True
            return states.get(sectionId, True)
