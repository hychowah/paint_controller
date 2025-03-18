from PySide6.QtCore import QObject, Signal, Property, Slot

class WarningHandler(QObject):

    warningChanged = Signal()

    def __init__(self):
        super().__init__()
        self._warnings = []

    def add_warning(self, message):
        if message not in self._warnings:
            self._warnings.append(message)
            self.warningChanged.emit()

    @Property(list, notify=warningChanged)
    def warnings(self):
        return self._warnings

    @Slot(int)
    def remove_warning(self, index):
        if 0 <= index < len(self._warnings):
            del self._warnings[index]
            self.warningChanged.emit()

    @Slot()
    def clear(self):
        self._warnings.clear()
        self.warningChanged.emit()