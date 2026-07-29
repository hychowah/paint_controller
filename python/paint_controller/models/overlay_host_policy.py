from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot


class OverlayHostPolicy(QObject):
    """Own overlay host placement and fullscreen-video host state."""

    layout_changed = Signal()
    video_fullscreen_active_changed = Signal(bool)
    video_fullscreen_source_changed = Signal(str)

    def __init__(self, shell_state: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._shell_state = shell_state
        self._system_control_on_main_surface = True
        self._system_control_on_secondary_surface = False
        self._joystick_overlay_on_main_surface = True
        self._joystick_overlay_on_secondary_surface = False
        self._video_fullscreen_on_main_surface = True
        self._video_fullscreen_on_secondary_surface = False
        self._emergency_overlay_on_main_surface = True
        self._emergency_overlay_on_secondary_surface = False
        self._video_fullscreen_active = False
        self._video_fullscreen_source = ""

        for signal_name in (
            "screen_count_changed",
            "secondary_surface_active_changed",
            "show_system_control_on_main_surface_changed",
            "show_system_control_on_secondary_surface_changed",
            "video_fullscreen_on_main_surface_changed",
        ):
            signal = getattr(shell_state, signal_name, None)
            if signal is not None:
                signal.connect(self.refresh_layout)

        self.refresh_layout()

    @Property(bool, notify=layout_changed)
    def system_control_on_main_surface(self) -> bool:
        return self._system_control_on_main_surface

    @Property(bool, notify=layout_changed)
    def system_control_on_secondary_surface(self) -> bool:
        return self._system_control_on_secondary_surface

    @Property(bool, notify=layout_changed)
    def joystick_overlay_on_main_surface(self) -> bool:
        return self._joystick_overlay_on_main_surface

    @Property(bool, notify=layout_changed)
    def joystick_overlay_on_secondary_surface(self) -> bool:
        return self._joystick_overlay_on_secondary_surface

    @Property(bool, notify=layout_changed)
    def video_fullscreen_on_main_surface(self) -> bool:
        return self._video_fullscreen_on_main_surface

    @Property(bool, notify=layout_changed)
    def video_fullscreen_on_secondary_surface(self) -> bool:
        return self._video_fullscreen_on_secondary_surface

    @Property(bool, notify=layout_changed)
    def emergency_overlay_on_main_surface(self) -> bool:
        return self._emergency_overlay_on_main_surface

    @Property(bool, notify=layout_changed)
    def emergency_overlay_on_secondary_surface(self) -> bool:
        return self._emergency_overlay_on_secondary_surface

    @Property(int, constant=True)
    def system_control_layer(self) -> int:
        return 1001

    @Property(int, constant=True)
    def joystick_overlay_layer(self) -> int:
        return 1000

    @Property(int, constant=True)
    def video_fullscreen_layer(self) -> int:
        return 500

    @Property(int, constant=True)
    def emergency_overlay_layer(self) -> int:
        return 3000

    @Property(bool, notify=video_fullscreen_active_changed)
    def video_fullscreen_active(self) -> bool:
        return self._video_fullscreen_active

    @Property(str, notify=video_fullscreen_source_changed)
    def video_fullscreen_source(self) -> str:
        return self._video_fullscreen_source

    @Slot()
    def refresh_layout(self) -> None:
        secondary_surface_active = bool(getattr(self._shell_state, "secondary_surface_active", False))
        video_on_main = bool(getattr(self._shell_state, "video_fullscreen_on_main_surface", True))
        system_on_main = bool(getattr(self._shell_state, "show_system_control_on_main_surface", True))
        system_on_secondary = bool(getattr(self._shell_state, "show_system_control_on_secondary_surface", False))

        changed = False
        changed |= self._set_layout_attr("_system_control_on_main_surface", system_on_main)
        changed |= self._set_layout_attr("_system_control_on_secondary_surface", system_on_secondary)
        changed |= self._set_layout_attr("_joystick_overlay_on_main_surface", not secondary_surface_active)
        changed |= self._set_layout_attr("_joystick_overlay_on_secondary_surface", secondary_surface_active)
        changed |= self._set_layout_attr("_video_fullscreen_on_main_surface", video_on_main)
        changed |= self._set_layout_attr(
            "_video_fullscreen_on_secondary_surface",
            secondary_surface_active and not video_on_main,
        )
        changed |= self._set_layout_attr("_emergency_overlay_on_main_surface", True)
        changed |= self._set_layout_attr("_emergency_overlay_on_secondary_surface", secondary_surface_active)

        if changed:
            self.layout_changed.emit()

    @Slot(str)
    def toggle_video_fullscreen(self, video_source: str) -> None:
        if self._video_fullscreen_active:
            self.hide_video_fullscreen()
            return
        self.show_video_fullscreen(video_source)

    @Slot(str)
    def show_video_fullscreen(self, video_source: str) -> None:
        self.set_video_fullscreen_source(video_source)
        self._set_video_fullscreen_active(True)

    @Slot()
    def hide_video_fullscreen(self) -> None:
        self._set_video_fullscreen_active(False)

    @Slot(str)
    def set_video_fullscreen_source(self, video_source: str) -> None:
        if video_source == self._video_fullscreen_source:
            return
        self._video_fullscreen_source = video_source
        self.video_fullscreen_source_changed.emit(video_source)

    def _set_layout_attr(self, name: str, value: bool) -> bool:
        if getattr(self, name) == value:
            return False
        setattr(self, name, value)
        return True

    def _set_video_fullscreen_active(self, active: bool) -> None:
        if active == self._video_fullscreen_active:
            return
        self._video_fullscreen_active = active
        self.video_fullscreen_active_changed.emit(active)
