from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Slot

from paint_controller.utils.constants import ControlMode
from paint_controller.utils.input import DoublePressDetector

if TYPE_CHECKING:
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.core.settings import SettingsManager
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.control_processor import ControlProcessor
    from paint_controller.models.joystick_selection import JoystickSelectionModel
    from paint_controller.ui.overlay import OverlayController


logger = logging.getLogger(__name__)

# Mode-switch timing budget (video-first on Deck — do not collapse without re-measure).
# | Delay | Owner                         | Role                                      |
# | 0 ms  | this module, _apply_mode      | commit StateStore.control_mode → video URL |
# | 0 ms  | VideoFullscreenWorkspace      | chromeFeed after videoSource               |
# | ~1 ms | EndEffectorOverlay heavyDecor | Canvas after EF chrome item                |
# | 80 ms | this module, popup            | toast after video + chrome tick            |
# | 66 ms | VideoFullscreenWorkspace      | ~15 Hz active-feed Image pull              |
_MODE_APPLY_DELAY_MS = 0
_MODE_POPUP_DELAY_MS = 80
_PHASE1_WARN_MS = 25.0


class UIInputHandler(QObject):
    def __init__(
        self,
        teensy: TeensyController,
        overlay: OverlayController,
        selection_model: JoystickSelectionModel,
        control_processor: ControlProcessor,
        settings_manager: SettingsManager | None,
        state_store: StateStore,
        show_popup_fn: Callable[..., None],
        close_popup_fn: Callable[[], None],
    ) -> None:
        super().__init__()
        self._teensy = teensy
        self._overlay = overlay
        self._selection_model = selection_model
        self._control_processor = control_processor
        self._settings_manager = settings_manager
        self._state_store = state_store
        self._show_popup_fn = show_popup_fn
        self._close_popup_fn = close_popup_fn

        self._l5_double_press = DoublePressDetector(threshold=1.0)
        self._r5_double_press = DoublePressDetector(threshold=1.0)
        self._a_double_press = DoublePressDetector(threshold=1.0)

        # In-flight session mode for early-return / stick transition while phase2 is pending.
        self._pending_control_mode: str | None = None
        self._mode_switch_generation = 0

        # Get arm extension presets from settings_manager if available
        if settings_manager is not None:
            self._arm_retract_length = settings_manager.get("arm_retract_length") or 250
            self._arm_extend_length = settings_manager.get("arm_extend_length") or 800
            settings_manager.arm_retract_length_changed.connect(self._on_arm_retract_length_changed)
            settings_manager.arm_extend_length_changed.connect(self._on_arm_extend_length_changed)
        else:
            self._arm_retract_length = 250
            self._arm_extend_length = 800
        self._arm_preset_index = 0

    def _on_arm_retract_length_changed(self, new_value: int) -> None:
        """Handle arm_retract_length change from SettingsManager"""
        self._arm_retract_length = new_value
        logger.info("Arm retract length updated to: %s", new_value)

    def _on_arm_extend_length_changed(self, new_value: int) -> None:
        """Handle arm_extend_length change from SettingsManager"""
        self._arm_extend_length = new_value
        logger.info("Arm extend length updated to: %s", new_value)

    @staticmethod
    def _normalize_control_mode(mode: object) -> str:
        """Return canonical ``base`` / ``ef`` (do not use str(str-Enum); that is the member name)."""
        if isinstance(mode, ControlMode):
            return mode.value
        value = getattr(mode, "value", None)
        if isinstance(value, str):
            return value
        return str(mode)

    def _effective_control_mode(self) -> str:
        """Session mode including an in-flight deferred apply (not store alone)."""
        if self._pending_control_mode is not None:
            return self._normalize_control_mode(self._pending_control_mode)
        return self._normalize_control_mode(self._state_store.control_mode)

    def switch_control_mode(self, target_mode: str) -> None:
        """Switch session control mode and restore per-mode joystick assignments.

        Absolute (not toggle). Top-bar EF/BASE requests call this so stream switch
        and stick modes stay one decision. Video follows via ``control_mode_changed``.

        Phase 1 (this turn): stick memory + winch reset when entering EF.
        Phase 2 (next event-loop turn): ``control_mode`` so video/chrome do not nest
        under stick NOTIFY. Rapid re-entry cancels/replaces the pending apply via
        generation counter so sticks and store stay on the last request.
        """
        target = self._normalize_control_mode(target_mode)
        current = self._effective_control_mode()
        if current == target:
            return

        t0 = time.perf_counter()
        try:
            self._close_popup_fn()
        except Exception as e:
            logger.warning("Could not close popup: %s", e)

        self._selection_model.transition_controls(current, target)

        if target == ControlMode.END_EFFECTOR.value:
            self._control_processor.reset_winch_activation()
            message = "Switched to EF control mode"
        else:
            message = "Switched to Base control mode (Track Control)"

        self._pending_control_mode = target
        self._mode_switch_generation += 1
        generation = self._mode_switch_generation

        def _apply_mode() -> None:
            if generation != self._mode_switch_generation:
                return
            self._state_store.control_mode = target
            if self._pending_control_mode == target:
                self._pending_control_mode = None

        def _show_mode_popup() -> None:
            if generation != self._mode_switch_generation:
                return
            self._show_popup_fn("Control Mode", message, "info")

        QTimer.singleShot(_MODE_APPLY_DELAY_MS, _apply_mode)
        QTimer.singleShot(_MODE_POPUP_DELAY_MS, _show_mode_popup)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if elapsed_ms >= _PHASE1_WARN_MS:
            logger.warning(
                "switch_control_mode(%s→%s) phase1 took %.1f ms",
                current,
                target,
                elapsed_ms,
            )

    @Slot()
    def on_l5_pressed(self):
        self._show_popup_fn("Extending Arm", "Press again to retract the arm", "info")
        if self._l5_double_press.press():
            self._teensy.extendArm(self._arm_retract_length)

    @Slot()
    def on_r5_pressed(self):
        self._show_popup_fn("Extending Arm", "Press again to extend the arm", "info")
        if self._r5_double_press.press():
            self._teensy.extendArm(self._arm_extend_length)

    @Slot()
    def on_up_pressed(self):
        if self._overlay.is_showing_menu():
            self._overlay.move_up()

    @Slot()
    def on_down_pressed(self):
        if self._overlay.is_showing_menu():
            self._overlay.move_down()

    @Slot()
    def on_left_pressed(self):
        if self._overlay.is_showing_menu():
            self._overlay.move_to_first()

    @Slot()
    def on_right_pressed(self):
        if self._overlay.is_showing_menu():
            self._overlay.move_to_last()

    @Slot()
    def on_r4_pressed(self):
        self._overlay.toggle_right_menu()

    @Slot()
    def on_l4_pressed(self):
        self._overlay.toggle_left_menu()

    @Slot()
    def on_menu_pressed(self):
        self._overlay.toggle_system_menu()

    @Slot()
    def on_l1_pressed(self):
        """Toggle thrust force on/off"""
        current_enabled = self._teensy.thrust_force_enabled
        new_enabled = not current_enabled
        self._teensy.set_thrust_force_enabled(new_enabled)
        status = "enabled" if new_enabled else "disabled"
        self._show_popup_fn("Thrust Force", f"Thrust force {status}", "info")

    @Slot()
    def on_a_pressed(self):
        """Send wheel travel position command when A button is double-pressed"""
        self._show_popup_fn("Wheel Travel", "Press again to send position command", "info")
        if self._a_double_press.press():
            self._control_processor.send_wheel_travel_command()
            self._show_popup_fn("Wheel Travel", "Position command sent", "info")
