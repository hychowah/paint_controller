import QtQuick
import QtQuick.Controls
import "../../core"

Rectangle {
    id: button
    color: mouseArea.pressed ? pressedColor : (isSpecial ? specialColor : normalColor)
    border.color: borderColorValue
    border.width: 1
    radius: radiusValue
    
    property string text: ""
    property bool isSpecial: false
    property color normalColor: CommonStyle.cardBackground
    property color specialColor: CommonStyle.backgroundL1
    property color pressedColor: CommonStyle.buttonPressed
    property color borderColorValue: CommonStyle.borderFocused
    property color textColorValue: CommonStyle.textPrimary
    property int fontSize: CommonStyle.fontHeading
    property int radiusValue: CommonStyle.radiusSm
    signal clicked()
    
    Behavior on color {
        ColorAnimation { duration: 100 }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: button.clicked()
    }

    Text {
        anchors.centerIn: parent
        text: button.text
        color: button.textColorValue
        font.pixelSize: button.fontSize
        font.bold: button.isSpecial
    }
}
