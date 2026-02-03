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
    
    // LEFT SIDE - Left Motor Data (RPM, Current, Travel)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item { 
        id: leftDataPanel
        // Width and Height are still necessary for layout calculation
        width: style.panelWidth 
        height: style.panelHeight * 1.5
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.left: parent.left
        anchors.leftMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---

        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 0 // Reduced margin for pure text look
            spacing: style.contentSpacing * 1.2
            
            // Left RPM Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "L RPM"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.left_wheel_speed.toFixed(0)
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Left Current Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "L CURR"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.left_wheel_current.toFixed(1) + " A"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Left Travel Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "L TRAVEL"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.left_wheel_position.toFixed(0) + " mm"
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
    
    // RIGHT SIDE - Right Motor Data (RPM, Current, Travel)
    // --- CHANGE: Replaced Rectangle with Item for no visual container ---
    Item {
        id: rightDataPanel
        width: style.panelWidth
        height: style.panelHeight * 1.5
        
        anchors.bottom: parent.bottom
        anchors.bottomMargin: style.controlPanelBottomMargin
        anchors.right: parent.right
        anchors.rightMargin: style.controlPanelSideMargin + style.controlPanelWidth + 10
        
        // --- REMOVED: All background, border, and gradient code ---
        
        Column {
            anchors.fill: parent
            anchors.margins: style.panelMargins
            anchors.topMargin: 0 // Reduced margin
            spacing: style.contentSpacing * 1.2
            
            // Right RPM Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "R RPM"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.right_wheel_speed.toFixed(0)
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Right Current Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "R CURR"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.right_wheel_current.toFixed(1) + " A"
                    color: style.valueColor
                    font.pixelSize: style.valueFontSize
                    font.bold: true
                    font.family: "Courier New"
                    font.letterSpacing: style.valueLetterSpacing
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
            
            // Right Travel Row
            Row {
                width: parent.width
                height: (parent.height - style.contentSpacing * 2.4) / 3
                
                Text {
                    text: "R TRAVEL"
                    color: style.labelColor
                    font.pixelSize: style.labelFontSize
                    font.bold: false
                    font.letterSpacing: style.labelLetterSpacing
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                
                Text {
                    text: wheelController.right_wheel_position.toFixed(0) + " mm"
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
    
    // BIRD VIEW - Right side middle display
    Rectangle {
        id: birdViewWidget
        width: 200  // Scaled down from 300 to fit better
        height: 267  // Maintain aspect ratio (300/400 = 0.75, so 200*4/3 = 267)
        
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 20
        
        color: "#1a1a1a"
        border.color: style.borderColor
        border.width: 2
        radius: 8
        
        z: 100  // Above data panels but below top bar
        
        Image {
            id: birdViewDisplay
            anchors.fill: parent
            anchors.margins: 2
            source: "image://bird_view/frame"
            fillMode: Image.PreserveAspectFit
            cache: false
            asynchronous: false
        }
        
        // Label overlay
        Text {
            text: "BIRD VIEW"
            color: style.labelColor
            font.pixelSize: 10
            font.bold: true
            font.letterSpacing: 1
            anchors.top: parent.top
            anchors.topMargin: 5
            anchors.horizontalCenter: parent.horizontalCenter
            z: 1
        }
        
        // Point editor overlay (shown when in edit mode)
        PointEditorOverlay {
            id: pointEditor
            anchors.fill: parent
            z: 200
        }
        
        // Tap to open settings (only when not in edit mode)
        MouseArea {
            anchors.fill: parent
            enabled: !birdViewController.editMode
            cursorShape: Qt.PointingHandCursor
            onClicked: birdViewSettingsPopup.open()
        }
    }
    
    // Bird View Settings Popup
    BirdViewSettingsPopup {
        id: birdViewSettingsPopup
    }
    
    // Connections to refresh bird view when new frame is ready
    Connections {
        target: birdViewController
        function onFrameReady() {
            birdViewDisplay.source = ""
            birdViewDisplay.source = "image://bird_view/frame"
        }
    }
}
