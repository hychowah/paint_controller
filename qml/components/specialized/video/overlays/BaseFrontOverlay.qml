import QtQuick 2.15
import QtQuick.Controls 2.15
import "."

/**
 * BaseFrontOverlay - Modern DJI-style telemetry overlay for base front camera
 * Displays: Speed/Heading (top-left) and Distance/Status (top-right)
 */

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
    
    // TOP-LEFT: Speed and Heading (wheel status)
    Rectangle {
        id: topLeftPanel
        width: style.panelWidth
        height: style.panelHeight
        radius: style.panelRadius
        color: style.panelBackground
        
        anchors.top: parent.top
        anchors.topMargin: style.sideMargin
        anchors.left: parent.left
        anchors.leftMargin: style.sideMargin
        
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
        
        border.width: style.borderWidth
        border.color: wheelController.enabled ? style.panelBorderEnabled : style.panelBorderDisabled
        
        Behavior on border.color {
            ColorAnimation { duration: style.colorAnimationDuration }
        }
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 8
            spacing: style.contentSpacing
            
            // Speed Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "SPEED"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.wheel_speed ? wheelController.wheel_speed.toFixed(1) + " m/s" : "0.0 m/s"
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
            
            // Heading Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "HEAD"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "0.0°"
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
    
    // TOP-RIGHT: Distance and Status (LiDAR status)
    Rectangle {
        id: topRightPanel
        width: style.panelWidth
        height: style.panelHeight
        radius: style.panelRadius
        color: style.panelBackground
        
        anchors.top: parent.top
        anchors.topMargin: style.sideMargin
        anchors.right: parent.right
        anchors.rightMargin: style.sideMargin
        
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
        
        border.width: style.borderWidth
        border.color: lidarController.enabled ? style.panelBorderEnabled : style.panelBorderDisabled
        
        Behavior on border.color {
            ColorAnimation { duration: style.colorAnimationDuration }
        }
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 8
            spacing: style.contentSpacing
            
            // Distance Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "DIST"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "0.0 m"
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
            
            // Status Row
            Row {
                width: parent.width
                height: (style.panelHeight - style.panelMargins * 2 - style.panelMargins / 2 - style.contentSpacing - style.dividerHeight) / 2
                
                Text {
                    text: "STATUS"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: true
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: "OK"
                    color: style.panelBorderEnabled
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
