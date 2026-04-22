// Wheels Card - Left and Right wheel telemetry
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../../../core"

IndustrialCard {
    title: "Wheels"

    required property real maxWheelCurrent
    
    RowLayout {
        anchors.fill: parent
        spacing: CommonStyle.spacingMd
        
        // Left Wheel
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: CommonStyle.spacingSm
            
            Row {
                spacing: 6
                Layout.alignment: Qt.AlignHCenter
                
                Text {
                    text: "L"
                    font.pixelSize: CommonStyle.fontHeading
                    font.bold: true
                    font.family: CommonStyle.fontSans
                    color: CommonStyle.textSecondary
                }
                
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: wheelController.left_motor_available ? CommonStyle.statusSuccess : CommonStyle.statusError
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            Text {
                text: Math.abs(wheelController.left_wheel_speed || 0).toFixed(2)
                font.pixelSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
                font.family: CommonStyle.fontMono
                font.bold: true
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: "m/s"
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: Math.abs(wheelController.left_wheel_current || 0).toFixed(1) + " A"
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                Layout.margins: 4
                value: Math.abs(wheelController.left_wheel_current || 0)
                maxValue: maxWheelCurrent
                barColor: CommonStyle.statusSuccess
            }
        }
        
        // Right Wheel
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: CommonStyle.spacingSm
            
            Row {
                spacing: 6
                Layout.alignment: Qt.AlignHCenter
                
                Text {
                    text: "R"
                    font.pixelSize: CommonStyle.fontHeading
                    font.bold: true
                    font.family: CommonStyle.fontSans
                    color: CommonStyle.textSecondary
                }
                
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: wheelController.right_motor_available ? CommonStyle.statusSuccess : CommonStyle.statusError
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            Text {
                text: Math.abs(wheelController.right_wheel_speed || 0).toFixed(2)
                font.pixelSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
                font.family: CommonStyle.fontMono
                font.bold: true
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: "m/s"
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: Math.abs(wheelController.right_wheel_current || 0).toFixed(1) + " A"
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                Layout.margins: 4
                value: Math.abs(wheelController.right_wheel_current || 0)
                maxValue: maxWheelCurrent
                barColor: CommonStyle.statusSuccess
            }
        }
    }
}
