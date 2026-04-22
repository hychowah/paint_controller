from PySide6.QtCore import QObject, Property, Signal, Slot

class WarningHandler(QObject):

    warningChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._warnings: list[str] = []

    def add_warning(self, message: str) -> None:
        if message not in self._warnings:
            self._warnings.append(message)
            self.warningChanged.emit()

    @Property(list, notify=warningChanged)
    def warnings(self) -> list[str]:
        return self._warnings

    @Slot(int)
    def remove_warning(self, index: int) -> None:
        if 0 <= index < len(self._warnings):
            del self._warnings[index]
            self.warningChanged.emit()

    @Slot()
    def clear(self) -> None:
        self._warnings.clear()
        self.warningChanged.emit()