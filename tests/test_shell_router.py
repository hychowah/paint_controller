"""Tests for the ShellRouter routing model."""

from __future__ import annotations

from PySide6.QtCore import QMetaMethod

import pytest

from paint_controller.models.shell_router import ShellRouter


@pytest.fixture
def router(qtbot):
    return ShellRouter()


def test_default_route_is_home(router):
    assert router.currentRoute == "home"
    assert router.currentRouteOrder == 0


def test_current_route_notify_signal_is_camel_case_for_qml_connections(router):
    """QML Connections matches signal names; snake_case would silently no-op replace."""
    meta = router.metaObject()
    signal_names = {
        bytes(meta.method(i).name()).decode()
        for i in range(meta.methodCount())
        if meta.method(i).methodType() == QMetaMethod.MethodType.Signal
    }
    assert "currentRouteChanged" in signal_names
    assert "current_route_changed" not in signal_names
    assert "routeRegistryChanged" in signal_names
    assert "route_registry_changed" not in signal_names


def test_navigate_to_valid_route_changes_current_route(router):
    changed = []
    router.currentRouteChanged.connect(lambda route: changed.append(route))

    assert router.navigateTo("monitor") is True
    assert router.currentRoute == "monitor"
    assert router.currentRouteOrder == 3
    assert changed == ["monitor"]


def test_navigate_to_same_route_does_not_emit(router):
    changed = []
    router.currentRouteChanged.connect(lambda route: changed.append(route))

    assert router.navigateTo("home") is True
    assert router.currentRoute == "home"
    assert changed == []


def test_navigate_to_invalid_route_returns_false(router):
    assert router.navigateTo("unknown") is False
    assert router.currentRoute == "home"


def test_route_registry_has_expected_entries(router):
    registry = router.routeRegistry
    keys = [entry["key"] for entry in registry]
    assert keys == ["home", "base", "winch", "monitor", "tuning", "launcher", "settings"]
    assert registry[0]["title"] == "Home"
    assert registry[0]["iconScale"] == 0.7


def test_route_order_for_unknown_route_is_negative(router):
    assert router.routeOrder("nonexistent") == -1
