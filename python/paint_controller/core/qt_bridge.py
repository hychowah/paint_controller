"""Qt/QML UI bridge — owns signals, popup, and toggle methods."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QMetaObject, QObject, Signal, Slot


class QtBridge(QObject):
    """Bridges controller events to QML UI. Owns UI-facing signals and actions."""

    frame_ready = Signal()
    emergency_overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    status_updated = Signal()
    display_message_changed = Signal(str)

    # QML-bound signals (consumed by Connections {} in MainWindow.qml)
    showPopupRequested = Signal(str, str, str, int)  # title, message, type, delay
    closePopupRequested = Signal()
    toggleSidebarRequested = Signal()
    toggleVideoOverlayRequested = Signal(bool, str)  # active, videoSource
    updateVideoSourceRequested = Signal(str)  # videoSource

    def __init__(
        self,
        engine: Any,
        state_store: Any,
        logger: Any = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.engine = engine
        self._state_store = state_store
        self._logger = logger
        self._base_top_view_service: Any | None = None
        self._input_handler: Any | None = None
        # Forward StateStore status line for TopBar (TD-032: retire stateStore root).
        store_signal = getattr(state_store, "display_message_changed", None)
        if callable(getattr(store_signal, "connect", None)):
            store_signal.connect(self.display_message_changed.emit)

    @Property(str, notify=display_message_changed)
    def display_message(self) -> str:
        return str(getattr(self._state_store, "display_message", "") or "")

    def set_base_top_view_service(self, service: Any) -> None:
        """Set after factory creates controllers (deferred wiring)."""
        self._base_top_view_service = service

    def set_input_handler(self, handler: Any) -> None:
        """Set after factory creates controllers (deferred wiring)."""
        self._input_handler = handler

    def _log_info(self, msg: str) -> None:
        if self._logger:
            self._logger.info(msg)

    def _log_error(self, msg: str) -> None:
        if self._logger:
            self._logger.error(msg)

    def _video_source_for_control_mode(self) -> str:
        """Return the video image-provider URI for the current control mode."""
        return (
            "image://ef_live/frame"
            if getattr(self._state_store, "control_mode", None) == "ef"
            else "image://base_front_live/frame"
        )

    @Slot(str, str, str, int)
    def show_popup(self, title: str, message: str, popup_type: str = "info", dismiss_delay: int = 500):
        self.showPopupRequested.emit(title, message, popup_type, dismiss_delay)
        self._log_info(f'Showing {popup_type} popup: {title} - {message}')

    @Slot()
    def close_popup(self):
        self.closePopupRequested.emit()

    @Slot()
    def toggle_sidebar(self):
        self.toggleSidebarRequested.emit()
        self._log_info('Toggled sidebar state')

    @Slot()
    def toggle_fullscreen(self):
        # Determine new state and source
        # QML side will handle the actual toggle logic via the signal
        video_source = self._video_source_for_control_mode()
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
        video_source = self._video_source_for_control_mode()
        self.updateVideoSourceRequested.emit(video_source)
        self._log_info(f'Updated fullscreen video source to: {video_source}')
        if self._base_top_view_service:
            self._base_top_view_service.enabled = (self._state_store.control_mode == "base")
