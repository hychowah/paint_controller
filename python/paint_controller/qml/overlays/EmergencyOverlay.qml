import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Item {
    id: root
    required property var qtBridge
    anchors.fill: parent
    z: 2000
    
    // Public properties - using internal state management
    property real progress: 0.0
    property real currentDuration: 0.0
    property real targetDuration: 1.0
    
    // Internal state to prevent flickering
    property bool shouldBeVisible: false
    property bool isAnimating: false
    
    // Colors matching the main UI theme
    readonly property color backgroundColor: CommonStyle.cardBackground
    readonly property color primaryRed: CommonStyle.statusError
    readonly property color primaryText: CommonStyle.textPrimary
    readonly property color secondaryText: CommonStyle.textSecondary
    readonly property color borderColor: CommonStyle.statusError
    readonly property color progressBackground: CommonStyle.backgroundL2
    
    // Connect to the backend signal with better state management
    Connections {
        target: root.qtBridge
        function onEmergency_overlay_changed(visible, currentDuration, targetDuration) {
            // Only change visibility if it's actually different
            if (visible !== root.shouldBeVisible) {
                root.shouldBeVisible = visible
                
                if (visible) {
                    // Show immediately
                    overlay.visible = true
                    dimmer.visible = true
                    root.progress = 0
                    showAnimation.start()
                } else {
                    // Reset progress when hiding
                    root.progress = 0
                    root.currentDuration = 0
                    // Hide with animation
                    hideAnimation.start()
                }
            }
            
            // Always update progress during visible state
            if (visible) {
                root.progress = currentDuration / targetDuration
                root.currentDuration = currentDuration
                root.targetDuration = targetDuration
            }
        }
    }
    
    // Background dimmer
    Rectangle {
        id: dimmer
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        opacity: 0
        visible: false
        
        MouseArea {
            anchors.fill: parent
            // Consume all mouse events
            enabled: dimmer.visible
        }
    }
    
    // Main overlay container
    Rectangle {
        id: overlay
        anchors.centerIn: parent
        width: Math.round(480 * CommonStyle.scaleFactor)
        height: Math.round(240 * CommonStyle.scaleFactor)
        color: backgroundColor
        radius: CommonStyle.radiusLg
        border.color: borderColor
        border.width: CommonStyle.borderWidthThick
        visible: false
        opacity: 0
        scale: 0.9
        
        ColumnLayout {
            anchors.centerIn: parent
            anchors.margins: CommonStyle.spacingXxl + CommonStyle.spacingSm
            spacing: CommonStyle.spacingXxl
            
            // Emergency header
            ColumnLayout {
                spacing: CommonStyle.spacingMd
                Layout.alignment: Qt.AlignHCenter
                
                // Warning icon (styled as a circle with exclamation)
                Rectangle {
                    width: Math.round(48 * CommonStyle.scaleFactor)
                    height: Math.round(48 * CommonStyle.scaleFactor)
                    radius: 24
                    color: primaryRed
                    Layout.alignment: Qt.AlignHCenter
                    
                    Text {
                        anchors.centerIn: parent
                        text: "!"
                        color: CommonStyle.textPrimary
                        font.pixelSize: Math.round(32 * CommonStyle.scaleFactor)
                        font.bold: true
                    }
                }
                
                Text {
                    text: "EMERGENCY STOP"
                    color: primaryText
                    font.pixelSize: CommonStyle.fontDisplay
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Text {
                    text: "Hold Steam Button"
                    color: secondaryText
                    font.pixelSize: CommonStyle.fontCaption
                    Layout.alignment: Qt.AlignHCenter
                }
            }
            
            // Progress section
            ColumnLayout {
                spacing: CommonStyle.spacingMd
                Layout.fillWidth: true
                
                // Progress bar container with modern styling
                Rectangle {
                    Layout.fillWidth: true
                    height: CommonStyle.spacingSm
                    color: progressBackground
                    radius: 4
                    
                    Rectangle {
                        id: progressBar
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: parent.width * progress
                        color: primaryRed
                        radius: 4
                        
                        // Smooth animation for progress
                        Behavior on width {
                            enabled: root.shouldBeVisible && progress > 0
                            NumberAnimation {
                                duration: 50
                                easing.type: Easing.OutQuart
                            }
                        }
                    }
                }
                
                // Progress text
                RowLayout {
                    Layout.fillWidth: true
                    
                    Text {
                        text: `${Math.round(progress * 100)}%`
                        color: primaryRed
                        font.pixelSize: CommonStyle.fontBody + 2
                        font.bold: true
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Text {
                        text: `${(currentDuration * 1000).toFixed(0)} / ${(targetDuration * 1000).toFixed(0)} ms`
                        color: secondaryText
                        font.pixelSize: CommonStyle.fontCaption
                    }
                }
            }
        }
        
        // Subtle border glow when close to completion
        Rectangle {
            anchors.fill: parent
            radius: parent.radius
            border.color: primaryRed
            border.width: progress > 0.8 ? 3 : 2
            color: "transparent"
            visible: progress > 0.8
            
            Behavior on border.width {
                NumberAnimation {
                    duration: 150
                    easing.type: Easing.InOutQuad
                }
            }
        }
    }
    
    // Show animation
    ParallelAnimation {
        id: showAnimation
        
        onStarted: {
            root.isAnimating = true
        }
        
        onStopped: {
            root.isAnimating = false
        }
        
        PropertyAnimation {
            target: overlay
            property: "opacity"
            from: 0
            to: 1
            duration: 250
            easing.type: Easing.OutQuart
        }
        
        PropertyAnimation {
            target: overlay
            property: "scale"
            from: 0.9
            to: 1.0
            duration: 250
            easing.type: Easing.OutQuart
        }
        
        PropertyAnimation {
            target: dimmer
            property: "opacity"
            from: 0
            to: 0.85
            duration: 250
            easing.type: Easing.OutQuart
        }
    }
    
    // Hide animation
    ParallelAnimation {
        id: hideAnimation
        
        onStarted: {
            root.isAnimating = true
            // Reset progress immediately when starting to hide
            root.progress = 0
            root.currentDuration = 0
        }
        
        onStopped: {
            root.isAnimating = false
            overlay.visible = false
            dimmer.visible = false
        }
        
        PropertyAnimation {
            target: overlay
            property: "opacity"
            from: 1
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }
        
        PropertyAnimation {
            target: overlay
            property: "scale"
            from: 1.0
            to: 0.9
            duration: 200
            easing.type: Easing.InQuart
        }
        
        PropertyAnimation {
            target: dimmer
            property: "opacity"
            from: 0.85
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }
        
        // Also reset the progress bar width to 0 smoothly
        PropertyAnimation {
            target: progressBar
            property: "width"
            to: 0
            duration: 200
            easing.type: Easing.InQuart
        }
    }
}