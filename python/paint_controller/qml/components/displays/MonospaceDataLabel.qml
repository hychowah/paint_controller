// Monospace label for numerical data to prevent layout shift
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: root
    
    // Properties
    property string label: ""
    property string value: "0.0"
    property string unit: ""
    property color valueColor: "#FFFFFF"
    property color labelColor: "#AAAAAA"
    property int valueFontSize: 16
    property int labelFontSize: 12
    
    spacing: 6
    
    // Label text
    Text {
        visible: label !== ""
        text: label
        font.pixelSize: labelFontSize
        font.family: "Roboto"
        color: labelColor
    }
    
    // Value (monospace)
    Text {
        text: value
        font.pixelSize: valueFontSize
        font.family: "Monospace"
        font.bold: true
        color: valueColor
    }
    
    // Unit
    Text {
        visible: unit !== ""
        text: unit
        font.pixelSize: labelFontSize
        font.family: "Roboto"
        color: labelColor
    }
}
