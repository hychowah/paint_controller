// Teensy Arm Card - Extension and current data
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../../core"

IndustrialCard {
    title: "Teensy Arm"
    
    property real maxArmCurrent: 200
    property real maxArmExtension: 1500
    
    ColumnLayout {
        anchors.fill: parent
        spacing: CommonStyle.spacingLg
        
        // Extension
        ColumnLayout {
            Layout.fillWidth: true
            spacing: CommonStyle.spacingXs + 2
            
            Text {
                text: "Extension"
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
            }
            
            Text {
                text: ((teensyController.all_status.arm_extension_dist || 0)).toFixed(0) + " mm"
                font.pixelSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
                font.family: CommonStyle.fontMono
                font.bold: true
                color: CommonStyle.accentPrimary
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                value: teensyController.all_status.arm_extension_dist || 0
                maxValue: maxArmExtension
                barColor: CommonStyle.statusSuccess
                barHeight: CommonStyle.spacingSm + 2
            }
        }
        
        Item { Layout.preferredHeight: CommonStyle.spacingSm }
        
        // Current comparison
        RowLayout {
            Layout.fillWidth: true
            spacing: CommonStyle.spacingXl
            
            // Arm Current
            ColumnLayout {
                Layout.fillWidth: true
                spacing: CommonStyle.spacingSm
                
                Text {
                    text: "Arm Current"
                    font.pixelSize: CommonStyle.fontCaption
                    font.family: CommonStyle.fontSans
                    color: CommonStyle.textSecondary
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Item {
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 80
                    Layout.alignment: Qt.AlignHCenter
                    
                    property real heightRatio: maxArmCurrent > 0 ? Math.abs(teensyController.all_status.arm_rail_current || 0) / maxArmCurrent : 0
                    
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: Math.max(12, parent.height * parent.heightRatio)
                        color: CommonStyle.accentPrimary
                        radius: CommonStyle.radiusSm
                        
                        Behavior on height {
                            NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
                        }
                    }
                }
                
                Text {
                    text: (Math.abs(teensyController.all_status.arm_rail_current || 0) / 10).toFixed(0) + " A"
                    font.pixelSize: CommonStyle.fontBody
                    font.family: CommonStyle.fontMono
                    color: CommonStyle.accentPrimary
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
            
            // Spray Gun Current
            ColumnLayout {
                Layout.fillWidth: true
                spacing: CommonStyle.spacingSm
                
                Text {
                    text: "Spray Gun"
                    font.pixelSize: CommonStyle.fontCaption
                    font.family: CommonStyle.fontSans
                    color: CommonStyle.textSecondary
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Item {
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 80
                    Layout.alignment: Qt.AlignHCenter
                    
                    property real heightRatio: maxArmCurrent > 0 ? Math.abs(teensyController.all_status.gimbal_pitch_motor_current || 0) / maxArmCurrent : 0
                    
                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: Math.max(12, parent.height * parent.heightRatio)
                        color: CommonStyle.accentPrimary
                        radius: CommonStyle.radiusSm
                        
                        Behavior on height {
                            NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
                        }
                    }
                }
                
                Text {
                    text: (Math.abs(teensyController.all_status.gimbal_pitch_motor_current || 0) / 10).toFixed(0) + " A"
                    font.pixelSize: CommonStyle.fontBody
                    font.family: CommonStyle.fontMono
                    color: CommonStyle.accentPrimary
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
