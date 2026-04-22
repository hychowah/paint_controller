// SettingsSection.qml - Collapsible section component for settings
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Rectangle {
    id: settingsSection
    
    // Properties
    required property string title
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
    width: parent ? parent.width : Math.round(400 * CommonStyle.scaleFactor)
    height: headerContainer.height + (expanded ? contentHeight : 0)
    
    // Styling
    color: CommonStyle.cardBackground
    border.color: expanded ? CommonStyle.borderFocused : CommonStyle.inputBorder
    border.width: 1
    radius: CommonStyle.radiusMd
    
    // Smooth height animation
    Behavior on height {
        NumberAnimation { 
            duration: CommonStyle.motionStandard
            easing.type: Easing.InOutQuad 
        }
    }
    
    Behavior on border.color {
        ColorAnimation { duration: CommonStyle.motionFast }
    }
    
    // Header container
    Rectangle {
        id: headerContainer
        width: parent.width
        height: Math.round(52 * CommonStyle.scaleFactor)
        color: "transparent"
        radius: parent.radius
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: CommonStyle.spacingLg
            anchors.rightMargin: CommonStyle.spacingLg
            spacing: CommonStyle.spacingMd
            
            // Chevron icon
            Text {
                id: chevron
                text: expanded ? "▼" : "▶"
                color: CommonStyle.textSecondary
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption
            }
            
            // Title and description
            ColumnLayout {
                Layout.fillWidth: true
                spacing: Math.max(2, CommonStyle.spacingXs)
                
                Text {
                    text: settingsSection.title
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                }
                
                Text {
                    visible: settingsSection.description !== ""
                    text: settingsSection.description
                    color: CommonStyle.textDisabled
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
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
            color: CommonStyle.inputBorder
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
            NumberAnimation { duration: CommonStyle.motionFast }
        }
        
        Loader {
            id: contentLoader
            // Don't use anchors.fill - let it size naturally
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: CommonStyle.spacingLg
            anchors.topMargin: CommonStyle.spacingMd
            // Keep active always so content is preserved
            active: true
        }
    }
}
