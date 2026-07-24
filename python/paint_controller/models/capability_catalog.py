from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import QObject, Property, Slot


_SETTINGS_ROUTE_PAGES: tuple[dict[str, Any], ...] = (
    {
        "page": "main",
        "title": "Settings",
        "status": "mixed-admin",
        "primarySurface": "settings_route:main",
        "summary": "Mixed admin route for persisted settings and maintenance entry points.",
        "settingKeys": [],
        "actionKeys": [],
    },
    {
        "page": "winch",
        "title": "Winch",
        "status": "truthful",
        "primarySurface": "settings_route:winch",
        "summary": "Schema-backed winch limits live here; runtime motion stays on the dedicated winch surfaces.",
        "settingKeys": ["winch_max_speed_mmps"],
        "actionKeys": [],
    },
    {
        "page": "wheels",
        "title": "Wheels",
        "status": "truthful",
        "primarySurface": "settings_route:wheels",
        "summary": "Schema-backed wheel and travel settings live here; runtime enabling and motion stay on the runtime pages.",
        "settingKeys": [
            "track_max_speed",
            "track_min_speed",
            "wheel_travel_max",
            "wheel_travel_rate",
            "wheel_travel_rpm",
        ],
        "actionKeys": [],
    },
    {
        "page": "camera",
        "title": "Camera",
        "status": "summary-only",
        "primarySurface": "overlay_popup:base_top_view",
        "summary": "Camera calibration is overlay-primary; the Settings route is summary-only in Stage 4.",
        "settingKeys": ["base_top_view_zoom", "base_top_view_crop_enabled"],
        "actionKeys": [
            "camera.base_top_view.live_adjustments",
            "camera.base_top_view.save",
            "camera.base_top_view.reset",
        ],
    },
    {
        "page": "arm",
        "title": "Arm",
        "status": "mixed-admin",
        "primarySurface": "settings_route:arm",
        "summary": "Arm presets and selected live end-effector settings are owned here; direct motion controls stay on runtime surfaces.",
        "settingKeys": [
            "arm_retract_length",
            "arm_extend_length",
            "thrust_force",
            "thrust_ramp_rate",
            "valve_turn_max",
        ],
        "actionKeys": [],
    },
)


