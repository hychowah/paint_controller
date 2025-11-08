import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: controlPanel
    property string controlName: "Control"
    property string controlStatus: "Unknown"
    property bool enabledState: false
    property string iconText: "X"
    property bool selfContained: false
    
    signal clicked()
    
    height: 60
    radius: 10
    color: enabledState ? "#252A36" : "#222222"
    border.color: enabledState ? "#3A5A8C" : "#333333"
    border.width: 1
    
    // This ensures consistent layout across all control panels
    Layout.fillWidth: true
    
    // Subtle transition animations
    Behavior on color {
        ColorAnimation { duration: 200 }
    }
    
    Behavior on border.color {
        ColorAnimation { duration: 200 }
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
            parent.color = enabledState ? "#2A3040" : "#2A2A2A"
        }
        
        onExited: {
            parent.color = enabledState ? "#252A36" : "#222222"
        }
    }
    
    // Use Row instead of RowLayout for more consistent sizing
    Row {
        anchors {
            fill: parent
            margins: 10
            // Add right margin to create space between toggle and right edge
            rightMargin: 15
        }
        spacing: 10
        
        // Icon
        Rectangle {
            width: 36
            height: 36
            radius: 18
            color: enabledState ? "#3A5A8C" : "#444444"
            anchors.verticalCenter: parent.verticalCenter
            
            Text {
                anchors.centerIn: parent
                text: controlPanel.iconText
                font.pixelSize: 16
                color: "white"
                font.bold: true
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: 200 }
            }
        }
        
        // Text with status - using a Rectangle with Column inside to fill available space
        Rectangle {
            width: parent.width - 36 - 10 - 48 - 5 // parent width minus icon width, spacing, switch width, and extra margin
            height: parent.height - 20
            color: "transparent" // Make this visible for debugging: "#550000"
            anchors.verticalCenter: parent.verticalCenter
            
            Column {
                anchors.verticalCenter: parent.verticalCenter
                spacing: 2
                
                Text {
                    text: controlPanel.controlName
                    font.pixelSize: 16
                    font.bold: true
                    color: "#FFFFFF"
                }
                
                Text {
                    text: controlPanel.controlStatus
                    font.pixelSize: 13
                    color: enabledState ? "#90CAF9" : "#999999"
                    
                    // Color transition
                    Behavior on color {
                        ColorAnimation { duration: 200 }
                    }
                }
            }
        }
        
        // Toggle switch - simple Rectangle with fixed width
        Rectangle {
            width: 48
            height: 24
            radius: 12
            color: enabledState ? "#3A5A8C" : "#444444"
            anchors.verticalCenter: parent.verticalCenter
            
            Rectangle {
                width: 18
                height: 18
                radius: 9
                color: "#FFFFFF"
                anchors.verticalCenter: parent.verticalCenter
                x: enabledState ? parent.width - width - 3 : 3
                
                Behavior on x {
                    NumberAnimation { 
                        duration: 200
                        easing.type: Easing.OutCubic
                    }
                }
            }
            
            // Color transition
            Behavior on color {
                ColorAnimation { duration: 200 }
            }
        }
    }
}