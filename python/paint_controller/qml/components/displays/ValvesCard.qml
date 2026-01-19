// Valves Card - Flow rate, position, and motor data
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    id: valvesCard
    title: "Valves"
    
    // Consistent sizing for all metrics
    property int metricValueSize: 28
    property int metricLabelSize: 13
    property int metricUnitSize: 12
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 10
        
        // Top row: Flow Rate, Motor Current, Total Volume
        RowLayout {
            Layout.fillWidth: true
            spacing: 0
            
            Item { Layout.fillWidth: true }
            
            // Flow Rate
            MetricValue {
                label: "Flow Rate"
                value: (teensyController.all_status.valve_rate || 0).toFixed(1)
                unit: "L/min"
                valueColor: "#3498db"
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
            
            // Motor Current
            MetricValue {
                label: "Motor Current"
                value: (teensyController.all_status.valve_motor_current || 0).toFixed(1)
                unit: "A"
                valueColor: "#2ecc71"
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
            
            // Total Volume
            MetricValue {
                label: "Total Volume"
                value: (teensyController.all_status.total_volumne || 0).toFixed(1)
                unit: "L"
                valueColor: "#f39c12"
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
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
    }
}