_SETTING_CAPABILITIES: dict[str, dict[str, Any]] = {
    "winch_max_speed_mmps": {
        "title": "Maximum Speed",
        "surfaceKeys": ["settings_route:winch"],
        "primarySurface": "settings_route:winch",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-editable",
        "order": 10,
    },
    "track_max_speed": {
        "title": "Track Maximum Speed",
        "surfaceKeys": ["settings_route:wheels"],
        "primarySurface": "settings_route:wheels",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-editable",
        "order": 10,
    },
    "track_min_speed": {
        "title": "Track Minimum Speed",
        "surfaceKeys": ["settings_route:wheels"],
        "primarySurface": "settings_route:wheels",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-editable",
        "order": 20,
    },
    "thrust_force": {
        "title": "Thrust Force",
        "surfaceKeys": ["settings_route:arm", "settings_overlay:systemcontrol"],
        "primarySurface": "settings_overlay:systemcontrol",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-and-overlay-editable",
        "order": 30,
    },
    "thrust_ramp_rate": {
        "title": "Thrust Ramp Rate",
        "surfaceKeys": ["settings_route:arm", "settings_overlay:systemcontrol"],
        "primarySurface": "settings_overlay:systemcontrol",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-and-overlay-editable",
        "order": 40,
    },
    "valve_turn_max": {
        "title": "Valve Turn Maximum",
        "surfaceKeys": ["settings_route:arm", "settings_overlay:systemcontrol"],
        "primarySurface": "settings_overlay:systemcontrol",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "mixed-admin-route",
        "surfaceRole": "route-and-overlay-editable",
        "order": 50,
    },
    "arm_retract_length": {
        "title": "Retract Length",
        "surfaceKeys": ["settings_route:arm"],
        "primarySurface": "settings_route:arm",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "maintenance-preset",
        "surfaceRole": "route-editable",
        "order": 10,
    },
    "arm_extend_length": {
        "title": "Extend Length",
        "surfaceKeys": ["settings_route:arm"],
        "primarySurface": "settings_route:arm",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "maintenance-preset",
        "surfaceRole": "route-editable",
        "order": 20,
    },
    "wheel_travel_max": {
        "title": "Wheel Travel Maximum",
        "surfaceKeys": ["settings_route:wheels"],
        "primarySurface": "settings_route:wheels",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "maintenance-preset",
        "surfaceRole": "route-editable",
        "order": 30,
    },
    "wheel_travel_rate": {
        "title": "Wheel Travel Rate",
        "surfaceKeys": ["settings_route:wheels"],
        "primarySurface": "settings_route:wheels",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "maintenance-preset",
        "surfaceRole": "route-editable",
        "order": 40,
    },
    "wheel_travel_rpm": {
        "title": "Wheel Travel RPM",
        "surfaceKeys": ["settings_route:wheels"],
        "primarySurface": "settings_route:wheels",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "maintenance-preset",
        "surfaceRole": "route-editable",
        "order": 50,
    },
    "emergency_hold_duration_s": {
        "title": "Emergency Hold Duration",
        "surfaceKeys": ["settings_route:main"],
        "primarySurface": "settings_route:main",
        "capabilityClass": "persisted-setting",
        "legalStateClass": "safety-admin",
        "surfaceRole": "route-editable",
        "order": 10,
    },
    "base_top_view_zoom": {
        "title": "Base Top View Zoom",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "summarySurfaceKeys": ["settings_route:camera"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 10,
    },
    "base_top_view_offset_x": {
        "title": "Base Top View Horizontal Pan",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 20,
    },
    "base_top_view_offset_y": {
        "title": "Base Top View Vertical Pan",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 30,
    },
    "base_top_view_crop_enabled": {
        "title": "Base Top View Crop Enabled",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "summarySurfaceKeys": ["settings_route:camera"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 40,
    },
    "base_top_view_crop_width_ratio": {
        "title": "Base Top View Crop Width",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 50,
    },
    "base_top_view_crop_center_x": {
        "title": "Base Top View Crop Center",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 60,
    },
    "base_top_view_k1": {
        "title": "Base Top View Distortion K1",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 70,
    },
    "base_top_view_k2": {
        "title": "Base Top View Distortion K2",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 80,
    },
    "base_top_view_k3": {
        "title": "Base Top View Distortion K3",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 90,
    },
    "base_top_view_k4": {
        "title": "Base Top View Distortion K4",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 100,
    },
    "base_top_view_src_points": {
        "title": "Base Top View Source Points",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "capabilityClass": "persisted-and-live-apply",
        "legalStateClass": "overlay-primary-calibration",
        "surfaceRole": "overlay-editable",
        "order": 110,
    },
}


_ACTION_CAPABILITIES: dict[str, dict[str, Any]] = {
    "camera.base_top_view.live_adjustments": {
        "title": "Base Top View Live Adjustments",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "authority": "baseTopViewAdminHandler",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "overlay-primary-calibration",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [
            "base_top_view_zoom",
            "base_top_view_offset_x",
            "base_top_view_offset_y",
            "base_top_view_crop_enabled",
            "base_top_view_crop_width_ratio",
            "base_top_view_crop_center_x",
            "base_top_view_k1",
            "base_top_view_k2",
            "base_top_view_k3",
            "base_top_view_k4",
            "base_top_view_src_points",
        ],
    },
    "camera.base_top_view.save": {
        "title": "Base Top View Save",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "authority": "baseTopViewAdminHandler.saveSettings",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "overlay-primary-calibration",
        "immediateRuntimeSideEffect": False,
        "persistenceKeys": [
            "base_top_view_zoom",
            "base_top_view_offset_x",
            "base_top_view_offset_y",
            "base_top_view_crop_enabled",
            "base_top_view_crop_width_ratio",
            "base_top_view_crop_center_x",
            "base_top_view_k1",
            "base_top_view_k2",
            "base_top_view_k3",
            "base_top_view_k4",
            "base_top_view_src_points",
        ],
    },
    "camera.base_top_view.reset": {
        "title": "Base Top View Reset",
        "surfaceKeys": ["overlay_popup:base_top_view"],
        "primarySurface": "overlay_popup:base_top_view",
        "authority": "baseTopViewAdminHandler.resetToDefaults",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "overlay-primary-calibration",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [
            "base_top_view_zoom",
            "base_top_view_offset_x",
            "base_top_view_offset_y",
            "base_top_view_crop_enabled",
            "base_top_view_crop_width_ratio",
            "base_top_view_crop_center_x",
            "base_top_view_k1",
            "base_top_view_k2",
            "base_top_view_k3",
            "base_top_view_k4",
            "base_top_view_src_points",
        ],
    },
    "tuning.short_yaw_pid": {
        "title": "Short Yaw PID",
        "surfaceKeys": ["page:tuning"],
        "primarySurface": "page:tuning",
        "authority": "tuningAdminHandler.requestShortYawPid",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "tuning-calibration",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "tuning.long_yaw_pid": {
        "title": "Long Yaw PID",
        "surfaceKeys": ["page:tuning"],
        "primarySurface": "page:tuning",
        "authority": "tuningAdminHandler.requestLongYawPid",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "tuning-calibration",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "status.winch_enable": {
        "title": "Winch Enable Toggle",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:status", "page:winch"],
        "primarySurface": "page:status",
        "authority": "deviceActionHandler.requestWinchEnabled",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "status-admin",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "status.teensy_enable": {
        "title": "Teensy Enable Toggle",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:status"],
        "primarySurface": "page:status",
        "authority": "deviceActionHandler.requestTeensyEnabled",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "status-admin",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "status.teensy_relay": {
        "title": "Teensy Relay Toggle",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:status"],
        "primarySurface": "page:status",
        "authority": "deviceActionHandler.requestTeensyRelayEnabled",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "status-admin",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "wheel.enable": {
        "title": "Wheel Enable Toggle",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:wheel"],
        "primarySurface": "page:wheel",
        "authority": "deviceActionHandler.requestWheelEnabled",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "status-admin",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "wheel.reset_position": {
        "title": "Reset Wheel Position",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:wheel"],
        "primarySurface": "page:wheel",
        "authority": "deviceActionHandler.resetWheelPosition",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "maintenance-preset",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.load_detection": {
        "title": "Load Detection Toggle",
        "surfaceKeys": ["overlay:systemcontrol:devices", "page:winch"],
        "primarySurface": "page:winch",
        "authority": "deviceOperationsHandler.requestLoadDetectionEnabled",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "status-admin",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.move_increment": {
        "title": "Winch Increment Move",
        "surfaceKeys": ["page:winch"],
        "primarySurface": "page:winch",
        "authority": "winchActions.moveIncrement",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "live-operational-motion",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.move_absolute": {
        "title": "Winch Absolute Move",
        "surfaceKeys": ["page:winch"],
        "primarySurface": "page:winch",
        "authority": "winchActions.moveAbsolute",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "live-operational-motion",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.retract_full": {
        "title": "Winch Full Retract",
        "surfaceKeys": ["page:winch"],
        "primarySurface": "page:winch",
        "authority": "winchActions.retractFull",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "live-operational-motion",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.extend_one_meter": {
        "title": "Winch Extend 1m",
        "surfaceKeys": ["page:winch"],
        "primarySurface": "page:winch",
        "authority": "winchActions.extendOneMeter",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "live-operational-motion",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
    "winch.emergency_stop": {
        "title": "Winch Emergency Stop",
        "surfaceKeys": ["page:winch"],
        "primarySurface": "page:winch",
        "authority": "winchActions.emergencyStop",
        "capabilityClass": "direct-admin-action",
        "legalStateClass": "emergency-exception",
        "immediateRuntimeSideEffect": True,
        "persistenceKeys": [],
    },
}


class CapabilityCatalog(QObject):
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager

    def _get_schema(self, key: str) -> dict[str, Any]:
        if self._settings_manager is None:
            return {}
        schema = self._settings_manager.get_schema(key)
        return deepcopy(schema) if schema is not None else {}

    def _setting_capability(self, key: str) -> dict[str, Any]:
        metadata = deepcopy(_SETTING_CAPABILITIES.get(key, {}))
        schema = self._get_schema(key)
        if not metadata and not schema:
            return {}

        capability = {"key": key}
        capability.update(schema)
        capability.update(metadata)
        capability.setdefault("surfaceKeys", [])
        capability.setdefault("summarySurfaceKeys", [])
        capability.setdefault("capabilityClass", "persisted-setting")
        capability.setdefault("legalStateClass", "unclassified")
        capability.setdefault("surfaceRole", "unclassified")
        capability.setdefault("order", 999)
        return capability

    @Property("QVariantList", constant=True)
    def settingsRoutePages(self):
        return [deepcopy(page) for page in _SETTINGS_ROUTE_PAGES]

    @Property("QVariantList", constant=True)
    def adminActionInventory(self):
        return [self.getActionCapability(key) for key in sorted(_ACTION_CAPABILITIES)]

    @Slot(str, result="QVariantMap")
    def getRoutePageCapability(self, page: str):
        for entry in _SETTINGS_ROUTE_PAGES:
            if entry["page"] == page:
                return deepcopy(entry)
        return {}

    @Slot(str, result="QVariantMap")
    def getSettingCapability(self, key: str):
        return self._setting_capability(key)

    @Slot(str, result="QVariantMap")
    def getActionCapability(self, key: str):
        metadata = _ACTION_CAPABILITIES.get(key)
        if metadata is None:
            return {}
        capability = {"key": key}
        capability.update(deepcopy(metadata))
        return capability

    @Slot(str, result="QVariantList")
    def getSurfaceSettings(self, surface_key: str):
        matches = [
            self._setting_capability(key)
            for key in _SETTING_CAPABILITIES
            if surface_key in _SETTING_CAPABILITIES[key].get("surfaceKeys", [])
        ]
        return sorted(matches, key=lambda item: (item.get("order", 999), item["key"]))

    @Slot(str, result="QVariantList")
    def getSurfaceActions(self, surface_key: str):
        matches = [
            self.getActionCapability(key)
            for key in _ACTION_CAPABILITIES
            if surface_key in _ACTION_CAPABILITIES[key].get("surfaceKeys", [])
        ]
        return sorted(matches, key=lambda item: item["key"])
