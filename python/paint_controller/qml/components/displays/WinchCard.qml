// Winch Card - Cable and motor data
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    title: "Winch Data"
    
    property real maxWinchTorque: 100.0
    
    GridLayout {
        anchors.fill: parent
        columns: 2
        rowSpacing: 12
        columnSpacing: 20
        
        // Cable Length
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            
            Text {
                text: "📏 Cable Length"
                font.pixelSize: 13
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: ((winchController.cable_length || 0) / 1000).toFixed(2) + " m"
                font.pixelSize: 26
                font.family: "Monospace"
                font.bold: true
                color: "#3498db"
            }
        }
        
        // Cable Speed
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            
            Row {
                spacing: 6
                
                Text {
                    text: (winchController.cable_speed || 0) >= 0 ? "↑" : "↓"
                    font.pixelSize: 18
                    color: "#f39c12"
                }
                
                Text {
                    text: "Cable Speed"
                    font.pixelSize: 13
                    font.family: "Roboto"
                    color: "#AAAAAA"
                }
            }
            
            Text {
                text: Math.abs(winchController.cable_speed || 0).toFixed(1) + " m/s"
                font.pixelSize: 26
                font.family: "Monospace"
                font.bold: true
                color: "#f39c12"
            }
        }
        
        // Voltage
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: "Voltage"
                font.pixelSize: 12
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: (winchController.motor_voltage || 0).toFixed(1) + " V"
                font.pixelSize: 16
                font.family: "Monospace"
                color: "#2ecc71"
            }
        }
        
        // Temperature
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: "Temperature"
                font.pixelSize: 12
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                text: (winchController.motor_temperature || 0).toFixed(1) + " °C"
                font.pixelSize: 16
                font.family: "Monospace"
                color: "#2ecc71"
            }
        }
        
        // Torque
        ColumnLayout {
            Layout.fillWidth: true
            Layout.columnSpan: 2
            spacing: 2
            
            Text {
                text: "Torque"
                font.pixelSize: 12
                font.family: "Roboto"
                color: "#AAAAAA"
            }
            
            Text {
                property real torquePercent: maxWinchTorque > 0 ? (winchController.winch_torque || 0) / maxWinchTorque * 100 : 0
                text: (winchController.winch_torque || 0).toFixed(1) + " Nm (" + torquePercent.toFixed(0) + "%)"
                font.pixelSize: 16
                font.family: "Monospace"
                color: torquePercent > 80 ? "#f39c12" : "#2ecc71"
            }
        }
    }
}
