import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "../../components/popups"
import "../../navigation"
import "../../overlays/systemcontrol" as LegacySystemControl

Item {
    id: systemControlWorkspace

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
    readonly property bool showSystemMenu: showOverlay && activeMenu === "system"

    visible: true

    Rectangle {
        id: systemOverlayBackground
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: showSystemMenu ? 0.5 : 0
        visible: opacity > 0

        Behavior on opacity {
            NumberAnimation {
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad
            }
        }

        MouseArea {
            anchors.fill: parent
            enabled: showSystemMenu
            onClicked: {}
        }
    }

    Rectangle {
        id: systemMenuContainer
        width: Math.round(800 * CommonStyle.scaleFactor)
        height: Math.round(700 * CommonStyle.scaleFactor)
        radius: CommonStyle.radiusMd + 2
        color: CommonStyle.backgroundL0
        opacity: showSystemMenu ? 1 : 0
        visible: opacity > 0

        border.color: CommonStyle.borderDefault
        border.width: 1

        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            horizontalCenterOffset: showSystemMenu ? 0 : -(parent.width / 2 + systemMenuContainer.width / 2)
        }

        Behavior on anchors.horizontalCenterOffset {
            NumberAnimation {
                duration: CommonStyle.motionSlow
                easing.type: Easing.OutBack
                easing.overshoot: 0.7
            }
        }

        Behavior on opacity {
            NumberAnimation {
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors {
                fill: parent
                margins: CommonStyle.spacingLg + CommonStyle.spacingSm
            }
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: CommonStyle.spacingLg - 1

                Text {
                    text: "System Control"
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontHeading + 6
                    font.bold: true
                    Layout.fillWidth: true
                }

                Rectangle {
                    width: CommonStyle.controlHeightMd
                    height: CommonStyle.controlHeightMd
                    radius: 16
                    color: closeMouseArea.containsMouse ? CommonStyle.backgroundL2 : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: CommonStyle.textSecondary
                        font.pixelSize: CommonStyle.fontDisplay
                        font.bold: true
                    }

                    MouseArea {
                        id: closeMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: systemControlWorkspace.overlayController.hide_menu()
                    }
                }
            }

            // Navigation chrome: segmented track (not content cards)
            Rectangle {
                id: tabTrack
                Layout.fillWidth: true
                Layout.preferredHeight: Math.round(48 * CommonStyle.scaleFactor)
                Layout.bottomMargin: CommonStyle.spacingMd
                color: CommonStyle.backgroundL1
                radius: CommonStyle.radiusMd
                border.color: CommonStyle.borderDefault
                border.width: CommonStyle.borderWidthThin

                ListView {
                    id: tabBar
                    anchors {
                        fill: parent
                        margins: CommonStyle.spacingXs
                    }
                    orientation: ListView.Horizontal
                    spacing: CommonStyle.spacingXs
                    clip: true
                    flickableDirection: Flickable.HorizontalFlick
                    boundsBehavior: Flickable.StopAtBounds

                    ScrollBar.horizontal: ScrollBar {
                        policy: ScrollBar.AsNeeded
                        visible: tabBar.contentWidth > tabBar.width
                    }

                    model: ListModel {
                        ListElement { tabText: "Devices"; tabIndex: 0 }
                        ListElement { tabText: "Command"; tabIndex: 1 }
                        ListElement { tabText: "Settings"; tabIndex: 2 }
                        ListElement { tabText: "WorkFlow"; tabIndex: 3 }
                    }

                    delegate: TabButton {
                        width: Math.round(148 * CommonStyle.scaleFactor)
                        height: tabBar.height
                        text: tabText
                        checked: tabView.currentIndex === tabIndex
                        onClicked: tabView.currentIndex = tabIndex
                    }
                }
            }

            // Content well: inset canvas so tab chrome ≠ panel body
            Rectangle {
                id: contentWell
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: CommonStyle.inputBackground
                radius: CommonStyle.radiusMd
                border.color: CommonStyle.borderDefault
                border.width: CommonStyle.borderWidthThin

                StackLayout {
                    id: tabView
                    anchors {
                        fill: parent
                        margins: CommonStyle.spacingMd
                    }
                    currentIndex: 0

                    LegacySystemControl.DeviceControlTab {
                        id: deviceControlTabContent
                        recordingStatus: systemControlWorkspace.recordingStatus
                        wheelStatus: systemControlWorkspace.wheelStatus
                        winchStatus: systemControlWorkspace.winchStatus
                        teensyStatus: systemControlWorkspace.teensyStatus
                        wheelActions: systemControlWorkspace.wheelActions
                        winchActions: systemControlWorkspace.winchActions
                        teensyActions: systemControlWorkspace.teensyActions
                        recordingActions: systemControlWorkspace.recordingActions
                        systemActions: systemControlWorkspace.systemActions
                        actionLegality: systemControlWorkspace.actionLegality
                        settingsManager: systemControlWorkspace.settingsManager
                    }

                    LegacySystemControl.CommandTab {
                        id: commandTabContent
                        manualCommandHandler: systemControlWorkspace.systemControlServices.manualCommandHandler
                    }

                    LegacySystemControl.SettingsTab {
                        id: settingsTabContent
                        confirmationPopup: sharedConfirmationPopup
                        settingsManager: systemControlWorkspace.settingsManager
                    }

                    LegacySystemControl.WorkFlowTab {
                        id: workFlowTabContent
                        workflowRunner: systemControlWorkspace.systemControlServices.workflowRunner
                        workflowEditor: systemControlWorkspace.systemControlServices.workflowEditor
                        overlayController: systemControlWorkspace.overlayController
                    }
                }
            }
        }
    }

    Rectangle {
        id: systemMenuCloseButton
        z: 10
        width: Math.round(72 * CommonStyle.scaleFactor)
        height: width
        radius: Math.round(12 * CommonStyle.scaleFactor)

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        color: systemMenuCloseMouseArea.pressed
            ? CommonStyle.backgroundL2
            : (systemMenuCloseMouseArea.containsMouse ? CommonStyle.backgroundL1 : CommonStyle.videoSurface)
        border.color: systemMenuCloseMouseArea.pressed
            ? CommonStyle.accentPrimary
            : CommonStyle.borderDefault
        border.width: CommonStyle.borderWidthThin
        opacity: showSystemMenu ? 0.85 : 0
        visible: opacity > 0

        Behavior on color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on border.color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on opacity { NumberAnimation { duration: CommonStyle.motionStandard } }
        Behavior on scale { NumberAnimation { duration: CommonStyle.motionFast } }

        MouseArea {
            id: systemMenuCloseMouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: systemControlWorkspace.overlayController.hide_menu()
            onPressed: systemMenuCloseButton.scale = 0.92
            onReleased: systemMenuCloseButton.scale = 1.0
            onCanceled: systemMenuCloseButton.scale = 1.0
        }

        Text {
            anchors.centerIn: parent
            text: "×"
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontDisplay
            font.bold: true
        }
    }

    // Segment control segment — filled pill when active; no card-style outline
    // (content sections own the blue bordered-card look).
    component TabButton: Rectangle {
        id: tabButton
        property string text: ""
        property bool checked: false
        signal clicked()

        readonly property color idleColor: "transparent"
        readonly property color hoverColor: CommonStyle.backgroundL2
        readonly property color activeColor: CommonStyle.chromeBackground

        color: checked ? activeColor : (tabMouse.containsMouse ? hoverColor : idleColor)
        border.width: 0
        radius: CommonStyle.radiusSm

        Behavior on color {
            ColorAnimation { duration: CommonStyle.motionFast }
        }

        MouseArea {
            id: tabMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: tabButton.clicked()
        }

        Text {
            anchors.centerIn: parent
            text: tabButton.text
            color: tabButton.checked ? CommonStyle.textPrimary : CommonStyle.textSecondary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontBody
            font.bold: tabButton.checked

            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionFast }
            }
        }

        // Active indicator: bottom accent bar (nav chrome, not content card)
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 2
            width: tabButton.checked ? Math.round(parent.width * 0.55) : 0
            height: 3
            radius: 1
            color: CommonStyle.accentPrimary
            visible: width > 0

            Behavior on width {
                NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic }
            }
        }
    }

    CustomPopup {
        id: sharedConfirmationPopup
        width: CommonStyle.popupWidth - CommonStyle.spacingXl
        height: CommonStyle.popupHeight - CommonStyle.spacingSm
        dismissDelay: 2000
    }
}