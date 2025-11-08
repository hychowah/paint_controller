import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../components/panels"
import "../navigation"

Item {
    id: powerControlMenu

    // These properties can now be directly bound to the overlayController
    property bool showOverlay: overlayController.show_overlay
    property string activeMenu: overlayController.active_menu
    property bool showPowerMenu: showOverlay && activeMenu === "power"

    // Ensure the menu is visible
    visible: true

    Rectangle {
        id: powerOverlayBackground
        anchors.fill: parent
        color: "#000000"
        opacity: showPowerMenu ? 0.5 : 0
        visible: opacity > 0
        
        Behavior on opacity {
            NumberAnimation { 
                duration: 250
                easing.type: Easing.InOutQuad 
            }
        }
    }

    Rectangle {
        id: powerMenuContainer
        width: 800 // Slightly wider to accommodate tabs
        height: 700 // Increased height for tab bar
        radius: 12
        color: "#1A1A1A"  // Darker background for modern look
        opacity: showPowerMenu ? 1 : 0
        visible: opacity > 0
        
        // Modern subtle border
        border.color: "#333333"
        border.width: 1
        
        // Centered positioning with animation
        anchors {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            verticalCenterOffset: showPowerMenu ? 0 : -parent.height
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

            // Header with close button
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
                
                // Close button
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

            // Tab Bar
            Rectangle {
                Layout.fillWidth: true
                height: 50
                color: "transparent"
                Layout.bottomMargin: 10

                RowLayout {
                    anchors.fill: parent
                    spacing: 2

                    // Power Control Tab
                    TabButton {
                        id: powerTab
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: "Power Control"
                        checked: tabView.currentIndex === 0
                        onClicked: tabView.currentIndex = 0
                    }

                    // Command Tab
                    TabButton {
                        id: commandTab
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: "Command"
                        checked: tabView.currentIndex === 1
                        onClicked: tabView.currentIndex = 1
                    }
                }
            }

            // Tab Content
            StackLayout {
                id: tabView
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: 0

                // Power Control Tab Content
                PowerControlTab {
                    id: powerControlTabContent
                }

                // Command Tab Content
                CommandTab {
                    id: commandTabContent
                }
            }
        }
    }

    // Custom Tab Button Component
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
}