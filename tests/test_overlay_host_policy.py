from __future__ import annotations

from paint_controller.models.overlay_host_policy import OverlayHostPolicy
from paint_controller.models.shell_state import ShellState
from tests.test_shell_state import FakeScreenManager


def test_overlay_host_policy_defaults_to_single_surface_hosts(qt_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    policy = OverlayHostPolicy(shell_state=shell_state)

    assert policy.system_control_on_main_surface is True
    assert policy.system_control_on_secondary_surface is False
    assert policy.joystick_overlay_on_main_surface is True
    assert policy.joystick_overlay_on_secondary_surface is False
    assert policy.video_fullscreen_on_main_surface is True
    assert policy.video_fullscreen_on_secondary_surface is False
    assert policy.emergency_overlay_on_main_surface is True
    assert policy.emergency_overlay_on_secondary_surface is False


def test_overlay_host_policy_uses_dual_surface_host_matrix(qt_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=2))
    policy = OverlayHostPolicy(shell_state=shell_state)

    assert policy.system_control_on_main_surface is False
    assert policy.system_control_on_secondary_surface is True
    assert policy.joystick_overlay_on_main_surface is False
    assert policy.joystick_overlay_on_secondary_surface is True
    assert policy.video_fullscreen_on_main_surface is True
    assert policy.video_fullscreen_on_secondary_surface is False
    assert policy.emergency_overlay_on_main_surface is True
    assert policy.emergency_overlay_on_secondary_surface is True


def test_overlay_host_policy_reacts_to_shell_state_changes(qt_app) -> None:
    screen_manager = FakeScreenManager(screen_count=1)
    shell_state = ShellState(screen_manager=screen_manager)
    policy = OverlayHostPolicy(shell_state=shell_state)

    screen_manager.set_screen_count(2)

    assert policy.system_control_on_main_surface is False
    assert policy.system_control_on_secondary_surface is True
    assert policy.joystick_overlay_on_main_surface is False
    assert policy.joystick_overlay_on_secondary_surface is True
    assert policy.emergency_overlay_on_secondary_surface is True


def test_overlay_host_policy_tracks_video_fullscreen_state(qt_app) -> None:
    shell_state = ShellState(screen_manager=FakeScreenManager(screen_count=1))
    policy = OverlayHostPolicy(shell_state=shell_state)

    policy.toggle_video_fullscreen("image://base_front_live/frame")
    assert policy.video_fullscreen_active is True
    assert policy.video_fullscreen_source == "image://base_front_live/frame"

    policy.set_video_fullscreen_source("image://ef_live/frame")
    assert policy.video_fullscreen_source == "image://ef_live/frame"

    policy.hide_video_fullscreen()
    assert policy.video_fullscreen_active is False
