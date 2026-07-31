"""Schema-driven base class for simple device status wrappers.

A "simple" wrapper projects scalar controller attributes to camelCase QML
properties with one notify signal per property. It keeps per-property NOTIFY
(TD-037) and fail-loud wiring via ``connect_required``.

Complex wrappers (e.g. ``TeensyStatus`` with dict caching and controller
property refresh) should remain hand-written.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required


def _make_status_field(controller_attr: str, py_type: type, default: Any) -> tuple[Signal, Property]:
    """Create a ``(Signal, Property)`` pair for one status field.

    The property reads ``controller_attr`` from the wrapper's controller and
    coerces it with the wrapper's ``_bool`` / ``_float`` helpers.
    """
    signal = Signal()

    def getter(self) -> Any:
        if py_type is bool:
            return self._bool(controller_attr, default)
        if py_type is float:
            return self._float(controller_attr, default)
        return getattr(self._c, controller_attr, default)

    return signal, Property(py_type, getter, notify=signal)


class SimpleDeviceStatus(QObject):
    """Base for per-property-NOTIFY status wrappers.

    Subclasses must define ``_STATUS_SCHEMA`` entries of the form::

        (producer_signal, controller_attr, notify_signal_name, py_type)

    and declare one ``notify_signal_name, property_name = _make_status_field(...)``
    class attribute per entry.
    """

    _STATUS_SCHEMA: tuple[tuple[str, str, str, type], ...] = ()

    def __init__(self, controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = controller
        for producer_signal, _controller_attr, notify_signal_name, _py_type in self._STATUS_SCHEMA:
            notify = getattr(self, notify_signal_name, None)
            if notify is None or not hasattr(notify, "emit"):
                raise AttributeError(f"Missing notify signal {notify_signal_name!r} on {type(self).__name__}")
            connect_required(controller, producer_signal, notify.emit)

    def _bool(self, name: str, default: bool = False) -> bool:
        return bool(getattr(self._c, name, default))

    def _float(self, name: str, default: float = 0.0) -> float:
        value = getattr(self._c, name, default)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0
