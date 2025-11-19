import QtQuick 2.15
import QtQuick.Controls 2.15
import "."

Rectangle {
    id: overlay
    anchors.fill: parent
    color: "transparent"
    
    VideoOverlayStyle { id: style }
    
    // WorkFlow Status Overlay - Full screen with blinking border
    WorkFlowStatusOverlay {
        id: workFlowStatusOverlay
        z: 150  // Above other overlays but below top bar
    }
    
    // Top bar
    VideoOverlayTopBar {
        id: topBar
        z: 200  // Highest z-index
    }
    
    // LEFT SIDE - Wheel Data (Speed & Heading)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item { 
        id: leftDataPanel
        // Width and Height are still necessary for layout calculation
        width: style.panelWidth 
        height: style.panelHeight 
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---

        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 0 // Reduced margin for pure text look
            spacing: style.contentSpacing * 1.5 // Increased spacing between data pairs
            
            // Speed Row
            Row {
                width: parent.width
                // Simplified height calculation as divider is gone
                height: (parent.height - style.contentSpacing * 1.5) / 2 
                
                Text {
                    text: "SPEED"
                    color: style.labelColor // Softer color for secondary text
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.wheel_speed ? wheelController.wheel_speed.toFixed(1) + " m/s" : "0.0 m/s"
                    color: style.valueColor // Bright/White for primary value
                    font.pixelSize: style.valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // --- REMOVED: Divider line ---
            
            // Heading Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "HEADING"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "0.0°"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
    
    // RIGHT SIDE - LiDAR Data (Distance & Status)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item {
        id: rightDataPanel
        width: style.panelWidth
        height: style.panelHeight
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: style.contentSpacing * 1.5 // Increased spacing between data pairs
            
            // Distance Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "DISTANCE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "0.0 m"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // --- REMOVED: Divider line ---
            
            // Status Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "STATUS"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "OK"
                    color: style.panelBorderEnabled
                    font.pixelSize: style.valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
