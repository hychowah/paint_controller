import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

/**
 * ControlInfoPanel - Compact Steam Deck optimized display
 * Clean and large text for readability on small screen
 */

Rectangle {
    id: panel
    
    // Public properties
    property string controlMode: "None"
    property string controlValue: ""
    property string title: "CONTROL"
    property string position: "left"
    property int leftMargin: 20
    property int rightMargin: 20
    property int bottomMargin: 20
    
    // UI Design properties
    property color backgroundColor: "#30000000"
    property color borderColor: "#AAAAAA"
    property color titleColor: "#CCCCCC"
    property color modeColor: "#00FF00"
    property color valueColor: "#FFFFFF"
    property int borderWidth: 1
    property int cornerRadius: 6
    
    // Dynamic font sizes based on panel height
    property real titleFontSize: Math.max(8, panel.height * 0.14)
    property real modeFontSize: Math.max(12, panel.height * 0.20)
    property real valueFontSize: Math.max(10, panel.height * 0.16)
    
    radius: cornerRadius
    color: backgroundColor
    border.color: borderColor
    border.width: borderWidth
    
    // Anchor positioning
    anchors.bottom: parent.bottom
    anchors.bottomMargin: bottomMargin
    
    Component.onCompleted: {
        if (position === "left") {
            anchors.left = parent.left
            anchors.leftMargin = leftMargin
        } else {
            anchors.right = parent.right
            anchors.rightMargin = rightMargin
        }
    }
    
    // Subtle gradient
    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#40000000" }
            GradientStop { position: 1.0; color: "#20000000" }
        }
        z: -1
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6
        
        // Title - simple and clean
        Label {
            text: title
            color: panel.titleColor
            font.pixelSize: panel.titleFontSize
            font.bold: true
            font.letterSpacing: 0.2
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        
        // Mode value - large and prominent
        Label {
            text: controlMode
            color: panel.modeColor
            font.pixelSize: panel.modeFontSize
            font.bold: true
            font.family: "Courier New"
            Layout.fillWidth: true
            maximumLineCount: 1
            elide: Text.ElideRight
        }
        
        // Control value - readable size
        Label {
            text: controlValue
            color: panel.valueColor
            font.pixelSize: panel.valueFontSize
            font.family: "Courier New"
            Layout.fillWidth: true
            maximumLineCount: 1
            elide: Text.ElideRight
        }
    }
    
    // Smooth animations
    Behavior on borderColor {
        ColorAnimation { duration: 150 }
    }
}
