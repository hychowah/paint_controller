import QtQuick
import "../../theme"

/**
 * Spotlight ring for an operator-guide step anchor.
 * Parent coordinate space is the full video workspace.
 */
Item {
    id: root

    property real relX: 0
    property real relY: 0
    property real relW: 0.1
    property real relH: 0.1
    property color ringColor: CommonStyle.accentSecondary
    property real ringWidth: CommonStyle.borderWidthThick
    property bool active: true

    x: parent ? parent.width * relX : 0
    y: parent ? parent.height * relY : 0
    width: parent ? parent.width * relW : 0
    height: parent ? parent.height * relH : 0
    visible: active
    opacity: active ? 1 : 0

    Behavior on x { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }
    Behavior on y { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }
    Behavior on width { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }
    Behavior on height { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: CommonStyle.motionFast } }

    Rectangle {
        id: ring
        anchors.fill: parent
        anchors.margins: -4
        radius: CommonStyle.radiusMd
        color: "transparent"
        border.color: root.ringColor
        border.width: root.ringWidth

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: parent.radius + 2
            color: "transparent"
            border.color: root.ringColor
            border.width: CommonStyle.borderWidthThin
            opacity: 0.35
        }
    }

    // No perpetual animation — keeps scene-graph quiet during video chrome swaps.
}

