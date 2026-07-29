from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Slot

from paint_controller.utils.constants import ControlMode, JoystickControl
from paint_controller.utils.input import DoublePressDetector

if TYPE_CHECKING:
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.core.settings import SettingsManager
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.control_processor import ControlProcessor
    from paint_controller.models.joystick_selection import JoystickSelectionModel
    from paint_controller.ui.overlay import OverlayController


logger = logging.getLogger(__name__)


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
    def on_switch_pressed(self):
        # Close any existing popup to prevent rendering conflicts during overlay switch
        try:
            self._close_popup_fn()
        except Exception as e:
            logger.warning("Could not close popup: %s", e)

        current_mode = self._state_store.control_mode
        self._selection_model.remember_current_controls(current_mode)

        if self._state_store.control_mode == ControlMode.BASE:
            # Switch to EF mode (triggers video overlay change)
            self._state_store.control_mode = ControlMode.END_EFFECTOR

            remembered_controls = self._selection_model.get_remembered_controls(ControlMode.END_EFFECTOR)
            if remembered_controls is None:
                remembered_controls = (JoystickControl.NONE, JoystickControl.WINCH_SPEED)

            left_control, right_control = remembered_controls
            self._selection_model.set_joystick_controls(left_control, right_control)

            # Reset winch activation to prevent spurious commands from centered joystick
            self._control_processor.reset_winch_activation()

            # Defer popup to let video overlay Loader stabilize (150ms)
            QTimer.singleShot(150, lambda: self._show_popup_fn("Control Mode", "Switched to EF control mode", "info"))
        else:
            # Switch to base mode (triggers video overlay change)
            self._state_store.control_mode = ControlMode.BASE

            remembered_controls = self._selection_model.get_remembered_controls(ControlMode.BASE)
            if remembered_controls is None:
                remembered_controls = (JoystickControl.TRACK_LEFT, JoystickControl.TRACK_RIGHT)

            left_control, right_control = remembered_controls
            self._selection_model.set_joystick_controls(left_control, right_control)

            # Defer popup to let video overlay Loader stabilize (150ms)
            QTimer.singleShot(
                150,
                lambda: self._show_popup_fn("Control Mode", "Switched to Base control mode (Track Control)", "info"),
            )

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
