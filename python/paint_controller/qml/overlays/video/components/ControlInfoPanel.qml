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
    property string controlValue: "12.7 km/h" // Example value to match image style
    property string title: "H.S" // Example title to match image style
    property string position: "left"
    property int leftMargin: 20
    property int rightMargin: 20
    property int bottomMargin: 20

    // UI Design properties
    property color backgroundColor: "#AA000000" // Semi-transparent dark background for readability
    property color borderColor: "#AAAAAA" // Border is removed, but keeping property for flexibility
    property color titleColor: "#CCCCCC" // Lighter for secondary text
    property color modeColor: "#00FF00" // Green for mode (as in image's "Descending")
    property color valueColor: "#FFFFFF" // White for emphasized value
    property int borderWidth: 0 // <--- Removed border by setting width to 0
    property int cornerRadius: 6

    // Dynamic font sizes based on panel height - adjusted for new emphasis
    property real titleFontSize: Math.max(8, panel.height * 0.12) // Slightly smaller
    property real modeFontSize: Math.max(12, panel.height * 0.16) // Slightly smaller
    property real valueFontSize: Math.max(10, panel.height * 0.25) // <--- Larger for emphasis

    radius: cornerRadius
    color: backgroundColor
    border.color: borderColor
    border.width: borderWidth // <--- Will be 0
    antialiasing: true // For smoother text

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

    // Removed the subtle gradient as it's not needed with transparent background
    // Rectangle {
    //     anchors.fill: parent
    //     radius: parent.radius
    //     gradient: Gradient {
    //         GradientStop { position: 0.0; color: "#40000000" }
    //         GradientStop { position: 1.0; color: "#20000000" }
    //     }
    //     z: -1
    // }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 0 // <--- Reduced spacing for a more compact look, similar to image
        
        // Title - simple and clean, less dominant
        Label {
            text: title
            color: panel.titleColor
            font.pixelSize: panel.titleFontSize
            font.bold: false // <--- Not bold for less emphasis
            font.letterSpacing: 0.2
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        // Mode value - smaller focus on text, but still distinct if needed
        Label {
            text: controlMode
            color: panel.modeColor // Keep green for mode
            font.pixelSize: panel.modeFontSize
            font.bold: true // Keep bold for mode readability
            font.family: "Courier New"
            Layout.fillWidth: true
            maximumLineCount: 1
            elide: Text.ElideRight
        }

        // Control value - larger and more prominent for emphasis
        Label {
            text: controlValue
            color: panel.valueColor
            font.pixelSize: panel.valueFontSize // <--- Emphasized font size
            font.bold: true // <--- Make bold for emphasis
            font.family: "Courier New" // Using a monospaced font as in the image
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