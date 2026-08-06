import QtQuick
import QtQuick.Controls
import "../../../components/displays"
import "."
import "../../../theme"


Rectangle {
    id: overlay
    anchors.fill: parent
    color: "transparent"
    required property var workflowRunner
    required property var videoRuntime
    required property var winchStatus
    required property var teensyStatus
    required property var valveStatus
    required property var lidarStatus
    // Workspace may own a single shared top bar (avoid recreate on base↔EF).
    property bool showTopBar: true

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

    function formatFixed(value, digits, suffix) {
        return numericValue(value, 0).toFixed(digits) + suffix
    }
    
    // Pure QML HUDs (no Canvas/Context2D — first Canvas paint blocked Deck ~2s).
    PitchIndicatorDial {
        anchors.top: parent.top
        anchors.topMargin: 50
        anchors.horizontalCenter: parent.horizontalCenter
        z: 50
        currentPitch: numericValue(overlay.teensyStatus ? overlay.teensyStatus.imuPitch : 0.0, 0.0)
    }

    WallDetectionOverlay {
        lidarStatus: overlay.lidarStatus
    }
    
    // WorkFlow Status Overlay - Full screen with blinking border
    WorkFlowStatusOverlay {
        id: workFlowStatusOverlay
        z: 150  // Above wall detection but below top bar
        workflowRunner: overlay.workflowRunner
    }
    
    // Top bar only when this overlay owns it (fullscreen workspace uses shared bar).
    Loader {
        active: overlay.showTopBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: active ? 50 : 0
        z: 200
        sourceComponent: VideoOverlayTopBar {
            topBarModel: overlay.videoRuntime ? overlay.videoRuntime.topBar : null
            selectedOverlay: "ef"
        }
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
                    text: formatFixed(overlay.teensyStatus.armExtensionDist, 0, " mm")
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
                    text: formatFixed(overlay.teensyStatus.gimbalPitchMotorAngle, 1, "°")
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
                    text: formatFixed(overlay.winchStatus.winchTorque / 100, 2, " A")
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
                    text: formatFixed(overlay.winchStatus.cableLength, 0, " mm")
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
                        color: overlay.valveStatus.valveMotorConnected ? "#00FF00" : "#FF3333"
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
                        color: overlay.valveStatus.flowMeterConnected ? "#00FF00" : "#FF3333"
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
                    text: formatFixed(overlay.valveStatus.valvePosition, 1, "")
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
                    text: formatFixed(overlay.valveStatus.valveRate, 2, "")
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
                    text: formatFixed(overlay.valveStatus.totalVolume, 2, "")
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