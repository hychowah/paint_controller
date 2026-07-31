"""Regression coverage for the joystick overlay QML surface."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from paint_controller.handlers.policy import teleop_modes
from tests.startup_smoke_support import _qml_import_url


class FakeOverlayController(QObject):
    """Test double that exposes the same QML contract as OverlayController."""

    show_overlay_changed = Signal(bool)
    left_selected_index_changed = Signal(int)
    right_selected_index_changed = Signal(int)
    active_menu_changed = Signal(str)
    control_options_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self._show_overlay = False
        self._left_selected_index = 0
        self._right_selected_index = 0
        self._active_menu = ""
        self._control_options = teleop_modes.menu_labels()

    @Property(bool, notify=show_overlay_changed)
    def show_overlay(self) -> bool:
        return self._show_overlay

    @Property(int, notify=left_selected_index_changed)
    def left_selected_index(self) -> int:
        return self._left_selected_index

    @Property(int, notify=right_selected_index_changed)
    def right_selected_index(self) -> int:
        return self._right_selected_index

    @Property(str, notify=active_menu_changed)
    def active_menu(self) -> str:
        return self._active_menu

    @Property(object, notify=control_options_changed)
    def control_options(self) -> list[str]:
        return self._control_options

    @Slot(int, result=bool)
    def select_index(self, index: int) -> bool:
        if index < 0:
            return False
        if self._active_menu == "left":
            self._left_selected_index = index
            self.left_selected_index_changed.emit(index)
        elif self._active_menu == "right":
            self._right_selected_index = index
            self.right_selected_index_changed.emit(index)
        self._show_overlay = False
        self.show_overlay_changed.emit(False)
        return True


def _find_items_by_object_name(item: QObject, name: str) -> list[QObject]:
    """Recursively walk QQuickItem.childItems() to find items by objectName.

    QObject.findChildren does not reliably locate ListView delegates because they
    live under the ListView's contentItem in the QQuickItem tree.
    """
    results: list[QObject] = []
    if item.objectName() == name:
        results.append(item)
    child_items = getattr(item, "childItems", lambda: [])()
    for child in child_items:
        results.extend(_find_items_by_object_name(child, name))
    return results


def test_pressed_feedback_hides_when_menu_closes(qt_app, qtbot) -> None:
    """The delegate's pressed highlight must not remain visible after the menu hides.

    Regression for the lingering lighter-blue pressed background reported on the
    joystick selection overlay. The pressed-feedback rectangle is guarded by
    menuVisible so delegate recycling cannot resurrect the highlight.
    """
    repo_root = Path(__file__).resolve().parent.parent
    qml_dir = repo_root / "python" / "paint_controller" / "qml"
    overlays_import_url = _qml_import_url(qml_dir / "overlays")

    controller = FakeOverlayController()

    engine = QQmlApplicationEngine()
    engine.addImportPath(str(qml_dir))

    harness_dir = qml_dir / "test_harness"
    harness_dir.mkdir(exist_ok=True)
    harness_path = harness_dir / "JoystickOverlayHarness.qml"
    harness_path.write_text(
        '''
import QtQuick
import "../overlays"

Item {
    id: harnessRoot
    width: 1280
    height: 800

    property bool showOverlay: false
    property int leftSelectedIndex: 0
    property int rightSelectedIndex: 0
    property string activeMenu: ""
    property var controlOptions: []
    property var overlayController: null

    JoystickOverlay {
        objectName: "joystickOverlayInstance"
        anchors.fill: parent
        showOverlay: parent.showOverlay
        leftSelectedIndex: parent.leftSelectedIndex
        rightSelectedIndex: parent.rightSelectedIndex
        activeMenu: parent.activeMenu
        controlOptions: parent.controlOptions
        overlayController: parent.overlayController
    }
}
'''
    )

    try:
        component = QQmlComponent(engine)
        component.loadUrl(QUrl.fromLocalFile(str(harness_path)))
        qtbot.waitUntil(lambda: component.isReady() or component.isError(), timeout=2000)
        assert component.isReady(), [str(error) for error in component.errors()]

        initial_props = {
            "showOverlay": True,
            "leftSelectedIndex": 0,
            "rightSelectedIndex": 0,
            "activeMenu": "left",
            "controlOptions": controller.control_options,
            "overlayController": controller,
        }
        root = component.createWithInitialProperties(initial_props)
        qt_app.processEvents()
        assert root is not None, [str(error) for error in component.errors()]

        overlay = root.findChild(QObject, "joystickOverlayInstance")
        assert overlay is not None

        qtbot.wait(100)
        qt_app.processEvents()

        delegates = _find_items_by_object_name(overlay, "joystickMenuDelegate")
        assert len(delegates) > 0, "JoystickOverlay rendered no delegates"
        first_delegate = delegates[0]

        first_delegate.setProperty("visuallyPressed", True)
        assert first_delegate.property("visuallyPressed") is True

        feedback_items = _find_items_by_object_name(first_delegate, "joystickPressedFeedback")
        assert len(feedback_items) == 1
        assert feedback_items[0].property("visible") is True

        # Hide the menu. The pressed feedback must disappear even though the
        # delegate's visuallyPressed state is still true.
        overlay.setProperty("showOverlay", False)
        qtbot.wait(50)
        qt_app.processEvents()

        assert feedback_items[0].property("visible") is False
    finally:
        harness_path.unlink(missing_ok=True)
        root_objects = engine.rootObjects()
        for obj in root_objects:
            obj.deleteLater()
        qt_app.processEvents()
