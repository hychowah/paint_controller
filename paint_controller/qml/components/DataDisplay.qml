import QtQuick 2.15
import QtQuick.Layouts 1.15
import "../"

Rectangle {
    id: root
    property string title: "WHEEL SPEED"
    property string unit: "RPM"
    property real value: 0
    property string valueSource: ""
    property color backgroundColor: "#E2E2E2"
    property color lineColor: "blue"
    property real maxAbsValue: 40
    property real titleFontSize: 22
    property real valueFontSize: 40
    property real unitFontSize: 16

    Layout.fillWidth: true
    Layout.preferredHeight: 150 // Default height, can be overridden
    color: backgroundColor
    radius: 10
    border.width: 2

    Text {
        id: valueTitle
        text: root.title
        font.bold: true
        font.pixelSize: titleFontSize
        color: "#000000"
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 10
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
        color: "#000000"
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.rightMargin: 50
    }

    Text {
        id: unitText
        text: unit
        font.pixelSize: unitFontSize
        color: "#000000"
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