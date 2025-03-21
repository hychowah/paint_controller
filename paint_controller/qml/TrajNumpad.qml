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
                    if(selectedInputField.inputInx === 0) {
                        var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + inputChar;
                        sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                    }
                    else if(selectedInputField.inputInx === 1) {
                        var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + inputChar;
                        sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                    }
                    else if(selectedInputField.inputInx === 2) {
                        var newInput = sequence.get(selectedInputField.itemInx).input3.toString() + inputChar;
                        sequence.setProperty(selectedInputField.itemInx, "input3", parseInt(newInput));
                    }
                    else if(selectedInputField.inputInx === 3) {
                        var newInput = sequence.get(selectedInputField.itemInx).input4.toString() + inputChar;
                        sequence.setProperty(selectedInputField.itemInx, "input4", parseInt(newInput));
                    }
                }
                trajectoryNumpads.lastClickedButton = inputChar
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


                function deleteChar(inputField) {
                    var newInput = sequence.get(selectedInputField.itemInx)[inputField].toString();
                    if(newInput.length > 1) {
                        newInput = newInput.substring(0, newInput.length - 1);
                    }
                    else if(newInput.length == 1) {
                        newInput = "0";
                    }
                    sequence.setProperty(selectedInputField.itemInx, inputField, parseInt(newInput));
                }

                onClicked: {
                    if(selectedInputField.itemInx != -1 && selectedInputField.inputInx != -1) {
                        if(selectedInputField.inputInx === 0) {
                            deleteChar("input1");
                        }
                        else if(selectedInputField.inputInx === 1) {
                            deleteChar("input2");
                        }
                        else if(selectedInputField.inputInx === 2) {
                            deleteChar("input3");
                        }
                        else if(selectedInputField.inputInx === 3) {
                            deleteChar("input4");
                        }
                    }
                    trajectoryNumpads.lastClickedButton = "del"
                }
            }
        }
    }
}