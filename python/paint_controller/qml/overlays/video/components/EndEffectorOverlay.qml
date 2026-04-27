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

    readonly property int panelWidth: CommonStyle.panelWidth
    readonly property int panelHeight: CommonStyle.panelHeight
    readonly property int panelMargins: CommonStyle.panelMargins
    readonly property real contentSpacing: CommonStyle.contentSpacing
    readonly property int controlPanelWidth: CommonStyle.controlPanelWidth
    readonly property int controlPanelBottomMargin: CommonStyle.controlPanelBottomMargin
    readonly property int controlPanelSideMargin: CommonStyle.controlPanelSideMargin
    readonly property color labelColor: CommonStyle.labelColor
    readonly property color valueColor: CommonStyle.valueColor
    readonly property int labelFontSize: CommonStyle.labelFontSize
    readonly property int valueFontSize: CommonStyle.valueFontSize
    readonly property real labelLetterSpacing: CommonStyle.labelLetterSpacing
    readonly property real valueLetterSpacing: CommonStyle.valueLetterSpacing

    function numericValue(value, fallback) {
        return (typeof value === "number" && isFinite(value)) ? value : fallback
    }

    function controllerValue(controller, key, fallback) {
        if (!controller) {
            return fallback
        }
        var value = controller[key]
        return value === undefined || value === null ? fallback : value
    }

    function statusValue(key, fallback) {
        if (!teensyController || !teensyController.all_status) {
            return fallback
        }
        var value = teensyController.all_status[key]
        return value === undefined || value === null ? fallback : value
    }

    function formatFixed(value, digits, suffix) {
        return numericValue(value, 0).toFixed(digits) + suffix
    }
    
    // Top Center - Pitch Indicator Dial
    PitchIndicatorDial {
        id: pitchIndicator
        anchors.top: parent.top
        anchors.topMargin: 50
        anchors.horizontalCenter: parent.horizontalCenter
        
        currentPitch: numericValue(statusValue("imu_pitch", 0.0), 0.0)
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
        width: panelWidth
        height: panelHeight
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: controlPanelSideMargin + controlPanelWidth + 10
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0

        Column {
            anchors.fill: parent
            anchors.margins: panelMargins
            anchors.topMargin: 0 // Reduced margin for pure text look
            spacing: contentSpacing * 1.5 // Increased spacing between data pairs
            
            // Extension Distance Row
            Item {
                width: parent.width
                // Simplified height calculation as divider is gone
                height: (parent.height - contentSpacing * 1.5) / 2 
                
                Text {
                    text: "EXT"
                    color: labelColor // Softer color for secondary text
                    font.pixelSize: labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(statusValue("arm_extension_dist", 0.0), 0, " mm")
                    color: valueColor // Bright/White for primary value
                    font.pixelSize: valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // --- REMOVED: Divider line ---
            
            // Gimbal Angle Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 1.5) / 2
                
                Text {
                    text: "GIMBAL"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(statusValue("gimbal_pitch_motor_angle", 0.0), 1, "°")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
    
    // RIGHT SIDE - Winch Data (Torque & Cable Length)
    Rectangle {
        id: rightDataPanel
        width: panelWidth
        height: panelHeight
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: controlPanelSideMargin + controlPanelWidth + 10
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0
        
        Column {
            anchors.fill: parent
            anchors.margins: panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: contentSpacing * 1.5 // Increased spacing between data pairs
            
            // Winch Torque Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 1.5) / 2
                
                Text {
                    text: "CURRENT"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(numericValue(controllerValue(winchController, "winch_torque", 0.0), 0.0) / 100, 2, " A")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // --- REMOVED: Divider line ---
            
            // Cable Length Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 1.5) / 2
                
                Text {
                    text: "CABLE"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false // Less emphasis
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(winchController, "cable_length", 0.0), 0, " mm")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true // Strong emphasis
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
    
    // RIGHT SIDE MIDDLE - Valve Status Data
    Rectangle {
        id: valveStatusPanel
        width: panelWidth
        height: panelHeight + 50  // Increased height for 3 rows
        
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: controlPanelSideMargin  // Align with rightControlPanel
        
        color: "#AA000000" // Semi-transparent dark background for readability
        radius: 6
        border.width: 0
        
        Column {
            anchors.fill: parent
            anchors.margins: panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: contentSpacing * 0.8 // Spacing between data rows
            
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
                        color: labelColor
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
                        color: labelColor
                        font.pixelSize: 8
                        font.bold: false
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
            
            // Valve Position Row
            Item {
                width: parent.width
                height: 30
                
                Text {
                    text: "POSITION"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(esp32ValveController, "valve_position", 0.0), 1, "")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Flow Rate Row
            Item {
                width: parent.width
                height: 30
                
                Text {
                    text: "FLOW RATE"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(esp32ValveController, "valve_rate", 0.0), 2, "")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Total Volume Row
            Item {
                width: parent.width
                height: 30
                
                Text {
                    text: "VOLUME"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(esp32ValveController, "total_volume", 0.0), 2, "")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}