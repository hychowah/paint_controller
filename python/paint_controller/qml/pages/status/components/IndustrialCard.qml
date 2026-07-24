// Industrial-styled card component with dark theme
import QtQuick
import QtQuick.Controls
import "../../../theme"

Rectangle {
    id: root
    
    required property string title
    property bool showTitle: title !== ""
    
    // Industrial dark theme colors
    color: CommonStyle.cardBackground
    radius: CommonStyle.radiusMd
    border.color: CommonStyle.cardBorder
    border.width: CommonStyle.borderWidthThin
    
    // Default content container
    default property alias content: contentArea.data
    
    Column {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingMd
        spacing: CommonStyle.spacingSm
        
        // Optional title
        Text {
            visible: showTitle
            text: root.title
            font.pixelSize: CommonStyle.fontBody
            font.bold: true
            font.family: CommonStyle.fontSans
            color: CommonStyle.textPrimary
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
