import QtQuick 2.15
import QtQuick.Controls 2.15

/**
 * Reusable battery display component
 * Shows a battery icon with fill level and percentage text
 */
Item {
    id: batteryDisplay
    width: 100
    height: 40
    
    // Properties
    property real batteryPercent: 0
    property real borderWidth: 1
    property real iconWidth: 28
    property real iconHeight: 14
    property color borderColor: "#AAAAAA"
    property color dividerColor: "#666666"
    
    // Functions
    function getBatteryColor(percent) {
        if (percent > 50) return "#00FF00"      // Green
        if (percent > 25) return "#FFAA00"      // Orange
        return "#FF3333"                         // Red
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
                width: parent.width * (batteryDisplay.batteryPercent / 100)
                height: parent.height - 2
                color: batteryDisplay.getBatteryColor(batteryDisplay.batteryPercent)
                radius: 1
                anchors.left: parent.left
                anchors.leftMargin: 1
                anchors.verticalCenter: parent.verticalCenter
            }
        }
        
        // Battery percentage text
        Text {
            text: Math.round(batteryDisplay.batteryPercent) + "%"
            color: batteryDisplay.getBatteryColor(batteryDisplay.batteryPercent)
            font.pixelSize: 11
            font.bold: true
            font.family: "Courier New"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
