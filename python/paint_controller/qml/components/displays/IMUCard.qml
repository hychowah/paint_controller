// IMU Card - Sensor grid with sparklines
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "."
import "../../core"

IndustrialCard {
    id: imuCard
    title: "IMU"
    
    // === CONFIGURABLE SIZES (adjust these for different displays) ===
    property int labelFontSize: CommonStyle.fontBody      // Header and row labels
    property int valueFontSize: CommonStyle.fontHeading   // Data values
    property int labelWidth: 100                          // "Data Type" column width
    property int valueWidth: 60                           // X, Y, Z column widths
    property int rowSpacing: CommonStyle.spacingSm        // Spacing between elements
    
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
                font.family: CommonStyle.fontSans
                font.bold: true
                color: CommonStyle.textSecondary
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "X"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                font.bold: true
                color: CommonStyle.textSecondary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "Y"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                font.bold: true
                color: CommonStyle.textSecondary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: "Z"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                font.bold: true
                color: CommonStyle.textSecondary
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: CommonStyle.cardBorder }
        
        // Angle row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Angle (°)"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                color: CommonStyle.textPrimary
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_pitch || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_roll || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_yaw || 0).toFixed(1)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: CommonStyle.cardBorder }
        
        // Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Accel (g)"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                color: CommonStyle.textPrimary
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_x || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_y || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_acc_z || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
        }
        
        Rectangle { Layout.fillWidth: true; height: 1; color: CommonStyle.cardBorder }
        
        // Angular Acceleration row
        RowLayout {
            Layout.fillWidth: true
            spacing: imuCard.rowSpacing
            
            Text {
                Layout.preferredWidth: imuCard.labelWidth
                text: "Ang Accel"
                font.pixelSize: imuCard.labelFontSize
                font.family: CommonStyle.fontSans
                color: CommonStyle.textPrimary
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_x || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_y || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
            
            Text {
                Layout.preferredWidth: imuCard.valueWidth
                text: (teensyController.all_status.imu_angular_acc_z || 0).toFixed(2)
                font.pixelSize: imuCard.valueFontSize
                font.family: CommonStyle.fontMono
                color: CommonStyle.accentPrimary
                horizontalAlignment: Text.AlignRight
            }
        }
    }
}
