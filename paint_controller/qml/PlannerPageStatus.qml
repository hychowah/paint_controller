import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: plannerPageStatus
    color: "#ffffff"
    radius: 15
    border.color: "#e0e0e0"
    border.width: 1
    
    // Define a theme color property
    property color themeColor: "#4374A2"
    property color themeBgColor: Qt.rgba(
        themeColor.r, 
        themeColor.g, 
        themeColor.b, 
        0.1
    )
    
    // Add a subtle gradient background
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#ffffff" }
        GradientStop { position: 1.0; color: "#f7f7f7" }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 0

        Text {
            Layout.fillWidth: true
            text: "System Status"
            font.pixelSize: 18
            font.bold: true
            color: "#333333"
            Layout.bottomMargin: 15
        }
        
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#e0e0e0"
            Layout.bottomMargin: 15
        }
        
        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            rowSpacing: 16
            columnSpacing: 20

            // Row 1 - Winch Torque
            Rectangle {
                Layout.fillWidth: true
                color: "transparent"
                height: 28
                
                RowLayout {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    
                    Rectangle {
                        width: 4
                        height: 20
                        radius: 2
                        color: plannerPageStatus.themeColor
                    }
                    
                    Text {
                        text: "Winch Torque"
                        font.pixelSize: 14
                        font.bold: true
                        color: "#444444"
                    }
                }
            }
            
            Rectangle {
                Layout.preferredWidth: 100
                color: "transparent"
                height: 28
                
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: 70
                    height: 24
                    radius: 4
                    color: plannerPageStatus.themeBgColor
                    border.color: plannerPageStatus.themeColor
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: winchController.winch_torque.toFixed(1)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
            // Row 2 - Cable Length
            Rectangle {
                Layout.fillWidth: true
                color: "transparent"
                height: 28
                
                RowLayout {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    
                    Rectangle {
                        width: 4
                        height: 20
                        radius: 2
                        color: plannerPageStatus.themeColor
                    }
                    
                    Text {
                        text: "Cable Length"
                        font.pixelSize: 14
                        font.bold: true
                        color: "#444444"
                    }
                }
            }
            
            Rectangle {
                Layout.preferredWidth: 100
                color: "transparent"
                height: 28
                
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: 70
                    height: 24
                    radius: 4
                    color: plannerPageStatus.themeBgColor
                    border.color: plannerPageStatus.themeColor
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: Math.round(winchController.cable_length).toFixed(0)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
            // Row 3 - Cable Speed
            Rectangle {
                Layout.fillWidth: true
                color: "transparent"
                height: 28
                
                RowLayout {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    
                    Rectangle {
                        width: 4
                        height: 20
                        radius: 2
                        color: plannerPageStatus.themeColor
                    }
                    
                    Text {
                        text: "Cable Speed"
                        font.pixelSize: 14
                        font.bold: true
                        color: "#444444"
                    }
                }
            }
            
            Rectangle {
                Layout.preferredWidth: 100
                color: "transparent"
                height: 28
                
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: 70
                    height: 24
                    radius: 4
                    color: plannerPageStatus.themeBgColor
                    border.color: plannerPageStatus.themeColor
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: Math.abs(winchController.cable_speed).toFixed(1)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
            // Row 4 - Arm Extension
            Rectangle {
                Layout.fillWidth: true
                color: "transparent"
                height: 28
                
                RowLayout {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    
                    Rectangle {
                        width: 4
                        height: 20
                        radius: 2
                        color: plannerPageStatus.themeColor
                    }
                    
                    Text {
                        text: "Arm Extension"
                        font.pixelSize: 14
                        font.bold: true
                        color: "#444444"
                    }
                }
            }
            
            Rectangle {
                Layout.preferredWidth: 100
                color: "transparent"
                height: 28
                
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: 70
                    height: 24
                    radius: 4
                    color: plannerPageStatus.themeBgColor
                    border.color: plannerPageStatus.themeColor
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: teensyController.all_status.arm_extension_dist.toFixed(0)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
            // Row 5 - Status5
            Rectangle {
                Layout.fillWidth: true
                color: "transparent"
                height: 28
                
                RowLayout {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 10
                    
                    Rectangle {
                        width: 4
                        height: 20
                        radius: 2
                        color: plannerPageStatus.themeColor
                    }
                    
                    Text {
                        text: "Status5"
                        font.pixelSize: 14
                        font.bold: true
                        color: "#444444"
                    }
                }
            }
            
            Rectangle {
                Layout.preferredWidth: 100
                color: "transparent"
                height: 28
                
                Rectangle {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: 70
                    height: 24
                    radius: 4
                    color: plannerPageStatus.themeBgColor
                    border.color: plannerPageStatus.themeColor
                    border.width: 1
                    
                    Text {
                        anchors.centerIn: parent
                        text: "Value5"
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
        }
    }
}