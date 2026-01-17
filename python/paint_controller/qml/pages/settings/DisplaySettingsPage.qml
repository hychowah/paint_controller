import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

ScrollView {
    id: root
    contentWidth: availableWidth
    clip: true
    
    signal backRequested()
    
    ColumnLayout {
        width: parent.width
        spacing: 0
        
        SettingsHeader {
            title: "Display Settings"
            showBack: true
            onBackClicked: root.backRequested()
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            color: "#F5F5F5"
        }
        
        SettingsCategory {
            title: "Multi-Screen Support"
        }
        
        // Screen count info
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "#FFFFFF"
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 15
                
                Column {
                    Layout.fillWidth: true
                    spacing: 4
                    
                    Text {
                        text: "Connected Displays"
                        font.pixelSize: 16
                        font.bold: true
                        color: "#1C1C1E"
                    }
                    
                    Text {
                        text: {
                            if (typeof screenManager !== 'undefined' && screenManager) {
                                var count = screenManager.screen_count
                                return count + " display" + (count !== 1 ? "s" : "") + " detected"
                            }
                            return "Screen manager not available"
                        }
                        font.pixelSize: 13
                        color: "#8E8E93"
                    }
                }
                
                // Refresh button
                Button {
                    text: "↻"
                    font.pixelSize: 18
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 40
                    
                    background: Rectangle {
                        color: parent.pressed ? "#E0E0E0" : (parent.hovered ? "#F0F0F0" : "#FFFFFF")
                        border.color: "#C8C7CC"
                        border.width: 1
                        radius: 8
                    }
                    
                    onClicked: {
                        console.log("Refreshing screen information...")
                        screenListRepeater.model = null
                        screenListRepeater.model = getScreenList()
                    }
                }
            }
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 0.5
                color: "#C8C7CC"
            }
        }
        
        // Screen selection list
        SettingsCategory {
            title: "Select Display Target"
        }
        
        Repeater {
            id: screenListRepeater
            model: getScreenList()
            
            delegate: Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 80
                color: mouseArea.pressed ? "#F0F0F0" : "#FFFFFF"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 15
                    
                    Column {
                        Layout.fillWidth: true
                        spacing: 4
                        
                        Row {
                            spacing: 8
                            
                            Text {
                                text: modelData.name
                                font.pixelSize: 16
                                font.bold: true
                                color: "#1C1C1E"
                            }
                            
                            Rectangle {
                                visible: modelData.isPrimary
                                color: "#007AFF"
                                radius: 4
                                width: 60
                                height: 20
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "Primary"
                                    font.pixelSize: 11
                                    color: "#FFFFFF"
                                }
                            }
                            
                            Rectangle {
                                visible: modelData.index === mainWindow.targetScreenIndex
                                color: "#34C759"
                                radius: 4
                                width: 50
                                height: 20
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "Active"
                                    font.pixelSize: 11
                                    color: "#FFFFFF"
                                }
                            }
                        }
                        
                        Text {
                            text: modelData.width + " × " + modelData.height + " @ " + 
                                  modelData.refreshRate.toFixed(0) + " Hz"
                            font.pixelSize: 13
                            color: "#8E8E93"
                        }
                        
                        Text {
                            text: "Position: (" + modelData.virtualX + ", " + modelData.virtualY + ")"
                            font.pixelSize: 12
                            color: "#AEAEB2"
                        }
                    }
                    
                    // Checkmark indicator
                    Text {
                        text: modelData.index === mainWindow.targetScreenIndex ? "✓" : ""
                        font.pixelSize: 24
                        color: "#34C759"
                        Layout.preferredWidth: 30
                        horizontalAlignment: Text.AlignRight
                    }
                }
                
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 0.5
                    color: "#C8C7CC"
                }
                
                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    onClicked: {
                        console.log("Switching to screen " + modelData.index + ": " + modelData.name)
                        mainWindow.switchToScreen(modelData.index)
                    }
                }
            }
        }
        
        // Info section
        SettingsCategory {
            title: "About Multi-Screen Support"
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: infoText.height + 40
            color: "#FFFFFF"
            
            Text {
                id: infoText
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 20
                wrapMode: Text.WordWrap
                font.pixelSize: 13
                color: "#8E8E93"
                lineHeight: 1.4
                text: "The application supports adaptive multi-screen display. " +
                      "When you connect or disconnect external monitors, the display list " +
                      "updates automatically in real-time. Select a display from the list above " +
                      "to move the application window to that screen.\n\n" +
                      "✓ Real-time screen detection\n" +
                      "✓ Automatic geometry adjustment\n" +
                      "✓ Support for extended and duplicate modes"
            }
        }
        
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            color: "transparent"
        }
    }
    
    // Function to get screen list from screenManager
    function getScreenList() {
        if (typeof screenManager !== 'undefined' && screenManager) {
            return screenManager.get_all_screens_info()
        }
        return []
    }
    
    // Update screen list when screens change
    Connections {
        target: typeof screenManager !== 'undefined' ? screenManager : null
        
        function onScreens_changed() {
            console.log("DisplaySettingsPage: Screens changed, updating list")
            screenListRepeater.model = null
            screenListRepeater.model = getScreenList()
        }
    }
}
