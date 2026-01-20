// Wheels Card - Left and Right wheel telemetry
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    title: "Wheels"
    
    property real maxWheelCurrent: 10.0
    
    RowLayout {
        anchors.fill: parent
        spacing: 12
        
        // Left Wheel
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8
            
            Row {
                spacing: 6
                Layout.alignment: Qt.AlignHCenter
                
                Text {
                    text: "L"
                    font.pixelSize: 20
                    font.bold: true
                    font.family: "Roboto"
                    color: "#AAAAAA"
                }
                
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: wheelController.left_motor_available ? "#2ecc71" : "#e74c3c"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            Text {
                text: Math.abs(wheelController.left_wheel_speed || 0).toFixed(2)
                font.pixelSize: 32
                font.family: "Monospace"
                font.bold: true
                color: "#3498db"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: "m/s"
                font.pixelSize: 14
                font.family: "Roboto"
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: Math.abs(wheelController.left_wheel_current || 0).toFixed(1) + " A"
                font.pixelSize: 16
                font.family: "Monospace"
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                Layout.margins: 4
                value: Math.abs(wheelController.left_wheel_current || 0)
                maxValue: maxWheelCurrent
                barColor: "#2ecc71"
            }
        }
        
        // Right Wheel
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 8
            
            Row {
                spacing: 6
                Layout.alignment: Qt.AlignHCenter
                
                Text {
                    text: "R"
                    font.pixelSize: 20
                    font.bold: true
                    font.family: "Roboto"
                    color: "#AAAAAA"
                }
                
                Rectangle {
                    width: 14
                    height: 14
                    radius: 7
                    color: wheelController.right_motor_available ? "#2ecc71" : "#e74c3c"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            Text {
                text: Math.abs(wheelController.right_wheel_speed || 0).toFixed(2)
                font.pixelSize: 32
                font.family: "Monospace"
                font.bold: true
                color: "#3498db"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: "m/s"
                font.pixelSize: 14
                font.family: "Roboto"
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: Math.abs(wheelController.right_wheel_current || 0).toFixed(1) + " A"
                font.pixelSize: 16
                font.family: "Monospace"
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                Layout.margins: 4
                value: Math.abs(wheelController.right_wheel_current || 0)
                maxValue: maxWheelCurrent
                barColor: "#2ecc71"
            }
        }
    }
}
