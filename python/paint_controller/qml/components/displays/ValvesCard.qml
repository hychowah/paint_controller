// Valves Card - Flow rate, position, and motor data
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    title: "Valves"
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        
        // Flow Rate
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            
            Text {
                text: "Flow Rate"
                font.pixelSize: 13
                font.family: "Roboto"
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: (teensyController.all_status.valve_rate || 0).toFixed(1)
                font.pixelSize: 34
                font.family: "Monospace"
                font.bold: true
                color: "#3498db"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
            
            Text {
                text: "L/min"
                font.pixelSize: 12
                font.family: "Roboto"
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
            }
        }
        
        Item { Layout.preferredHeight: 6 }
        
        // Valve Position
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            
            property real valvePositionPercent: (teensyController.all_status.valve_position || 0)
            
            Text {
                text: "Position: " + parent.valvePositionPercent.toFixed(0) + "%"
                font.pixelSize: 12
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                
                property real valvePositionPercent: parent.valvePositionPercent
                property real normalizedPosition: valvePositionPercent / 100.0
                
                Rectangle {
                    anchors.fill: parent
                    color: "#1e222b"
                    radius: 9
                }
                
                Rectangle {
                    width: Math.max(0, Math.min(parent.width * parent.normalizedPosition, parent.width))
                    height: parent.height
                    color: "#3498db"
                    radius: 9
                    
                    Behavior on width {
                        NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                    }
                }
                
                Rectangle {
                    x: Math.max(4, Math.min(parent.width * parent.normalizedPosition - 4, parent.width - 12))
                    y: parent.height / 2 - 6
                    width: 12
                    height: 12
                    color: "#FFFFFF"
                    radius: 6
                    border.color: "#3498db"
                    border.width: 2
                    
                    Behavior on x {
                        NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
                    }
                }
            }
        }
        
        Item { Layout.preferredHeight: 6 }
        
        // Additional data
        GridLayout {
            Layout.fillWidth: true
            columns: 2
            rowSpacing: 6
            columnSpacing: 10
            
            Text {
                text: "Motor Current:"
                font.pixelSize: 11
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: (teensyController.all_status.valve_motor_current || 0).toFixed(1) + " A"
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                text: "Total Volume:"
                font.pixelSize: 11
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: (teensyController.all_status.total_volumne || 0).toFixed(1) + " L"
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#FFFFFF"
                horizontalAlignment: Text.AlignRight
            }
        }
    }
}
