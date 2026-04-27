import QtQuick
import QtQuick.Controls
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
    readonly property color dividerColor: CommonStyle.dividerColor
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
    
    // WorkFlow Status Overlay - Full screen with blinking border
    WorkFlowStatusOverlay {
        id: workFlowStatusOverlay
        z: 150  // Above other overlays but below top bar
        workflowRunner: overlay.workflowRunner
    }
    
    // Top bar
    VideoOverlayTopBar {
        id: topBar
        z: 200  // Highest z-index
        topBarModel: overlay.videoRuntime.topBar
    }
    
    // LEFT SIDE - Left Motor Data (RPM, Current, Travel)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item { 
        id: leftDataPanel
        // Width and Height are still necessary for layout calculation
        width: panelWidth
        height: panelHeight * 1.5
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: controlPanelSideMargin + controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---

        Column {
            anchors.fill: parent
            anchors.margins: panelMargins
            anchors.topMargin: 0 // Reduced margin for pure text look
            spacing: contentSpacing * 1.2
            
            // Left RPM Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "L RPM"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "left_wheel_speed", 0.0), 0, "")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Left Current Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "L CURR"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "left_wheel_current", 0.0), 1, " A")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Left Travel Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "L TRAVEL"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "left_wheel_position", 0.0), 0, " mm")
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
    
    // RIGHT SIDE - Right Motor Data (RPM, Current, Travel)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item {
        id: rightDataPanel
        width: panelWidth
        height: panelHeight * 1.5
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: controlPanelSideMargin + controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---
        
        Column {
            anchors.fill: parent
            anchors.margins: panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: contentSpacing * 1.2
            
            // Right RPM Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "R RPM"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "right_wheel_speed", 0.0), 0, "")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Right Current Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "R CURR"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "right_wheel_current", 0.0), 1, " A")
                    color: valueColor
                    font.pixelSize: valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Right Travel Row
            Item {
                width: parent.width
                height: (parent.height - contentSpacing * 2.4) / 3
                
                Text {
                    text: "R TRAVEL"
                    color: labelColor
                    font.pixelSize: labelFontSize
                    font.bold: false
                    font.letterSpacing: labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: formatFixed(controllerValue(wheelController, "right_wheel_position", 0.0), 0, " mm")
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
    
    // BASE TOP VIEW - Right side middle display (square — fisheye circle content)
    Rectangle {
        id: baseTopViewWidget
        width: 200
        height: 200  // Square — lens projects a circle, sensor aspect ratio is irrelevant
        
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 20
        
        color: "#1a1a1a"
        border.color: dividerColor
        border.width: 2
        radius: 8
        
        z: 100  // Above data panels but below top bar
        
        Image {
            id: baseTopViewDisplay
            anchors.fill: parent
            anchors.margins: 2
            source: "image://base_top_view/frame"
            fillMode: Image.PreserveAspectFit
            cache: false
            asynchronous: false
        }
        
        // Label overlay
        Text {
            text: "BASE TOP VIEW"
            color: labelColor
            font.pixelSize: 10
            font.bold: true
            font.letterSpacing: 1
            anchors.top: parent.top
            anchors.topMargin: 5
            anchors.horizontalCenter: parent.horizontalCenter
            z: 1
        }
        
        // Tap to open settings (only when not in edit mode)
        MouseArea {
            anchors.fill: parent
            enabled: !controllerValue(baseTopViewController, "editMode", false)
            cursorShape: Qt.PointingHandCursor
            onClicked: baseTopViewSettingsPopup.open()
        }
    }
    
    // Base Top View Settings Popup
    BaseTopViewSettingsPopup {
        id: baseTopViewSettingsPopup
    }
    
    // Connections to refresh base top view when new frame is ready
    Connections {
        target: baseTopViewController
        function onFrameReady() {
            baseTopViewDisplay.source = ""
            baseTopViewDisplay.source = "image://base_top_view/frame"
        }
    }
}
