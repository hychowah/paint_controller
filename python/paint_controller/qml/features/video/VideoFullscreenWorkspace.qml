import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"
import "../../overlays/video/components"
import "../../overlays/guide"

/*
 * Fullscreen video contract (base↔EF on Deck):
 * 1. Active feed Image visibility flips on videoSource (last texture kept per layer).
 * 2. chromeFeed commits next event-loop turn; exactly one mode chrome Loader is active.
 * 3. Shared VideoOverlayTopBar lives here; mode overlays set showTopBar: false.
 * 4. Frames: timer-coalesced generation pull (~15 Hz), not per-frame Connections thrash.
 * 5. Do not dual-warm mode chromes (binding storms / false device disconnects).
 * 6. EF pitch/wall HUDs are pure QML (no Canvas/Context2D — first Canvas paint froze Deck ~2s).
 *
 * Timing (paired with handlers/input.py):
 * control_mode 0 ms → chrome 0 ms → popup 80 ms; frame pull 66 ms.
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
        if (kind === "ef") {
            gen = feeds.endEffectorFrameGeneration
            baseUrl = "image://ef_live/frame"
            if (!force && gen === root._efDisplayGen)
                return
            root._efDisplayGen = gen
            root.efDisplayUrl = feeds.versionedImageUrl(baseUrl, gen)
        } else if (kind === "base_front") {
            gen = feeds.baseFrontFrameGeneration
            baseUrl = "image://base_front_live/frame"
            if (!force && gen === root._baseFrontDisplayGen)
                return
            root._baseFrontDisplayGen = gen
            root.baseFrontDisplayUrl = feeds.versionedImageUrl(baseUrl, gen)
        } else if (kind === "base_rear") {
            gen = feeds.baseRearFrameGeneration
            baseUrl = "image://base_rear_live/frame"
            if (!force && gen === root._baseRearDisplayGen)
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
            if (root.operatorGuideOpen)
                root.closeOperatorGuide()
            root.chromeFeed = ""
            return
        }
        var next = ""
        if (root.isEfFeed)
            next = "ef"
        else if (root.isBaseFrontFeed)
            next = "base"
        // Mode-specific packs: close guide when EF↔BASE chrome swaps.
        if (next !== root.chromeFeed && root.operatorGuideOpen)
            root.closeOperatorGuide()
        root.chromeFeed = next
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
            root.closeOperatorGuide()
        }
    }

    /** Default chrome guide pack (ef | base). Hardware buttons use "deck_buttons". */
    readonly property string operatorGuideContext: root.chromeIsBase ? "base" : "ef"
    readonly property bool operatorGuideOpen: operatorGuideHost.open

    function openOperatorGuide(startIndex) {
        openOperatorGuideContext(root.operatorGuideContext, startIndex)
    }

    function openOperatorGuideContext(contextId, startIndex) {
        operatorGuideHost.openGuide(contextId || root.operatorGuideContext, startIndex || 0)
    }

    function closeOperatorGuide() {
        operatorGuideHost.closeGuide()
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
        objectName: "systemMenuButton"
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
        visible: root.active && !root.operatorGuideOpen

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

    // Operator help (?) — chrome guide for active EF/BASE surface.
    Rectangle {
        id: helpGuideButton
        objectName: "helpGuideButton"
        z: 10
        width: Math.round(72 * CommonStyle.scaleFactor)
        height: width
        radius: Math.round(12 * CommonStyle.scaleFactor)

        anchors.left: parent.left
        anchors.bottom: systemMenuButton.top
        anchors.bottomMargin: Math.round(12 * CommonStyle.scaleFactor)

        color: helpGuideMouseArea.pressed
            ? CommonStyle.backgroundL2
            : (helpGuideMouseArea.containsMouse ? CommonStyle.backgroundL1 : CommonStyle.videoSurface)
        border.color: helpGuideMouseArea.pressed
            ? CommonStyle.accentPrimary
            : CommonStyle.borderDefault
        border.width: CommonStyle.borderWidthThin
        opacity: 0.85
        visible: root.active && !root.operatorGuideOpen

        Behavior on color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on border.color { ColorAnimation { duration: CommonStyle.motionFast } }
        Behavior on scale { NumberAnimation { duration: CommonStyle.motionFast } }

        MouseArea {
            id: helpGuideMouseArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: root.openOperatorGuide(0)
            onPressed: helpGuideButton.scale = 0.92
            onReleased: helpGuideButton.scale = 1.0
            onCanceled: helpGuideButton.scale = 1.0
        }

        Text {
            anchors.centerIn: parent
            text: "?"
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: Math.round(28 * CommonStyle.scaleFactor)
            font.bold: true
        }
    }

    // Exactly one mode chrome active (destroy inactive — no dual-warm).
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

    // Demand-load guide so chrome EF↔BASE Loader swaps stay free of guide scene graph.
    // z above HUD chrome (top bar 200); shell system/joystick (~1000) and emergency stay higher.
    GuideHost {
        id: operatorGuideHost
        z: 400
        loaderObjectName: "operatorGuideLoader"
        switchButtonVisible: true
        switchButtonLabel: operatorGuideHost.activeContextId === "deck_buttons" ? "UI Guide" : "Deck Buttons"
        onSwitchContextRequested: {
            if (operatorGuideHost.activeContextId === "deck_buttons")
                operatorGuideHost.openGuide(root.operatorGuideContext, 0)
            else
                operatorGuideHost.openGuide("deck_buttons", 0)
        }
    }

    Behavior on opacity {
        NumberAnimation { duration: CommonStyle.motionSlow }
    }

    opacity: active ? 1.0 : 0.0
}
