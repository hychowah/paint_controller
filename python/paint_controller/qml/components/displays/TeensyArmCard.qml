// Teensy Arm Card - Extension and current data
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    title: "Teensy Arm"
    
    property real maxArmCurrent: 200
    property real maxArmExtension: 1500
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 14
        
        // Extension
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                text: "Extension"
                font.pixelSize: 14
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: ((teensyController.all_status.arm_extension_dist || 0)).toFixed(0) + " mm"
                font.pixelSize: 32
                font.family: "Monospace"
                font.bold: true
                color: "#3498db"
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                value: teensyController.all_status.arm_extension_dist || 0
                maxValue: maxArmExtension
                barColor: "#2ecc71"
                barHeight: 10
            }
        }
        
        Item { Layout.preferredHeight: 8 }
        
        // Current comparison
        RowLayout {
            Layout.fillWidth: true
            spacing: 24
            
            // Arm Current
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                
                Text {
                    text: "Arm Current"
                    font.pixelSize: 13
                    font.family: "Roboto"
                    color: "#AAAAAA"
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
                        color: "#3498db"
                        radius: 5
                        
                        Behavior on height {
                            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                        }
                    }
                }
                
                Text {
                    text: (Math.abs(teensyController.all_status.arm_rail_current || 0) / 10).toFixed(0) + " A"
                    font.pixelSize: 14
                    font.family: "Monospace"
                    color: "#3498db"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
            
            // Spray Gun Current
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 8
                
                Text {
                    text: "Spray Gun"
                    font.pixelSize: 13
                    font.family: "Roboto"
                    color: "#AAAAAA"
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
                        color: "#3498db"
                        radius: 5
                        
                        Behavior on height {
                            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                        }
                    }
                }
                
                Text {
                    text: (Math.abs(teensyController.all_status.gimbal_pitch_motor_current || 0) / 10).toFixed(0) + " A"
                    font.pixelSize: 14
                    font.family: "Monospace"
                    color: "#3498db"
                    horizontalAlignment: Text.AlignHCenter
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
