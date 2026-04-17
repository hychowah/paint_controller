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
    
    // Add a control mode property (bound to the UI data model)
    property string controlMode: stateStore.control_mode
    
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
            text: controlMode === "base" ? "Base Control Mode" : "EF Control Mode"
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
        
        // Base Mode Status
        GridLayout {
            id: baseStatusGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            rowSpacing: 16
            columnSpacing: 20
            visible: controlMode === "base"

            // Row 1 - Left Wheel Speed
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
                        text: "Left Wheel Speed"
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
                        text: wheelController.left_wheel_speed.toFixed(1)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
            // Row 2 - Right Wheel Speed
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
                        text: "Right Wheel Speed"
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
                        text: wheelController.right_wheel_speed.toFixed(1)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
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
                        text: "LEFT CURRENT"
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
                        text: wheelController.left_wheel_current.toFixed(2) 
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
            
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
                        text: "RIGHT CURRENT"
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
                        text: wheelController.right_wheel_current.toFixed(2)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }

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
                        text: "TRAVEL"
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
                        text: wheelController.right_wheel_position.toFixed(0)
                        font.pixelSize: 14
                        font.bold: true
                        color: plannerPageStatus.themeColor
                    }
                }
            }
        }
        
        // EF Mode Status
        GridLayout {
            id: efStatusGrid
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 2
            rowSpacing: 16
            columnSpacing: 20
            visible: controlMode === "ef"

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
            
            // Row 3 - EF Yaw Angle
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
                        text: "EF Yaw Angle"
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
                        text: teensyController.all_status.imu_yaw.toFixed(1)
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
        }
    }
    
    // Add a smooth transition animation when switching modes
    Behavior on controlMode {
        SequentialAnimation {
            // Fade out current view
            NumberAnimation {
                target: controlMode === "base" ? baseStatusGrid : efStatusGrid
                property: "opacity"
                from: 1.0
                to: 0.0
                duration: 150
            }
            
            // Switch visibility
            ScriptAction {
                script: {
                    baseStatusGrid.visible = (controlMode === "base");
                    efStatusGrid.visible = (controlMode === "ef");
                }
            }
            
            // Fade in new view
            NumberAnimation {
                target: controlMode === "base" ? baseStatusGrid : efStatusGrid
                property: "opacity"
                from: 0.0
                to: 1.0
                duration: 150
            }
        }
    }
}