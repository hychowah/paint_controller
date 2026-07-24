// Valves Card - Flow rate, position, and motor data
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../../../theme"

IndustrialCard {
    id: valvesCard
    title: "Valves"
    required property var valveStatus
    
    // Consistent sizing for all metrics
    readonly property int metricValueSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
    readonly property int metricLabelSize: CommonStyle.fontCaption
    readonly property int metricUnitSize: CommonStyle.fontLabel
    
    ColumnLayout {
        anchors.fill: parent
        spacing: CommonStyle.spacingSm + 2
        
        // Top row: Flow Rate, Motor Current, Total Volume
        RowLayout {
            Layout.fillWidth: true
            spacing: 0
            
            Item { Layout.fillWidth: true }
            
            // Flow Rate
            MetricValue {
                label: "Flow Rate"
                value: valvesCard.valveStatus.valveRate.toFixed(1)
                unit: "L/min"
                valueColor: CommonStyle.accentPrimary
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
            
            // Motor Current
            MetricValue {
                label: "Motor Current"
                value: valvesCard.valveStatus.valveMotorCurrent.toFixed(1)
                unit: "A"
                valueColor: CommonStyle.accentPrimary
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
            
            // Total Volume
            MetricValue {
                label: "Total Volume"
                value: valvesCard.valveStatus.totalVolume.toFixed(1)
                unit: "L"
                valueColor: CommonStyle.accentPrimary
                valueFontSize: valvesCard.metricValueSize
                labelFontSize: valvesCard.metricLabelSize
                unitFontSize: valvesCard.metricUnitSize
            }
            
            Item { Layout.fillWidth: true }
        }
        
        Item { Layout.preferredHeight: CommonStyle.spacingXs + 2 }
        
        // Valve Position
        ColumnLayout {
            Layout.fillWidth: true
            spacing: CommonStyle.spacingXs + 2
            
            property real valvePositionPercent: valvesCard.valveStatus.valvePosition
            
            Text {
                text: "Position: " + parent.valvePositionPercent.toFixed(0) + "%"
                font.pixelSize: CommonStyle.fontLabel
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
            }
            
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 18
                
                property real valvePositionPercent: parent.valvePositionPercent
                property real normalizedPosition: valvePositionPercent / 100.0
                
                Rectangle {
                    anchors.fill: parent
                    color: CommonStyle.inputBackground
                    radius: 9
                }
                
                Rectangle {
                    width: Math.max(0, Math.min(parent.width * parent.normalizedPosition, parent.width))
                    height: parent.height
                    color: CommonStyle.accentPrimary
                    radius: 9
                    
                    Behavior on width {
                        NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
                    }
                }
                
                Rectangle {
                    x: Math.max(4, Math.min(parent.width * parent.normalizedPosition - 4, parent.width - 12))
                    y: parent.height / 2 - 6
                    width: 12
                    height: 12
                    color: CommonStyle.textPrimary
                    radius: 6
                    border.color: CommonStyle.accentPrimary
                    border.width: 2
                    
                    Behavior on x {
                        NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
                    }
                }
            }
        }
    }
}
