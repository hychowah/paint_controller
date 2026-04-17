// ConnectionStatusPanel.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: connectionStatusPanel
    width: parent.width
    color: "#A4A589"
    
    // Properties
    property bool expanded: true
    property bool showDeviceStatus: true
    
    // Height adapts based on expanded state
    height: expanded ? 100 : 60
    
    Behavior on height {
        NumberAnimation { duration: 250; easing.type: Easing.InOutQuad }
    }

    // Define colors for status indicators
    property color availableColor: "#7ED957"  // Softer green
    property color idleColor: "#4CD964"       // Natural green
    property color onTaskColor: "#4A90E2"     // Soft blue
    property color warningColor: "#FFCC00"    // Amber yellow
    property color errorColor: "#FF5E3A"      // Soft red
    property color offlineColor: "#8E8E93"    // Medium gray
    
    // Helper function to get status color
    function getHeartbeatColor(isOnline, status) {
        if (!isOnline) return offlineColor;
        switch(status) {
            case 0x00: return idleColor;     // IDLE
            case 0x01: return onTaskColor;   // ONTASK
            case 0x02: return warningColor;  // WARNING
            case 0x03: return errorColor;    // ERROR
            default: return offlineColor;
        }
    }
    
    // Helper function to get status text
    function getHeartbeatText(isOnline, status) {
        if (!isOnline) {
            return "OFFLINE";
        } else {
            switch(status) {
                case 0x00: return "IDLE";
                case 0x01: return "ONTASK";
                case 0x02: return "WARNING";
                case 0x03: return "ERROR";
                case 0x04: return "CLEAR_ERROR";
                default: return "Unknown";
            }
        }
    }

    // FOR COLLAPSED STATE
    Item {
        visible: !expanded
        anchors.fill: parent
        
        // Status dots
        Column {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 16
            spacing: 6
            
            // WINCH indicators
            Row {
                spacing: 4
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: winchController.available ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(heartbeatHandler.base_online, heartbeatHandler.base_status)
                }
            }
            
            // WHEEL indicators
            Row {
                spacing: 4
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: wheelController.available ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(heartbeatHandler.base_online, heartbeatHandler.base_status)
                }
            }
            
            // EF indicators
            Row {
                spacing: 4
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: teensyController.available ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(heartbeatHandler.ef_online, heartbeatHandler.ef_status)
                }
            }
        }
    }

    // FOR EXPANDED STATE
    Item {
        visible: expanded
        anchors.fill: parent

        MouseArea {
            anchors.fill: parent
            onClicked: connectionStatusPanel.showDeviceStatus = !connectionStatusPanel.showDeviceStatus
        }
        
        Column {
            anchors.fill: parent
            spacing: 8
            anchors.margins: 12
    
            // Device Status View - only visible when expanded and showDeviceStatus is true
            Column {
                visible: connectionStatusPanel.showDeviceStatus
                width: parent.width
                spacing: parent.spacing
    
                // WINCH status row
                Row {
                    spacing: 8
                    width: parent.width
    
                    Text {
                        text: "WINCH"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: winchController.available ? availableColor : warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // Base heartbeat status indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: getHeartbeatColor(heartbeatHandler.base_online, heartbeatHandler.base_status)
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                    }
                }
    
                // WHEEL status row
                Row {
                    spacing: 8
                    width: parent.width
    
                    Text {
                        text: "WHEEL"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: wheelController.available ? availableColor : warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // Base heartbeat status indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: getHeartbeatColor(heartbeatHandler.base_online, heartbeatHandler.base_status)
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                    }
                }
    
                // EF status row
                Row {
                    spacing: 8
                    width: parent.width
    
                    Text {
                        text: "EF"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: teensyController.available ? availableColor : warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // EF heartbeat status indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: getHeartbeatColor(heartbeatHandler.ef_online, heartbeatHandler.ef_status)
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                    }
                }
            }
    
            // IP Status View - only visible when expanded and showDeviceStatus is false
            Column {
                visible: !connectionStatusPanel.showDeviceStatus
                width: parent.width
                spacing: parent.spacing
    
                // EF IP row
                Row {
                    spacing: 5
                    width: parent.width
    
                    Text {
                        text: "EF IP:"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        width: parent.parent.parent.parent.width * 0.7
                    }
                    Text {
                        text: uiData.ef_ip
                        color: "white"
                        font.bold: true
                        font.pixelSize: 10
                        Layout.fillWidth: true
                        anchors.right: parent.right
                    }
                }
    
                // BASE IP row
                Row {
                    spacing: 5
                    width: parent.width
    
                    Text {
                        text: "BASE IP:"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        width: parent.parent.parent.parent.width * 0.7
                    }
                    Text {
                        text: uiData.base_ip
                        color: "white"
                        font.bold: true
                        font.pixelSize: 10
                        Layout.fillWidth: true
                        anchors.right: parent.right
                    }
                }
            }
    
            // Instruction text - only visible when expanded
            Text {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                text: connectionStatusPanel.showDeviceStatus ? "Touch to show IP" : "Touch to show Device Status"
                color: "white"
                font.pixelSize: 10
                font.italic: true
            }
        }
    }
}