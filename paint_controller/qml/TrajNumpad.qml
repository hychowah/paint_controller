// TrajNumpad.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: trajectoryNumpads
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1

    property string lastClickedButton: "del"
    property var selectedInputField
    property var sequence

    // Helper function to get current value or empty string if invalid
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

    // Helper function to update a value in the model
    function updateValue(itemIndex, inputField, value) {
        if (itemIndex < 0 || !sequence || sequence.count <= itemIndex) {
            return;
        }
        
        console.log("Setting " + inputField + " to: " + value);
        sequence.setProperty(itemIndex, inputField, value);
    }

    component NumpadRect: Rectangle {
        property string inputChar: ""
        width: 40
        height: 40
        color: "#d8d8d8"
        radius: 20
        border.color: trajectoryNumpads.lastClickedButton === inputChar ? "#ff0000" : "#000000"

        Text {
            text: inputChar
            anchors.centerIn: parent
            anchors.horizontalCenter: parent.horizontalCenter
            color: selectedInputField.itemInx != -1 && selectedInputField.inputInx != -1 ? "#000000" : "#b3b3b3"
            font.pixelSize: 15
            font.bold: true
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                if(selectedInputField.itemInx != -1 && selectedInputField.inputInx != -1) {
                    var inputField;
                    
                    if(selectedInputField.inputInx === 0) {
                        inputField = "input1";
                    } else if(selectedInputField.inputInx === 1) {
                        inputField = "input2";
                    } else if(selectedInputField.inputInx === 2) {
                        inputField = "input3";
                    } else if(selectedInputField.inputInx === 3) {
                        inputField = "input4";
                    } else {
                        return;
                    }
                    
                    var currentValue = getCurrentValue(selectedInputField.itemInx, inputField);
                    // If current value is 0, replace it
                    if (currentValue === "0") {
                        currentValue = "";
                    }
                    
                    var newValue = currentValue + inputChar;
                    updateValue(selectedInputField.itemInx, inputField, newValue);
                }
                trajectoryNumpads.lastClickedButton = inputChar;
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 10
        anchors.margins: 10

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: parent.height / 2
                spacing: 40

                NumpadRect { inputChar: "0" }
                NumpadRect { inputChar: "1" }
                NumpadRect { inputChar: "2" }
                NumpadRect { inputChar: "3" }
                NumpadRect { inputChar: "4" }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: parent.height / 2
                spacing: 40

                NumpadRect { inputChar: "5" }
                NumpadRect { inputChar: "6" }
                NumpadRect { inputChar: "7" }
                NumpadRect { inputChar: "8" }
                NumpadRect { inputChar: "9" }
            }
        }

        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 70
            color: "#d8d8d8"
            border.color: trajectoryNumpads.lastClickedButton === "del" ? "#ff0000" : "#000000"
            radius: 5

            Text {
                text: "⌫"
                anchors.centerIn: parent
                anchors.horizontalCenter: parent.horizontalCenter
                color: selectedInputField.itemInx != -1 && selectedInputField.inputInx != -1 ? "#000000" : "#b3b3b3"
                font.pixelSize: 30
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if(selectedInputField.itemInx != -1 && selectedInputField.inputInx != -1) {
                        var inputField;
                        
                        if(selectedInputField.inputInx === 0) {
                            inputField = "input1";
                        } else if(selectedInputField.inputInx === 1) {
                            inputField = "input2";
                        } else if(selectedInputField.inputInx === 2) {
                            inputField = "input3";
                        } else if(selectedInputField.inputInx === 3) {
                            inputField = "input4";
                        } else {
                            return;
                        }
                        
                        var currentValue = getCurrentValue(selectedInputField.itemInx, inputField);
                        var newValue;
                        
                        if (currentValue.length > 1) {
                            newValue = currentValue.substring(0, currentValue.length - 1);
                        } else {
                            newValue = "0";
                        }
                        
                        updateValue(selectedInputField.itemInx, inputField, newValue);
                    }
                    trajectoryNumpads.lastClickedButton = "del";
                }
            }
        }
    }
}