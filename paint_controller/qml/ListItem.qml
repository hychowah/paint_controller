// ListItem.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Rectangle {
    id: root
    width: parent ? parent.width : 100
    height: CommonStyle.itemHeight
    color: selected ? selectedColor : defaultColor
    border.color: CommonStyle.borderColor
    border.width: CommonStyle.borderWidth
    radius: CommonStyle.smallRadius
    
    property string text: ""
    property bool selected: false
    property color defaultColor: CommonStyle.secondaryColor
    property color selectedColor: CommonStyle.successColor
    property alias mouseArea: mouseArea
    signal clicked()
    
    Text {
        anchors.fill: parent
        anchors.margins: CommonStyle.defaultMargin
        text: root.text
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
        font.pixelSize: CommonStyle.fontSizeNormal
        font.bold: true
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: root.clicked()
    }
}