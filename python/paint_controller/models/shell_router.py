"""Python-owned shell routing policy."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot


class ShellRouter(QObject):
    """Own the operator-visible page route registry and current route.

    This model moves routing policy out of ``MainWindow.qml`` so QML stays
    declarative and Python owns which pages exist, their order, and navigation
    state.
    """

    current_route_changed = Signal(str)
    route_registry_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._current_route = "home"
        self._route_registry: list[dict[str, Any]] = [
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

    @Property(list, notify=route_registry_changed)
    def routeRegistry(self) -> list[dict[str, Any]]:
        return list(self._route_registry)

    @Property(str, notify=current_route_changed)
    def currentRoute(self) -> str:
        return self._current_route

    @Property(int, notify=current_route_changed)
    def currentRouteOrder(self) -> int:
        return self.routeOrder(self._current_route)

    @Slot(str, result=bool)
    def navigateTo(self, route: str) -> bool:
        if route == self._current_route:
            return True
        if not self._is_valid_route(route):
            return False
        self._current_route = route
        self.current_route_changed.emit(route)
        return True

    @Slot(str, result=int)
    def routeOrder(self, route: str) -> int:
        for entry in self._route_registry:
            if entry.get("key") == route:
                return int(entry.get("order", -1))
        return -1

    def _is_valid_route(self, route: str) -> bool:
        return any(entry.get("key") == route for entry in self._route_registry)
