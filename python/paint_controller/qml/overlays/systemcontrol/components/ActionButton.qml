import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Rectangle {
    id: actionButton
    required property string buttonText
    required property string buttonDescription
    property string iconColor: CommonStyle.statusSuccess
    property string iconType: "reset" // "reset", "warning", "info", etc.
    
    signal clicked()
    
    function showFeedback() {
        feedbackOverlay.visible = true
        feedbackTimer.restart()
    }
    
    height: CommonStyle.itemHeight
    radius: CommonStyle.radiusMd
    color: actionMouseArea.containsMouse ? CommonStyle.cardBackgroundAlt : CommonStyle.cardBackground
    border.width: 1
    border.color: CommonStyle.borderDefault
    
    // This ensures consistent layout
    Layout.fillWidth: true
    
    // Button hover and pressed states
    states: [
        State {
            name: "hovered"
            PropertyChanges { target: actionButton; color: CommonStyle.cardBackgroundAlt }
        },
        State {
            name: "pressed"
            PropertyChanges { target: actionButton; color: CommonStyle.backgroundL1 }
        }
    ]
    
    // Button transitions
    transitions: [
        Transition {
            from: "*"; to: "*"
            ColorAnimation { duration: CommonStyle.motionFast }
        }
    ]
    
    // Mouse handling
    MouseArea {
        id: actionMouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: actionButton.clicked()
        onEntered: parent.state = "hovered"
        onExited: parent.state = ""
        onPressed: parent.state = "pressed"
        onReleased: {
            if (containsMouse)
                parent.state = "hovered"
            else
                parent.state = ""
        }
    }
    
    // Button contents
    RowLayout {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingMd
        spacing: CommonStyle.spacingMd
        
        // Icon with different types
        Rectangle {
            width: Math.round(32 * CommonStyle.scaleFactor)
            height: Math.round(32 * CommonStyle.scaleFactor)
            radius: width / 2
            color: actionButton.iconColor
            
            // Icon content based on type
            Item {
                anchors.fill: parent
                
                // Reset icon (circular arrow)
                Canvas {
                    anchors.fill: parent
                    visible: iconType === "reset"
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        ctx.beginPath();
                        ctx.arc(16, 16, 8, 0, 1.5 * Math.PI, false);
                        ctx.strokeStyle = CommonStyle.textPrimary;
                        ctx.lineWidth = 2;
                        ctx.stroke();
                        
                        // Arrow head
                        ctx.beginPath();
                        ctx.moveTo(16, 8);
                        ctx.lineTo(12, 12);
                        ctx.lineTo(20, 12);
                        ctx.fillStyle = CommonStyle.textPrimary;
                        ctx.fill();
                    }
                }
                
                // Warning icon
                Text {
                    anchors.centerIn: parent
                    text: "⚠"
                    font.pixelSize: CommonStyle.fontBody
                    color: CommonStyle.textPrimary
                    font.bold: true
                    visible: iconType === "warning"
                }
                
                // Info icon
                Text {
                    anchors.centerIn: parent
                    text: "i"
                    font.pixelSize: CommonStyle.fontBody
                    color: CommonStyle.textPrimary
                    font.bold: true
                    visible: iconType === "info"
                }
                
                // Generic action icon
                Text {
                    anchors.centerIn: parent
                    text: "⚡"
                    font.pixelSize: CommonStyle.fontBody
                    color: CommonStyle.textPrimary
                    font.bold: true
                    visible: iconType !== "reset" && iconType !== "warning" && iconType !== "info"
                }
            }
        }
        
        // Text label
        ColumnLayout {
            Layout.fillWidth: true
            spacing: Math.max(2, CommonStyle.spacingXs)
            
            Text {
                text: actionButton.buttonText
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                font.bold: true
                color: CommonStyle.textPrimary
            }
            
            Text {
                text: actionButton.buttonDescription
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption
                color: CommonStyle.accentMuted
            }
        }
    }
    
    // Visual feedback when button is pressed
    Rectangle {
        id: feedbackOverlay
        anchors.fill: parent
        radius: CommonStyle.radiusMd
        color: "#32" + actionButton.iconColor.substring(1) // Semi-transparent version of icon color
        visible: false
        
        // Success check mark
        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: CommonStyle.spacingLg
            anchors.verticalCenter: parent.verticalCenter
            width: Math.round(24 * CommonStyle.scaleFactor)
            height: Math.round(24 * CommonStyle.scaleFactor)
            radius: 12
            color: actionButton.iconColor
            
            Text {
                anchors.centerIn: parent
                text: "✓"
                color: CommonStyle.textPrimary
                font.pixelSize: CommonStyle.fontBody
                font.bold: true
            }
        }
    }
    
    // Timer to hide feedback
    Timer {
        id: feedbackTimer
        interval: 500
        onTriggered: feedbackOverlay.visible = false
    }
}