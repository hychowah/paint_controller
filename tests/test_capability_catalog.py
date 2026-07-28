from __future__ import annotations

from pathlib import Path

from paint_controller.core.settings import SettingsManager, _SETTINGS_SCHEMA
from paint_controller.models.capability_catalog import (
    CapabilityCatalog,
    _SETTING_CAPABILITIES,
)


def _make_manager(monkeypatch, tmp_path: Path) -> SettingsManager:
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    return SettingsManager()


def test_capability_catalog_exposes_truthful_settings_route_pages(monkeypatch, tmp_path, qt_core_app):
    manager = _make_manager(monkeypatch, tmp_path)
    catalog = CapabilityCatalog(settings_manager=manager)

    pages = {entry["page"]: entry for entry in catalog.settingsRoutePages}

    assert pages["winch"]["status"] == "truthful"
    assert pages["wheels"]["status"] == "truthful"
    assert pages["arm"]["status"] == "mixed-admin"
    assert pages["camera"]["primarySurface"] == "overlay_popup:base_top_view"
    assert pages["camera"]["status"] == "summary-only"


def test_capability_catalog_merges_settings_schema_with_surface_metadata(monkeypatch, tmp_path, qt_core_app):
    manager = _make_manager(monkeypatch, tmp_path)
    catalog = CapabilityCatalog(settings_manager=manager)

    thrust = catalog.getSettingCapability("thrust_force")
    wheel_rpm = catalog.getSettingCapability("wheel_travel_rpm")
    camera_zoom = catalog.getSettingCapability("base_top_view_zoom")

    assert thrust["min"] == -1.5
    assert thrust["max"] == 1.5
    assert thrust["capabilityClass"] == "persisted-and-live-apply"
    assert thrust["primarySurface"] == "settings_overlay:systemcontrol"
    assert "settings_route:arm" in thrust["surfaceKeys"]

    assert wheel_rpm["type"] == "int"
    assert wheel_rpm["primarySurface"] == "settings_route:wheels"

    assert camera_zoom["primarySurface"] == "overlay_popup:base_top_view"
    assert "settings_route:camera" in camera_zoom["summarySurfaceKeys"]


def test_capability_catalog_inventories_known_admin_mutators(monkeypatch, tmp_path, qt_core_app):
    manager = _make_manager(monkeypatch, tmp_path)
    catalog = CapabilityCatalog(settings_manager=manager)

    tuning = catalog.getActionCapability("tuning.short_yaw_pid")
    relay = catalog.getActionCapability("status.teensy_relay")
    wheel_reset = catalog.getActionCapability("wheel.reset_position")
    winch_increment = catalog.getActionCapability("winch.move_increment")
    camera_actions = catalog.getSurfaceActions("overlay_popup:base_top_view")
    winch_actions = catalog.getSurfaceActions("page:winch")

    assert tuning["authority"] == "tuningActions.setShortYawPid"
    assert tuning["immediateRuntimeSideEffect"] is True
    assert tuning["legalStateClass"] == "tuning-calibration"

    assert relay["authority"] == "deviceActionHandler.requestTeensyRelayEnabled"
    assert relay["primarySurface"] == "page:status"

    assert wheel_reset["authority"] == "wheelActions.resetPosition"
    assert wheel_reset["legalStateClass"] == "maintenance-preset"

    assert winch_increment["authority"] == "winchActions.moveIncrement"
    assert winch_increment["legalStateClass"] == "live-operational-motion"

    load_detection = catalog.getActionCapability("winch.load_detection")
    assert load_detection["authority"] == "winchActions.setLoadDetectionEnabled"

    assert [action["key"] for action in camera_actions] == [
        "camera.base_top_view.live_adjustments",
        "camera.base_top_view.reset",
        "camera.base_top_view.save",
    ]
    assert [action["key"] for action in winch_actions] == [
        "status.winch_enable",
        "winch.emergency_stop",
        "winch.extend_one_meter",
        "winch.load_detection",
        "winch.move_absolute",
        "winch.move_increment",
        "winch.retract_full",
    ]


def test_machine_schema_keys_have_setting_capabilities() -> None:
    """TD-036: QML-writable machine settings must have catalog legal metadata."""
    skip = {"ui_section_states", "action_legality_enforced"}
    missing = [
        key
        for key in _SETTINGS_SCHEMA
        if key not in skip and key not in _SETTING_CAPABILITIES
    ]
    assert missing == [], f"schema keys missing _SETTING_CAPABILITIES: {missing}"


def test_capability_catalog_filters_surface_settings(monkeypatch, tmp_path, qt_core_app):
    manager = _make_manager(monkeypatch, tmp_path)
    catalog = CapabilityCatalog(settings_manager=manager)

    arm_settings = catalog.getSurfaceSettings("settings_route:arm")
    wheel_settings = catalog.getSurfaceSettings("settings_route:wheels")

    assert [item["key"] for item in arm_settings] == [
        "arm_retract_length",
        "arm_extend_length",
        "thrust_force",
        "thrust_ramp_rate",
        "valve_turn_max",
    ]
    assert [item["key"] for item in wheel_settings] == [
        "track_max_speed",
        "track_min_speed",
        "wheel_travel_max",
        "wheel_travel_rate",
        "wheel_travel_rpm",
    ]