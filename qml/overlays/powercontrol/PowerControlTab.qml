import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/panels"

Item {
    id: powerControlTab

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Two-column layout
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 20
            
            // Left column - Base Controls
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10
                
                // Base Controls Category
                Item {
                    Layout.fillWidth: true
                    height: 32
                    
                    Text {
                        text: "Base Controls"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 18
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Rectangle {
                        height: 1
                        width: parent.width - 120
                        color: "#333333"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Winch Enable Control
                ControlPanel {
                    Layout.fillWidth: true
                    controlName: "Winch Enable"
                    controlStatus: winchController.enabled ? "Enabled" : "Disabled"
                    enabledState: winchController.enabled
                    iconText: "W"
                    
                    onClicked: winchController.setEnabled(!winchController.enabled)
                }
                
                // Winch Load Detection Control
                ControlPanel {
                    Layout.fillWidth: true
                    controlName: "Load Detection"
                    controlStatus: winchController.load_detection_enabled ? "Active" : "Inactive"
                    enabledState: winchController.load_detection_enabled
                    iconText: "LD"
                    
                    onClicked: winchController.setLoadDetectionEnabled(!winchController.load_detection_enabled)
                }
                
                // Wheel Enable Control
                ControlPanel {
                    Layout.fillWidth: true
                    controlName: "Wheel Enable"
                    controlStatus: wheelController ? (wheelController.enabled ? "Motors active" : "Motors inactive") : "Unavailable"
                    enabledState: wheelController ? wheelController.enabled : false
                    iconText: "🛞"
                    
                    onClicked: {
                        if (wheelController) {
                            wheelController.setEnabled(!wheelController.enabled)
                        } else {
                            console.log("Wheel controller not available")
                        }
                    }
                }
                
                // Wheel Reset Position Button
                ActionButton {
                    Layout.fillWidth: true
                    buttonText: "Reset Wheel Position"
                    buttonDescription: "Set wheel position counters to zero"
                    iconColor: "#4CAF50"
                    iconType: "reset"
                    
                    onClicked: {
                        if (wheelController) {
                            wheelController.resetWheelPosition()
                            showFeedback()
                        } else {
                            console.log("Wheel controller not available")
                        }
                    }
                }
                
                // Spacer
                Item { 
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                }
            }
            
            // Vertical Separator
            Rectangle {
                width: 1
                Layout.fillHeight: true
                color: "#333333"
            }
            
            // Right column - End Effector Controls (Scrollable)
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10
                
                // End Effector Category Header
                Item {
                    Layout.fillWidth: true
                    height: 32
                    
                    Text {
                        text: "End Effector Controls"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 18
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Rectangle {
                        height: 1
                        width: parent.width - 180
                        color: "#333333"
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // Scrollable Controls Area
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    
                    ColumnLayout {
                        width: parent.width
                        spacing: 10
                        
                        // Camera Recording Control
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "Camera Recording"
                            controlStatus: videoStreamer.is_recording ? "Recording" : "Streaming"
                            enabledState: videoStreamer.is_recording
                            iconText: "REC"
                            
                            onClicked: videoStreamer.toggleRecording()
                        }

                        // Teensy Relay Control
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "Teensy Relay"
                            controlStatus: teensyController.all_status.relay_on ? "Connected" : "Disconnected"
                            enabledState: teensyController.all_status.relay_on
                            iconText: "TR"
                            
                            onClicked: teensyController.setRelayEnabled(!teensyController.all_status.relay_on)
                        }
                        
                        // Teensy Enable Control
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "Teensy Enable"
                            controlStatus: teensyController.all_status.enabled ? "Powered" : "Unpowered"
                            enabledState: teensyController.all_status.enabled
                            iconText: "T"
                            
                            onClicked: teensyController.setEnabled(!teensyController.all_status.enabled)
                        }
                        
                        // Yaw Control
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "Yaw Control"
                            controlStatus: teensyController.all_status.yaw_enabled ? "Active" : "Inactive"
                            enabledState: teensyController.all_status.yaw_enabled
                            iconText: "Y"
                            
                            onClicked: teensyController.setYawEnabled(!teensyController.all_status.yaw_enabled)
                        }

                        // SprayGun Levelling
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "SprayGun Levelling"
                            controlStatus: teensyController.spray_gun_leveling_enabled ? "Active" : "Inactive"
                            enabledState: teensyController.spray_gun_leveling_enabled
                            iconText: "SL"

                            onClicked: teensyController.setSprayGunLevelingEnabled(!teensyController.spray_gun_leveling_enabled)
                        }

                        // SprayGun Led Control
                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "SprayGun LED"
                            controlStatus: teensyController.spray_gun_led_on ? "On" : "Off"
                            enabledState: teensyController.spray_gun_led_on
                            iconText: "LED"
                            
                            onClicked: teensyController.setSprayGunLED(!teensyController.spray_gun_led_on)
                        }

                        ControlPanel {
                            Layout.fillWidth: true
                            controlName: "Lidar Power"
                            iconText: "LED"
                            selfContained: true 
                            
                            onClicked: teensyController.setLidarPower(enabledState)
                        }
                        
                        ActionButton {
                            Layout.fillWidth: true
                            buttonText: "Home Top Rail"
                            buttonDescription: "(Be careful of the tilting during the process)"
                            iconColor: "#4CAF50"
                            iconType: "reset"
                            
                            onClicked: {
                                if (teensyController) {
                                    teensyController.homeTopRail(true)
                                    showFeedback()
                                } else {
                                    console.log("Teensy controller not available")
                                }
                            }
                        }

                        ActionButton {
                            buttonText: "Home Arm Rail"
                            buttonDescription: "(Be careful of the tilting during the process)"
                            iconColor: "#4CAF50"
                            iconType: "reset"

                            onClicked: {
                                if (teensyController) {
                                    teensyController.homeArm(true)
                                    showFeedback()
                                } else {
                                    console.log("Teensy controller not available")
                                }
                            }
                        }
                        
                        // Bottom spacer to ensure last item isn't cut off
                        Item { 
                            Layout.fillWidth: true
                            height: 10
                        }
                    }
                }
            }
        }
        
        // Error Cleaning Button Section
        Item {
            Layout.fillWidth: true
            Layout.topMargin: 10
            height: 32
            
            Text {
                text: "System Errors"
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 18
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            
            Rectangle {
                height: 1
                width: parent.width - 120
                color: "#333333"
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        // Error Clear Button
        Rectangle {
            id: errorClearButton
            Layout.fillWidth: true
            height: 60
            radius: 10
            color: errorClearMouseArea.containsMouse ? "#4A2C2C" : "#3A2222"
            border.color: "#8C3A3A"
            border.width: 1
            
            Behavior on color {
                ColorAnimation { duration: 200 }
            }
            
            MouseArea {
                id: errorClearMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    heartbeatHandler.clear_error_state()
                }
            }
            
            RowLayout {
                anchors {
                    fill: parent
                    margins: 10
                }
                spacing: 15
                
                // Icon
                Rectangle {
                    width: 36
                    height: 36
                    radius: 18
                    color: "#8C3A3A"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "⚠"
                        font.pixelSize: 16
                        color: "white"
                        font.bold: true
                    }
                }
                
                // Text
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    
                    Text {
                        text: "Clear Error States"
                        font.pixelSize: 16
                        font.bold: true
                        color: "#FFFFFF"
                    }
                    
                    Text {
                        text: "Reset all error flags in system components"
                        font.pixelSize: 13
                        color: "#F99090"
                    }
                }
                
                // Reset icon
                Rectangle {
                    width: 36
                    height: 36
                    radius: 18
                    color: "#8C3A3A"
                    
                    Text {
                        anchors.centerIn: parent
                        text: "↺"
                        font.pixelSize: 20
                        color: "white"
                        font.bold: true
                    }
                }
            }
        }
    }
}