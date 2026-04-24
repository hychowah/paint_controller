import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components/popups"
import "../../navigation"
import "../../overlays/systemcontrol" as LegacySystemControl

Item {
    id: systemControlWorkspace

    required property bool showOverlay
    required property string activeMenu
    readonly property bool showSystemMenu: showOverlay && activeMenu === "system"

    visible: true

    Rectangle {
        id: systemOverlayBackground
        anchors.fill: parent
        color: "#000000"
        opacity: showSystemMenu ? 0.5 : 0
        visible: opacity > 0

        Behavior on opacity {
            NumberAnimation {
                duration: 250
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
        width: 800
        height: 700
        radius: 12
        color: "#1A1A1A"
        opacity: showSystemMenu ? 1 : 0
        visible: opacity > 0

        border.color: "#333333"
        border.width: 1

        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: showSystemMenu ? 0 : -parent.height
        }

        Behavior on anchors.verticalCenterOffset {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutBack
                easing.overshoot: 0.7
            }
        }

        Behavior on opacity {
            NumberAnimation {
                duration: 250
                easing.type: Easing.InOutQuad
            }
        }

        ColumnLayout {
            anchors {
                fill: parent
                margins: 20
            }
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 15

                Text {
                    text: "System Control"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 26
                    font.bold: true
                    Layout.fillWidth: true
                }

                Rectangle {
                    width: 32
                    height: 32
                    radius: 16
                    color: closeMouseArea.containsMouse ? "#333333" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: "#CCCCCC"
                        font.pixelSize: 24
                        font.bold: true
                    }

                    MouseArea {
                        id: closeMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: overlayController.hide_menu()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 50
                color: "transparent"
                Layout.bottomMargin: 10

                ListView {
                    id: tabBar
                    anchors.fill: parent
                    orientation: ListView.Horizontal
                    spacing: 2
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
                        ListElement { tabText: "Edit WorkFlow"; tabIndex: 4 }
                    }

                    delegate: TabButton {
                        width: 150
                        height: tabBar.height
                        text: tabText
                        checked: tabView.currentIndex === tabIndex
                        onClicked: tabView.currentIndex = tabIndex
                    }
                }
            }

            StackLayout {
                id: tabView
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: 0

                LegacySystemControl.DeviceControlTab {
                    id: deviceControlTabContent
                }

                LegacySystemControl.CommandTab {
                    id: commandTabContent
                }

                LegacySystemControl.SettingsTab {
                    id: settingsTabContent
                    confirmationPopup: sharedConfirmationPopup
                }

                LegacySystemControl.WorkFlowTab {
                    id: workFlowTabContent
                }

                LegacySystemControl.EditWorkFlowTab {
                    id: editWorkFlowTabContent
                }
            }
        }
    }

    component TabButton: Rectangle {
        property string text: ""
        property bool checked: false
        signal clicked()

        color: checked ? "#2A3040" : "#1A1A1A"
        border.color: checked ? "#3A5A8C" : "#333333"
        border.width: 1
        radius: 8

        Behavior on color {
            ColorAnimation { duration: 200 }
        }

        Behavior on border.color {
            ColorAnimation { duration: 200 }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: parent.clicked()

            onEntered: {
                if (!parent.checked) {
                    parent.color = "#252525"
                }
            }

            onExited: {
                if (!parent.checked) {
                    parent.color = "#1A1A1A"
                }
            }
        }

        Text {
            anchors.centerIn: parent
            text: parent.text
            color: parent.checked ? "#FFFFFF" : "#CCCCCC"
            font.family: "Helvetica"
            font.pixelSize: 16
            font.bold: parent.checked

            Behavior on color {
                ColorAnimation { duration: 200 }
            }
        }
    }

    CustomPopup {
        id: sharedConfirmationPopup
        width: 400
        height: 180
        dismissDelay: 2000
    }
}