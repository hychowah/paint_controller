import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: actionButton
    property string buttonText: "Action"
    property string buttonDescription: "Perform action"
    property string iconColor: "#4CAF50"
    property string iconType: "reset" // "reset", "warning", "info", etc.
    
    signal clicked()
    
    function showFeedback() {
        feedbackOverlay.visible = true
        feedbackTimer.restart()
    }
    
    height: 60
    radius: 10
    color: actionMouseArea.containsMouse ? "#2A3040" : "#252A36"
    border.width: 1
    border.color: "#3A5A8C"
    
    // This ensures consistent layout
    Layout.fillWidth: true
    
    // Button hover and pressed states
    states: [
        State {
            name: "hovered"
            PropertyChanges { target: actionButton; color: "#2A3040" }
        },
        State {
            name: "pressed"
            PropertyChanges { target: actionButton; color: "#1E2530" }
        }
    ]
    
    // Button transitions
    transitions: [
        Transition {
            from: "*"; to: "*"
            ColorAnimation { duration: 150 }
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
        anchors.margins: 12
        spacing: 12
        
        // Icon with different types
        Rectangle {
            width: 32
            height: 32
            radius: 16
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
                        ctx.strokeStyle = "white";
                        ctx.lineWidth = 2;
                        ctx.stroke();
                        
                        // Arrow head
                        ctx.beginPath();
                        ctx.moveTo(16, 8);
                        ctx.lineTo(12, 12);
                        ctx.lineTo(20, 12);
                        ctx.fillStyle = "white";
                        ctx.fill();
                    }
                }
                
                // Warning icon
                Text {
                    anchors.centerIn: parent
                    text: "⚠"
                    font.pixelSize: 16
                    color: "white"
                    font.bold: true
                    visible: iconType === "warning"
                }
                
                // Info icon
                Text {
                    anchors.centerIn: parent
                    text: "i"
                    font.pixelSize: 16
                    color: "white"
                    font.bold: true
                    visible: iconType === "info"
                }
                
                // Generic action icon
                Text {
                    anchors.centerIn: parent
                    text: "⚡"
                    font.pixelSize: 16
                    color: "white"
                    font.bold: true
                    visible: iconType !== "reset" && iconType !== "warning" && iconType !== "info"
                }
            }
        }
        
        // Text label
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            
            Text {
                text: actionButton.buttonText
                font.pixelSize: 16
                font.bold: true
                color: "#FFFFFF"
            }
            
            Text {
                text: actionButton.buttonDescription
                font.pixelSize: 13
                color: "#90CAF9"
            }
        }
    }
    
    // Visual feedback when button is pressed
    Rectangle {
        id: feedbackOverlay
        anchors.fill: parent
        radius: 10
        color: "#32" + actionButton.iconColor.substring(1) // Semi-transparent version of icon color
        visible: false
        
        // Success check mark
        Rectangle {
            anchors.right: parent.right
            anchors.rightMargin: 15
            anchors.verticalCenter: parent.verticalCenter
            width: 24
            height: 24
            radius: 12
            color: actionButton.iconColor
            
            Text {
                anchors.centerIn: parent
                text: "✓"
                color: "white"
                font.pixelSize: 16
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