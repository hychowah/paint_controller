// Card.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "."

Rectangle {
    id: root
    color: CommonStyle.backgroundColor
    radius: CommonStyle.radius
    border.color: CommonStyle.borderColor
    border.width: CommonStyle.borderWidth
    
    property alias title: titleText.text
    property bool showTitle: title !== ""
    property int contentMargins: CommonStyle.defaultMargin
    default property alias content: contentItem.data
    
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        
        // Optional title section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: showTitle ? 50 : 0
            visible: showTitle
            color: "transparent"
            
            Text {
                id: titleText
                anchors.fill: parent
                anchors.margins: CommonStyle.defaultMargin
                font.pixelSize: CommonStyle.fontSizeLarge
                font.bold: true
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: CommonStyle.borderColor
                visible: showTitle
            }
        }
        
        // Content area
        Item {
            id: contentItem
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: contentMargins
        }
    }
}