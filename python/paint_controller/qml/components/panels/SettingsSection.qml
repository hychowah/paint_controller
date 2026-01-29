// SettingsSection.qml - Collapsible section component for settings
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: settingsSection
    
    // Properties
    property string title: "Section Title"
    property string description: ""
    property string sectionId: ""  // Unique ID for state persistence
    property bool expanded: true
    property alias contentItem: contentLoader.sourceComponent
    
    // Calculate content height from loaded item
    property real contentHeight: contentLoader.item ? contentLoader.item.implicitHeight + 30 : 100
    
    // Load persisted state on component completion
    Component.onCompleted: {
        if (sectionId !== "" && typeof settingsManager !== "undefined" && settingsManager) {
            expanded = settingsManager.getSectionExpanded(sectionId)
        }
    }
    
    // Save state when expanded changes
    onExpandedChanged: {
        if (sectionId !== "" && typeof settingsManager !== "undefined" && settingsManager) {
            settingsManager.setSectionExpanded(sectionId, expanded)
        }
    }
    
    // Sizing
    width: parent ? parent.width : 400
    height: headerContainer.height + (expanded ? contentHeight : 0)
    
    // Styling
    color: "#1E2433"
    border.color: expanded ? "#3A5A8C" : "#333333"
    border.width: 1
    radius: 8
    
    // Smooth height animation
    Behavior on height {
        NumberAnimation { 
            duration: 200
            easing.type: Easing.InOutQuad 
        }
    }
    
    Behavior on border.color {
        ColorAnimation { duration: 150 }
    }
    
    // Header container
    Rectangle {
        id: headerContainer
        width: parent.width
        height: 52  // Slightly taller for better Steam Deck touch targets
        color: "transparent"
        radius: parent.radius
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 15
            anchors.rightMargin: 15
            spacing: 10
            
            // Chevron icon
            Text {
                id: chevron
                text: expanded ? "▼" : "▶"
                color: "#AAAAAA"
                font.pixelSize: 14  // Larger for Steam Deck
            }
            
            // Title and description
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                
                Text {
                    text: settingsSection.title
                    color: "#FFFFFF"
                    font.pixelSize: 16  // Larger for Steam Deck
                    font.bold: true
                }
                
                Text {
                    visible: settingsSection.description !== ""
                    text: settingsSection.description
                    color: "#888888"
                    font.pixelSize: 13  // Larger for Steam Deck readability
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                }
            }
        }
        
        // Click to toggle
        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: settingsSection.expanded = !settingsSection.expanded
        }
        
        // Bottom separator when expanded
        Rectangle {
            visible: expanded
            anchors.bottom: parent.bottom
            width: parent.width - 20
            height: 1
            color: "#333333"
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
    
    // Content container
    Item {
        id: contentContainer
        anchors.top: headerContainer.bottom
        width: parent.width
        height: expanded ? contentHeight : 0
        clip: true
        
        // Keep content always loaded, just hide with opacity
        opacity: expanded ? 1.0 : 0.0
        Behavior on opacity {
            NumberAnimation { duration: 150 }
        }
        
        Loader {
            id: contentLoader
            // Don't use anchors.fill - let it size naturally
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 15
            anchors.topMargin: 10
            // Keep active always so content is preserved
            active: true
        }
    }
}
