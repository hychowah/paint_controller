import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: CommonStyle.spacingSm

    function currentSettingText() {
        if (!settingsManager) {
            return root.defaultValue
        }

        var value = root.decimalPlaces === 0
            ? settingsManager.getInt(root.settingKey)
            : settingsManager.getFloat(root.settingKey)
        return root.decimalPlaces === 0 ? value.toString() : value.toFixed(root.decimalPlaces)
    }

    function refreshDisplayText() {
        inputField.text = root.currentSettingText()
    }
    
    // Component properties
    required property string label
    required property string settingKey
    property int decimalPlaces: 1
    property string unitSuffix: ""
    property string defaultValue: "0"
    required property var numberPadTarget
    property var confirmationPopup: null
    property int fieldHeight: CommonStyle.itemHeight
    property int buttonWidth: Math.round(220 * CommonStyle.scaleFactor)
    
    // Label
    Text {
        text: root.label
        color: CommonStyle.textPrimary
        font.family: CommonStyle.fontSans
        font.pixelSize: CommonStyle.fontCaption
        font.bold: true
    }
    
    // Input row
    RowLayout {
        Layout.fillWidth: true
        spacing: CommonStyle.spacingMd
        
        // Input field
        Rectangle {
            Layout.fillWidth: true
            height: root.fieldHeight
            color: CommonStyle.inputBackground
            border.color: inputField.activeFocus ? CommonStyle.inputFocusBorder : CommonStyle.inputBorder
            border.width: 1
            radius: CommonStyle.radiusSm
            
            TextInput {
                id: inputField
                anchors.fill: parent
                anchors.margins: CommonStyle.spacingMd
                text: root.defaultValue
                color: CommonStyle.textPrimary
                font.family: CommonStyle.fontMono
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
            radius: CommonStyle.radiusSm
            color: saveArea.containsMouse ? Qt.lighter(CommonStyle.statusSuccess, 1.08) : CommonStyle.statusSuccess
            
            Text {
                anchors.centerIn: parent
                text: "Save"
                color: CommonStyle.textStrong
                font.family: CommonStyle.fontSans
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
                        var updated = root.decimalPlaces === 0
                            ? settingsManager.setInt(root.settingKey, num)
                            : settingsManager.setFloat(root.settingKey, num)
                        if (updated) {
                            settingsManager.saveSetting(root.settingKey)
                            root.refreshDisplayText()
                        }
                    }
                }
            }
        }
    }

    Connections {
        target: settingsManager

        function onSetting_changed(key, value) {
            if (key === root.settingKey) {
                root.refreshDisplayText()
            }
        }
    }

    Component.onCompleted: root.refreshDisplayText()
}
