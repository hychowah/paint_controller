import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components/panels"
import "components"

Rectangle {
    id: root
    
    property string videoSource: ""
    property bool active: false
    
    // Control panel shared properties
    property int panelWidth: 200
    property int panelHeight: 120
    property int panelBottomMargin: 40
    property int panelSideMargin: 20
    
    visible: active
    anchors.fill: parent
    color: "black"
    
    // MouseArea to consume all touch/mouse events when active
    MouseArea {
        anchors.fill: parent
        enabled: root.active
        // Touch-to-exit disabled - use controller button instead
        // onClicked: root.active = false
    }
    
    // Video background
    Image {
        id: videoFrame
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        cache: false
        asynchronous: false
        source: root.videoSource
    }
    
    
    // Top telemetry bar - removed, now using overlay system
    
    // Bottom status bar - removed, now using overlay system
    
    
    // Center crosshair or reticle - optional
    Rectangle {
        id: centerCrosshair
        anchors.centerIn: parent
        width: 30
        height: 30
        color: "transparent"
        border.color: "#80FFFFFF"
        border.width: 2
        radius: 15
        visible: false  // Hidden for now
        
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: -10
            width: 2
            height: 10
            color: "#80FFFFFF"
        }
        
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: -10
            width: 2
            height: 10
            color: "#80FFFFFF"
        }
        
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: -10
            width: 10
            height: 2
            color: "#80FFFFFF"
        }
        
        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: -10
            width: 10
            height: 2
            color: "#80FFFFFF"
        }
    }
    
    // Dynamic Overlay Loader - switches based on video source
    Loader {
        id: overlayLoader
        anchors.fill: parent
        enabled: root.active
        
        sourceComponent: {
            if (root.videoSource.indexOf("ef_live") >= 0) {
                return endEffectorOverlayComponent
            } else if (root.videoSource.indexOf("base_front_live") >= 0) {
                return baseFrontOverlayComponent
            }
            return null
        }
    }
    
    Component {
        id: endEffectorOverlayComponent
        EndEffectorOverlay { }
    }
    
    Component {
        id: baseFrontOverlayComponent
        BaseFrontOverlay { }
    }

    // Bottom Left Info Panel
    ControlInfoPanel {
        id: leftControlPanel
        position: "left"
        leftMargin: root.panelSideMargin
        rightMargin: 20
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: controlProcessor.left_control_mode
        controlValue: controlProcessor.left_control_value
        title: "LEFT CONTROL"
    }

    // Bottom Right Info Panel
    ControlInfoPanel {
        id: rightControlPanel
        position: "right"
        leftMargin: 20
        rightMargin: root.panelSideMargin
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: controlProcessor.right_control_mode
        controlValue: controlProcessor.right_control_value
        title: "RIGHT CONTROL"
    }

    // Exit hint at bottom center - hidden since touch-to-exit is disabled
    Rectangle {
        visible: false  // Touch-to-exit disabled
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: 20
        width: 200
        height: 40
        radius: 20
        color: "#60000000"
        border.color: "#80FFFFFF"
        border.width: 1
        
        Label {
            anchors.centerIn: parent
            text: "Tap to exit fullscreen"
            color: "white"
            font.pixelSize: 14
        }
        
        // Fade out after a few seconds
        opacity: fadeOutTimer.running ? 1.0 : 0.0
        
        Behavior on opacity {
            NumberAnimation { duration: 500 }
        }
    }
    
    Timer {
        id: fadeOutTimer
        interval: 3000
        running: root.active
        repeat: false
    }
    
    // Direct connections to video stream updates
    Connections {
        target: baseStreamHandler
        enabled: root.active
        
        function onEndEffectorFrameReady() {
            if (root.videoSource.indexOf("ef_live") >= 0) {
                videoFrame.source = ""
                videoFrame.source = "image://ef_live/frame"
            }
        }
        
        function onBaseFrontFrameReady() {
            if (root.videoSource.indexOf("base_front_live") >= 0) {
                videoFrame.source = ""
                videoFrame.source = "image://base_front_live/frame"
            }
        }
        
        function onBaseRearFrameReady() {
            if (root.videoSource.indexOf("base_rear_live") >= 0) {
                videoFrame.source = ""
                videoFrame.source = "image://base_rear_live/frame"
            }
        }
    }
    
    // Smooth fade in/out animation
    Behavior on opacity {
        NumberAnimation { duration: 300 }
    }
    
    opacity: active ? 1.0 : 0.0
}
