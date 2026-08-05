// SettingsSection.qml - Collapsible section for settings / device panels
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"

Rectangle {
    id: settingsSection

    required property string title
    required property var settingsManager
    property string description: ""
    property string sectionId: ""
    property bool defaultExpanded: true
    property bool expanded: defaultExpanded
    property bool _sectionStateReady: false
    property alias contentItem: contentLoader.sourceComponent

    // Content measurement must not rely on Layout-only height (often 0).
    readonly property real contentPadding: CommonStyle.spacingMd + CommonStyle.spacingLg
    readonly property real measuredContentHeight: {
        if (!contentLoader.item)
            return CommonStyle.spacingXl
        var item = contentLoader.item
        var h = Math.max(item.implicitHeight, item.childrenRect.height)
        if (h <= 0)
            h = CommonStyle.spacingXl
        return h + contentPadding
    }
    readonly property real headerHeight: description !== ""
        ? Math.round(56 * CommonStyle.scaleFactor)
        : Math.round(48 * CommonStyle.scaleFactor)
    readonly property real bodyHeight: expanded ? measuredContentHeight : 0

    // ColumnLayout sizes children by implicitHeight, not height.
    implicitWidth: parent ? parent.width : Math.round(400 * CommonStyle.scaleFactor)
    implicitHeight: headerHeight + bodyHeight
    width: implicitWidth
    height: implicitHeight
    clip: true

    color: expanded ? CommonStyle.cardBackground : CommonStyle.backgroundL1
    border.color: expanded ? CommonStyle.accentPrimary : CommonStyle.borderDefault
    border.width: expanded ? CommonStyle.borderWidthThick : CommonStyle.borderWidthThin
    radius: CommonStyle.radiusMd

    Behavior on implicitHeight {
        NumberAnimation {
            duration: CommonStyle.motionStandard
            easing.type: Easing.InOutQuad
        }
    }

    Behavior on color {
        ColorAnimation { duration: CommonStyle.motionFast }
    }

    Behavior on border.color {
        ColorAnimation { duration: CommonStyle.motionFast }
    }

    Component.onCompleted: {
        if (sectionId !== "" && settingsSection.settingsManager) {
            expanded = settingsSection.settingsManager.getSectionExpanded(
                sectionId, settingsSection.defaultExpanded)
        } else {
            expanded = settingsSection.defaultExpanded
        }
        _sectionStateReady = true
    }

    onExpandedChanged: {
        if (!settingsSection._sectionStateReady)
            return
        if (sectionId !== "" && settingsSection.settingsManager) {
            settingsSection.settingsManager.setSectionExpanded(sectionId, expanded)
        }
    }

    // Header
    Item {
        id: headerContainer
        width: parent.width
        height: settingsSection.headerHeight
        z: 1

        Rectangle {
            anchors.fill: parent
            color: headerMouse.containsMouse ? CommonStyle.backgroundL2 : "transparent"
            radius: settingsSection.radius
            Behavior on color { ColorAnimation { duration: CommonStyle.motionFast } }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: CommonStyle.spacingMd
            anchors.rightMargin: CommonStyle.spacingMd
            spacing: CommonStyle.spacingMd

            // Chevron chip — strong expand affordance
            Rectangle {
                Layout.preferredWidth: Math.round(28 * CommonStyle.scaleFactor)
                Layout.preferredHeight: Math.round(28 * CommonStyle.scaleFactor)
                Layout.alignment: Qt.AlignVCenter
                radius: CommonStyle.radiusSm
                color: expanded ? CommonStyle.accentPrimary : CommonStyle.backgroundL2
                border.color: expanded ? CommonStyle.accentPrimary : CommonStyle.borderDefault
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: expanded ? "▾" : "▸"
                    color: expanded ? CommonStyle.textOnPrimary : CommonStyle.textSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 1

                Text {
                    Layout.fillWidth: true
                    text: settingsSection.title
                    color: CommonStyle.textPrimary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody
                    font.bold: true
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    visible: settingsSection.description !== ""
                    text: settingsSection.description
                    color: CommonStyle.textDisabled
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption
                    elide: Text.ElideRight
                }
            }

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: expanded ? "Hide" : "Show"
                color: CommonStyle.accentMuted
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption
                font.bold: true
            }
        }

        MouseArea {
            id: headerMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: settingsSection.expanded = !settingsSection.expanded
        }

        Rectangle {
            visible: expanded
            anchors.bottom: parent.bottom
            width: parent.width - CommonStyle.spacingLg
            height: 1
            color: CommonStyle.inputBorder
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    // Content
    Item {
        id: contentContainer
        anchors.top: headerContainer.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: settingsSection.bodyHeight
        clip: true
        visible: height > 0
        opacity: expanded ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation { duration: CommonStyle.motionFast }
        }

        Loader {
            id: contentLoader
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.leftMargin: CommonStyle.spacingMd
            anchors.rightMargin: CommonStyle.spacingMd
            anchors.topMargin: CommonStyle.spacingSm
            active: true
            // Width must be set before content measures itself
            width: parent.width - CommonStyle.spacingMd * 2
        }
    }
}
