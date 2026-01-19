// MetricValue - Reusable centered label/value/unit display
import QtQuick 2.15
import QtQuick.Layouts 1.15

ColumnLayout {
    id: root
    
    // Required properties
    property string label: "Label"
    property string value: "0.0"
    property string unit: ""
    
    // Optional styling
    property color valueColor: "#3498db"
    property int labelFontSize: 13
    property int valueFontSize: 34
    property int unitFontSize: 12
    property int itemSpacing: 4
    
    spacing: itemSpacing
    
    Text {
        text: root.label
        font.pixelSize: root.labelFontSize
        font.family: "Roboto"
        color: "#AAAAAA"
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
    
    Text {
        text: root.value
        font.pixelSize: root.valueFontSize
        font.family: "Monospace"
        font.bold: true
        color: root.valueColor
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
    
    Text {
        visible: root.unit !== ""
        text: root.unit
        font.pixelSize: root.unitFontSize
        font.family: "Roboto"
        color: "#AAAAAA"
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
}
