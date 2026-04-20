import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    property string title: ""
    property string subtitle: ""
    property string icon: ""
    property bool showToggle: false
    property bool toggleValue: false
    property bool showArrow: true
    
    signal clicked()
    signal toggled(bool value)
    
    width: parent.width
    height: subtitle !== "" ? 72 : 56
    color: mouseArea.pressed ? "#E0E0E0" : "white"
    
    Rectangle {
        width: parent.width - 72
        height: 1
        color: "#E0E0E0"
        anchors.bottom: parent.bottom
        anchors.right: parent.right
    }
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 16
        
        Text {
            text: icon
            font.pixelSize: 24
            color: "#757575"
            Layout.preferredWidth: 32
        }
        
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: title
                font.pixelSize: 16
                color: "#212121"
                Layout.fillWidth: true
            }
            
            Text {
                visible: subtitle !== ""
                text: subtitle
                font.pixelSize: 14
                color: "#757575"
                Layout.fillWidth: true
            }
        }
        
        Switch {
            visible: showToggle
            checked: toggleValue
            Layout.preferredWidth: 52
            
            onToggled: parent.parent.parent.toggled(checked)
            
            indicator: Rectangle {
                implicitWidth: 52
                implicitHeight: 26
                radius: 13
                color: parent.checked ? "#4CAF50" : "#BDBDBD"
                
                Rectangle {
                    x: parent.parent.checked ? parent.width - width - 2 : 2
                    y: 2
                    width: 22
                    height: 22
                    radius: 11
                    color: "white"
                    
                    Behavior on x {
                        NumberAnimation { duration: 150 }
                    }
                }
            }
        }
        
        Text {
            visible: showArrow && !showToggle
            text: "❯"
            font.pixelSize: 14
            color: "#9E9E9E"
            Layout.preferredWidth: 16
        }
    }
    
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        enabled: !showToggle
        onClicked: parent.clicked()
    }
}