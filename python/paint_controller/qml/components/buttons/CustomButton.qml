// CustomButton.qml
import QtQuick
import QtQuick.Controls
import "../../core"

Button {
    id: control
    
    property color backgroundColor: CommonStyle.backgroundColor
    property color textColor: CommonStyle.textPrimary
    property color borderColor: CommonStyle.borderColor
    property int cornerRadius: CommonStyle.smallRadius
    property bool outlined: false
    property bool boldText: false
    
    contentItem: Text {
        text: control.text
        font.pixelSize: CommonStyle.fontSizeNormal
        font.bold: boldText
        color: textColor
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    
    background: Rectangle {
        implicitWidth: 100
        implicitHeight: CommonStyle.buttonHeight
        color: control.down ? Qt.darker(backgroundColor, 1.1) : 
               control.hovered ? Qt.lighter(backgroundColor, 1.1) : backgroundColor
        border.color: outlined ? borderColor : "transparent"
        border.width: outlined ? CommonStyle.borderWidth : 0
        radius: cornerRadius
    }
}