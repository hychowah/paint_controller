import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../theme"

ColumnLayout {
    id: root
    Layout.fillWidth: true
    spacing: CommonStyle.spacingSm

    // Idle | "success" | "error" — brief post-commit chrome (pure QML).
    property string saveFeedback: ""
    property bool visuallyPressed: false

    readonly property color saveIdleColor: CommonStyle.statusSuccess
    readonly property color saveHoverColor: Qt.lighter(CommonStyle.statusSuccess, 1.08)
    readonly property color savePressedColor: Qt.darker(CommonStyle.statusSuccess, 1.15)
    readonly property color saveSuccessColor: Qt.lighter(CommonStyle.statusSuccess, 1.18)
    readonly property color saveErrorColor: CommonStyle.statusError

    function currentSettingText() {
        if (!root.settingsManager) {
            return root.defaultValue
        }

        var value = root.decimalPlaces === 0
            ? root.settingsManager.getInt(root.settingKey)
            : root.settingsManager.getFloat(root.settingKey)
        return root.decimalPlaces === 0 ? value.toString() : value.toFixed(root.decimalPlaces)
    }

    function refreshDisplayText() {
        inputField.text = root.currentSettingText()
    }

    function showSaveFeedback(success) {
        root.saveFeedback = success ? "success" : "error"
        saveFeedbackTimer.restart()
    }

    // Component properties
    required property string label
    required property string settingKey
    required property var settingsManager
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
        
        // Save button — press linger + success/error result feedback
        Rectangle {
            id: saveButton
            width: root.buttonWidth
            height: root.fieldHeight
            radius: CommonStyle.radiusSm
            color: {
                if (root.saveFeedback === "success")
                    return root.saveSuccessColor
                if (root.saveFeedback === "error")
                    return root.saveErrorColor
                if (root.visuallyPressed)
                    return root.savePressedColor
                if (saveArea.containsMouse)
                    return root.saveHoverColor
                return root.saveIdleColor
            }

            Behavior on color {
                ColorAnimation { duration: CommonStyle.motionFast }
            }

            Text {
                anchors.centerIn: parent
                text: {
                    if (root.saveFeedback === "success")
                        return "Saved ✓"
                    if (root.saveFeedback === "error")
                        return "Failed"
                    return "Save"
                }
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
                onPressed: root.visuallyPressed = true
                onCanceled: {
                    root.visuallyPressed = false
                    pressLingerTimer.stop()
                }
                onClicked: {
                    var num = root.decimalPlaces === 0
                        ? parseInt(inputField.text)
                        : parseFloat(inputField.text)
                    var success = false

                    if (!isNaN(num) && root.settingsManager) {
                        // TD-036: single gated write path (set+persist).
                        if (root.decimalPlaces === 0) {
                            success = root.settingsManager.applyInt(root.settingKey, num)
                        } else {
                            success = root.settingsManager.applyFloat(root.settingKey, num)
                        }
                        // Always refresh so a gate deny restores the truthful value.
                        root.refreshDisplayText()
                    }

                    root.showSaveFeedback(success)
                    // Linger press highlight briefly so a short touch still registers.
                    pressLingerTimer.restart()
                }
            }

            Timer {
                id: pressLingerTimer
                interval: 150
                repeat: false
                onTriggered: root.visuallyPressed = false
            }

            Timer {
                id: saveFeedbackTimer
                interval: 900
                repeat: false
                onTriggered: root.saveFeedback = ""
            }
        }
    }

    Connections {
        target: root.settingsManager

        function onSetting_changed(key, value) {
            if (key === root.settingKey) {
                root.refreshDisplayText()
            }
        }
    }

    Component.onCompleted: root.refreshDisplayText()
}
