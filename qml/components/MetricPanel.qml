import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../"

// Reusable metric panel component
Rectangle {
    id: metricPanel
    Layout.fillWidth: true
    Layout.preferredHeight: 75
    color: "#F5F5F5"
    radius: 10
    
    // Properties that can be set from outside
    property string title: "METRIC"
    property double value: 0
    property string unit: ""
    property double maxValue: 1
    property color barColor: "#2196F3"
    property int decimalPlaces: 3  // New property for decimal places
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 4
        
        Label {
            text: title
            font.pixelSize: 14
            font.bold: true
            color: "#555555"
        }
        
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            
            Label {
                text: Number(value).toFixed(decimalPlaces)  // Using the property
                font.pixelSize: 28
                font.bold: true
                Layout.alignment: Qt.AlignVCenter
            }
            
            Label {
                text: unit
                font.pixelSize: 14
                color: "#777777"
                Layout.alignment: Qt.AlignVCenter | Qt.AlignBottom
                Layout.bottomMargin: 3
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 6
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 10
                radius: 3
                
                Rectangle {
                    width: parent.width * Math.min(Math.abs(Number(value)) / maxValue, 1)
                    height: parent.height
                    color: barColor
                    radius: 3
                }
            }
        }
    }
}