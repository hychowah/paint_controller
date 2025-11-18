
from PySide6.QtCore import QObject, Slot
import time

class UIInputHandler(QObject):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self._r1_last_press_time = 0.0
        self._l1_last_press_time = 0.0
        self._arm_extension_presets = [800]
        self._arm_preset_index = 0

    @Slot()
    def on_l5_pressed(self):
        current_time = time.time()
        time_since_last_press = current_time - self._l1_last_press_time
        self._l1_last_press_time = current_time

        self.controller.show_popup("Extending Arm", "Press again to retract the arm", "info")
        if time_since_last_press <= 1:
            self.controller.teensy_controller.extendArm(250)

    @Slot()
    def on_r5_pressed(self):
        current_time = time.time()
        time_since_last_press = current_time - self._r1_last_press_time
        self._r1_last_press_time = current_time

        self.controller.show_popup("Extending Arm", "Press again to extend the arm", "info")
        if time_since_last_press <= 1:
            preset_value = self._arm_extension_presets[self._arm_preset_index]
            self.controller.teensy_controller.extendArm(preset_value)
            self._arm_preset_index = (self._arm_preset_index + 1) % len(self._arm_extension_presets)

    @Slot()
    def on_switch_pressed(self):
        if self.controller.control_mode == "base":
            self.controller.control_mode = "ef"
            # self.controller.overlayController.set_joystick_controls("EF Yaw Angle", "Winch Speed")
            self.controller.show_popup("Control Mode", "Switched to EF control mode", "info")
        else:
            self.controller.control_mode = "base"
            # self.controller.overlayController.set_joystick_controls("Track Control", "None")
            self.controller.show_popup("Control Mode", "Switched to Base control mode (Track Control)", "info")

    @Slot()
    def on_up_pressed(self):
        if self.controller.overlayController.is_showing_menu():
            self.controller.overlayController.move_up()

    @Slot()
    def on_down_pressed(self):
        if self.controller.overlayController.is_showing_menu():
            self.controller.overlayController.move_down()

    @Slot()
    def on_left_pressed(self):
        if self.controller.overlayController.is_showing_menu():
            self.controller.overlayController.move_to_first()
        else:
            self.controller.trajectoryHandler.switch_to_page(0)

    @Slot()
    def on_right_pressed(self):
        if self.controller.overlayController.is_showing_menu():
            self.controller.overlayController.move_to_last()
        else:
            self.controller.trajectoryHandler.switch_to_page(1)

    @Slot()
    def on_r4_pressed(self):
        self.controller.overlayController.set_active_menu("right")
        self.controller.overlayController.toggle_right_menu()

    @Slot()
    def on_l4_pressed(self):
        self.controller.overlayController.set_active_menu("left")
        self.controller.overlayController.toggle_left_menu()

    @Slot()
    def on_menu_pressed(self):
        self.controller.overlayController.set_active_menu("power")
        self.controller.overlayController.toggle_power_menu()

    @Slot()
    def on_l1_pressed(self):
        """Toggle thrust force on/off"""
        current_enabled = self.controller.teensy_controller.thrust_force_enabled
        new_enabled = not current_enabled
        self.controller.teensy_controller.set_thrust_force_enabled(new_enabled)
        status = "enabled" if new_enabled else "disabled"
        self.controller.show_popup("Thrust Force", f"Thrust force {status}", "info")