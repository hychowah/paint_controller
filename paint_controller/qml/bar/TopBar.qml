// TopBar.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../"

Rectangle {
    id: topBar
    height: 56  // Slightly taller for modern proportions
    color: "#28445E"  // Keeping the original color
    z: 1  // Ensure top bar is above the StackView
    
    // Subtle gradient overlay for depth
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.05) }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.1) }
        }
    }
    
    // Thin bottom line (more subtle than before)
    Rectangle {
        id: bottomLine
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: Qt.rgba(1, 1, 1, 0.5)  // Semi-transparent white
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16  // Increased margins
        spacing: 16  // Increased spacing
        
        // App message with improved typography
        Text {
            text: uiData ? uiData.display_message || "" : ""
            color: "white"
            font.family: "Roboto"
            font.pixelSize: 16
            font.weight: Font.Medium
            opacity: 0.9  // Slightly reduced opacity for softer look
        }
        
        Item { Layout.fillWidth: true } // Spacer
        
        // Redesigned warning button
        Button {
            id: warningButton
            Layout.preferredHeight: 36
            
            contentItem: Row {
                spacing: 8
                anchors.centerIn: parent
                
                Text {
                    text: "⚠️"
                    font.pixelSize: 16
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "Warnings (" + warningHandler.warnings.length + ")"
                    color: warningHandler.warnings.length === 0 ? "#333333" : "#ffffff"
                    font.family: "Roboto"
                    font.pixelSize: 14
                    font.weight: Font.Medium
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            background: Rectangle {
                color: warningHandler.warnings.length === 0 ? "#ffffff" : "#ff5252"  // Slightly modernized red
                radius: 18  // Pill-shaped button
                
                // Add subtle gradient
                Rectangle {
                    anchors.fill: parent
                    radius: 18
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.1) }
                        GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.1) }
                    }
                }
            }
            
            onClicked: warningPopup.open()
        }
        
        // Modern digital clock
        Rectangle {
            color: Qt.rgba(1, 1, 1, 0.1)  // Semi-transparent white background
            radius: 6
            Layout.preferredHeight: 36
            Layout.preferredWidth: clockText.width + 24
            
            Text {
                id: clockText
                anchors.centerIn: parent
                text: Qt.formatDateTime(new Date(), "hh:mm:ss")
                color: "white"
                font.family: "Roboto Mono"  // Monospaced font for clock
                font.pixelSize: 18
                font.weight: Font.Medium
                
                Timer {
                    interval: 1000
                    running: true
                    repeat: true
                    onTriggered: parent.text = Qt.formatDateTime(new Date(), "hh:mm:ss")
                }
            }
        }
    }
    
    // Modernized warning popup
    Popup {
        id: warningPopup
        parent: Overlay.overlay
        width: Math.min(Overlay.overlay.width * 0.8, 600)
        height: Math.min(Overlay.overlay.height * 0.8, 400)
        x: (Overlay.overlay.width - width) / 2
        y: (Overlay.overlay.height - height) / 2
        padding: 24  // Increased padding
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        // Dark themed background matching the application style
        background: Rectangle {
            color: "#2c3e50"  // Dark blue-gray background
            radius: 8  // Rounded corners
            border.width: 1
            border.color: "#34495e"
        }
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 16  // Increased spacing
            
            // Header with line separator
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                
                Text {
                    text: "Warnings"
                    font.family: "Roboto"
                    font.pixelSize: 20
                    font.weight: Font.Medium
                    color: "white"
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: "#455a64"  // Darker separator
                }
            }
            
            // Warnings list
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ListView {
                    id: listView
                    model: warningHandler.warnings
                    spacing: 12
                    boundsBehavior: Flickable.StopAtBounds
                    width: parent.width
                    
                    delegate: Rectangle {
                        width: ListView.view.width - 20
                        height: warningLayout.implicitHeight + 24
                        color: "#344352"  // Darker background for warning items
                        radius: 6
                        border.width: 1
                        border.color: "#ff5252"  // Red border for warnings
                        
                        RowLayout {
                            id: warningLayout
                            width: parent.width - 24  // Fixed width with margins
                            anchors.centerIn: parent  // Center in parent
                            spacing: 16
                            
                            Text {
                                text: "⚠️"
                                font.pixelSize: 16
                            }
                            
                            Text {
                                text: modelData
                                color: "#ff9e80"  // Light orange for warning text
                                font.family: "Roboto"
                                font.pixelSize: 14
                                wrapMode: Text.Wrap
                                Layout.fillWidth: true
                            }
                            
                            Button {
                                text: "Dismiss"
                                Layout.alignment: Qt.AlignVCenter  // Vertical alignment
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.family: "Roboto"
                                    font.pixelSize: 13
                                    color: "#e0e0e0"  // Light text color
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                
                                background: Rectangle {
                                    color: parent.hovered ? "#28445E" : "#1e313d"  // Blue tones matching the app
                                    radius: 4
                                    implicitHeight: 32
                                    implicitWidth: 80
                                }
                                
                                onClicked: {
                                    if(warningHandler.warnings.length == 1) {
                                        warningPopup.close()
                                    }
                                    warningHandler.remove_warning(index)
                                }
                            }
                        }
                    }
                }
            }
            
            // Footer actions
            RowLayout {
                Layout.fillWidth: true
                Item { Layout.fillWidth: true }  // Right-align the button
                
                Button {
                    text: "Clear All"
                    
                    contentItem: Text {
                        text: parent.text
                        font.family: "Roboto"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        color: "#ffffff"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    background: Rectangle {
                        color: parent.hovered ? "#c62828" : "#d32f2f"  // Darker red
                        radius: 4
                        implicitHeight: 36
                        implicitWidth: 100
                    }
                    
                    onClicked: {
                        warningHandler.clear()
                        warningPopup.close()
                    }
                }
            }
        }
    }
}