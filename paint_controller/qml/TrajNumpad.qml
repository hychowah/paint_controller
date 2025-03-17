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

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "0" ? "#ff0000" : "#000000"

                    Text {
                        text: "0"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "0"
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "0"
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "0"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "1" ? "#ff0000" : "#000000"

                    Text {
                        text: "1"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "1";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "1";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "1"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "2" ? "#ff0000" : "#000000"

                    Text {
                        text: "2"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "2";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "2";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "2"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "3" ? "#ff0000" : "#000000"

                    Text {
                        text: "3"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "3";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "3";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "3"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "4" ? "#ff0000" : "#000000"

                    Text {
                        text: "4"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "4";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "4";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "4"
                        }
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: parent.height / 2
                spacing: 40

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "5" ? "#ff0000" : "#000000"

                    Text {
                        text: "5"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "5";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "5";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "5"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "6" ? "#ff0000" : "#000000"

                    Text {
                        text: "6"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "6";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "6";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "6"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "7" ? "#ff0000" : "#000000"

                    Text {
                        text: "7"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "7";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "7";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "7"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "8" ? "#ff0000" : "#000000"

                    Text {
                        text: "8"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "8";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "8";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "8"
                        }
                    }
                }

                Rectangle {
                    width: 40
                    height: 40
                    color: "#d8d8d8"
                    radius: 20
                    border.color: trajectoryNumpads.lastClickedButton === "9" ? "#ff0000" : "#000000"

                    Text {
                        text: "9"
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
                                    var newInput = sequence.get(selectedInputField.itemInx).input1.toString() + "9";
                                    sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                                }
                                else {
                                    var newInput = sequence.get(selectedInputField.itemInx).input2.toString() + "9";
                                    sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                                }
                            }
                            trajectoryNumpads.lastClickedButton = "9"
                        }
                    }
                }
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
                        if(selectedInputField.inputInx === 0) {
                            var newInput = sequence.get(selectedInputField.itemInx).input1.toString();
                            if(newInput.length > 1) {
                                newInput = newInput.substring(0, newInput.length - 1);
                            }
                            else if(newInput.length == 1) {
                                newInput = "0";
                            }
                            sequence.setProperty(selectedInputField.itemInx, "input1", parseInt(newInput));
                        }
                        else {
                            var newInput = sequence.get(selectedInputField.itemInx).input2.toString();
                            if(newInput.length > 1) {
                                newInput = newInput.substring(0, newInput.length - 1);
                            }
                            else if(newInput.length == 1) {
                                newInput = "0";
                            }
                            sequence.setProperty(selectedInputField.itemInx, "input2", parseInt(newInput));
                        }
                    }
                    trajectoryNumpads.lastClickedButton = "del"
                }
            }
        }
    }
}