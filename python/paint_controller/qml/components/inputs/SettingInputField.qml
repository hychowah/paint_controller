import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: 8
    
    // Component properties
    property string label: ""
    property string settingKey: ""
    property int decimalPlaces: 1
    property string unitSuffix: ""
    property string defaultValue: "0"
    property var numberPadTarget: null
    property var confirmationPopup: null
    property int fieldHeight: 60  // Configurable height for input and button
    property int buttonWidth: 220  // Configurable width for save button
    
    // Label
    Text {
        text: root.label
        color: "#FFFFFF"
        font.pixelSize: 13
        font.bold: true
    }
    
    // Input row
    RowLayout {
        Layout.fillWidth: true
        spacing: 10
        
        // Input field
        Rectangle {
            Layout.fillWidth: true
            height: root.fieldHeight
            color: "#1A1A1A"
            border.color: inputField.activeFocus ? "#3A5A8C" : "#333333"
            border.width: 1
            radius: 6
            
            TextInput {
                id: inputField
                anchors.fill: parent
                anchors.margins: 10
                text: {
                    if (!settingsManager) return root.defaultValue
                    var value = settingsManager[root.settingKey]
                    if (value === undefined || value === null) return root.defaultValue
                    return root.decimalPlaces === 0 ? value.toString() : value.toFixed(root.decimalPlaces)
                }
                color: "#FFFFFF"
                font.pixelSize: Math.max(14, root.fieldHeight * 0.35)
                verticalAlignment: TextInput.AlignVCenter
                horizontalAlignment: TextInput.AlignRight
                readOnly: true  // Prevent keyboard, only use numberPad
            }
            
            // MouseArea to require explicit click to open numberPad
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    inputField.forceActiveFocus()
                    if (root.numberPadTarget) {
                        root.numberPadTarget.targetField = inputField
                        root.numberPadTarget.open()
                    }
                }
            }
        }
        
        // Save button
        Rectangle {
            width: root.buttonWidth
            height: root.fieldHeight
            radius: 6
            color: saveArea.containsMouse ? "#4CAF50" : "#3A8F3A"
            
            Text {
                anchors.centerIn: parent
                text: "Save"
                color: "#FFFFFF"
                font.pixelSize: Math.max(12, root.fieldHeight * 0.30)
                font.bold: true
            }
            
            MouseArea {
                id: saveArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    var num = root.decimalPlaces === 0 ? 
                        parseInt(inputField.text) : 
                        parseFloat(inputField.text)
                    
                    if (!isNaN(num) && settingsManager) {
                        settingsManager[root.settingKey] = num
                        settingsManager.saveSetting(root.settingKey)
                    }
                }
            }
        }
    }
}
