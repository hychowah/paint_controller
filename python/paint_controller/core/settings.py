"""
SettingsManager - Centralized settings management with file persistence

This module provides a centralized location for application parameters that were
previously scattered across multiple controller classes. Settings are persisted
to ~/ros2_ws/src/paint_controller_ros2/python/config/settings.json and can be modified at runtime.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from PySide6.QtCore import QObject, Signal, Slot, Property


class SettingsManager(QObject):
    """
    Centralized settings manager with file persistence and QML integration.
    
    Settings are stored in ~/ros2_ws/src/paint_controller_ros2/python/config/settings.json
    Each setting has metadata including: value, default, min, max, type, requires_restart, description
    """
    
    # Signals for individual setting changes
    winch_max_speed_mmps_changed = Signal(float)
    track_max_speed_changed = Signal(float)
    track_min_speed_changed = Signal(float)
    thrust_force_changed = Signal(float)
    thrust_ramp_rate_changed = Signal(float)
    valve_turn_max_changed = Signal(float)
    arm_retract_length_changed = Signal(int)
    arm_extend_length_changed = Signal(int)
    wheel_travel_max_changed = Signal(float)
    wheel_travel_rate_changed = Signal(float)
    wheel_travel_rpm_changed = Signal(int)
    
    # Bird view setting signals
    bird_view_zoom_changed = Signal(float)
    bird_view_offset_x_changed = Signal(float)
    bird_view_offset_y_changed = Signal(float)
    bird_view_crop_enabled_changed = Signal(bool)
    bird_view_crop_width_ratio_changed = Signal(float)
    bird_view_crop_center_x_changed = Signal(float)
    bird_view_k1_changed = Signal(float)
    bird_view_k2_changed = Signal(float)
    bird_view_src_points_changed = Signal(object)
    
    # Signal for any setting change (key, value)
    setting_changed = Signal(str, object)
    
    # Signal for save/reset feedback (success, message)
    operation_result = Signal(bool, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Define settings schema with metadata
        self._settings_schema: Dict[str, Dict[str, Any]] = {
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
                "min": -1.0,
                "max": 1.0,
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
            "ui_section_states": {
                "default": {},
                "type": "dict",
                "requires_restart": False,
                "description": "Collapsed/expanded state of UI sections"
            },
            "bird_view_zoom": {
                "default": 0.606,
                "min": 0.1,
                "max": 2.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird's eye view zoom factor"
            },
            "bird_view_offset_x": {
                "default": 0.026,
                "min": -1.0,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird's eye view horizontal offset"
            },
            "bird_view_offset_y": {
                "default": 0.474,
                "min": -1.0,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird's eye view vertical offset"
            },
            "bird_view_crop_enabled": {
                "default": True,
                "type": "bool",
                "requires_restart": False,
                "description": "Enable bird view cropping"
            },
            "bird_view_crop_width_ratio": {
                "default": 0.9,
                "min": 0.1,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird view crop width ratio"
            },
            "bird_view_crop_center_x": {
                "default": 0.5,
                "min": 0.0,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird view crop center X position"
            },
            "bird_view_k1": {
                "default": 0.32,
                "min": 0.0,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird view fisheye distortion coefficient k1"
            },
            "bird_view_k2": {
                "default": 0.272,
                "min": 0.0,
                "max": 1.0,
                "type": "float",
                "requires_restart": False,
                "description": "Bird view fisheye distortion coefficient k2"
            },
            "bird_view_src_points": {
                "default": [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]],
                "type": "list",
                "requires_restart": False,
                "description": "Bird view source trapezoid points (normalized coordinates)"
            }
        }
        
        # Current values (will be loaded from file or defaults)
        self._values: Dict[str, Any] = {}
        
        # Config directory and file path
        package_dir = Path(__file__).parent.parent.parent
        self._config_dir = package_dir / "config"
        self._config_file = self._config_dir / "settings.json"
        
        # Load settings from file (or use defaults)
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
        for key, schema in self._settings_schema.items():
            self._values[key] = schema["default"]
        
        config_path = self._get_config_path()
        
        if not config_path.exists():
            print(f"[SettingsManager] No config file found, using defaults")
            return False
        
        try:
            with open(config_path, 'r') as f:
                saved_values = json.load(f)
            
            # Merge saved values with defaults (validate each)
            for key, value in saved_values.items():
                if key in self._settings_schema:
                    validated = self._validate_value(key, value)
                    if validated is not None:
                        self._values[key] = validated
            
            print(f"[SettingsManager] Loaded settings from {config_path}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[SettingsManager] Error parsing config file: {e}")
            return False
        except Exception as e:
            print(f"[SettingsManager] Error loading config: {e}")
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
            print(f"[SettingsManager] Validation error for {key}: {e}")
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
        
        old_value = self._values.get(key)
        self._values[key] = validated
        
        # Emit specific signal for this setting
        self._emit_setting_signal(key, validated)
        
        # Emit generic setting changed signal
        self.setting_changed.emit(key, validated)
        
        return (True, f"Setting {key} updated to {validated}")
    
    def _emit_setting_signal(self, key: str, value: Any):
        """Emit the specific signal for a setting change"""
        signal_map = {
            "winch_max_speed_mmps": self.winch_max_speed_mmps_changed,
            "track_max_speed": self.track_max_speed_changed,
            "track_min_speed": self.track_min_speed_changed,
            "thrust_force": self.thrust_force_changed,
            "thrust_ramp_rate": self.thrust_ramp_rate_changed,
            "valve_turn_max": self.valve_turn_max_changed,
            "arm_retract_length": self.arm_retract_length_changed,
            "arm_extend_length": self.arm_extend_length_changed,
            "wheel_travel_max": self.wheel_travel_max_changed,
            "wheel_travel_rate": self.wheel_travel_rate_changed,
            "wheel_travel_rpm": self.wheel_travel_rpm_changed,
            "bird_view_zoom": self.bird_view_zoom_changed,
            "bird_view_offset_x": self.bird_view_offset_x_changed,
            "bird_view_offset_y": self.bird_view_offset_y_changed,
            "bird_view_crop_enabled": self.bird_view_crop_enabled_changed,
            "bird_view_crop_width_ratio": self.bird_view_crop_width_ratio_changed,
            "bird_view_crop_center_x": self.bird_view_crop_center_x_changed,
            "bird_view_k1": self.bird_view_k1_changed,
            "bird_view_k2": self.bird_view_k2_changed,
            "bird_view_src_points": self.bird_view_src_points_changed
        }
        
        if key in signal_map:
            signal_map[key].emit(value)
    
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
            with open(config_path, 'w') as f:
                json.dump(self._values, f, indent=2)
            
            print(f"[SettingsManager] Saved settings to {config_path}")
            return (True, "Settings saved successfully")
            
        except Exception as e:
            error_msg = f"Failed to save settings: {e}"
            print(f"[SettingsManager] {error_msg}")
            return (False, error_msg)
    
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
        self._values[key] = default_value
        
        # Emit signals
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
        for key, schema in self._settings_schema.items():
            self._values[key] = schema["default"]
            self._emit_setting_signal(key, schema["default"])
            self.setting_changed.emit(key, schema["default"])
        
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
    # Qt Properties for QML binding
    # =====================================================
    
    @Property(float, notify=winch_max_speed_mmps_changed)
    def winch_max_speed_mmps(self) -> float:
        return self._values.get("winch_max_speed_mmps", 400.0)
    
    @winch_max_speed_mmps.setter
    def winch_max_speed_mmps(self, value: float):
        self.set("winch_max_speed_mmps", value)
    
    @Property(float, notify=track_max_speed_changed)
    def track_max_speed(self) -> float:
        return self._values.get("track_max_speed", 500.0)
    
    @track_max_speed.setter
    def track_max_speed(self, value: float):
        self.set("track_max_speed", value)
    
    @Property(float, notify=track_min_speed_changed)
    def track_min_speed(self) -> float:
        return self._values.get("track_min_speed", 50.0)
    
    @track_min_speed.setter
    def track_min_speed(self, value: float):
        self.set("track_min_speed", value)
    
    @Property(float, notify=thrust_force_changed)
    def thrust_force(self) -> float:
        return self._values.get("thrust_force", -1.0)
    
    @thrust_force.setter
    def thrust_force(self, value: float):
        self.set("thrust_force", value)
    
    @Property(float, notify=thrust_ramp_rate_changed)
    def thrust_ramp_rate(self) -> float:
        return self._values.get("thrust_ramp_rate", 1.0)
    
    @thrust_ramp_rate.setter
    def thrust_ramp_rate(self, value: float):
        self.set("thrust_ramp_rate", value)
    
    @Property(float, notify=valve_turn_max_changed)
    def valve_turn_max(self) -> float:
        return self._values.get("valve_turn_max", 6.0)
    
    @valve_turn_max.setter
    def valve_turn_max(self, value: float):
        self.set("valve_turn_max", value)
    
    @Property(int, notify=arm_retract_length_changed)
    def arm_retract_length(self) -> int:
        return self._values.get("arm_retract_length", 250)
    
    @arm_retract_length.setter
    def arm_retract_length(self, value: int):
        self.set("arm_retract_length", value)
    
    @Property(int, notify=arm_extend_length_changed)
    def arm_extend_length(self) -> int:
        return self._values.get("arm_extend_length", 800)
    
    @arm_extend_length.setter
    def arm_extend_length(self, value: int):
        self.set("arm_extend_length", value)
    
    @Property(float, notify=wheel_travel_max_changed)
    def wheel_travel_max(self) -> float:
        return self._values.get("wheel_travel_max", 500.0)
    
    @wheel_travel_max.setter
    def wheel_travel_max(self, value: float):
        self.set("wheel_travel_max", value)
    
    @Property(float, notify=wheel_travel_rate_changed)
    def wheel_travel_rate(self) -> float:
        return self._values.get("wheel_travel_rate", 100.0)
    
    @wheel_travel_rate.setter
    def wheel_travel_rate(self, value: float):
        self.set("wheel_travel_rate", value)
    
    @Property(int, notify=wheel_travel_rpm_changed)
    def wheel_travel_rpm(self) -> int:
        return self._values.get("wheel_travel_rpm", 300)
    
    @wheel_travel_rpm.setter
    def wheel_travel_rpm(self, value: int):
        self.set("wheel_travel_rpm", value)
    
    # Bird view properties
    @Property(float, notify=bird_view_zoom_changed)
    def bird_view_zoom(self) -> float:
        return self._values.get("bird_view_zoom", 0.606)
    
    @bird_view_zoom.setter
    def bird_view_zoom(self, value: float):
        self.set("bird_view_zoom", value)
    
    @Property(float, notify=bird_view_offset_x_changed)
    def bird_view_offset_x(self) -> float:
        return self._values.get("bird_view_offset_x", 0.026)
    
    @bird_view_offset_x.setter
    def bird_view_offset_x(self, value: float):
        self.set("bird_view_offset_x", value)
    
    @Property(float, notify=bird_view_offset_y_changed)
    def bird_view_offset_y(self) -> float:
        return self._values.get("bird_view_offset_y", 0.474)
    
    @bird_view_offset_y.setter
    def bird_view_offset_y(self, value: float):
        self.set("bird_view_offset_y", value)
    
    @Property(bool, notify=bird_view_crop_enabled_changed)
    def bird_view_crop_enabled(self) -> bool:
        return self._values.get("bird_view_crop_enabled", True)
    
    @bird_view_crop_enabled.setter
    def bird_view_crop_enabled(self, value: bool):
        self.set("bird_view_crop_enabled", value)
    
    @Property(float, notify=bird_view_crop_width_ratio_changed)
    def bird_view_crop_width_ratio(self) -> float:
        return self._values.get("bird_view_crop_width_ratio", 0.9)
    
    @bird_view_crop_width_ratio.setter
    def bird_view_crop_width_ratio(self, value: float):
        self.set("bird_view_crop_width_ratio", value)
    
    @Property(float, notify=bird_view_crop_center_x_changed)
    def bird_view_crop_center_x(self) -> float:
        return self._values.get("bird_view_crop_center_x", 0.5)
    
    @bird_view_crop_center_x.setter
    def bird_view_crop_center_x(self, value: float):
        self.set("bird_view_crop_center_x", value)
    
    @Property(float, notify=bird_view_k1_changed)
    def bird_view_k1(self) -> float:
        return self._values.get("bird_view_k1", 0.32)
    
    @bird_view_k1.setter
    def bird_view_k1(self, value: float):
        self.set("bird_view_k1", value)
    
    @Property(float, notify=bird_view_k2_changed)
    def bird_view_k2(self) -> float:
        return self._values.get("bird_view_k2", 0.272)
    
    @bird_view_k2.setter
    def bird_view_k2(self, value: float):
        self.set("bird_view_k2", value)
    
    @Property('QVariantList', notify=bird_view_src_points_changed)
    def bird_view_src_points(self) -> list:
        return self._values.get("bird_view_src_points", [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]])
    
    @bird_view_src_points.setter
    def bird_view_src_points(self, value: list):
        self.set("bird_view_src_points", value)
    
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
        states = self._values.get("ui_section_states", {})
        if not isinstance(states, dict):
            states = {}
        states[sectionId] = expanded
        self._values["ui_section_states"] = states
        self.save_all()
    
    @Slot(str, result=bool)
    def getSectionExpanded(self, sectionId: str) -> bool:
        """Get the expanded state of a UI section (QML callable). Returns True by default."""
        states = self._values.get("ui_section_states", {})
        if not isinstance(states, dict):
            return True
        return states.get(sectionId, True)
