// Horizontal progress bar for showing load/current indicators
import QtQuick 2.15

Item {
    id: root
    
    // Properties
    property real value: 0.0
    property real maxValue: 100.0
    property color barColor: "#2ecc71"
    property color backgroundColor: "#1e222b"
    property int barHeight: 12
    
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
            NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
        }
    }
}
