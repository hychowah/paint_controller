// settings/SettingsCategory.qml
import QtQuick

Rectangle {
    property string title: ""
    
    width: parent.width
    height: 48
    color: "#F5F5F5"
    
    Text {
        text: title.toUpperCase()
        anchors.left: parent.left
        anchors.leftMargin: 72
        anchors.verticalCenter: parent.verticalCenter
        font.pixelSize: 18
        font.weight: Font.Medium
        color: "#3F51B5"
    }
}