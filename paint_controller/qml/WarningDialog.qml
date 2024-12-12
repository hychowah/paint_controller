import QtQuick 2.15
import QtQuick.Controls 2.15

Dialog {
    id: warningDialog
    title: "Warning"
    modal: true
    padding: 20
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property int dialogWidth: 300
    property int dialogHeight: 200
    property int headerFontSize: 16
    property int contentFontSize: 14
    property int warningIconSize: 24
    property string warningText: "WARNING TEXT"

    width: dialogWidth
    height: dialogHeight
    
    background: Rectangle {
        color: "#ffffff"
        radius: 10
        border.color: "#e0e0e0"
        border.width: 1
    }
    
    header: Rectangle {
        color: "transparent"
        height: 40
        
        Label {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: 20
            text: warningDialog.title
            font.bold: true
            font.pixelSize: headerFontSize
            color: "#2c3e50"
        }
    }
    
    contentItem: Column {
        spacing: 20
        padding: 20
        
        Row {
            spacing: 10
            
            Text {
                text: "⚠️"
                font.pixelSize: 24
                anchors.verticalCenter: parent.verticalCenter
            }
            
            Label {
                text: warningDialog.warningText
                font.pixelSize: contentFontSize
                color: "#2c3e50"
                wrapMode: Text.WordWrap
                width: warningDialog.width - 100
            }
        }
    }
    
    footer: Rectangle {
        color: "transparent"
        height: 60
        
        Button {
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.verticalCenter: parent.verticalCenter
            text: "OK"
            width: 100
            height: 36
            
            background: Rectangle {
                color: parent.down ? "#2980b9" : "#3498db"
                radius: 5
                
                Behavior on color {
                    ColorAnimation { duration: 100 }
                }
            }
            
            contentItem: Text {
                text: parent.text
                color: "white"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: contentFontSize
                font.bold: true
            }
            
            onClicked: warningDialog.close()
        }
    }
}