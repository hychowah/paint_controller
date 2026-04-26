"""Runtime tests for paint_controller.core.settings.SettingsManager."""

from __future__ import annotations

import json
from pathlib import Path

from paint_controller.core.settings import SettingsManager


def _make_manager(monkeypatch, tmp_path: Path, show_popup_fn=None) -> tuple[SettingsManager, Path]:
    config_path = tmp_path / "config" / "settings.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)
    manager = SettingsManager(show_popup_fn=show_popup_fn)
    return manager, config_path


def test_settings_manager_load_uses_defaults_when_config_missing(monkeypatch, tmp_path, qt_core_app):
    manager, config_path = _make_manager(monkeypatch, tmp_path)
    if config_path.exists():
        config_path.unlink()

    assert manager.load() is False
    assert manager.get("winch_max_speed_mmps") == 200.0
    assert manager.get("arm_extend_length") == 800
    assert manager.get("base_top_view_crop_enabled") is True
    assert manager.get("base_top_view_src_points") == [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]]


def test_settings_manager_load_merges_clamps_and_ignores_unknown_keys(monkeypatch, tmp_path, qt_core_app):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "settings.json"
    config_path.write_text(json.dumps({
        "winch_max_speed_mmps": 999.0,
        "arm_extend_length": 1200,
        "base_top_view_crop_enabled": False,
        "base_top_view_src_points": "invalid",
        "ui_section_states": ["bad"],
        "unknown_key": 123,
    }))
    monkeypatch.setattr(SettingsManager, "_get_config_path", lambda self: config_path)

    manager = SettingsManager()

    assert manager.get("winch_max_speed_mmps") == 400.0
    assert manager.get("arm_extend_length") == 1200
    assert manager.get("base_top_view_crop_enabled") is False
    assert manager.get("base_top_view_src_points") == [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]]
    assert manager.get("ui_section_states") == {}
    assert manager.get("unknown_key") is None


def test_settings_manager_set_emits_specific_and_generic_signals_with_clamped_value(monkeypatch, tmp_path, qt_core_app):
    manager, _ = _make_manager(monkeypatch, tmp_path)
    specific_events = []
    generic_events = []

    manager.winch_max_speed_mmps_changed.connect(specific_events.append)
    manager.setting_changed.connect(lambda key, value: generic_events.append((key, value)))

    success, message = manager.set("winch_max_speed_mmps", 999.0)

    assert success is True
    assert "400.0" in message
    assert manager.get("winch_max_speed_mmps") == 400.0
    assert specific_events == [400.0]
    assert generic_events == [("winch_max_speed_mmps", 400.0)]


def test_settings_manager_rejects_unknown_and_invalid_values_without_signals(monkeypatch, tmp_path, qt_core_app):
    manager, _ = _make_manager(monkeypatch, tmp_path)
    generic_events = []
    manager.setting_changed.connect(lambda key, value: generic_events.append((key, value)))
    original = manager.get("arm_retract_length")

    missing_success, missing_message = manager.set("missing_key", 1)
    invalid_success, invalid_message = manager.set("arm_retract_length", "bad")

    assert missing_success is False
    assert "Unknown setting" in missing_message
    assert invalid_success is False
    assert "Invalid value" in invalid_message
    assert manager.get("arm_retract_length") == original
    assert generic_events == []


def test_emergency_hold_duration_defaults_clamps_and_emits(monkeypatch, tmp_path, qt_core_app):
    manager, _ = _make_manager(monkeypatch, tmp_path)
    specific_events = []
    generic_events = []

    manager.emergency_hold_duration_s_changed.connect(specific_events.append)
    manager.setting_changed.connect(lambda key, value: generic_events.append((key, value)))

    assert manager.get("emergency_hold_duration_s") == 1.0

    success, _ = manager.set("emergency_hold_duration_s", 9.5)
    assert success is True
    assert manager.get("emergency_hold_duration_s") == 2.0

    success, _ = manager.set("emergency_hold_duration_s", 0.01)
    assert success is True
    assert manager.get("emergency_hold_duration_s") == 0.2

    assert specific_events == [2.0, 0.2]
    assert generic_events == [
        ("emergency_hold_duration_s", 2.0),
        ("emergency_hold_duration_s", 0.2),
    ]


