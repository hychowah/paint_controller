import QtQuick
import "../../features/systemcontrol"

Item {
    id: systemControlMenu

    required property bool showOverlay
    required property string activeMenu

    SystemControlWorkspace {
        anchors.fill: parent
        showOverlay: systemControlMenu.showOverlay
        activeMenu: systemControlMenu.activeMenu
    }
}