import QtQuick
import "../../features/systemcontrol"

Item {
    id: systemControlMenu

    required property bool showOverlay
    required property string activeMenu
    required property var systemControlServices
    required property var recordingStatus
    required property var winchStatus
    required property var teensyStatus

    SystemControlWorkspace {
        anchors.fill: parent
        showOverlay: systemControlMenu.showOverlay
        activeMenu: systemControlMenu.activeMenu
        systemControlServices: systemControlMenu.systemControlServices
        recordingStatus: systemControlMenu.recordingStatus
        winchStatus: systemControlMenu.winchStatus
        teensyStatus: systemControlMenu.teensyStatus
    }
}