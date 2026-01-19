// Industrial-styled card component with dark theme
import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    
    // Properties
    property string title: ""
    property bool showTitle: title !== ""
    
    // Industrial dark theme colors
    color: "#29303b"
    radius: 8
    
    // Default content container
    default property alias content: contentArea.data
    
    Column {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        
        // Optional title
        Text {
            visible: showTitle
            text: root.title
            font.pixelSize: 14
            font.bold: true
            font.family: "Roboto"
            color: "#FFFFFF"
            width: parent.width
        }
        
        // Content area
        Item {
            id: contentArea
            width: parent.width
            height: parent.height - (showTitle ? 22 : 0)
        }
    }
}
