import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"
import "../../overlays/video/components"

Rectangle {
    id: root

    property string videoSource: ""
    property bool active: false
    required property var workflowServices
    required property var videoRuntime
    required property var wheelStatus
    required property var winchStatus
    required property var teensyStatus
    required property var valveStatus
    required property var lidarStatus

    readonly property int panelWidth: CommonStyle.videoControlPanelWidth
    readonly property int panelHeight: CommonStyle.videoControlPanelHeight
    readonly property int panelBottomMargin: CommonStyle.videoPanelBottomMargin
    readonly property int panelSideMargin: CommonStyle.videoPanelSideMargin

    visible: active
    anchors.fill: parent
    color: CommonStyle.backgroundL0

    MouseArea {
        anchors.fill: parent
        enabled: root.active
    }

    Image {
        id: videoFrame
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        cache: false
        asynchronous: false
        source: root.videoSource
    }

    Rectangle {
        id: centerCrosshair
        anchors.centerIn: parent
        width: 30
        height: 30
        color: "transparent"
        border.color: CommonStyle.videoCrosshair
        border.width: 2
        radius: 15
        visible: false

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: -10
            width: 2
            height: 10
            color: CommonStyle.videoCrosshair
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: -10
            width: 2
            height: 10
            color: CommonStyle.videoCrosshair
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: -10
            width: 10
            height: 2
            color: CommonStyle.videoCrosshair
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: -10
            width: 10
            height: 2
            color: CommonStyle.videoCrosshair
        }
    }

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
        EndEffectorOverlay {
            workflowRunner: root.workflowServices.workflowRunner
            videoRuntime: root.videoRuntime
            winchStatus: root.winchStatus
            teensyStatus: root.teensyStatus
            valveStatus: root.valveStatus
            lidarStatus: root.lidarStatus
        }
    }

    Component {
        id: baseFrontOverlayComponent
        BaseFrontOverlay {
            workflowRunner: root.workflowServices.workflowRunner
            videoRuntime: root.videoRuntime
            wheelStatus: root.wheelStatus
        }
    }

    ControlInfoPanel {
        id: leftControlPanel
        position: "left"
        leftMargin: root.panelSideMargin
        rightMargin: 20
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: root.videoRuntime.controls.leftMode
        controlModeDisplay: root.videoRuntime.controls.leftModeDisplay
        controlValue: root.videoRuntime.controls.leftValue
        title: "LEFT CONTROL"
        onPanelClicked: overlayController.open_menu("left")
    }

    ControlInfoPanel {
        id: rightControlPanel
        position: "right"
        leftMargin: 20
        rightMargin: root.panelSideMargin
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: root.videoRuntime.controls.rightMode
        controlModeDisplay: root.videoRuntime.controls.rightModeDisplay
        controlValue: root.videoRuntime.controls.rightValue
        title: "RIGHT CONTROL"
        onPanelClicked: overlayController.open_menu("right")
    }

    Rectangle {
        visible: false
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: CommonStyle.spacingLg + CommonStyle.spacingXs
        width: 200
        height: 40
        radius: CommonStyle.radiusLg + CommonStyle.spacingXs / 2
        color: CommonStyle.videoSurface
        border.color: CommonStyle.videoCrosshair
        border.width: 1

        Label {
            anchors.centerIn: parent
            text: "Tap to exit fullscreen"
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontCaption + 1
        }

        opacity: fadeOutTimer.running ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation { duration: CommonStyle.motionSlow + 200 }
        }
    }

    Timer {
        id: fadeOutTimer
        interval: 3000
        running: root.active
        repeat: false
    }

    Connections {
        target: root.videoRuntime.feeds
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

    Behavior on opacity {
        NumberAnimation { duration: CommonStyle.motionSlow }
    }

    opacity: active ? 1.0 : 0.0
}