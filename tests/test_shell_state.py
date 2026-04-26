from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.shell_state import ShellState


class FakeScreenManager(QObject):
    screens_changed = Signal()

    def __init__(self, screen_count: int = 1) -> None:
        super().__init__()
        self._screen_count = screen_count

    @Slot(result=int)
    def get_screen_count(self) -> int:
        return self._screen_count

    def set_screen_count(self, screen_count: int) -> None:
        self._screen_count = screen_count
        self.screens_changed.emit()


def test_shell_state_defaults_to_single_surface_policy(qt_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))

    assert shell_state.screen_count == 1
    assert shell_state.main_surface_screen_index == 0
    assert shell_state.secondary_surface_screen_index == 0
    assert shell_state.secondary_surface_active is False
    assert shell_state.secondary_surface_fullscreen is False
    assert shell_state.show_system_control_on_main_surface is True
    assert shell_state.show_system_control_on_secondary_surface is False
    assert shell_state.video_fullscreen_on_main_surface is True


def test_shell_state_uses_dual_surface_policy_when_second_screen_exists(qt_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=2))

    assert shell_state.screen_count == 2
    assert shell_state.main_surface_screen_index == 1
    assert shell_state.secondary_surface_screen_index == 0
    assert shell_state.secondary_surface_active is True
    assert shell_state.secondary_surface_fullscreen is True
    assert shell_state.show_system_control_on_main_surface is False
    assert shell_state.show_system_control_on_secondary_surface is True


def test_shell_state_reacts_to_screen_manager_changes(qt_app) -> None:
    screen_manager = FakeScreenManager(screen_count=1)
    shell_state = ShellState(screen_manager=screen_manager)

    screen_manager.set_screen_count(2)

    assert shell_state.screen_count == 2
    assert shell_state.main_surface_screen_index == 1
    assert shell_state.secondary_surface_active is True
    assert shell_state.show_system_control_on_main_surface is False
    assert shell_state.show_system_control_on_secondary_surface is True

    screen_manager.set_screen_count(1)

    assert shell_state.screen_count == 1
    assert shell_state.main_surface_screen_index == 0
    assert shell_state.secondary_surface_active is False
    assert shell_state.show_system_control_on_main_surface is True
    assert shell_state.show_system_control_on_secondary_surface is False