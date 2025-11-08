import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: button
    color: mouseArea.pressed ? parent.parent.specialButtonColor : (isSpecial ? parent.parent.specialButtonColor : parent.parent.buttonColor)
    border.color: parent.parent.buttonBorderColor
    border.width: 1
    radius: parent.parent.buttonRadius
    
    property string text: ""
    property bool isSpecial: false
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
        color: parent.parent.buttonTextColor
        font.pixelSize: parent.parent.buttonFontSize
        font.bold: button.isSpecial
    }
}
