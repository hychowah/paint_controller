// TrajNumpad.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../core"
import "../buttons"

Rectangle {
    id: workFlowNumpads
    color: CommonStyle.sidebarButtonSelected
    radius: CommonStyle.radiusMd
    border.color: CommonStyle.borderDefault
    border.width: 1

    property string lastClickedButton: "del"
    property var selectedInputField
    property var sequence

    // Helper functions
    function getCurrentValue(itemIndex, inputField) {
        if (itemIndex < 0 || !sequence || sequence.count <= itemIndex) {
            return "";
        }
        
        var item = sequence.get(itemIndex);
        if (!item || item[inputField] === undefined) {
            return "";
        }
        
        var value = item[inputField];
        if (value === null || value === "-1" || value === "") {
            return "0";
        }
        
        return value.toString();
    }

    function updateValue(itemIndex, inputField, value) {
        if (itemIndex < 0 || !sequence || sequence.count <= itemIndex) {
            return;
        }
        
        // console.log("Setting " + inputField + " to: " + value);
        sequence.setProperty(itemIndex, inputField, value);
    }

    function handleNumpadClick(buttonValue) {
        if (selectedInputField.itemInx === -1 || selectedInputField.inputInx === -1) {
            return;
        }
        
        var inputField;
        // Support for up to 6 input fields
        if (selectedInputField.inputInx === 0) {
            inputField = "input1";
        } else if (selectedInputField.inputInx === 1) {
            inputField = "input2";
        } else if (selectedInputField.inputInx === 2) {
            inputField = "input3";
        } else if (selectedInputField.inputInx === 3) {
            inputField = "input4";
        } else if (selectedInputField.inputInx === 4) {
            inputField = "input5";
        } else if (selectedInputField.inputInx === 5) {
            inputField = "input6";
        } else {
            return;
        }
        
        var currentValue = getCurrentValue(selectedInputField.itemInx, inputField);
        
        if (buttonValue === "del") {
            var newValue;
            if (currentValue.length > 1) {
                newValue = currentValue.substring(0, currentValue.length - 1);
            } else {
                newValue = "0";
            }
            updateValue(selectedInputField.itemInx, inputField, newValue);
        } else {
            // If current value is 0, replace it
            if (currentValue === "0") {
                currentValue = "";
            }
            
            updateValue(selectedInputField.itemInx, inputField, currentValue + buttonValue);
        }
        
        workFlowNumpads.lastClickedButton = buttonValue;
    }

    // Create a button with consistent styling
    component NumpadButton: Button {
        property string numValue: ""
        
        Layout.fillWidth: true
        Layout.fillHeight: true
        text: numValue
        enabled: selectedInputField.itemInx !== -1 && selectedInputField.inputInx !== -1
        
        background: Rectangle {
            color: parent.down ? Qt.lighter(CommonStyle.accentPrimary, 1.7) : CommonStyle.textPrimary
            radius: CommonStyle.radiusSm
            border.width: workFlowNumpads.lastClickedButton === numValue ? 2 : 1
            border.color: workFlowNumpads.lastClickedButton === numValue ? CommonStyle.accentPrimary : CommonStyle.borderDefault
        }
        
        contentItem: Text {
            text: parent.text
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.fontBody + 2
            font.bold: true
            color: parent.enabled ? CommonStyle.textStrong : CommonStyle.textDisabled
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        onClicked: handleNumpadClick(numValue)
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: CommonStyle.spacingXs + 1
        spacing: CommonStyle.spacingXs + 1

        // Numbers grid
        GridLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            columns: 5
            rowSpacing: CommonStyle.spacingXs + 1
            columnSpacing: CommonStyle.spacingXs + 1

            // Row 1: 1-5
            NumpadButton { numValue: "1" }
            NumpadButton { numValue: "2" }
            NumpadButton { numValue: "3" }
            NumpadButton { numValue: "4" }
            NumpadButton { numValue: "5" }
            
            // Row 2: 6-9 and 0 under 5
            NumpadButton { numValue: "6" }
            NumpadButton { numValue: "7" }
            NumpadButton { numValue: "8" }
            NumpadButton { numValue: "9" }
            NumpadButton { numValue: "0" }
        }
        
        // Delete button on right side
        Button {
            Layout.fillHeight: true
            Layout.preferredWidth: height * 0.8
            text: "⌫"
            enabled: selectedInputField.itemInx !== -1 && selectedInputField.inputInx !== -1
            
            background: Rectangle {
                color: parent.down ? Qt.lighter(CommonStyle.accentPrimary, 1.7) : CommonStyle.textPrimary
                radius: CommonStyle.radiusSm
                border.width: workFlowNumpads.lastClickedButton === "del" ? 2 : 1
                border.color: workFlowNumpads.lastClickedButton === "del" ? CommonStyle.accentPrimary : CommonStyle.borderDefault
            }
            
            contentItem: Text {
                text: parent.text
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontDisplay
                font.bold: true
                color: parent.enabled ? CommonStyle.textStrong : CommonStyle.textDisabled
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            onClicked: handleNumpadClick("del")
        }
    }
}