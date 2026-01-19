// Winch Card - Cable and motor data
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    id: winchCard
    title: "Winch Data"
    
    property real maxWinchTorque: 100.0
    
    // Consistent sizing for all metrics
    property int metricValueSize: 28
    property int metricLabelSize: 13
    property int metricUnitSize: 12
    
    GridLayout {
        anchors.fill: parent
        columns: 2
        rowSpacing: 12
        columnSpacing: 20
        
        // Cable Length
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Cable Length"
            value: ((winchController.cable_length || 0) / 1000).toFixed(2)
            unit: "m"
            valueColor: "#3498db"
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Cable Speed
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: ((winchController.cable_speed || 0) >= 0 ? "↑" : "↓") + " Cable Speed"
            value: Math.abs(winchController.cable_speed || 0).toFixed(1)
            unit: "m/s"
            valueColor: "#f39c12"
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Voltage
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Voltage"
            value: (winchController.motor_voltage || 0).toFixed(1)
            unit: "V"
            valueColor: "#2ecc71"
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Temperature
        MetricValue {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            label: "Temperature"
            value: (winchController.motor_temperature || 0).toFixed(1)
            unit: "°C"
            valueColor: "#2ecc71"
            valueFontSize: winchCard.metricValueSize
            labelFontSize: winchCard.metricLabelSize
            unitFontSize: winchCard.metricUnitSize
        }
        
        // Torque with progress bar
        ColumnLayout {
            Layout.fillWidth: true
            Layout.columnSpan: 2
            spacing: 6
            
            property real torquePercent: winchCard.maxWinchTorque > 0 ? (winchController.winch_torque || 0) / winchCard.maxWinchTorque * 100 : 0
            
            Text {
                text: "Torque"
                font.pixelSize: winchCard.metricLabelSize
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: (winchController.winch_torque || 0).toFixed(1) + " Nm (" + parent.torquePercent.toFixed(0) + "%)"
                font.pixelSize: winchCard.metricValueSize
                font.family: "Monospace"
                font.bold: true
                color: parent.torquePercent > 80 ? "#f39c12" : "#2ecc71"
            }
            
            ProgressBarIndicator {
                Layout.fillWidth: true
                value: winchController.winch_torque || 0
                maxValue: winchCard.maxWinchTorque
                barColor: parent.torquePercent > 80 ? "#f39c12" : "#2ecc71"
                barHeight: 10
            }
        }
    }
}
