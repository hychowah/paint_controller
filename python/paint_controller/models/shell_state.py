from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot


class ShellState(QObject):
    """Own product shell policy derived from screen facts."""

    screen_count_changed = Signal(int)
    main_surface_screen_index_changed = Signal(int)
    secondary_surface_screen_index_changed = Signal(int)
    secondary_surface_active_changed = Signal(bool)
    secondary_surface_fullscreen_changed = Signal(bool)
    show_system_control_on_main_surface_changed = Signal(bool)
    show_system_control_on_secondary_surface_changed = Signal(bool)
    video_fullscreen_on_main_surface_changed = Signal(bool)

    def __init__(self, screen_manager: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._screen_manager = screen_manager
        self._screen_count = 1
        self._main_surface_screen_index = 0
        self._secondary_surface_screen_index = 0
        self._secondary_surface_active = False
        self._secondary_surface_fullscreen = False
        self._show_system_control_on_main_surface = True
        self._show_system_control_on_secondary_surface = False
        self._video_fullscreen_on_main_surface = True

        if hasattr(screen_manager, "screens_changed"):
            screen_manager.screens_changed.connect(self.refresh_from_screen_manager)

        self.refresh_from_screen_manager()

    @Property(int, notify=screen_count_changed)
    def screen_count(self) -> int:
        return self._screen_count

    @Property(int, notify=main_surface_screen_index_changed)
    def main_surface_screen_index(self) -> int:
        return self._main_surface_screen_index

    @Property(int, notify=secondary_surface_screen_index_changed)
    def secondary_surface_screen_index(self) -> int:
        return self._secondary_surface_screen_index

    @Property(bool, notify=secondary_surface_active_changed)
    def secondary_surface_active(self) -> bool:
        return self._secondary_surface_active

    @Property(bool, notify=secondary_surface_fullscreen_changed)
    def secondary_surface_fullscreen(self) -> bool:
        return self._secondary_surface_fullscreen

    @Property(bool, notify=show_system_control_on_main_surface_changed)
    def show_system_control_on_main_surface(self) -> bool:
        return self._show_system_control_on_main_surface

    @Property(bool, notify=show_system_control_on_secondary_surface_changed)
    def show_system_control_on_secondary_surface(self) -> bool:
        return self._show_system_control_on_secondary_surface

    @Property(bool, notify=video_fullscreen_on_main_surface_changed)
    def video_fullscreen_on_main_surface(self) -> bool:
        return self._video_fullscreen_on_main_surface

    @Slot()
    def refresh_from_screen_manager(self) -> None:
        if self._screen_manager is None or not hasattr(self._screen_manager, "get_screen_count"):
            self.apply_screen_count(1)
            return

        screen_count = int(self._screen_manager.get_screen_count())
        self.apply_screen_count(screen_count)

    @Slot(int)
    def apply_screen_count(self, screen_count: int) -> None:
        normalized_count = max(1, screen_count)
        has_secondary_surface = normalized_count > 1

        self._set_screen_count(normalized_count)
        self._set_main_surface_screen_index(1 if has_secondary_surface else 0)
        self._set_secondary_surface_screen_index(0)
        self._set_secondary_surface_active(has_secondary_surface)
        self._set_secondary_surface_fullscreen(has_secondary_surface)
        self._set_show_system_control_on_main_surface(not has_secondary_surface)
        self._set_show_system_control_on_secondary_surface(has_secondary_surface)
        self._set_video_fullscreen_on_main_surface(True)

    def _set_screen_count(self, value: int) -> None:
        if self._screen_count == value:
            return
        self._screen_count = value
        self.screen_count_changed.emit(value)

    def _set_main_surface_screen_index(self, value: int) -> None:
        if self._main_surface_screen_index == value:
            return
        self._main_surface_screen_index = value
        self.main_surface_screen_index_changed.emit(value)

    def _set_secondary_surface_screen_index(self, value: int) -> None:
        if self._secondary_surface_screen_index == value:
            return
        self._secondary_surface_screen_index = value
        self.secondary_surface_screen_index_changed.emit(value)

    def _set_secondary_surface_active(self, value: bool) -> None:
        if self._secondary_surface_active == value:
            return
        self._secondary_surface_active = value
        self.secondary_surface_active_changed.emit(value)

    def _set_secondary_surface_fullscreen(self, value: bool) -> None:
        if self._secondary_surface_fullscreen == value:
            return
        self._secondary_surface_fullscreen = value
        self.secondary_surface_fullscreen_changed.emit(value)

    def _set_show_system_control_on_main_surface(self, value: bool) -> None:
        if self._show_system_control_on_main_surface == value:
            return
        self._show_system_control_on_main_surface = value
        self.show_system_control_on_main_surface_changed.emit(value)

    def _set_show_system_control_on_secondary_surface(self, value: bool) -> None:
        if self._show_system_control_on_secondary_surface == value:
            return
        self._show_system_control_on_secondary_surface = value
        self.show_system_control_on_secondary_surface_changed.emit(value)

    def _set_video_fullscreen_on_main_surface(self, value: bool) -> None:
        if self._video_fullscreen_on_main_surface == value:
            return
        self._video_fullscreen_on_main_surface = value
        self.video_fullscreen_on_main_surface_changed.emit(value)
