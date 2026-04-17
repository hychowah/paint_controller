"""Qt/QML UI bridge — owns signals, popup, and toggle methods."""

from PySide6.QtCore import QMetaObject, QObject, Signal, Slot


class QtBridge(QObject):
    """Bridges controller events to QML UI. Owns UI-facing signals and actions."""

    frame_ready = Signal()
    emergency_overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    status_updated = Signal()

    # QML-bound signals (consumed by Connections {} in MainWindow.qml)
    showPopupRequested = Signal(str, str, str, int)  # title, message, type, delay
    closePopupRequested = Signal()
    navigateToPageRequested = Signal(int)
    toggleSidebarRequested = Signal()
    toggleVideoOverlayRequested = Signal(bool, str)  # active, videoSource
    updateVideoSourceRequested = Signal(str)  # videoSource

    def __init__(self, engine, state_store, logger=None, parent=None):
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
        self.showPopupRequested.emit(title, message, popup_type, dismiss_delay)
        self._log_info(f'Showing {popup_type} popup: {title} - {message}')

    @Slot()
    def close_popup(self):
        self.closePopupRequested.emit()

    def _handle_wheel_motor_error(self, has_error: bool, error_message: str):
        """Handle wheel motor error — trigger emergency stop and show popup."""
        if not has_error:
            return
        self._log_error(f'Wheel motor error detected: {error_message}')
        self.show_popup("MOTOR ERROR", error_message, "error", 5000)
        self.emergency_triggered.emit()

    @Slot()
    def toggle_sidebar(self):
        self.toggleSidebarRequested.emit()
        self._log_info('Toggled sidebar state')

    @Slot()
    def toggle_fullscreen(self):
        # Determine new state and source
        # QML side will handle the actual toggle logic via the signal
        video_source = (
            "image://ef_live/frame"
            if self._state_store.control_mode == "ef"
            else "image://base_front_live/frame"
        )
        # Emit toggle — QML reads current active state and flips it
        self.toggleVideoOverlayRequested.emit(True, video_source)
        self._log_info(f'Requested fullscreen toggle with source: {video_source}')

        if self._base_top_view_service:
            self._base_top_view_service.enabled = (self._state_store.control_mode == "base")

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
        video_source = (
            "image://ef_live/frame"
            if self._state_store.control_mode == "ef"
            else "image://base_front_live/frame"
        )
        self.updateVideoSourceRequested.emit(video_source)
        self._log_info(f'Updated fullscreen video source to: {video_source}')
        if self._base_top_view_service:
            self._base_top_view_service.enabled = (self._state_store.control_mode == "base")
