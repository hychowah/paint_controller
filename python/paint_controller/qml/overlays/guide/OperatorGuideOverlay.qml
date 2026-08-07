import QtQuick
import QtQuick.Layouts
import "../../theme"
import "."

/**
 * Context-aware step-carousel guide.
 *
 * Hosts pass a contextId matching GuideCatalog packs (ef, base, system_*,
 * workflow_editor). Presentation only — no hardware/safety policy.
 */
Item {
    id: root
    objectName: "operatorGuideOverlay"
    anchors.fill: parent
    visible: open
    focus: open

    property bool open: false
    property int stepIndex: 0
    /** Catalog key — see GuideCatalog.qml */
    property string contextId: "ef"

    signal closed()
    signal finished()

    GuideCatalog {
        id: catalog
    }

    readonly property var steps: catalog.stepsFor(root.contextId)
    readonly property string contextTitle: catalog.titleFor(root.contextId)
    readonly property int stepCount: steps ? steps.length : 0
    readonly property var currentStep: (stepCount > 0 && stepIndex >= 0 && stepIndex < stepCount)
                                       ? steps[stepIndex] : null

    readonly property real _margin: CommonStyle.spacingSm
    readonly property real _footerReserve: Math.round(72 * CommonStyle.scaleFactor)

    readonly property real calloutXPos: {
        if (!currentStep || width <= 0)
            return _margin
        var x = width * currentStep.calloutX
        var maxX = Math.max(_margin, width - callout.width - _margin)
        return Math.max(_margin, Math.min(x, maxX))
    }
    readonly property real calloutYPos: {
        if (!currentStep || height <= 0)
            return _margin
        var y = height * currentStep.calloutY
        var maxY = Math.max(_margin, height - callout.height - _footerReserve)
        return Math.max(_margin, Math.min(y, maxY))
    }

    /**
     * Open guide for a surface context.
     * @param contextId catalog pack key (ef|base|system_*|workflow_editor)
     * @param startIndex optional step index within that pack
     */
    function openGuide(contextId, startIndex) {
        if (typeof contextId === "string" && contextId.length > 0)
            root.contextId = contextId
        var idx = (typeof startIndex === "number") ? startIndex : 0
        stepIndex = Math.max(0, Math.min(idx, Math.max(0, stepCount - 1)))
        open = true
        forceActiveFocus()
    }

    function closeGuide() {
        if (!open)
            return
        open = false
        closed()
    }

    function nextStep() {
        if (stepIndex >= stepCount - 1) {
            open = false
            finished()
            closed()
            return
        }
        stepIndex += 1
    }

    function prevStep() {
        if (stepIndex > 0)
            stepIndex -= 1
    }

    Rectangle {
        id: scrim
        anchors.fill: parent
        color: CommonStyle.overlayScrim
        objectName: "guideScrim"

        MouseArea {
            anchors.fill: parent
            onClicked: { }
        }
    }

    Repeater {
        model: (root.open && root.currentStep) ? root.currentStep.hotspots : []

        GuideHotspot {
            required property var modelData
            relX: modelData.x
            relY: modelData.y
            relW: modelData.w
            relH: modelData.h
            active: root.open
        }
    }

    GuideCallout {
        id: callout
        objectName: "guideCallout"
        title: root.currentStep ? root.currentStep.title : ""
        body: root.currentStep ? root.currentStep.body : ""
        badge: (root.currentStep && root.currentStep.badge) ? root.currentStep.badge : ""
        x: root.calloutXPos
        y: root.calloutYPos
    }

    Rectangle {
        id: footer
        objectName: "guideFooter"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: Math.round(64 * CommonStyle.scaleFactor)
        color: CommonStyle.videoSurfaceStrong
        border.color: CommonStyle.borderDefault
        border.width: CommonStyle.borderWidthThin

        RowLayout {
            anchors.fill: parent
            anchors.margins: CommonStyle.spacingMd
            spacing: CommonStyle.spacingMd

            GuideNavButton {
                objectName: "guideSkipButton"
                label: "Skip"
                secondary: true
                onClicked: root.closeGuide()
            }

            Item { Layout.fillWidth: true }

            Column {
                Layout.alignment: Qt.AlignVCenter
                spacing: 2
                Text {
                    objectName: "guideContextLabel"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.contextTitle
                    color: CommonStyle.accentSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontLabel
                    font.bold: true
                }
                Text {
                    objectName: "guideStepLabel"
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.stepCount > 0
                          ? ("Step " + (root.stepIndex + 1) + " / " + root.stepCount)
                          : ""
                    color: CommonStyle.textSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
                }
            }

            Item { Layout.fillWidth: true }

            GuideNavButton {
                objectName: "guideBackButton"
                label: "Back"
                secondary: true
                enabled: root.stepIndex > 0
                opacity: enabled ? 1 : 0.35
                onClicked: root.prevStep()
            }

            GuideNavButton {
                objectName: "guideNextButton"
                label: root.stepIndex >= root.stepCount - 1 ? "Finish" : "Next"
                secondary: false
                onClicked: root.nextStep()
            }
        }
    }

    Keys.onPressed: (event) => {
        if (!root.open) {
            event.accepted = false
            return
        }
        if (event.key === Qt.Key_Escape) {
            root.closeGuide()
            event.accepted = true
        } else if (event.key === Qt.Key_Right || event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            root.nextStep()
            event.accepted = true
        } else if (event.key === Qt.Key_Left) {
            root.prevStep()
            event.accepted = true
        }
    }

    component GuideNavButton: Rectangle {
        id: btn
        property string label: ""
        property bool secondary: false
        signal clicked()

        implicitWidth: Math.max(Math.round(88 * CommonStyle.scaleFactor), labelText.implicitWidth + CommonStyle.spacingXxl)
        implicitHeight: Math.round(40 * CommonStyle.scaleFactor)
        radius: CommonStyle.radiusSm
        color: secondary
               ? (mouse.pressed ? CommonStyle.backgroundL2 : CommonStyle.backgroundL1)
               : (mouse.pressed ? CommonStyle.buttonPressed : CommonStyle.buttonPrimary)
        border.color: secondary ? CommonStyle.borderDefault : CommonStyle.borderFocused
        border.width: CommonStyle.borderWidthThin
        opacity: enabled ? 1 : 0.4

        Text {
            id: labelText
            anchors.centerIn: parent
            text: btn.label
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontCaption
            font.bold: !btn.secondary
        }

        MouseArea {
            id: mouse
            anchors.fill: parent
            enabled: btn.enabled
            onClicked: btn.clicked()
        }
    }
}
