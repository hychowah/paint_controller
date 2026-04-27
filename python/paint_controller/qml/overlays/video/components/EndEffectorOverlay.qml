import QtQuick
import QtQuick.Controls
import "../../../components/displays"
import "."
import "../../../core"


Rectangle {
    id: overlay
    anchors.fill: parent
    color: "transparent"
    required property var workflowRunner
    required property var videoRuntime

    readonly property var style: CommonStyle
    
    // Top Center - Pitch Indicator Dial
    PitchIndicatorDial {
        id: pitchIndicator
        anchors.top: parent.top
        anchors.topMargin: 50
        anchors.horizontalCenter: parent.horizontalCenter
        
        currentPitch: teensyController.all_status.imu_pitch
        z: 50
    }
    
    // Wall Detection Overlay - Bottom Center
    WallDetectionOverlay {
        id: wallDetectionOverlay
    }
    
    // WorkFlow Status Overlay - Full screen with blinking border
    WorkFlowStatusOverlay {
        id: workFlowStatusOverlay
        z: 150  // Above wall detection but below top bar
        workflowRunner: overlay.workflowRunner
    }
    
    // Top bar
    VideoOverlayTopBar {
        id: topBar
        z: 200  // Highest z-index
        topBarModel: overlay.videoRuntime.topBar
    }
    
    // LEFT SIDE - Teensy Data (Extension & Gimbal Angle)
    Rectangle { 
        id: leftDataPanel
        // Width and Height are still necessary for layout calculation
        width: style.panelWidth 
        height: style.panelHeight 
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0

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
                    text: teensyController.all_status.gimbal_pitch_motor_angle.toFixed(1) + "°"
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
    Rectangle {
        id: rightDataPanel
        width: style.panelWidth
        height: style.panelHeight
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0
        
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
                    text: "CURRENT"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: (winchController.winch_torque / 100).toFixed(2) + " A"
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
                    text: (winchController.cable_length).toFixed(0) + " mm"
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
    
    // RIGHT SIDE MIDDLE - Valve Status Data
    Rectangle {
        id: valveStatusPanel
        width: style.panelWidth
        height: style.panelHeight + 50  // Increased height for 3 rows
        
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: style.controlPanelSideMargin  // Align with rightControlPanel
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: style.contentSpacing * 0.8 // Spacing between data rows
            
            // Connection Status Indicators Row
            Row {
                width: parent.width
                height: 15
                spacing: 8
                
                // Valve Motor Connection Indicator
                Row {
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter
                    
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: esp32ValveController.valve_motor_connected ? "#00FF00" : "#FF3333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Text {
                        text: "VALVE"
                        color: style.labelColor
                        font.pixelSize: 8
                        font.bold: false
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                
                // Flow Meter Connection Indicator
                Row {
                    spacing: 4
                    anchors.verticalCenter: parent.verticalCenter
                    
                    Rectangle {
                        width: 8
                        height: 8
                        radius: 4
                        color: esp32ValveController.flow_meter_connected ? "#00FF00" : "#FF3333"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    
                    Text {
                        text: "FLOW"
                        color: style.labelColor
                        font.pixelSize: 8
                        font.bold: false
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            
            // Valve Position Row
            Row {
                width: parent.width
                height: 30
                
                Text {
                    text: "POSITION"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: esp32ValveController.valve_position.toFixed(1)
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Flow Rate Row
            Row {
                width: parent.width
                height: 30
                
                Text {
                    text: "FLOW RATE"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: esp32ValveController.valve_rate.toFixed(2)
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Total Volume Row
            Row {
                width: parent.width
                height: 30
                
                Text {
                    text: "VOLUME"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: esp32ValveController.total_volume.toFixed(2)
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