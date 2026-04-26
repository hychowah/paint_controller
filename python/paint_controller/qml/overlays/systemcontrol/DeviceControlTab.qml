import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "./components"

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
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Hardware Power"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "Core power controls for system components"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }
                    
                    // Teensy Relay Control
                    ControlPanel {
                        objectName: "teensyRelayControl"
                        Layout.fillWidth: true
                        controlName: "Teensy Relay"
                        controlStatus: teensyController.all_status.relay_on ? "Connected" : "Disconnected"
                        enabledState: teensyController.all_status.relay_on
                        iconText: "TR"
                        actionKey: "status.teensy_relay"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleTeensyRelay(teensyController.all_status.relay_on)
                    }
                    
                    // Teensy Enable Control
                    ControlPanel {
                        objectName: "teensyEnableControl"
                        Layout.fillWidth: true
                        controlName: "Teensy Enable"
                        controlStatus: teensyController.all_status.enabled ? "Powered" : "Unpowered"
                        enabledState: teensyController.all_status.enabled
                        iconText: "T"
                        actionKey: "status.teensy_enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleTeensyEnable(teensyController.all_status.enabled)
                    }
                }
            }

            // =====================================================
            // Winch Section
            // =====================================================
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Winch"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "Winch motor and load controls"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }
                    
                    // Winch Enable Control
                    ControlPanel {
                        objectName: "winchEnableControl"
                        Layout.fillWidth: true
                        controlName: "Winch Enable"
                        controlStatus: winchController.enabled ? "Enabled" : "Disabled"
                        enabledState: winchController.enabled
                        iconText: "W"
                        actionKey: "status.winch_enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleWinchEnable(winchController.enabled)
                    }
                    
                    // Winch Load Detection Control
                    ControlPanel {
                        objectName: "loadDetectionControl"
                        Layout.fillWidth: true
                        controlName: "Load Detection"
                        controlStatus: winchController.load_detection_enabled ? "Active" : "Inactive"
                        enabledState: winchController.load_detection_enabled
                        iconText: "LD"
                        actionKey: "winch.load_detection"
                        legalityModel: actionLegality
                        
                        onClicked: deviceOperationsHandler.toggleLoadDetection(winchController.load_detection_enabled)
                    }
                }
            }

            // =====================================================
            // Wheel Section
            // =====================================================
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Wheel"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "Wheel motor controls"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }
                    
                    // Wheel Enable Control
                    ControlPanel {
                        objectName: "wheelEnableControl"
                        Layout.fillWidth: true
                        controlName: "Wheel Enable"
                        controlStatus: wheelController ? (wheelController.enabled ? "Motors active" : "Motors inactive") : "Unavailable"
                        enabledState: wheelController ? wheelController.enabled : false
                        iconText: "🛞"
                        actionKey: "wheel.enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleWheelEnable(wheelController ? wheelController.enabled : false)
                    }
                    
                    // Wheel Reset Position Button
                    ActionButton {
                        objectName: "wheelResetAction"
                        Layout.fillWidth: true
                        buttonText: "Reset Wheel Position"
                        buttonDescription: "Set wheel position counters to zero"
                        iconColor: "#4CAF50"
                        iconType: "reset"
                        actionKey: "wheel.reset_position"
                        legalityModel: actionLegality
                        
                        onClicked: {
                            if (deviceActionHandler.resetWheelPosition()) {
                                showFeedback()
                            }
                        }
                    }
                }
            }

            // =====================================================
            // Recording & Monitoring Section
            // =====================================================
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Recording & Monitoring"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "Camera, screen, and data recording"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }
                    
                    // Camera Recording Control (End Effector)
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "EF Camera Recording"
                        controlStatus: baseStreamHandler.is_recording ? "Recording" : "Streaming"
                        enabledState: baseStreamHandler.is_recording
                        iconText: "REC"
                        
                        onClicked: deviceOperationsHandler.toggleEndEffectorRecording()
                    }

                    // Base Camera Recording Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Base Camera Recording"
                        controlStatus: baseStreamHandler.is_base_recording ? "Recording" : "Streaming"
                        enabledState: baseStreamHandler.is_base_recording
                        iconText: "BASE"
                        
                        onClicked: deviceOperationsHandler.toggleBaseRecording()
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
                        
                        onClicked: deviceOperationsHandler.toggleScreenRecording()
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
                        
                        onClicked: deviceOperationsHandler.toggleRosBagRecording()
                    }
                }
            }

            // =====================================================
            // Stabilization Section
            // =====================================================
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Stabilization"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "Stability, yaw, and leveling controls"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }
                    
                    // Stability Controller (Master Enable)
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Stability Controller"
                        controlStatus: teensyController.stability_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.stability_enabled
                        iconText: "SC"
                        
                        onClicked: deviceOperationsHandler.toggleStability(teensyController.stability_enabled)
                    }

                    // Yaw Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Yaw Control"
                        controlStatus: teensyController.all_status.yaw_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.all_status.yaw_enabled
                        iconText: "Y"
                        
                        onClicked: deviceOperationsHandler.toggleYaw(teensyController.all_status.yaw_enabled)
                    }

                    // Auto Correction Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Auto Correction"
                        controlStatus: teensyController.auto_correction_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.auto_correction_enabled
                        iconText: "AC"
                        
                        onClicked: deviceOperationsHandler.toggleAutoCorrection(teensyController.auto_correction_enabled)
                    }

                    // SprayGun Levelling
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "SprayGun Levelling"
                        controlStatus: teensyController.spray_gun_leveling_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.spray_gun_leveling_enabled
                        iconText: "SL"

                        onClicked: deviceOperationsHandler.toggleSprayGunLeveling(teensyController.spray_gun_leveling_enabled)
                    }

                    // Roller Steering Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Roller Steering"
                        controlStatus: teensyController.roller_steering_enabled ? "Enabled" : "Disabled"
                        enabledState: teensyController.roller_steering_enabled
                        iconText: "RS"
                        
                        onClicked: deviceOperationsHandler.toggleRollerSteering(teensyController.roller_steering_enabled)
                    }

                    // Swing Damping Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Swing Damping"
                        controlStatus: teensyController.swing_damping_enabled ? "Active" : "Inactive"
                        enabledState: teensyController.swing_damping_enabled
                        iconText: "SD"
                        
                        onClicked: deviceOperationsHandler.toggleSwingDamping(teensyController.swing_damping_enabled)
                    }
                }
            }

            // =====================================================
            // Other Controls Section
            // =====================================================
            Rectangle {
                Layout.fillWidth: true
                color: "#1E2433"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 8
                height: childrenRect.height + 30
                
                ColumnLayout {
                    width: parent.width - 30
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: 15
                    spacing: 8
                    
                    // Section Header
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        
                        Text {
                            text: "Other Controls"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        
                        Text {
                            text: "LED, lidar, and homing actions"
                            color: "#888888"
                            font.pixelSize: 13
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                            Layout.topMargin: 5
                            Layout.bottomMargin: 5
                        }
                    }

                    // SprayGun Led Control
                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "SprayGun LED"
                        controlStatus: teensyController.spray_gun_led_on ? "On" : "Off"
                        enabledState: teensyController.spray_gun_led_on
                        iconText: "LED"
                        
                        onClicked: deviceOperationsHandler.toggleSprayGunLed(teensyController.spray_gun_led_on)
                    }

                    ControlPanel {
                        Layout.fillWidth: true
                        controlName: "Lidar Power"
                        controlStatus: enabledState ? "On" : "Off"
                        iconText: "LID"
                        selfContained: true 
                        
                        onClicked: deviceOperationsHandler.setLidarPower(enabledState)
                    }
                    
                    ActionButton {
                        Layout.fillWidth: true
                        buttonText: "Home Top Rail"
                        buttonDescription: "(Be careful of the tilting during the process)"
                        iconColor: "#4CAF50"
                        iconType: "reset"
                        
                        onClicked: {
                            if (deviceActionHandler.homeTopRail()) {
                                showFeedback()
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
                            if (deviceActionHandler.homeArm()) {
                                showFeedback()
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
                        deviceOperationsHandler.clearErrors()
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