// Horizontal progress bar for showing load/current indicators
import QtQuick
import "../../../theme"

Item {
    id: root
    
    required property real value
    required property real maxValue
    property color barColor: CommonStyle.statusSuccess
    property color backgroundColor: CommonStyle.inputBackground
    property int barHeight: CommonStyle.spacingMd
    readonly property real normalizedValue: maxValue > 0 ? Math.max(0, Math.min(value / maxValue, 1)) : 0
    
    height: barHeight
    
    // Background
    Rectangle {
        anchors.fill: parent
        color: backgroundColor
        radius: barHeight / 2
    }
    
    // Progress bar
    Rectangle {
        width: parent.width * root.normalizedValue
        height: parent.height
        color: barColor
        radius: barHeight / 2
        
        Behavior on width {
            NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
        }
    }
}
