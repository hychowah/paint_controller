import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: executorPageStatus
    color: "#1e293b"  // Solid dark background for better readability
    radius: 8

    // Main content container
    ColumnLayout {
        id: mainLayout
        anchors.fill: parent
        anchors.margins: 12
        spacing: 10

        // Status header with system indicator
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 24

            Rectangle {
                id: statusIndicator
                width: 8
                height: 8
                radius: 4
                color: "#4ade80" // Green for active status
                
                // Pulse animation for active status
                SequentialAnimation {
                    running: true
                    loops: Animation.Infinite
                    NumberAnimation {
                        target: statusIndicator
                        property: "opacity"
                        from: 1.0
                        to: 0.5
                        duration: 1000
                    }
                    NumberAnimation {
                        target: statusIndicator
                        property: "opacity"
                        from: 0.5
                        to: 1.0
                        duration: 1000
                    }
                }
            }

            Text {
                text: "SYSTEM STATUS: READY"
                font.pixelSize: 12
                font.bold: true
                color: "#ffffff"
                Layout.leftMargin: 6
            }
            
            Item { Layout.fillWidth: true } // Spacer
        }

        // Metrics in 2x2 grid layout
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 12
            columnSpacing: 24

            // Winch Torque Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    
                    Text {
                        text: "Winch Torque"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#ffffff"
                    }
                    
                    Item { Layout.fillWidth: true } // Spacer
                    
                    Text {
                        text: (winchController.winch_torque || 0).toFixed(1) + " / 1400"
                        font.pixelSize: 13
                        color: "#f0f0f0"
                    }
                }

                // Progress bar for winch torque
                Rectangle {
                    Layout.fillWidth: true
                    height: 6
                    radius: 3
                    color: "#2d3748"
                    
                    Rectangle {
                        id: winchTorqueBar
                        anchors.left: parent.left
                        height: parent.height
                        radius: parent.radius
                        width: Math.min(parent.width * (winchController.winch_torque || 0) / 1400, parent.width)
                        
                        // Gradient based on torque value
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#3b82f6" }
                            GradientStop { position: 1.0; color: "#60a5fa" }
                        }
                        
                        // Animated transitions
                        Behavior on width {
                            NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                        }
                    }
                }
            }

            // Cable Length Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    
                    Text {
                        text: "Cable Length"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#ffffff"
                    }
                    
                    Item { Layout.fillWidth: true } // Spacer
                    
                    Text {
                        text: Math.round(winchController.cable_length || 0) + " mm"
                        font.pixelSize: 13
                        color: "#f0f0f0"
                    }
                }
            }

            // Cable Speed Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    
                    Text {
                        text: "Cable Speed"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#ffffff"
                    }
                    
                    Item { Layout.fillWidth: true } // Spacer
                    
                    Text {
                        property real speed: Math.abs(winchController.cable_speed || 0)
                        text: speed.toFixed(1) + " mm/s"
                        font.pixelSize: 13
                        color: "#f0f0f0"
                    }
                }
            }

            // Arm Extension Section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4

                RowLayout {
                    Layout.fillWidth: true
                    
                    Text {
                        text: "Arm Extension"
                        font.pixelSize: 13
                        font.bold: true
                        color: "#ffffff"
                    }
                    
                    Item { Layout.fillWidth: true } // Spacer
                    
                    Text {
                        text: (teensyController.all_status.arm_extension_dist || 0).toFixed(0) + " / 1600"
                        font.pixelSize: 13
                        color: "#f0f0f0"
                    }
                }

                // Progress bar for arm extension
                Rectangle {
                    Layout.fillWidth: true
                    height: 6
                    radius: 3
                    color: "#2d3748"
                    
                    Rectangle {
                        id: armExtensionBar
                        anchors.left: parent.left
                        height: parent.height
                        radius: parent.radius
                        width: Math.min(parent.width * (teensyController.all_status.arm_extension_dist || 0) / 1600, parent.width)
                        
                        // Gradient based on extension value
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#10b981" }
                            GradientStop { position: 1.0; color: "#34d399" }
                        }
                        
                        // Animated transitions
                        Behavior on width {
                            NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                        }
                    }
                }
            }
        }
    }
}