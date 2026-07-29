import QtQuick
import "../../features/systemcontrol"

Item {
    id: systemControlMenu

    required property bool showOverlay
    required property string activeMenu
    required property var systemControlServices
    required property var recordingStatus
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var wheelActions
    required property var winchActions
    required property var teensyActions
    required property var recordingActions
    required property var systemActions
    required property var actionLegality
    required property var settingsManager
    required property var overlayController

    SystemControlWorkspace {
        anchors.fill: parent
        showOverlay: systemControlMenu.showOverlay
        activeMenu: systemControlMenu.activeMenu
        systemControlServices: systemControlMenu.systemControlServices
        recordingStatus: systemControlMenu.recordingStatus
        wheelStatus: systemControlMenu.wheelStatus
        winchStatus: systemControlMenu.winchStatus
        teensyStatus: systemControlMenu.teensyStatus
        wheelActions: systemControlMenu.wheelActions
        winchActions: systemControlMenu.winchActions
        teensyActions: systemControlMenu.teensyActions
        recordingActions: systemControlMenu.recordingActions
        systemActions: systemControlMenu.systemActions
        actionLegality: systemControlMenu.actionLegality
        settingsManager: systemControlMenu.settingsManager
        overlayController: systemControlMenu.overlayController
    }
}
