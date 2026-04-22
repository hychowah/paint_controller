import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"

// Reusable metric panel component
Rectangle {
    id: metricPanel
    Layout.fillWidth: true
    Layout.preferredHeight: 75
    color: CommonStyle.cardBackgroundAlt
    radius: CommonStyle.radiusMd
    border.color: CommonStyle.cardBorder
    border.width: CommonStyle.borderWidthThin
    
    required property string title
    required property real value
    property string unit: ""
    required property real maxValue
    property color barColor: CommonStyle.accentPrimary
    property int decimalPlaces: 3
    readonly property real normalizedValue: maxValue > 0 ? Math.min(Math.abs(Number(value)) / maxValue, 1) : 0
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingSm + 2
        spacing: CommonStyle.spacingXs
        
        Label {
            text: title
            font.pixelSize: CommonStyle.fontBody
            font.family: CommonStyle.fontSans
            font.bold: true
            color: CommonStyle.textSecondary
        }
        
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            Label {
                text: Number(value).toFixed(decimalPlaces)  // Using the property
                font.pixelSize: CommonStyle.fontDisplay + CommonStyle.spacingXs
                font.family: CommonStyle.fontMono
                font.bold: true
                color: CommonStyle.textPrimary
                Layout.alignment: Qt.AlignVCenter
            }
            
            Label {
                text: unit
                font.pixelSize: CommonStyle.fontBody
                font.family: CommonStyle.fontSans
                color: CommonStyle.textSecondary
                Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                Layout.bottomMargin: 3
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 6
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 10
                radius: 3
                color: CommonStyle.inputBackground
                
                Rectangle {
                    width: parent.width * metricPanel.normalizedValue
                    height: parent.height
                    color: barColor
                    radius: 3
                }
            }
        }
    }
}