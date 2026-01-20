// IMU Card - Sensor grid with sparklines
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

IndustrialCard {
    id: imuCard
    title: "IMU"
    
    // === CONFIGURABLE SIZES (adjust these for different displays) ===
    property int labelFontSize: 16      // Header and row labels
    property int valueFontSize: 18      // Data values
    property int labelWidth: 100        // "Data Type" column width
    property int valueWidth: 60         // X, Y, Z column widths
    property int rowSpacing: 8          // Spacing between elements
    
    ColumnLayout {
        anchors.fill: parent
        spacing: imuCard.rowSpacing
        
        // Header row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Data Type"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "X"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "Y"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "Z"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                font.bold: true
                color: "#AAAAAA"
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Angle row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Angle (°)"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_pitch || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_roll || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_yaw || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Accel (g)"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_x || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_y || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_z || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: "#3a4150" }
        
        // Angular Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Ang Accel"
                font.pixelSize: imuCard.labelFontSize
                font.family: "Roboto"
                color: "#FFFFFF"
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_x || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_y || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_z || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: "Monospace"
                color: "#3498db"
                horizontalAlignment: Text.AlignRight
            }
        }
    }
}