def test_save_setting_emits_operation_result_saved_signal_and_popup(monkeypatch, tmp_path, qt_core_app):
    popup_calls = []
    manager, config_path = _make_manager(monkeypatch, tmp_path, show_popup_fn=lambda *args: popup_calls.append(args))
    operation_results = []
    saved_events = []

    manager.operation_result.connect(lambda success, message: operation_results.append((success, message)))
    manager.setting_saved.connect(lambda key, value, description: saved_events.append((key, value, description)))

    manager.set("winch_max_speed_mmps", 250.0)

    assert manager.saveSetting("winch_max_speed_mmps") is True
    saved_json = json.loads(config_path.read_text())
    assert saved_json["winch_max_speed_mmps"] == 250.0
    assert operation_results == [(True, "Settings saved successfully")]
    assert saved_events == [(
        "winch_max_speed_mmps",
        250.0,
        "Maximum winch speed limit (mm/s)",
    )]
    assert popup_calls == [(
        "Setting Saved",
        "Maximum winch speed limit (mm/s): 250.0",
        "info",
        2000,
    )]


def test_section_expansion_state_persists_and_unknown_defaults_true(monkeypatch, tmp_path, qt_core_app):
    manager, config_path = _make_manager(monkeypatch, tmp_path)

    manager.setSectionExpanded("device_winch", False)

    assert manager.getSectionExpanded("device_winch") is False
    assert manager.getSectionExpanded("unknown_section") is True
    saved_json = json.loads(config_path.read_text())
    assert saved_json["ui_section_states"] == {"device_winch": False}

    reloaded_manager, _ = _make_manager(monkeypatch, tmp_path)
    assert reloaded_manager.getSectionExpanded("device_winch") is False
    assert reloaded_manager.getSectionExpanded("unknown_section") is True


def test_save_all_keeps_last_good_file_when_json_dump_fails(monkeypatch, tmp_path, qt_core_app):
    manager, config_path = _make_manager(monkeypatch, tmp_path)
    config_path.write_text(json.dumps({"winch_max_speed_mmps": 123.0}))

    settings_module = __import__("paint_controller.core.settings", fromlist=["json"])
    original_dump = settings_module.json.dump

    def faulty_dump(payload, handle, indent=2):
        handle.write('{"broken": ')
        raise RuntimeError("simulated write failure")

    monkeypatch.setattr(settings_module.json, "dump", faulty_dump)

    success, message = manager.save_all()

    assert success is False
    assert "Failed to save settings" in message
    assert json.loads(config_path.read_text()) == {"winch_max_speed_mmps": 123.0}
    assert list(config_path.parent.glob("*.tmp")) == []
    monkeypatch.setattr(settings_module.json, "dump", original_dump)


def test_typed_qml_slots_roundtrip_and_clamp_values(monkeypatch, tmp_path, qt_core_app):
    manager, _ = _make_manager(monkeypatch, tmp_path)

    assert manager.setFloat("winch_max_speed_mmps", 999.0) is True
    assert manager.getFloat("winch_max_speed_mmps") == 400.0

    assert manager.setInt("wheel_travel_rpm", 999) is True
    assert manager.getInt("wheel_travel_rpm") == 600


def test_apply_slots_persist_without_popup_side_effects(monkeypatch, tmp_path, qt_core_app):
    popup_calls = []
    manager, config_path = _make_manager(monkeypatch, tmp_path, show_popup_fn=lambda *args: popup_calls.append(args))
    operation_results = []

    manager.operation_result.connect(lambda success, message: operation_results.append((success, message)))

    assert manager.applyFloat("track_max_speed", 999.0) is True

    saved_json = json.loads(config_path.read_text())
    assert saved_json["track_max_speed"] == 500.0
    assert operation_results == [(True, "Settings saved successfully")]
    assert popup_calls == []


def test_settings_route_summaries_reflect_current_values(monkeypatch, tmp_path, qt_core_app):
    manager, _ = _make_manager(monkeypatch, tmp_path)

    manager.set("winch_max_speed_mmps", 250.5)
    manager.set("track_max_speed", 321.0)
    manager.set("wheel_travel_max", 888.0)
    manager.set("base_top_view_zoom", 0.73)
    manager.set("base_top_view_crop_enabled", False)
    manager.set("arm_retract_length", 111)
    manager.set("arm_extend_length", 999)

    assert manager.getRouteSummary("winch") == "Max speed: 250.5 mm/s"
    assert manager.getRouteSummary("wheels") == "Track max: 321.0, travel max: 888 mm"
    assert manager.getRouteSummary("camera") == "Base-top zoom: 0.73; full calibration remains overlay-primary"
    assert manager.getRouteSummary("arm") == "Retract: 111 mm, extend: 999 mm"
    assert manager.getCameraCalibrationSummary() == "Saved zoom 0.73, crop disabled. Full calibration remains overlay-primary."