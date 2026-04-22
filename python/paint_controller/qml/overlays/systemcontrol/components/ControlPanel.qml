import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Rectangle {
    id: controlPanel
    required property string controlName
    required property string controlStatus
    property bool enabledState: false
    required property string iconText
    property bool selfContained: false
    
    signal clicked()
    
    height: CommonStyle.itemHeight
    radius: CommonStyle.radiusMd
    color: enabledState ? CommonStyle.cardBackground : CommonStyle.backgroundL1
    border.color: enabledState ? CommonStyle.borderFocused : CommonStyle.inputBorder
    border.width: 1
    
    // This ensures consistent layout across all control panels
    Layout.fillWidth: true
    
    // Subtle transition animations
    Behavior on color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }
    
    Behavior on border.color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }
    
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (controlPanel.selfContained) {
                controlPanel.enabledState = !controlPanel.enabledState
                controlPanel.controlStatus = controlPanel.enabledState ? "Enabled" : "Disabled"
            }
            controlPanel.clicked()
        }
        // Hover effect
        onEntered: {
            parent.color = enabledState ? CommonStyle.cardBackgroundAlt : CommonStyle.backgroundL2
        }
        
        onExited: {
            parent.color = enabledState ? CommonStyle.cardBackground : CommonStyle.backgroundL1
        }
    }
    
    // Use Row instead of RowLayout for more consistent sizing
    Row {
        anchors {
            fill: parent
            margins: CommonStyle.spacingMd
            // Add right margin to create space between toggle and right edge
            rightMargin: CommonStyle.spacingLg
        }
        spacing: CommonStyle.spacingMd
        
        // Icon
        Rectangle {
            width: CommonStyle.controlHeightMd
            height: CommonStyle.controlHeightMd
            radius: width / 2
            color: enabledState ? CommonStyle.borderFocused : CommonStyle.textDisabled
            anchors.verticalCenter: parent.verticalCenter
            
            Text {
                anchors.centerIn: parent
                text: controlPanel.iconText
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                color: CommonStyle.textPrimary
                font.bold: true
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }
        
        // Text with status - using a Rectangle with Column inside to fill available space
        Rectangle {
            width: parent.width - 36 - 10 - 52 - 5 // parent width minus icon width, spacing, switch width, and extra margin
            height: parent.height - 20
            color: "transparent" // Make this visible for debugging: "#550000"
            anchors.verticalCenter: parent.verticalCenter
            
            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: Math.max(2, CommonStyle.spacingXs)
                
                Text {
                    text: controlPanel.controlName
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                    color: CommonStyle.textPrimary
                }
                
                Text {
                    text: controlPanel.controlStatus
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
                    color: enabledState ? CommonStyle.accentMuted : CommonStyle.textDisabled
                    
                    // Color transition
                    Behavior on color {
                        ColorAnimation { duration: CommonStyle.motionStandard }
                    }
                }
            }
        }
        
        // Toggle switch - simple Rectangle with fixed width
        Rectangle {
            width: 52
            height: 28
            radius: 14
            color: enabledState ? CommonStyle.borderFocused : CommonStyle.textDisabled
            anchors.verticalCenter: parent.verticalCenter
            
            Rectangle {
                width: 22
                height: 22
                radius: 11
                color: CommonStyle.textPrimary
                anchors.verticalCenter: parent.verticalCenter
                x: enabledState ? parent.width - width - 3 : 3
                
                Behavior on x {
                    NumberAnimation { 
                        duration: CommonStyle.motionStandard
                        easing.type: Easing.OutCubic
                    }
                }
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }
    }
}