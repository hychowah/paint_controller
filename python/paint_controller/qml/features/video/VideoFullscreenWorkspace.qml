import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "../../overlays/video/components"

/*
 * Fullscreen video contract (base↔EF on Deck):
 * 1. Active feed Image visibility flips on videoSource (last texture kept per layer).
 * 2. chromeFeed commits next event-loop turn; exactly one mode chrome Loader is active.
 * 3. Shared VideoOverlayTopBar lives here; mode overlays set showTopBar: false.
 * 4. Frames: timer-coalesced generation pull (~15 Hz), not per-frame Connections thrash.
 * 5. Do not dual-warm mode chromes (main-thread binding storms / false device disconnects).
 *
 * Timing (paired with handlers/input.py): control_mode 0 ms → chrome 0 ms → EF Canvas ~1 ms
 * → popup 80 ms; frame pull 66 ms.
 */
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
    required property var overlayController
    required property var baseTopViewStatus
    required property var baseTopViewActions
    required property var actionLegality

    readonly property int panelWidth: CommonStyle.videoControlPanelWidth
    readonly property int panelHeight: CommonStyle.videoControlPanelHeight
    readonly property int panelBottomMargin: CommonStyle.videoPanelBottomMargin
    readonly property int panelSideMargin: CommonStyle.videoPanelSideMargin

    // Active-feed UI rebind budget (ms). Product presentation; not machine policy.
    readonly property int framePullIntervalMs: 66

    // Feed kind — URL classification at the image-provider boundary (Python owns mode).
    readonly property bool isEfFeed: root.videoSource.indexOf("ef_live") >= 0
    readonly property bool isBaseFrontFeed: root.videoSource.indexOf("base_front_live") >= 0
    readonly property bool isBaseRearFeed: root.videoSource.indexOf("base_rear_live") >= 0

    readonly property bool efStreamAvailable: !!(root.videoRuntime && root.videoRuntime.feeds
                                                && root.videoRuntime.feeds.endEffectorStreamAvailable)
    readonly property bool baseFrontStreamAvailable: !!(root.videoRuntime && root.videoRuntime.feeds
                                                       && root.videoRuntime.feeds.baseFrontStreamAvailable)
    readonly property bool baseRearStreamAvailable: !!(root.videoRuntime && root.videoRuntime.feeds
                                                      && root.videoRuntime.feeds.baseRearStreamAvailable)

    readonly property bool activeStreamAvailable: {
        if (root.isEfFeed)
            return root.efStreamAvailable
        if (root.isBaseFrontFeed)
            return root.baseFrontStreamAvailable
        if (root.isBaseRearFeed)
            return root.baseRearStreamAvailable
        return false
    }

    // Chrome lags video by one event-loop turn so base↔EF first paints Images only.
    property string chromeFeed: ""  // "ef" | "base" | ""
    readonly property bool chromeIsEf: root.chromeFeed === "ef"
    readonly property bool chromeIsBase: root.chromeFeed === "base"

    property string efDisplayUrl: ""
    property string baseFrontDisplayUrl: ""
    property string baseRearDisplayUrl: ""
    property int _efDisplayGen: -1
    property int _baseFrontDisplayGen: -1
    property int _baseRearDisplayGen: -1

    function _feedsReady() {
        return !!(root.videoRuntime && root.videoRuntime.feeds)
    }

    function pullFrame(kind, force) {
        // kind: "ef" | "base_front" | "base_rear"
        if (!root._feedsReady())
            return
        var feeds = root.videoRuntime.feeds
        var gen = 0
        var baseUrl = ""
        var lastGen = -1
        if (kind === "ef") {
            gen = feeds.endEffectorFrameGeneration
            baseUrl = "image://ef_live/frame"
            lastGen = root._efDisplayGen
            if (!force && gen === lastGen)
                return
            root._efDisplayGen = gen
            root.efDisplayUrl = feeds.versionedImageUrl(baseUrl, gen)
        } else if (kind === "base_front") {
            gen = feeds.baseFrontFrameGeneration
            baseUrl = "image://base_front_live/frame"
            lastGen = root._baseFrontDisplayGen
            if (!force && gen === lastGen)
                return
            root._baseFrontDisplayGen = gen
            root.baseFrontDisplayUrl = feeds.versionedImageUrl(baseUrl, gen)
        } else if (kind === "base_rear") {
            gen = feeds.baseRearFrameGeneration
            baseUrl = "image://base_rear_live/frame"
            lastGen = root._baseRearDisplayGen
            if (!force && gen === lastGen)
                return
            root._baseRearDisplayGen = gen
            root.baseRearDisplayUrl = feeds.versionedImageUrl(baseUrl, gen)
        }
    }

    function pullActiveFrame(force) {
        if (root.isEfFeed)
            root.pullFrame("ef", force)
        else if (root.isBaseFrontFeed)
            root.pullFrame("base_front", force)
        else if (root.isBaseRearFeed)
            root.pullFrame("base_rear", force)
    }

    function commitChromeFeed() {
        if (!root.active) {
            root.chromeFeed = ""
            return
        }
        if (root.isEfFeed)
            root.chromeFeed = "ef"
        else if (root.isBaseFrontFeed)
            root.chromeFeed = "base"
        else
            root.chromeFeed = ""
    }

    onVideoSourceChanged: {
        root.pullActiveFrame(true)
        if (root.active)
            chromeCommitTimer.restart()
    }
    onActiveChanged: {
        if (root.active) {
            // Seed operator warm feeds (EF + base front); rear stays on demand.
            root.pullFrame("base_front", true)
            root.pullFrame("ef", true)
            root.pullActiveFrame(true)
            chromeCommitTimer.restart()
        } else {
            root.chromeFeed = ""
        }
    }
    Component.onCompleted: {
        if (root.active) {
            root.pullFrame("base_front", true)
            root.pullFrame("ef", true)
            root.pullActiveFrame(true)
            chromeCommitTimer.restart()
        }
    }

    Timer {
        id: chromeCommitTimer
        interval: 0
        repeat: false
        onTriggered: root.commitChromeFeed()
    }

    visible: active
    anchors.fill: parent
    color: CommonStyle.backgroundL0

    MouseArea {
        anchors.fill: parent
        enabled: root.active
    }

    Image {
        id: efVideoFrame
        objectName: "efVideoFrame"
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        cache: false
        asynchronous: false
        smooth: false
        source: root.efDisplayUrl
        visible: root.isEfFeed && root.efStreamAvailable
        z: 0
    }

    Image {
        id: baseFrontVideoFrame
        objectName: "baseFrontVideoFrame"
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        cache: false
        asynchronous: false
        smooth: false
        source: root.baseFrontDisplayUrl
        visible: root.isBaseFrontFeed && root.baseFrontStreamAvailable
        z: 0
    }

    Image {
        id: baseRearVideoFrame
        objectName: "baseRearVideoFrame"
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        cache: false
        asynchronous: false
        smooth: false
        source: root.baseRearDisplayUrl
        visible: root.isBaseRearFeed && root.baseRearStreamAvailable
        z: 0
    }

    Image {
        id: streamUnavailableIcon
        anchors.centerIn: parent
        width: Math.round(160 * CommonStyle.scaleFactor)
        height: width
        fillMode: Image.PreserveAspectFit
        source: "../../../resource/stream_not_available.png"
        visible: root.active && !root.activeStreamAvailable
        opacity: 0.85
        z: 1
    }

    Timer {
        id: frameRefreshTimer
        interval: root.framePullIntervalMs
        running: root.active
        repeat: true
        onTriggered: root.pullActiveFrame(false)
    }

    VideoOverlayTopBar {
        id: sharedTopBar
        objectName: "sharedVideoTopBar"
        z: 200
        visible: root.active && root.videoRuntime && root.videoRuntime.topBar
        topBarModel: root.videoRuntime ? root.videoRuntime.topBar : null
        selectedOverlay: root.isEfFeed ? "ef" : "base"
    }

    Rectangle {
        id: systemMenuButton
        z: 10
        width: Math.round(72 * CommonStyle.scaleFactor)
        height: width
        radius: Math.round(12 * CommonStyle.scaleFactor)

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        color: systemMenuMouseArea.pressed
            ? CommonStyle.backgroundL2
            : (systemMenuMouseArea.containsMouse ? CommonStyle.backgroundL1 : CommonStyle.videoSurface)
        border.color: systemMenuMouseArea.pressed
            ? CommonStyle.accentPrimary
            : CommonStyle.borderDefault
        border.width: CommonStyle.borderWidthThin
        opacity: 0.85

        Behavior on color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on border.color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on opacity { NumberAnimation { duration: CommonStyle.motionStandard } }
        Behavior on scale { NumberAnimation { duration: CommonStyle.motionFast } }

        MouseArea {
            id: systemMenuMouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.overlayController.toggle_system_menu()
            onPressed: systemMenuButton.scale = 0.92
            onReleased: systemMenuButton.scale = 1.0
            onCanceled: systemMenuButton.scale = 1.0
        }

        Column {
            anchors.centerIn: parent
            spacing: Math.round(5 * CommonStyle.scaleFactor)
            width: Math.round(22 * CommonStyle.scaleFactor)

            Repeater {
                model: 3
                Rectangle {
                    width: parent.width
                    height: Math.round(3 * CommonStyle.scaleFactor)
                    radius: height / 2
                    color: CommonStyle.textPrimary
                }
            }
        }
    }

    // Exactly one mode chrome. Destroy inactive to free binding storms.
    Loader {
        id: endEffectorOverlayLoader
        objectName: "endEffectorOverlayLoader"
        anchors.fill: parent
        z: 2
        active: root.active && root.chromeIsEf
        visible: status === Loader.Ready && root.chromeIsEf
        asynchronous: true
        sourceComponent: endEffectorOverlayComponent

        onLoaded: {
            if (item)
                item.objectName = "endEffectorOverlay"
        }
    }

    Loader {
        id: baseFrontOverlayLoader
        objectName: "baseFrontOverlayLoader"
        anchors.fill: parent
        z: 2
        active: root.active && root.chromeIsBase
        visible: status === Loader.Ready && root.chromeIsBase
        asynchronous: true
        sourceComponent: baseFrontOverlayComponent

        onLoaded: {
            if (item)
                item.objectName = "baseFrontOverlay"
        }
    }

    Component {
        id: endEffectorOverlayComponent
        EndEffectorOverlay {
            showTopBar: false
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
            showTopBar: false
            workflowRunner: root.workflowServices.workflowRunner
            videoRuntime: root.videoRuntime
            wheelStatus: root.wheelStatus
            baseTopViewStatus: root.baseTopViewStatus
            baseTopViewActions: root.baseTopViewActions
            actionLegality: root.actionLegality
        }
    }

    ControlInfoPanel {
        id: leftControlPanel
        z: 6
        position: "left"
        leftMargin: root.panelSideMargin
        rightMargin: 20
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.leftMode : ""
        controlModeDisplay: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.leftModeDisplay : ""
        controlValue: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.leftValue : ""
        title: "LEFT CONTROL"
        onPanelClicked: root.overlayController.open_menu("left")
    }

    ControlInfoPanel {
        id: rightControlPanel
        z: 6
        position: "right"
        leftMargin: 20
        rightMargin: root.panelSideMargin
        bottomMargin: root.panelBottomMargin
        width: root.panelWidth
        height: root.panelHeight
        controlMode: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.rightMode : ""
        controlModeDisplay: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.rightModeDisplay : ""
        controlValue: root.videoRuntime && root.videoRuntime.controls
            ? root.videoRuntime.controls.rightValue : ""
        title: "RIGHT CONTROL"
        onPanelClicked: root.overlayController.open_menu("right")
    }

    Behavior on opacity {
        NumberAnimation { duration: CommonStyle.motionSlow }
    }

    opacity: active ? 1.0 : 0.0
}
