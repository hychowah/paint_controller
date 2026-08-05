import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "./components"

Item {
    id: deviceControlTab
    required property var recordingStatus
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var wheelActions
    required property var winchActions
    required property var teensyActions
    required property var recordingActions
    required property var systemActions
    required property var actionLegality
    required property var settingsManager

    // Shared content column: Column (not ColumnLayout) so height is always real.
    component DeviceSectionBody: Column {
        width: parent ? parent.width : 300
        spacing: CommonStyle.spacingSm
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        ScrollBar.vertical.policy: ScrollBar.AsNeeded
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: CommonStyle.spacingSm + 2

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Hardware Power"
                description: "Core power controls for system components"
                sectionId: "devices_hardware_power"
                defaultExpanded: true

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "teensyRelayControl"
                            width: parent.width
                            controlName: "Teensy Relay"
                            controlStatus: deviceControlTab.teensyStatus.relayOn ? "Connected" : "Disconnected"
                            enabledState: deviceControlTab.teensyStatus.relayOn
                            iconText: "TR"
                            actionKey: "status.teensy_relay"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: deviceControlTab.teensyActions.toggleTeensyRelay()
                        }
                        ControlPanel {
                            objectName: "teensyEnableControl"
                            width: parent.width
                            controlName: "Teensy Enable"
                            controlStatus: deviceControlTab.teensyStatus.enabled ? "Powered" : "Unpowered"
                            enabledState: deviceControlTab.teensyStatus.enabled
                            iconText: "T"
                            actionKey: "status.teensy_enable"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: deviceControlTab.teensyActions.toggleTeensyEnable()
                        }
                    }
                }
            }

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Winch"
                description: "Winch motor and load controls"
                sectionId: "devices_winch"
                defaultExpanded: false

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "winchEnableControl"
                            width: parent.width
                            controlName: "Winch Enable"
                            controlStatus: deviceControlTab.winchStatus.enabled ? "Enabled" : "Disabled"
                            enabledState: deviceControlTab.winchStatus.enabled
                            iconText: "W"
                            actionKey: "status.winch_enable"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: deviceControlTab.winchActions.toggleWinchEnable()
                        }
                        ControlPanel {
                            objectName: "loadDetectionControl"
                            width: parent.width
                            controlName: "Load Detection"
                            controlStatus: deviceControlTab.winchStatus.loadDetectionEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.winchStatus.loadDetectionEnabled
                            iconText: "LD"
                            actionKey: "winch.load_detection"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: deviceControlTab.winchActions.toggleLoadDetection()
                        }
                    }
                }
            }

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Wheel"
                description: "Wheel motor controls"
                sectionId: "devices_wheel"
                defaultExpanded: false

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "wheelEnableControl"
                            width: parent.width
                            controlName: "Wheel Enable"
                            controlStatus: deviceControlTab.wheelStatus.available
                                ? (deviceControlTab.wheelStatus.enabled ? "Motors active" : "Motors inactive")
                                : "Unavailable"
                            enabledState: deviceControlTab.wheelStatus.enabled
                            iconText: "WH"
                            actionKey: "wheel.enable"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: deviceControlTab.wheelActions.toggleEnabled()
                        }
                        ActionButton {
                            objectName: "wheelResetAction"
                            width: parent.width
                            buttonText: "Reset Wheel Position"
                            buttonDescription: "Set wheel position counters to zero"
                            iconColor: CommonStyle.statusSuccess
                            iconType: "reset"
                            actionKey: "wheel.reset_position"
                            legalityModel: deviceControlTab.actionLegality
                            onClicked: {
                                if (deviceControlTab.wheelActions.resetPosition())
                                    showFeedback()
                            }
                        }
                    }
                }
            }

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Recording & Monitoring"
                description: "Camera, screen, and data recording"
                sectionId: "devices_recording"
                defaultExpanded: false

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "efRecordingControl"
                            width: parent.width
                            controlName: "EF Camera Recording"
                            controlStatus: deviceControlTab.recordingStatus.endEffectorRecording ? "Recording" : "Streaming"
                            enabledState: deviceControlTab.recordingStatus.endEffectorRecording
                            iconText: "REC"
                            onClicked: deviceControlTab.recordingActions.toggleEndEffectorRecording()
                        }
                        ControlPanel {
                            objectName: "baseRecordingControl"
                            width: parent.width
                            controlName: "Base Camera Recording"
                            controlStatus: deviceControlTab.recordingStatus.baseRecording ? "Recording" : "Streaming"
                            enabledState: deviceControlTab.recordingStatus.baseRecording
                            iconText: "BASE"
                            onClicked: deviceControlTab.recordingActions.toggleBaseRecording()
                        }
                        ControlPanel {
                            objectName: "screenRecordingControl"
                            width: parent.width
                            controlName: "Screen Recording"
                            controlStatus: {
                                if (deviceControlTab.recordingStatus.screenFreeSpaceGb < 5.0) {
                                    return "Low Storage! (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB)"
                                } else if (deviceControlTab.recordingStatus.screenRecording) {
                                    var mins = Math.floor(deviceControlTab.recordingStatus.screenRecordingDuration / 60)
                                    var secs = deviceControlTab.recordingStatus.screenRecordingDuration % 60
                                    return "Recording " + mins + ":" + (secs < 10 ? "0" : "") + secs
                                        + " (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB free)"
                                }
                                return "Idle (" + deviceControlTab.recordingStatus.screenFreeSpaceGb.toFixed(1) + " GB free)"
                            }
                            enabledState: deviceControlTab.recordingStatus.screenRecording
                            iconText: "SCR"
                            onClicked: deviceControlTab.recordingActions.toggleScreenRecording()
                        }
                        ControlPanel {
                            objectName: "rosBagRecordingControl"
                            width: parent.width
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
                                }
                                return "Idle (Remote EF)"
                            }
                            enabledState: deviceControlTab.recordingStatus.rosBagRecording
                            iconText: "BAG"
                            enabled: !deviceControlTab.recordingStatus.rosBagCompressing
                            opacity: deviceControlTab.recordingStatus.rosBagCompressing ? 0.6 : 1.0
                            onClicked: deviceControlTab.recordingActions.toggleRosBagRecording()
                        }
                    }
                }
            }

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Stabilization"
                description: "Stability, yaw, and leveling controls"
                sectionId: "devices_stabilization"
                defaultExpanded: false

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "stabilityControl"
                            width: parent.width
                            controlName: "Stability Controller"
                            controlStatus: deviceControlTab.teensyStatus.stabilityEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.teensyStatus.stabilityEnabled
                            iconText: "SC"
                            onClicked: deviceControlTab.teensyActions.toggleStability()
                        }
                        ControlPanel {
                            objectName: "yawControl"
                            width: parent.width
                            controlName: "Yaw Control"
                            controlStatus: deviceControlTab.teensyStatus.yawEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.teensyStatus.yawEnabled
                            iconText: "Y"
                            onClicked: deviceControlTab.teensyActions.toggleYaw()
                        }
                        ControlPanel {
                            objectName: "autoCorrectionControl"
                            width: parent.width
                            controlName: "Auto Correction"
                            controlStatus: deviceControlTab.teensyStatus.autoCorrectionEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.teensyStatus.autoCorrectionEnabled
                            iconText: "AC"
                            onClicked: deviceControlTab.teensyActions.toggleAutoCorrection()
                        }
                        ControlPanel {
                            objectName: "sprayGunLevelingControl"
                            width: parent.width
                            controlName: "SprayGun Levelling"
                            controlStatus: deviceControlTab.teensyStatus.sprayGunLevelingEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.teensyStatus.sprayGunLevelingEnabled
                            iconText: "SL"
                            onClicked: deviceControlTab.teensyActions.toggleSprayGunLeveling()
                        }
                        ControlPanel {
                            objectName: "rollerSteeringControl"
                            width: parent.width
                            controlName: "Roller Steering"
                            controlStatus: deviceControlTab.teensyStatus.rollerSteeringEnabled ? "Enabled" : "Disabled"
                            enabledState: deviceControlTab.teensyStatus.rollerSteeringEnabled
                            iconText: "RS"
                            onClicked: deviceControlTab.teensyActions.toggleRollerSteering()
                        }
                        ControlPanel {
                            objectName: "swingDampingControl"
                            width: parent.width
                            controlName: "Swing Damping"
                            controlStatus: deviceControlTab.teensyStatus.swingDampingEnabled ? "Active" : "Inactive"
                            enabledState: deviceControlTab.teensyStatus.swingDampingEnabled
                            iconText: "SD"
                            onClicked: deviceControlTab.teensyActions.toggleSwingDamping()
                        }
                    }
                }
            }

            SettingsSection {
                settingsManager: deviceControlTab.settingsManager
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                title: "Other Controls"
                description: "LED, lidar, and homing actions"
                sectionId: "devices_other"
                defaultExpanded: false

                contentItem: Component {
                    DeviceSectionBody {
                        ControlPanel {
                            objectName: "sprayGunLedControl"
                            width: parent.width
                            controlName: "SprayGun LED"
                            controlStatus: deviceControlTab.teensyStatus.sprayGunLedOn ? "On" : "Off"
                            enabledState: deviceControlTab.teensyStatus.sprayGunLedOn
                            iconText: "LED"
                            onClicked: deviceControlTab.teensyActions.toggleSprayGunLed()
                        }
                        ControlPanel {
                            width: parent.width
                            controlName: "Lidar Power"
                            controlStatus: deviceControlTab.teensyStatus.lidarPower ? "On" : "Off"
                            enabledState: deviceControlTab.teensyStatus.lidarPower
                            iconText: "LID"
                            onClicked: deviceControlTab.teensyActions.toggleLidarPower()
                        }
                        ActionButton {
                            width: parent.width
                            buttonText: "Home Top Rail"
                            buttonDescription: "(Be careful of the tilting during the process)"
                            iconColor: CommonStyle.statusWarning
                            iconType: "warning"
                            onClicked: {
                                if (deviceControlTab.teensyActions.homeTopRail())
                                    showFeedback()
                            }
                        }
                        ActionButton {
                            width: parent.width
                            buttonText: "Home Arm Rail"
                            buttonDescription: "(Be careful of the tilting during the process)"
                            iconColor: CommonStyle.statusWarning
                            iconType: "warning"
                            onClicked: {
                                if (deviceControlTab.teensyActions.homeArm())
                                    showFeedback()
                            }
                        }
                    }
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: CommonStyle.controlHeightMd
                Layout.topMargin: CommonStyle.spacingXs
                implicitHeight: CommonStyle.controlHeightMd
                height: implicitHeight

                Text {
                    text: "System Errors"
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                }

                Rectangle {
                    height: 1
                    width: parent.width - Math.round(120 * CommonStyle.scaleFactor)
                    color: CommonStyle.inputBorder
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            ActionButton {
                objectName: "clearErrorsAction"
                Layout.fillWidth: true
                Layout.preferredHeight: implicitHeight
                buttonText: "Clear Error States"
                buttonDescription: "Reset all error flags in system components"
                iconColor: CommonStyle.statusError
                iconType: "warning"
                onClicked: {
                    deviceControlTab.systemActions.clearErrors()
                    showFeedback()
                }
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: CommonStyle.spacingSm
                implicitHeight: CommonStyle.spacingSm
                height: implicitHeight
            }
        }
    }
}
