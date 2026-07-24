// ConnectionStatusPanel.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: connectionStatusPanel
    objectName: "connectionStatusPanel"
    width: parent.width
    color: CommonStyle.sidebarBackground
    
    required property bool expanded
    required property var shellConnectivityStatus
    property bool showDeviceStatus: true
    property int titleFontSize: CommonStyle.shellStatusTitleFont
    property int metaFontSize: CommonStyle.shellStatusMetaFont
    property color labelColor: CommonStyle.textPrimary
    property color secondaryLabelColor: CommonStyle.textSecondary
    property string efIpAddress: shellConnectivityStatus.endEffectorIpAddress
    property string baseIpAddress: shellConnectivityStatus.baseIpAddress
    
    // Height adapts based on expanded state
    height: expanded ? CommonStyle.shellStatusBarHeight : CommonStyle.itemHeight
    
    Behavior on height {
        NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.InOutQuad }
    }

    // Define colors for status indicators
    property color availableColor: CommonStyle.statusSuccess
    property color idleColor: CommonStyle.statusSuccess
    property color onTaskColor: CommonStyle.statusInfo
    property color warningColor: CommonStyle.statusWarning
    property color errorColor: CommonStyle.statusError
    property color offlineColor: CommonStyle.textDisabled
    
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
            anchors.rightMargin: CommonStyle.spacingLg
            spacing: CommonStyle.spacingXs + 2
            
            // WINCH indicators
            Row {
                spacing: CommonStyle.spacingXs
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: shellConnectivityStatus.winchAvailable ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(shellConnectivityStatus.baseOnline, shellConnectivityStatus.baseStatus)
                }
            }
            
            // WHEEL indicators
            Row {
                spacing: CommonStyle.spacingXs
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: shellConnectivityStatus.wheelAvailable ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(shellConnectivityStatus.baseOnline, shellConnectivityStatus.baseStatus)
                }
            }
            
            // EF indicators
            Row {
                spacing: CommonStyle.spacingXs
                
                // Availability indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: shellConnectivityStatus.endEffectorAvailable ? availableColor : warningColor
                }
                
                // Heartbeat indicator
                Rectangle {
                    width: 8
                    height: 8
                    radius: 4
                    color: getHeartbeatColor(shellConnectivityStatus.endEffectorOnline, shellConnectivityStatus.endEffectorStatus)
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
            spacing: CommonStyle.spacingSm
            anchors.margins: CommonStyle.spacingMd
    
            // Device Status View - only visible when expanded and showDeviceStatus is true
            Column {
                visible: connectionStatusPanel.showDeviceStatus
                width: parent.width
                spacing: parent.spacing
    
                // WINCH status row
                Row {
                    spacing: CommonStyle.spacingSm
                    width: parent.width
    
                    Text {
                        text: "WINCH"
                        color: connectionStatusPanel.labelColor
                        font.family: CommonStyle.fontSans
                        font.pixelSize: connectionStatusPanel.titleFontSize
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: CommonStyle.spacingSm
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: shellConnectivityStatus.winchAvailable ? availableColor : warningColor
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
                            color: getHeartbeatColor(shellConnectivityStatus.baseOnline, shellConnectivityStatus.baseStatus)
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
                    spacing: CommonStyle.spacingSm
                    width: parent.width
    
                    Text {
                        text: "WHEEL"
                        color: connectionStatusPanel.labelColor
                        font.family: CommonStyle.fontSans
                        font.pixelSize: connectionStatusPanel.titleFontSize
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: CommonStyle.spacingSm
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: shellConnectivityStatus.wheelAvailable ? availableColor : warningColor
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
                            color: getHeartbeatColor(shellConnectivityStatus.baseOnline, shellConnectivityStatus.baseStatus)
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
                    spacing: CommonStyle.spacingSm
                    width: parent.width
    
                    Text {
                        text: "EF"
                        color: connectionStatusPanel.labelColor
                        font.family: CommonStyle.fontSans
                        font.pixelSize: connectionStatusPanel.titleFontSize
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: parent.parent.parent.parent.width * 0.45
                    }
                    
                    // Status indicators
                    Row {
                        spacing: CommonStyle.spacingSm
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: shellConnectivityStatus.endEffectorAvailable ? availableColor : warningColor
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
                            color: getHeartbeatColor(shellConnectivityStatus.endEffectorOnline, shellConnectivityStatus.endEffectorStatus)
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
                    spacing: CommonStyle.spacingXs + 1
                    width: parent.width
    
                    Text {
                        text: "EF IP:"
                        color: connectionStatusPanel.labelColor
                        font.family: CommonStyle.fontSans
                        font.pixelSize: connectionStatusPanel.titleFontSize
                        font.bold: true
                        width: parent.parent.parent.parent.width * 0.7
                    }
                    Text {
                        text: connectionStatusPanel.efIpAddress
                        color: connectionStatusPanel.secondaryLabelColor
                        font.family: CommonStyle.fontMono
                        font.bold: true
                        font.pixelSize: connectionStatusPanel.metaFontSize
                        width: parent.width - (parent.parent.parent.parent.width * 0.7) - parent.spacing
                        horizontalAlignment: Text.AlignRight
                    }
                }
    
                // BASE IP row
                Row {
                    spacing: CommonStyle.spacingXs + 1
                    width: parent.width
    
                    Text {
                        text: "BASE IP:"
                        color: connectionStatusPanel.labelColor
                        font.family: CommonStyle.fontSans
                        font.pixelSize: connectionStatusPanel.titleFontSize
                        font.bold: true
                        width: parent.parent.parent.parent.width * 0.7
                    }
                    Text {
                        text: connectionStatusPanel.baseIpAddress
                        color: connectionStatusPanel.secondaryLabelColor
                        font.family: CommonStyle.fontMono
                        font.bold: true
                        font.pixelSize: connectionStatusPanel.metaFontSize
                        width: parent.width - (parent.parent.parent.parent.width * 0.7) - parent.spacing
                        horizontalAlignment: Text.AlignRight
                    }
                }
            }
    
            // Instruction text - only visible when expanded
            Text {
                width: parent.width
                text: connectionStatusPanel.showDeviceStatus ? "Touch to show IP" : "Touch to show Device Status"
                color: connectionStatusPanel.secondaryLabelColor
                font.family: CommonStyle.fontSans
                font.pixelSize: connectionStatusPanel.metaFontSize
                font.italic: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }
}