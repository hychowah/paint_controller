import QtQuick
import QtQuick.Controls
import "../../core"

/**
 * Reusable battery display component
 * Shows a battery icon with fill level and percentage text
 */
Item {
    id: batteryDisplay
    width: 100
    height: 40
    
    required property real batteryPercent
    property real borderWidth: 1
    property real iconWidth: 28
    property real iconHeight: 14
    property color borderColor: CommonStyle.textSecondary
    property color dividerColor: CommonStyle.textDisabled
    readonly property real clampedBatteryPercent: Math.max(0, Math.min(batteryPercent, 100))
    
    // Functions
    function getBatteryColor(percent) {
        if (percent > 50) return CommonStyle.statusSuccess
        if (percent > 25) return CommonStyle.statusWarning
        return CommonStyle.statusError
    }
    
    Row {
        anchors.centerIn: parent
        spacing: 8
        
        // Battery icon background
        Rectangle {
            width: batteryDisplay.iconWidth
            height: batteryDisplay.iconHeight
            radius: 2
            color: "transparent"
            border.color: batteryDisplay.borderColor
            border.width: batteryDisplay.borderWidth
            
            anchors.verticalCenter: parent.verticalCenter
            
            // Battery fill
            Rectangle {
                width: parent.width * (batteryDisplay.clampedBatteryPercent / 100)
                height: parent.height - 2
                color: batteryDisplay.getBatteryColor(batteryDisplay.clampedBatteryPercent)
                radius: 1
                anchors.left: parent.left
                anchors.leftMargin: 1
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        // Battery percentage text
        Text {
            text: Math.round(batteryDisplay.clampedBatteryPercent) + "%"
            color: batteryDisplay.getBatteryColor(batteryDisplay.clampedBatteryPercent)
            font.pixelSize: CommonStyle.fontLabel
            font.bold: true
            font.family: CommonStyle.fontMono
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
