import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    property string title: "Settings"
    property bool showBack: false
    
    signal backClicked()
    
    Layout.fillWidth: true
    Layout.preferredHeight: 56
    color: "#3F51B5"
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        
        Text {
            visible: showBack
            text: "⬅"
            font.pixelSize: 24
            color: "white"
            Layout.preferredWidth: 32
            
            MouseArea {
                anchors.fill: parent
                onClicked: parent.parent.parent.backClicked()
            }
        }
        
        Text {
            text: title
            font.pixelSize: 20
            font.weight: Font.Medium
            color: "white"
            Layout.fillWidth: true
        }
    }
}
