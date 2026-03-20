"""Qt/QML UI bridge — owns signals, popup, and toggle methods."""

from PySide6.QtCore import QObject, Signal, Slot, QMetaObject
from PySide6.QtQml import QQmlApplicationEngine, QQmlProperty


class QtBridge(QObject):
    """Bridges controller events to QML UI. Owns UI-facing signals and actions."""

    frame_ready = Signal()
    emergency_overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    status_updated = Signal()

    def __init__(self, engine: QQmlApplicationEngine, state_store, logger=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._state_store = state_store
        self._logger = logger
        self._base_top_view_service = None
        self._input_handler = None

    def set_base_top_view_service(self, service):
        """Set after factory creates controllers (deferred wiring)."""
        self._base_top_view_service = service

    def set_input_handler(self, handler):
        """Set after factory creates controllers (deferred wiring)."""
        self._input_handler = handler

    def _log_info(self, msg):
        if self._logger:
            self._logger.info(msg)

    def _log_error(self, msg):
        if self._logger:
            self._logger.error(msg)

    @Slot(str, str, str, int)
    def show_popup(self, title: str, message: str, popup_type: str = "info", dismiss_delay: int = 500):
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self._log_error('No root QML objects found')
            return

        root = root_objects[0]
        popup = root.findChild(QObject, "messagePopup")

        if popup:
            QQmlProperty.write(popup, "messageTitle", title)
            QQmlProperty.write(popup, "messageText", message)
            QQmlProperty.write(popup, "messageType", popup_type)
            QQmlProperty.write(popup, "dismissDelay", dismiss_delay)
            QMetaObject.invokeMethod(popup, "open")
            self._log_info(f'Showing {popup_type} popup: {title} - {message}')
        else:
            self._log_error('Popup not found in QML')

    def _handle_wheel_motor_error(self, has_error: bool, error_message: str):
        """Handle wheel motor error — trigger emergency stop and show popup."""
        if not has_error:
            return
        self._log_error(f'Wheel motor error detected: {error_message}')
        # Controllers are stopped via signal connections in wire_signals()
        self.show_popup("MOTOR ERROR", error_message, "error", 5000)
        self.emergency_triggered.emit()

    @Slot()
    def toggle_sidebar(self):
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self._log_error('No root QML objects found')
            return

        root = root_objects[0]
        select_bar = root.findChild(QObject, "selectBar")

        if select_bar:
            QMetaObject.invokeMethod(select_bar, "toggleSidebar")
            self._log_info('Toggled sidebar state')
        else:
            self._log_error('SelectBar not found in QML')

    @Slot()
    def toggle_fullscreen(self):
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self._log_error('No root QML objects found')
            return

        root = root_objects[0]
        video_overlay = root.findChild(QObject, "videoFullscreenOverlay")

        if video_overlay:
            is_active = QQmlProperty.read(video_overlay, "active")

            if is_active:
                QQmlProperty.write(video_overlay, "active", False)
                self._log_info('Deactivated fullscreen overlay')
                if self._base_top_view_service:
                    self._base_top_view_service.enabled = False
            else:
                video_source = (
                    "image://ef_live/frame"
                    if self._state_store.control_mode == "ef"
                    else "image://base_front_live/frame"
                )
                QQmlProperty.write(video_overlay, "videoSource", video_source)
                QQmlProperty.write(video_overlay, "active", True)
                self._log_info(f'Activated fullscreen overlay with source: {video_source}')
                if self._base_top_view_service:
                    self._base_top_view_service.enabled = (self._state_store.control_mode == "base")
        else:
            self._log_error('VideoFullscreenOverlay not found in QML')

    @Slot()
    def toggle_lidar_overlay(self):
        if self._input_handler:
            self._input_handler.on_a_pressed()

    @Slot()
    def toggle_multiscreen_window(self):
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self._log_error('No root QML objects found')
            return

        root = root_objects[0]
        QMetaObject.invokeMethod(root, "toggleMultiScreenWindow")
        self._log_info('Toggled multi-screen test window')

    @Slot()
    def update_fullscreen_video_source(self):
        root_objects = self.engine.rootObjects()
        if not root_objects:
            return

        root = root_objects[0]
        video_overlay = root.findChild(QObject, "videoFullscreenOverlay")

        if video_overlay:
            is_active = QQmlProperty.read(video_overlay, "active")
            if is_active:
                video_source = (
                    "image://ef_live/frame"
                    if self._state_store.control_mode == "ef"
                    else "image://base_front_live/frame"
                )
                QQmlProperty.write(video_overlay, "videoSource", video_source)
                self._log_info(f'Updated fullscreen video source to: {video_source}')
                if self._base_top_view_service:
                    self._base_top_view_service.enabled = (self._state_store.control_mode == "base")
