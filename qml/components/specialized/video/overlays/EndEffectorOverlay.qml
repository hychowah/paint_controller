import QtQuick 2.15
import QtQuick.Controls 2.15
import "."

/**
 * EndEffectorOverlay - Modern DJI-style telemetry overlay for end effector camera
 * Displays: Winch torque/cable length (right side) and Extension/Gimbal angle (left side)
 * Color-coded borders based on system enabled status
 */

Rectangle {
    id: overlay
    anchors.fill: parent
    color: "transparent"
    
    VideoOverlayStyle { id: style }
    
    // LEFT SIDE - Teensy Data (Extension & Gimbal Angle)
    Rectangle {
        id: leftDataPanel
        width: style.panelWidth
        height: style.panelHeight
        radius: style.panelRadius
        color: style.panelBackground
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // Modern gradient background
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            gradient: Gradient {
                GradientStop { position: 0.0; color: style.panelBackgroundLight }
                GradientStop { position: 1.0; color: style.panelBackground }
            }
            z: -1
        }
        
        // Border with status color
        border.width: style.borderWidth
        border.color: (teensyController.all_status.enabled && teensyController.all_status.relay_on) 
                      ? style.panelBorderEnabled 
                      : style.panelBorderDisabled
        
        Behavior on border.color {
            ColorAnimation { duration: style.colorAnimationDuration }
        }
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 8
            spacing: style.contentSpacing
            
            // Extension Distance Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "EXT"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: teensyController.all_status.arm_extension_dist.toFixed(0) + " mm"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Divider line (centered)
            Rectangle {
                width: parent.width
                height: style.dividerHeight
                color: style.dividerColor
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            // Gimbal Angle Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "GIMBAL"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: teensyController.all_status.spray_gun_motor_angle.toFixed(1) + "°"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
    
    // RIGHT SIDE - Winch Data (Torque & Cable Length)
    Rectangle {
        id: rightDataPanel
        width: style.panelWidth
        height: style.panelHeight
        radius: style.panelRadius
        color: style.panelBackground
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // Modern gradient background
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            gradient: Gradient {
                GradientStop { position: 0.0; color: style.panelBackgroundLight }
                GradientStop { position: 1.0; color: style.panelBackground }
            }
            z: -1
        }
        
        // Border with status color
        border.width: style.borderWidth
        border.color: winchController.enabled 
                      ? style.panelBorderEnabled 
                      : style.panelBorderDisabled
        
        Behavior on border.color {
            ColorAnimation { duration: style.colorAnimationDuration }
        }
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 8
            spacing: style.contentSpacing
            
            // Winch Torque Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "TORQUE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: winchController.winch_torque.toFixed(1) + " Nm"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Divider line (centered)
            Rectangle {
                width: parent.width
                height: style.dividerHeight
                color: style.dividerColor
                anchors.horizontalCenter: parent.horizontalCenter
            }
            
            // Cable Length Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "CABLE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: winchController.cable_length.toFixed(2) + " m"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
