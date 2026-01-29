import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/panels"

Item {
    id: deviceControlTab

    ScrollView {
        anchors.fill: parent
        clip: true
        ScrollBar.vertical.policy: ScrollBar.AsNeeded
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 8

            // =====================================================
            // Hardware Power Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_hardware_power"
                title: "Hardware Power"
                description: "Core power controls for system components"
                
                contentItem: ColumnLayout {
                    spacing: 8
                    
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
                }
            }

            // =====================================================
            // Winch Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_winch"
                title: "Winch"
                description: "Winch motor and load controls"
                
                contentItem: ColumnLayout {
                    spacing: 8
                    
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
                }
            }

            // =====================================================
            // Wheel Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_wheel"
                title: "Wheel"
                description: "Wheel motor controls"
                
                contentItem: ColumnLayout {
                    spacing: 8
                    
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
                }
            }

            // =====================================================
            // Recording & Monitoring Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_recording"
                title: "Recording & Monitoring"
                description: "Camera, screen, and data recording"
                
                contentItem: ColumnLayout {
                    spacing: 8
                    
                    // Camera Recording Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Camera Recording"
                        controlStatus: videoStreamer.is_recording ? "Recording" : "Streaming"
                        enabledState: videoStreamer.is_recording
                        iconText: "REC"
                        
                        onClicked: videoStreamer.toggleRecording()
                    }

                    // Screen Recording Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Screen Recording"
                        controlStatus: {
                            if (screenRecorder.free_space_gb < 5.0) {
                                return "Low Storage! (" + screenRecorder.free_space_gb.toFixed(1) + " GB)"
                            } else if (screenRecorder.is_recording) {
                                var mins = Math.floor(screenRecorder.recording_duration / 60)
                                var secs = screenRecorder.recording_duration % 60
                                return "Recording " + mins + ":" + (secs < 10 ? "0" : "") + secs + " (" + screenRecorder.free_space_gb.toFixed(1) + " GB free)"
                            } else {
                                return "Idle (" + screenRecorder.free_space_gb.toFixed(1) + " GB free)"
                            }
                        }
                        enabledState: screenRecorder.is_recording
                        iconText: "SCR"
                        
                        onClicked: screenRecorder.toggleRecording()
                    }

                    // ROS Bag Recording Control (Remote End Effector)
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "ROS Bag Recording"
                        controlStatus: {
                            if (rosBagRecorder.is_compressing) {
                                return "Compressing..."
                            } else if (rosBagRecorder.is_bag_recording) {
                                var mins = Math.floor(rosBagRecorder.bag_recording_duration / 60)
                                var secs = rosBagRecorder.bag_recording_duration % 60
                                return "Recording " + mins + ":" + (secs < 10 ? "0" : "") + secs
                            } else if (rosBagRecorder.bag_status_message !== "") {
                                return rosBagRecorder.bag_status_message
                            } else {
                                return "Idle (Remote EF)"
                            }
                        }
                        enabledState: rosBagRecorder.is_bag_recording
                        iconText: "BAG"
                        enabled: !rosBagRecorder.is_compressing
                        opacity: rosBagRecorder.is_compressing ? 0.6 : 1.0
                        
                        onClicked: rosBagRecorder.toggleBagRecording()
                    }
                }
            }

            // =====================================================
            // Stabilization Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_stabilization"
                title: "Stabilization"
                description: "Stability, yaw, and leveling controls"
                
                contentItem: ColumnLayout {
                    spacing: 8
                    
                    // Stability Controller (Master Enable)
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Stability Controller"
                        controlStatus: teensyController.stability_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.stability_enabled
                        iconText: "SC"
                        
                        onClicked: teensyController.setStabilityEnabled(!teensyController.stability_enabled)
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

                    // Auto Correction Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Auto Correction"
                        controlStatus: teensyController.auto_correction_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.auto_correction_enabled
                        iconText: "AC"
                        
                        onClicked: teensyController.setAutoCorrectonEnabled(!teensyController.auto_correction_enabled)
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

                    // Roller Steering Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Roller Steering"
                        controlStatus: teensyController.roller_steering_enabled ? "Enabled" : "Disabled"
                        enabledState: teensyController.roller_steering_enabled
                        iconText: "RS"
                        
                        onClicked: teensyController.setRollerSteeringEnabled(!teensyController.roller_steering_enabled)
                    }
                }
            }

            // =====================================================
            // Other Controls Section
            // =====================================================
            SettingsSection {
                Layout.fillWidth: true
                sectionId: "device_other"
                title: "Other Controls"
                description: "LED, lidar, and homing actions"
                
                contentItem: ColumnLayout {
                    spacing: 8

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
                        iconText: "LID"
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
                        Layout.fillWidth: true
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
                }
            }

            // =====================================================
            // System Errors Section (always visible, not collapsible)
            // =====================================================
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
                            font.pixelSize: 14
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
            
            // Bottom spacer
            Item {
                Layout.fillWidth: true
                height: 10
            }
        }
    }
}