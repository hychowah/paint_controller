// MetricValue - Reusable centered label/value/unit display
import QtQuick
import QtQuick.Layouts
import "../../../core"

ColumnLayout {
    id: root
    
    required property string label
    required property string value
    property string unit: ""
    
    // Optional styling
    property color valueColor: CommonStyle.accentPrimary
    property color labelColor: CommonStyle.textSecondary
    property int labelFontSize: CommonStyle.fontCaption
    property int valueFontSize: CommonStyle.fontDisplay
    property int unitFontSize: CommonStyle.fontLabel
    property int itemSpacing: CommonStyle.spacingXs
    
    spacing: itemSpacing
    
    Text {
        text: root.label
        font.pixelSize: root.labelFontSize
        font.family: CommonStyle.fontSans
        color: root.labelColor
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
    
    Text {
        text: root.value
        font.pixelSize: root.valueFontSize
        font.family: CommonStyle.fontMono
        font.bold: true
        color: root.valueColor
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
    
    Text {
        visible: root.unit !== ""
        text: root.unit
        font.pixelSize: root.unitFontSize
        font.family: CommonStyle.fontSans
        color: root.labelColor
        horizontalAlignment: Text.AlignHCenter
        Layout.alignment: Qt.AlignHCenter
    }
}
