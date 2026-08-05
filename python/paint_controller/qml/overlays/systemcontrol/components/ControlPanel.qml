import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"

Rectangle {
    id: controlPanel
    required property string controlName
    required property string controlStatus
    property bool enabledState: false
    required property string iconText
    property bool selfContained: false
    property string actionKey: ""
    property var legalityModel: null
    property var legality: controlPanel.defaultLegality()
    readonly property bool actionAllowed: !actionKey || !legalityModel || legality.allowed !== false
    readonly property string blockedReason: actionAllowed ? "" : String(legality.reason || "")
    readonly property color baseColor: !actionAllowed
        ? CommonStyle.warningSurface
        : (enabledState ? CommonStyle.cardBackground : CommonStyle.backgroundL1)
    readonly property color baseBorder: !actionAllowed
        ? CommonStyle.statusWarning
        : (enabledState ? CommonStyle.statusSuccess : CommonStyle.inputBorder)
    readonly property color activeAccent: CommonStyle.statusSuccess
    readonly property color inactiveAccent: CommonStyle.textDisabled

    signal clicked()

    function defaultLegality() {
        return {
            "allowed": true,
            "reason": "",
            "title": controlName,
        }
    }

    function refreshLegality() {
        legality = legalityModel && actionKey !== ""
            ? legalityModel.getActionLegality(actionKey)
            : defaultLegality()
    }

    // Layouts size by implicitHeight; keep height in sync for non-layout parents.
    implicitHeight: blockedReason !== "" ? CommonStyle.itemHeight + CommonStyle.spacingLg : CommonStyle.itemHeight
    height: implicitHeight
    implicitWidth: Math.round(200 * CommonStyle.scaleFactor)
    radius: CommonStyle.radiusMd
    color: baseColor
    border.color: baseBorder
    border.width: enabledState && actionAllowed ? CommonStyle.borderWidthThick : 1
    opacity: enabled ? 1.0 : 0.65
    Layout.fillWidth: true
    Layout.preferredHeight: implicitHeight
    Layout.minimumHeight: implicitHeight

    Component.onCompleted: refreshLegality()
    onActionKeyChanged: refreshLegality()
    onLegalityModelChanged: refreshLegality()

    Connections {
        target: legalityModel

        function onLegalityChanged() {
            controlPanel.refreshLegality()
        }
    }

    Behavior on color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }

    Behavior on border.color {
        ColorAnimation { duration: CommonStyle.motionStandard }
    }

    states: [
        State {
            name: "hovered"
            when: panelMouseArea.containsMouse && controlPanel.enabled && controlPanel.actionAllowed && !panelMouseArea.pressed
            PropertyChanges {
                target: controlPanel
                color: controlPanel.enabledState ? CommonStyle.cardBackgroundAlt : CommonStyle.backgroundL2
            }
        },
        State {
            name: "pressed"
            when: panelMouseArea.pressed && controlPanel.enabled && controlPanel.actionAllowed
            PropertyChanges {
                target: controlPanel
                color: CommonStyle.backgroundL1
            }
        }
    ]

    MouseArea {
        id: panelMouseArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: controlPanel.enabled && controlPanel.actionAllowed
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: {
            if (controlPanel.selfContained) {
                controlPanel.enabledState = !controlPanel.enabledState
                controlPanel.controlStatus = controlPanel.enabledState ? "Enabled" : "Disabled"
            }
            controlPanel.clicked()
        }
    }

    RowLayout {
        anchors {
            fill: parent
            margins: CommonStyle.spacingMd
            rightMargin: CommonStyle.spacingLg
        }
        spacing: CommonStyle.spacingMd

        Rectangle {
            Layout.preferredWidth: CommonStyle.controlHeightMd
            Layout.preferredHeight: CommonStyle.controlHeightMd
            Layout.alignment: Qt.AlignVCenter
            radius: width / 2
            color: enabledState ? controlPanel.activeAccent : controlPanel.inactiveAccent

            Text {
                anchors.centerIn: parent
                text: controlPanel.iconText
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                color: CommonStyle.textPrimary
                font.bold: true
            }

            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: Math.max(2, CommonStyle.spacingXs)

            Text {
                Layout.fillWidth: true
                text: controlPanel.controlName
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontBody
                font.bold: true
                color: CommonStyle.textPrimary
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: controlPanel.controlStatus
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption
                color: enabledState ? controlPanel.activeAccent : CommonStyle.textDisabled
                wrapMode: Text.WordWrap
                visible: controlPanel.controlStatus !== ""

                Behavior on color {
                    ColorAnimation { duration: CommonStyle.motionStandard }
                }
            }

            Text {
                Layout.fillWidth: true
                text: controlPanel.blockedReason
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption
                color: CommonStyle.warningText
                wrapMode: Text.WordWrap
                visible: controlPanel.blockedReason !== ""
            }
        }

        Rectangle {
            Layout.preferredWidth: Math.round(52 * CommonStyle.scaleFactor)
            Layout.preferredHeight: Math.round(28 * CommonStyle.scaleFactor)
            Layout.alignment: Qt.AlignVCenter
            radius: height / 2
            color: enabledState ? controlPanel.activeAccent : CommonStyle.backgroundL0
            border.width: 1
            border.color: enabledState ? controlPanel.activeAccent : CommonStyle.borderDefault

            Rectangle {
                width: Math.round(22 * CommonStyle.scaleFactor)
                height: width
                radius: width / 2
                color: CommonStyle.textPrimary
                anchors.verticalCenter: parent.verticalCenter
                x: enabledState ? parent.width - width - 3 : 3

                Behavior on x {
                    NumberAnimation {
                        duration: CommonStyle.motionStandard
                        easing.type: Easing.OutCubic
                    }
                }
            }

            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
            Behavior on border.color {
                ColorAnimation { duration: CommonStyle.motionStandard }
            }
        }
    }
}
