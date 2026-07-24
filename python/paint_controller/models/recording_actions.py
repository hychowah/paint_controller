"""Python-owned, feature-root action boundary for recording controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class RecordingActions(QObject):
    """Own recording toggles initiated from QML.

    This model absorbs the recording policy previously held by
    ``DeviceOperationsHandler`` so that QML accesses camera, screen, and ROS bag
    recording through a single feature-root object rather than a handler-shaped
    global.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        video_stream_handler: Any,
        screen_recorder: Any,
        ros_bag_recorder: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._video_stream_handler = video_stream_handler
        self._screen_recorder = screen_recorder
        self._ros_bag_recorder = ros_bag_recorder
        self._logger = logger

    @Slot(result=bool)
    def toggleEndEffectorRecording(self) -> bool:
        return self._run_action(
            name="EF camera recording",
            controller=self._video_stream_handler,
            method_name="toggleRecording",
        )

    @Slot(result=bool)
    def toggleBaseRecording(self) -> bool:
        return self._run_action(
            name="Base camera recording",
            controller=self._video_stream_handler,
            method_name="toggleBaseRecording",
        )

    @Slot(result=bool)
    def toggleScreenRecording(self) -> bool:
        return self._run_action(
            name="Screen recording",
            controller=self._screen_recorder,
            method_name="toggleRecording",
        )

    @Slot(result=bool)
    def toggleRosBagRecording(self) -> bool:
        return self._run_action(
            name="ROS bag recording",
            controller=self._ros_bag_recorder,
            method_name="toggleBagRecording",
        )

    def _run_action(
        self,
        *,
        name: str,
        controller: Any,
        method_name: str,
        args: tuple[Any, ...] = (),
    ) -> bool:
        if controller is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(controller, method_name, None)
        if not callable(method):
            return self._fail(f"{name} is unavailable")

        try:
            result = method(*args)
        except Exception as exc:  # pragma: no cover - defensive boundary guard
            return self._fail(f"{name} failed: {exc}")

        if result is False:
            return self._fail(f"{name} was rejected by the backend")

        message = f"{name} requested"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False
