"""Python-owned shell routing policy."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

# Single source for production + smoke FakeShellRouter (TD-042).
DEFAULT_ROUTE_REGISTRY: list[dict[str, Any]] = [
    {
        "key": "home",
        "title": "Home",
        "iconSource": "../../resource/homepage.svg",
        "iconScale": 0.7,
        "order": 0,
    },
    {
        "key": "base",
        "title": "Base",
        "iconSource": "../../resource/base.png",
        "iconScale": 0.7,
        "order": 1,
    },
    {
        "key": "winch",
        "title": "Winch",
        "iconSource": "../../resource/winch.png",
        "iconScale": 0.6,
        "order": 2,
    },
    {
        "key": "monitor",
        "title": "Monitor",
        "iconSource": "../../resource/monitor.svg",
        "iconScale": 0.6,
        "order": 3,
    },
    {
        "key": "tuning",
        "title": "Tuning",
        "iconSource": "../../resource/icon-pid.png",
        "iconScale": 0.6,
        "order": 4,
    },
    {
        "key": "launcher",
        "title": "Launcher",
        "iconSource": "../../resource/launcher.svg",
        "iconScale": 0.7,
        "order": 5,
    },
    {
        "key": "settings",
        "title": "Settings",
        "iconSource": "../../resource/setting.svg",
        "iconScale": 0.6,
        "order": 6,
    },
]


class ShellRouter(QObject):
    """Own the operator-visible page route registry and current route.

    This model moves routing policy out of ``MainWindow.qml`` so QML stays
    declarative and Python owns which pages exist, their order, and navigation
    state.
    """

    # CamelCase signal names: QML Connections matches by name
    # (onCurrentRouteChanged), same convention as QtBridge QML-facing signals.
    currentRouteChanged = Signal(str)
    routeRegistryChanged = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current_route = "home"
        self._route_registry: list[dict[str, Any]] = [dict(entry) for entry in DEFAULT_ROUTE_REGISTRY]

    @Property(list, notify=routeRegistryChanged)
    def routeRegistry(self) -> list[dict[str, Any]]:
        return list(self._route_registry)

    @Property(str, notify=currentRouteChanged)
    def currentRoute(self) -> str:
        return self._current_route

    @Property(int, notify=currentRouteChanged)
    def currentRouteOrder(self) -> int:
        return self.routeOrder(self._current_route)

    @Slot(str, result=bool)
    def navigateTo(self, route: str) -> bool:
        if route == self._current_route:
            return True
        if not self._is_valid_route(route):
            return False
        self._current_route = route
        self.currentRouteChanged.emit(route)
        return True

    @Slot(str, result=int)
    def routeOrder(self, route: str) -> int:
        for entry in self._route_registry:
            if entry.get("key") == route:
                return int(entry.get("order", -1))
        return -1

    def _is_valid_route(self, route: str) -> bool:
        return any(entry.get("key") == route for entry in self._route_registry)
