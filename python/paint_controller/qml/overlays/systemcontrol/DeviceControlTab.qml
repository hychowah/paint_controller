import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "./components"

Item {
    id: deviceControlTab
    required property var recordingStatus
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus

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
                        controlStatus: deviceControlTab.teensyStatus.relayOn ? "Connected" : "Disconnected"
                        enabledState: deviceControlTab.teensyStatus.relayOn
                        iconText: "TR"
                        actionKey: "status.teensy_relay"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleTeensyRelay(deviceControlTab.teensyStatus.relayOn)
                    }
                    
                    // Teensy Enable Control
                    ControlPanel {
                        objectName: "teensyEnableControl"
                        Layout.fillWidth: true
                        controlName: "Teensy Enable"
                        controlStatus: deviceControlTab.teensyStatus.enabled ? "Powered" : "Unpowered"
                        enabledState: deviceControlTab.teensyStatus.enabled
                        iconText: "T"
                        actionKey: "status.teensy_enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleTeensyEnable(deviceControlTab.teensyStatus.enabled)
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
                        controlStatus: deviceControlTab.winchStatus.enabled ? "Enabled" : "Disabled"
                        enabledState: deviceControlTab.winchStatus.enabled
                        iconText: "W"
                        actionKey: "status.winch_enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleWinchEnable(deviceControlTab.winchStatus.enabled)
                    }
                    
                    // Winch Load Detection Control
                    ControlPanel {
                        objectName: "loadDetectionControl"
                        Layout.fillWidth: true
                        controlName: "Load Detection"
                        controlStatus: deviceControlTab.winchStatus.loadDetectionEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.winchStatus.loadDetectionEnabled
                        iconText: "LD"
                        actionKey: "winch.load_detection"
                        legalityModel: actionLegality
                        
                        onClicked: deviceOperationsHandler.toggleLoadDetection(deviceControlTab.winchStatus.loadDetectionEnabled)
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
                        controlStatus: deviceControlTab.wheelStatus.available ? (deviceControlTab.wheelStatus.enabled ? "Motors active" : "Motors inactive") : "Unavailable"
                        enabledState: deviceControlTab.wheelStatus.enabled
                        iconText: "🛞"
                        actionKey: "wheel.enable"
                        legalityModel: actionLegality
                        
                        onClicked: deviceActionHandler.toggleWheelEnable(deviceControlTab.wheelStatus.enabled)
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
                        objectName: "efRecordingControl"
                        Layout.fillWidth: true
                        controlName: "EF Camera Recording"
                        controlStatus: deviceControlTab.recordingStatus.endEffectorRecording ? "Recording" : "Streaming"
                        enabledState: deviceControlTab.recordingStatus.endEffectorRecording
                        iconText: "REC"
                        
                        onClicked: deviceOperationsHandler.toggleEndEffectorRecording()
                    }

                    // Base Camera Recording Control
                    ControlPanel {
                        objectName: "baseRecordingControl"
                        Layout.fillWidth: true
                        controlName: "Base Camera Recording"
                        controlStatus: deviceControlTab.recordingStatus.baseRecording ? "Recording" : "Streaming"
                        enabledState: deviceControlTab.recordingStatus.baseRecording
                        iconText: "BASE"
                        
                        onClicked: deviceOperationsHandler.toggleBaseRecording()
                    }

                    // Screen Recording Control
                    ControlPanel {
                        objectName: "screenRecordingControl"
                        Layout.fillWidth: true
                        controlName: "Screen Recording"
                        controlStatus: {
                            if (deviceControlTab.recordingStatus.screenFreeSpaceGb < 5.0) {
                                return "Low Storage! (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB)"
                            } else if (deviceControlTab.recordingStatus.screenRecording) {
                                var mins = Math.floor(deviceControlTab.recordingStatus.screenRecordingDuration / 60)
                                var secs = deviceControlTab.recordingStatus.screenRecordingDuration % 60
                                return "Recording " + mins + ":" + (secs < 10 ? "0" : "") + secs + " (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB free)"
                            } else {
                                return "Idle (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB free)"
                            }
                        }
                        enabledState: deviceControlTab.recordingStatus.screenRecording
                        iconText: "SCR"
                        
                        onClicked: deviceOperationsHandler.toggleScreenRecording()
                    }

                    // ROS Bag Recording Control (Remote End Effector)
                    ControlPanel {
                        objectName: "rosBagRecordingControl"
                        Layout.fillWidth: true
                        controlName: "ROS Bag Recording"
                        controlStatus: {
                            if (deviceControlTab.recordingStatus.rosBagCompressing) {
                                return "Compressing..."
                            } else if (deviceControlTab.recordingStatus.rosBagRecording) {
                                var mins = Math.floor(deviceControlTab.recordingStatus.rosBagRecordingDuration / 60)
                                var secs = deviceControlTab.recordingStatus.rosBagRecordingDuration % 60
                                return "Recording " + mins + ":" + (secs < 10 ? "0" : "") + secs
                            } else if (deviceControlTab.recordingStatus.rosBagStatusMessage !== "") {
                                return deviceControlTab.recordingStatus.rosBagStatusMessage
                            } else {
                                return "Idle (Remote EF)"
                            }
                        }
                        enabledState: deviceControlTab.recordingStatus.rosBagRecording
                        iconText: "BAG"
                        enabled: !deviceControlTab.recordingStatus.rosBagCompressing
                        opacity: deviceControlTab.recordingStatus.rosBagCompressing ? 0.6 : 1.0
                        
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
                        objectName: "stabilityControl"
                        Layout.fillWidth: true
                        controlName: "Stability Controller"
                        controlStatus: deviceControlTab.teensyStatus.stabilityEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.teensyStatus.stabilityEnabled
                        iconText: "SC"
                        
                        onClicked: deviceOperationsHandler.toggleStability(deviceControlTab.teensyStatus.stabilityEnabled)
                    }

                    // Yaw Control
                    ControlPanel {
                        objectName: "yawControl"
                        Layout.fillWidth: true
                        controlName: "Yaw Control"
                        controlStatus: deviceControlTab.teensyStatus.yawEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.teensyStatus.yawEnabled
                        iconText: "Y"
                        
                        onClicked: deviceOperationsHandler.toggleYaw(deviceControlTab.teensyStatus.yawEnabled)
                    }

                    // Auto Correction Control
                    ControlPanel {
                        objectName: "autoCorrectionControl"
                        Layout.fillWidth: true
                        controlName: "Auto Correction"
                        controlStatus: deviceControlTab.teensyStatus.autoCorrectionEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.teensyStatus.autoCorrectionEnabled
                        iconText: "AC"
                        
                        onClicked: deviceOperationsHandler.toggleAutoCorrection(deviceControlTab.teensyStatus.autoCorrectionEnabled)
                    }

                    // SprayGun Levelling
                    ControlPanel {
                        objectName: "sprayGunLevelingControl"
                        Layout.fillWidth: true
                        controlName: "SprayGun Levelling"
                        controlStatus: deviceControlTab.teensyStatus.sprayGunLevelingEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.teensyStatus.sprayGunLevelingEnabled
                        iconText: "SL"

                        onClicked: deviceOperationsHandler.toggleSprayGunLeveling(deviceControlTab.teensyStatus.sprayGunLevelingEnabled)
                    }

                    // Roller Steering Control
                    ControlPanel {
                        objectName: "rollerSteeringControl"
                        Layout.fillWidth: true
                        controlName: "Roller Steering"
                        controlStatus: deviceControlTab.teensyStatus.rollerSteeringEnabled ? "Enabled" : "Disabled"
                        enabledState: deviceControlTab.teensyStatus.rollerSteeringEnabled
                        iconText: "RS"
                        
                        onClicked: deviceOperationsHandler.toggleRollerSteering(deviceControlTab.teensyStatus.rollerSteeringEnabled)
                    }

                    // Swing Damping Control
                    ControlPanel {
                        objectName: "swingDampingControl"
                        Layout.fillWidth: true
                        controlName: "Swing Damping"
                        controlStatus: deviceControlTab.teensyStatus.swingDampingEnabled ? "Active" : "Inactive"
                        enabledState: deviceControlTab.teensyStatus.swingDampingEnabled
                        iconText: "SD"
                        
                        onClicked: deviceOperationsHandler.toggleSwingDamping(deviceControlTab.teensyStatus.swingDampingEnabled)
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
                        objectName: "sprayGunLedControl"
                        Layout.fillWidth: true
                        controlName: "SprayGun LED"
                        controlStatus: deviceControlTab.teensyStatus.sprayGunLedOn ? "On" : "Off"
                        enabledState: deviceControlTab.teensyStatus.sprayGunLedOn
                        iconText: "LED"
                        
                        onClicked: deviceOperationsHandler.toggleSprayGunLed(deviceControlTab.teensyStatus.sprayGunLedOn)
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