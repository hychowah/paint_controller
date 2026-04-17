import QtQuick 2.15
import QtQuick.Controls 2.15
import "../../core"

Popup {
    id: customPopup
    width: CommonStyle.popupWidth
    height: CommonStyle.popupHeight
    modal: false
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    anchors.centerIn: Overlay.overlay
    padding: 0
    
    // Custom properties
    property string messageTitle: "Alert"
    property string messageText: "This is a popup message"
    property int dismissDelay: 3000
    property string messageType: "info"  // Can be "info", "warning", "error"
    
    // Apply different styles based on popup type
    property color headerColor: {
        switch(messageType) {
            case "warning": return CommonStyle.statusWarning;
            case "error": return CommonStyle.statusError;
            default: return CommonStyle.statusInfo;
        }
    }
    
    background: Rectangle {
        id: bgRect
        color: CommonStyle.cardBackground
        radius: CommonStyle.cardRadius
        
        // Top color bar indicating message type
        Rectangle {
            width: parent.width - 4  // Slightly inset from parent
            height: 6
            color: customPopup.headerColor
            radius: 3
            anchors.top: parent.top
            anchors.topMargin: 2
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
    
    // Appear animation
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { 
                property: "opacity"
                from: 0.0
                to: 1.0
                duration: CommonStyle.motionSlow
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                property: "y"
                from: customPopup.y - 30
                to: customPopup.y
                duration: CommonStyle.motionSlow
                easing.type: Easing.OutCubic
            }
        }
    }
    
    // Disappear animation
    exit: Transition {
        ParallelAnimation {
            NumberAnimation { 
                property: "opacity"
                from: 1.0
                to: 0.0
                duration: 800
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                property: "y"
                from: customPopup.y
                to: customPopup.y - 30
                duration: 800
                easing.type: Easing.InCubic
            }
        }
    }
    
    Timer {
        id: dismissTimer
        interval: customPopup.dismissDelay
        repeat: false
        running: false
        onTriggered: customPopup.close()
    }
    
    // When popup is opened, start the dismiss timer
    onOpened: {
        dismissTimer.restart()
    }
    
    // Set pointer cursor when hovering over popup
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: customPopup.close()
    }
    
    contentItem: Item {
        anchors.fill: parent
        
        Column {
            anchors.fill: parent
            anchors.margins: CommonStyle.spacingXl
            spacing: CommonStyle.spacingXl
            
            // Icon and title row
            Row {
                width: parent.width
                height: Math.round(30 * CommonStyle.scaleFactor)
                spacing: CommonStyle.spacingMd
                
                Rectangle {
                    width: 24
                    height: 24
                    radius: 12
                    color: customPopup.headerColor
                    anchors.verticalCenter: parent.verticalCenter
                    
                    Text {
                        anchors.centerIn: parent
                        color: CommonStyle.textPrimary
                        font.pixelSize: CommonStyle.fontCaption
                        font.bold: true
                        text: {
                            switch(customPopup.messageType) {
                                case "warning": return "!";
                                case "error": return "×";
                                default: return "i";
                            }
                        }
                    }
                }
                
                Text {
                    text: customPopup.messageTitle
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontHeading
                    font.bold: true
                    width: parent.width - 36
                    elide: Text.ElideRight
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Message text with proper wrapping
            Text {
                id: messageTextItem
                text: customPopup.messageText
                color: CommonStyle.textSecondary
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                width: parent.width
                height: parent.height - 50
                wrapMode: Text.WordWrap
                elide: Text.ElideRight
                maximumLineCount: 4
                lineHeight: 1.3
                verticalAlignment: Text.AlignTop
            }
        }
    }
}