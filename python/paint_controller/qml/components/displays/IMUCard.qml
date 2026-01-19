// IMU Card - Sensor grid with sparklines
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    title: "IMU"
    
    property var imuAccZHistory: []
    property var imuAngularAccZHistory: []
    property var imuRollHistory: []
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 6
        
        // Header row
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                Layout.preferredWidth: 90
                text: "Data Type"
                font.pixelSize: 11
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
            }
            
            Text {
                Layout.preferredWidth: 55
                text: "X"
                font.pixelSize: 11
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: "Y"
                font.pixelSize: 11
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: "Z"
                font.pixelSize: 11
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 50
                text: "Trend"
                font.pixelSize: 11
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignHCenter
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Angle row
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                Layout.preferredWidth: 90
                text: "Angle (°)"
                font.pixelSize: 11
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_pitch || 0).toFixed(1)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_roll || 0).toFixed(1)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_yaw || 0).toFixed(1)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Sparkline {
                Layout.preferredWidth: 50
                Layout.preferredHeight: 24
                dataPoints: imuRollHistory
                lineColor: "#3498db"
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                Layout.preferredWidth: 90
                text: "Accel (g)"
                font.pixelSize: 11
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_acc_x || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#2ecc71"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_acc_y || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#2ecc71"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_acc_z || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#2ecc71"
                horizontalAlignment: Text.AlignRight
            }
            
            Sparkline {
                Layout.preferredWidth: 50
                Layout.preferredHeight: 24
                dataPoints: imuAccZHistory
                lineColor: "#2ecc71"
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Angular Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            
            Text {
                Layout.preferredWidth: 90
                text: "Ang Accel"
                font.pixelSize: 11
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_angular_acc_x || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#f39c12"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_angular_acc_y || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#f39c12"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: 55
                text: (teensyController.all_status.imu_angular_acc_z || 0).toFixed(2)
                font.pixelSize: 12
                font.family: "Monospace"
                color: "#f39c12"
                horizontalAlignment: Text.AlignRight
            }
            
            Sparkline {
                Layout.preferredWidth: 50
                Layout.preferredHeight: 24
                dataPoints: imuAngularAccZHistory
                lineColor: "#f39c12"
            }
        }
    }
}
