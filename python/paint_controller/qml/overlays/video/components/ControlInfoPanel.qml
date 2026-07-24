import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"

/**
 * ControlInfoPanel - Compact Steam Deck optimized display
 * Clean and large text for readability on small screen
 */

Rectangle {
    id: panel

    // Public properties
    required property string controlMode
    required property string controlValue
    required property string title
    required property string position
    property string controlModeDisplay: controlMode
    property int leftMargin: 20
    property int rightMargin: 20
    property int bottomMargin: 20

    signal panelClicked(string position)

    // UI Design properties
    property color backgroundColor: CommonStyle.videoSurface
    property color borderColor: CommonStyle.borderDefault
    property color titleColor: CommonStyle.textSecondary
    property color modeColor: CommonStyle.videoBorderEnabled
    property color valueColor: CommonStyle.textPrimary
    property int borderWidth: CommonStyle.borderWidthThin
    property int cornerRadius: CommonStyle.radiusSm
    property bool visuallyPressed: false

    // Dynamic font sizes based on panel height - adjusted for new emphasis
    readonly property real titleFontSize: Math.max(8, panel.height * 0.12) // Slightly smaller
    readonly property real modeFontSize: Math.max(12, panel.height * 0.16) // Slightly smaller
    readonly property real valueFontSize: Math.max(10, panel.height * 0.25) // <--- Larger for emphasis

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
            font.family: CommonStyle.fontSans
            font.letterSpacing: 0.2
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        // Mode value - smaller focus on text, but still distinct if needed
        Label {
            text: panel.controlModeDisplay
            color: panel.modeColor // Keep green for mode
            font.pixelSize: panel.modeFontSize
            font.bold: true // Keep bold for mode readability
            font.family: CommonStyle.fontMono
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
            font.family: CommonStyle.fontMono
            Layout.fillWidth: true
            maximumLineCount: 1
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: panelMouse
        anchors.fill: parent
        onPressed: panel.visuallyPressed = true
        onClicked: {
            panel.panelClicked(panel.position)
            releaseTimer.start()
        }
        onCanceled: panel.visuallyPressed = false

        Timer {
            id: releaseTimer
            interval: 150
            repeat: false
            onTriggered: panel.visuallyPressed = false
        }
    }

    // Pressed feedback: high-contrast overlay so the tap is visible even over
    // a busy video background. The highlight lingers briefly after release.
    Rectangle {
        visible: panel.visuallyPressed
        anchors.fill: parent
        color: CommonStyle.accentPrimary
        opacity: 0.45
        border.color: CommonStyle.borderFocused
        border.width: 3
        radius: panel.cornerRadius

        Behavior on opacity {
            NumberAnimation { duration: CommonStyle.motionFast }
        }
    }

    // Smooth animations
    Behavior on borderColor {
        ColorAnimation { duration: CommonStyle.motionFast }
    }
}