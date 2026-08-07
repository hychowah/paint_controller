import QtQuick
import QtQuick.Layouts
import "../../theme"

/**
 * Instruction bubble for the operator guide carousel.
 */
Rectangle {
    id: root

    property string title: ""
    property string body: ""
    /** Optional hardware-button label (e.g. "L1", "A ×2") for non-UI steps. */
    property string badge: ""

    width: Math.min(Math.round(parent ? parent.width * 0.48 : 400), Math.round(460 * CommonStyle.scaleFactor))
    height: contentCol.implicitHeight + CommonStyle.spacingXl
    radius: CommonStyle.radiusMd
    color: CommonStyle.videoSurfaceStrong
    border.color: CommonStyle.accentPrimary
    border.width: CommonStyle.borderWidthThick
    antialiasing: true

    Behavior on x { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }
    Behavior on y { NumberAnimation { duration: CommonStyle.motionStandard; easing.type: Easing.OutCubic } }

    ColumnLayout {
        id: contentCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: CommonStyle.spacingMd
        spacing: CommonStyle.spacingSm

        Rectangle {
            visible: root.badge.length > 0
            Layout.preferredHeight: Math.round(28 * CommonStyle.scaleFactor)
            Layout.preferredWidth: badgeLabel.implicitWidth + CommonStyle.spacingLg
            radius: CommonStyle.radiusSm
            color: CommonStyle.backgroundL2
            border.color: CommonStyle.accentSecondary
            border.width: CommonStyle.borderWidthThin

            Text {
                id: badgeLabel
                anchors.centerIn: parent
                text: root.badge
                color: CommonStyle.accentSecondary
                font.family: CommonStyle.fontMono
                font.pixelSize: CommonStyle.fontCaption
                font.bold: true
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.title
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontBody
            font.bold: true
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            text: root.body
            color: CommonStyle.textSecondary
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontCaption
            wrapMode: Text.WordWrap
            lineHeight: 1.25
        }
    }
}
