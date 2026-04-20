// Monospace label for numerical data to prevent layout shift
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"

RowLayout {
    id: root
    
    // Properties
    property string label: ""
    property string value: "0.0"
    property string unit: ""
    property color valueColor: CommonStyle.textPrimary
    property color labelColor: CommonStyle.textSecondary
    property int valueFontSize: CommonStyle.fontBody
    property int labelFontSize: CommonStyle.fontCaption
    
    spacing: CommonStyle.spacingXs
    
    // Label text
    Text {
        visible: label !== ""
        text: label
        font.pixelSize: labelFontSize
        font.family: CommonStyle.fontSans
        color: labelColor
    }
    
    // Value (monospace)
    Text {
        text: value
        font.pixelSize: valueFontSize
        font.family: CommonStyle.fontMono
        font.bold: true
        color: valueColor
    }
    
    // Unit
    Text {
        visible: unit !== ""
        text: unit
        font.pixelSize: labelFontSize
        font.family: CommonStyle.fontSans
        color: labelColor
    }
}
