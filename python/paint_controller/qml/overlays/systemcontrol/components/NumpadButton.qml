import QtQuick
import QtQuick.Controls
import "../../../theme"

/**
 * Numpad key chrome. Owns press-linger feedback (KNOWLEDGE: touch feedback
 * should linger after release). Callers only set colors + handle clicked().
 */
Rectangle {
    id: button

    required property string text
    property bool isSpecial: false
    property bool isAccent: false
    property bool visuallyPressed: false
    property color normalColor: CommonStyle.cardBackground
    property color specialColor: CommonStyle.backgroundL1
    property color accentColor: CommonStyle.buttonPrimary
    property color pressedColor: CommonStyle.buttonPressed
    property color borderColorValue: CommonStyle.borderFocused
    property color textColorValue: CommonStyle.textPrimary
    property int fontSize: CommonStyle.fontHeading
    property int radiusValue: CommonStyle.radiusSm
    signal clicked()

    radius: radiusValue
    color: {
        if (visuallyPressed)
            return pressedColor
        if (isAccent)
            return accentColor
        if (isSpecial)
            return specialColor
        return normalColor
    }
    border.color: visuallyPressed ? CommonStyle.borderFocused : borderColorValue
    border.width: visuallyPressed ? CommonStyle.borderWidthThick : CommonStyle.borderWidthThin

    Behavior on color {
        ColorAnimation { duration: 60 }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onPressed: button.visuallyPressed = true
        onCanceled: {
            button.visuallyPressed = false
            pressLingerTimer.stop()
        }
        onClicked: {
            button.clicked()
            pressLingerTimer.restart()
        }
    }

    Timer {
        id: pressLingerTimer
        interval: 150
        repeat: false
        onTriggered: button.visuallyPressed = false
    }

    Text {
        anchors.centerIn: parent
        text: button.text
        color: button.textColorValue
        font.pixelSize: button.fontSize
        font.bold: button.isSpecial || button.isAccent || button.visuallyPressed
    }
}
