// Winch Card - Cable and motor data
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../../../core"

IndustrialCard {
    id: winchCard
    title: "Winch Data"

    required property var winchStatus
    required property real maxWinchCurrent
    
    // Consistent sizing for all metrics
    property int metricValueSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
    property int metricLabelSize: CommonStyle.fontCaption
    property int metricUnitSize: CommonStyle.fontLabel
    
    GridLayout {
        anchors.fill: parent
        columns: 2
        rowSpacing: CommonStyle.spacingMd
        columnSpacing: CommonStyle.spacingXl - CommonStyle.spacingXs
        
        // Cable Length
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Cable Length"
            value: (winchCard.winchStatus.cableLength / 1000).toFixed(2)
            unit: "m"
            valueColor: CommonStyle.accentPrimary
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Cable Speed
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: (winchCard.winchStatus.cableSpeed >= 0 ? "↑" : "↓") + " Cable Speed"
            value: Math.abs(winchCard.winchStatus.cableSpeed).toFixed(1)
            unit: "m/s"
            valueColor: CommonStyle.accentPrimary
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Voltage
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Voltage"
            value: winchCard.winchStatus.motorVoltage.toFixed(1)
            unit: "V"
            valueColor: CommonStyle.accentPrimary
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Temperature
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Temperature"
            value: winchCard.winchStatus.motorTemperature.toFixed(1)
            unit: "°C"
            valueColor: CommonStyle.accentPrimary
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Current with progress bar
        ColumnLayout {
            Layout.fillWidth: true
            Layout.columnSpan: 2
            spacing: CommonStyle.spacingXs + 2
            
            property real currentValue: winchCard.winchStatus.winchTorque / 100
            property real currentPercent: winchCard.maxWinchCurrent > 0 ? currentValue / winchCard.maxWinchCurrent * 100 : 0
            
            Text {
                text: "Current"
                font.pixelSize: winchCard.metricLabelSize
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
            }
            
            Text {
                text: parent.currentValue.toFixed(2) + " A (" + parent.currentPercent.toFixed(0) + "%)"
                font.pixelSize: winchCard.metricValueSize
                font.family: CommonStyle.fontMono
                font.bold: true
                color: CommonStyle.accentPrimary
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                value: parent.currentValue
                maxValue: winchCard.maxWinchCurrent
                barColor: parent.currentPercent > 80 ? CommonStyle.statusWarning : CommonStyle.statusSuccess
                barHeight: CommonStyle.spacingSm + 2
            }
        }
    }
}
