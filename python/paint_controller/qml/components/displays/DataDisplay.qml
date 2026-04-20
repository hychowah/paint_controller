import QtQuick
import QtQuick.Layouts
import "../../core"
import "."

Rectangle {
    id: root
    property string title: "WHEEL SPEED"
    property string unit: "RPM"
    property real value: 0
    property string valueSource: ""
    property color backgroundColor: CommonStyle.cardBackgroundAlt
    property color lineColor: CommonStyle.accentPrimary
    property real maxAbsValue: 40
    property real titleFontSize: CommonStyle.fontHeading + 2
    property real valueFontSize: CommonStyle.fontDisplay + CommonStyle.spacingLg
    property real unitFontSize: CommonStyle.fontBody

    Layout.fillWidth: true
    Layout.preferredHeight: 150 // Default height, can be overridden
    color: backgroundColor
    radius: CommonStyle.radiusMd
    border.width: CommonStyle.borderWidthThick
    border.color: CommonStyle.cardBorder

    Text {
        id: valueTitle
        text: root.title
        font.bold: true
        font.pixelSize: titleFontSize
        font.family: CommonStyle.fontSans
        color: CommonStyle.textPrimary
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: CommonStyle.spacingSm + 2
    }

    LineGraph {
        id: valueGraph
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: valueTitle.bottom
        anchors.bottom: valueText.top
        anchors.margins: 0
        maxAbsValue: root.maxAbsValue
        lineColor: root.lineColor
    }

    Text {
        id: valueText
        text: root.value.toFixed(1)
        font.pixelSize: valueFontSize
        font.family: CommonStyle.fontMono
        color: CommonStyle.textPrimary
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: 50
    }

    Text {
        id: unitText
        text: unit
        font.pixelSize: unitFontSize
        font.family: CommonStyle.fontSans
        color: CommonStyle.textSecondary
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.margins: 5
    }

    Timer {
        interval: 100  // Update every 100ms
        running: true
        repeat: true
        onTriggered: {
            valueGraph.addDataPoint(root.value);
        }
    }
}