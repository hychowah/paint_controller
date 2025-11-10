import QtQuick 2.15
import QtQuick.Controls 2.15
import "."


Rectangle {
    id: overlay
    anchors.fill: parent
    color: "transparent"
    
    VideoOverlayStyle { id: style }
    
    // Top bar
    VideoOverlayTopBar {
        id: topBar
        z: 100
    }
    
    // LEFT SIDE - Teensy Data (Extension & Gimbal Angle)
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
            
            // Extension Distance Row
            Row {
                width: parent.width
                // Simplified height calculation as divider is gone
                height: (parent.height - style.contentSpacing * 1.5) / 2 
                
                Text {
                    text: "EXT"
                    color: style.labelColor // Softer color for secondary text
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: teensyController.all_status.arm_extension_dist.toFixed(0) + " mm"
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
            
            // Gimbal Angle Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "GIMBAL"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: teensyController.all_status.spray_gun_motor_angle.toFixed(1) + "°"
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
    
    // RIGHT SIDE - Winch Data (Torque & Cable Length)
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
            
            // Winch Torque Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "TORQUE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: winchController.winch_torque.toFixed(1) + " Nm"
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
            
            // Cable Length Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 1.5) / 2
                
                Text {
                    text: "CABLE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: winchController.cable_length.toFixed(2) + " m"
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
}