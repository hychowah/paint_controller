"""Python-owned, feature-root action boundary for recording controls."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot


class SupportsEfBaseRecording(Protocol):
    def toggleRecording(self) -> object: ...

    def toggleBaseRecording(self) -> object: ...


class SupportsScreenRecording(Protocol):
    def toggleRecording(self) -> object: ...


class SupportsRosBagRecording(Protocol):
    def toggleBagRecording(self) -> object: ...


class RecordingActions(QObject):
    """Own recording toggles initiated from QML.

    TD-055.7: typed invoke — no string method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        video_stream_handler: SupportsEfBaseRecording | None,
        screen_recorder: SupportsScreenRecording | None,
        ros_bag_recorder: SupportsRosBagRecording | None,
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
        return self._run(
            name="EF camera recording",
            controller=self._video_stream_handler,
            invoke=lambda c: c.toggleRecording(),
        )

    @Slot(result=bool)
    def toggleBaseRecording(self) -> bool:
        return self._run(
            name="Base camera recording",
            controller=self._video_stream_handler,
            invoke=lambda c: c.toggleBaseRecording(),
        )

    @Slot(result=bool)
    def toggleScreenRecording(self) -> bool:
        return self._run(
            name="Screen recording",
            controller=self._screen_recorder,
            invoke=lambda c: c.toggleRecording(),
        )

    @Slot(result=bool)
    def toggleRosBagRecording(self) -> bool:
        return self._run(
            name="ROS bag recording",
            controller=self._ros_bag_recorder,
            invoke=lambda c: c.toggleBagRecording(),
        )

    def _run(self, *, name: str, controller: Any, invoke) -> bool:
        if controller is None:
            return self._fail(f"{name} is unavailable")
        try:
            result = invoke(controller)
        except Exception as exc:  # pragma: no cover
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
