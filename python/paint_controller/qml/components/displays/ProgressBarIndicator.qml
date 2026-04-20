// Horizontal progress bar for showing load/current indicators
import QtQuick
import "../../core"

Item {
    id: root
    
    // Properties
    property real value: 0.0
    property real maxValue: 100.0
    property color barColor: CommonStyle.statusSuccess
    property color backgroundColor: CommonStyle.inputBackground
    property int barHeight: CommonStyle.spacingMd
    
    height: barHeight
    
    // Background
    Rectangle {
        anchors.fill: parent
        color: backgroundColor
        radius: barHeight / 2
    }
    
    // Progress bar
    Rectangle {
        width: Math.max(0, Math.min(parent.width * (value / maxValue), parent.width))
        height: parent.height
        color: barColor
        radius: barHeight / 2
        
        Behavior on width {
            NumberAnimation { duration: CommonStyle.motionFast; easing.type: Easing.OutQuad }
        }
    }
}
