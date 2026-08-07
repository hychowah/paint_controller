import QtQuick

/**
 * Demand-load host for OperatorGuideOverlay.
 *
 * Owns Loader lifecycle so feature roots only choose context + when to open/close.
 * Presentation only — no hardware/safety policy.
 */
Item {
    id: root
    anchors.fill: parent

    /** findChild / smoke name for the inner Loader */
    property string loaderObjectName: "operatorGuideLoader"

    readonly property bool open: loader.item ? loader.item.open : false
    readonly property string activeContextId: loader.item ? loader.item.contextId : ""

    /** Optional companion-context switch (e.g. video UI guide ↔ deck-buttons guide). */
    property bool switchButtonVisible: false
    property string switchButtonLabel: ""

    signal switchContextRequested()

    function openGuide(contextId, startIndex) {
        loader.active = true
        // Sync Loader creates the item immediately when active becomes true.
        if (loader.item)
            loader.item.openGuide(contextId || "", startIndex || 0)
    }

    function closeGuide() {
        if (loader.item && loader.item.open)
            loader.item.closeGuide()
        loader.active = false
    }

    Loader {
        id: loader
        objectName: root.loaderObjectName
        anchors.fill: parent
        active: false
        sourceComponent: guideComponent
        onLoaded: {
            if (item) {
                item.closed.connect(function () {
                    loader.active = false
                })
                item.switchContextRequested.connect(root.switchContextRequested)
            }
        }
    }

    Component {
        id: guideComponent
        OperatorGuideOverlay {
            anchors.fill: parent
            switchButtonVisible: root.switchButtonVisible
            switchButtonLabel: root.switchButtonLabel
        }
    }
}
