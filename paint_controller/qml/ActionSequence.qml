// ActionSequence.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: actionSequence
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1

    property var sequence
    property var selectedInputField
    property var currentSeq

    property var itemInx
    property var inputInx

    signal saveSequence

    KeyboardPopup {
        id: keyboardPopup
        anchors.centerIn: parent
        
        onTextUpdated: {
            // Update main text when keyboard text changes
            currentSeq.seqName = newText
        }
        
        onClosed: {
            // Optional: Sync final text when popup closes
            currentSeq.seqName = keyboardPopup.currentText
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            height: 60
            spacing: 10
            
            // action item title
            Text {
                text: "Sequence"
                font.pixelSize: 20
                font.bold: true
                Layout.rightMargin: 40
            }

            Text {
                text: "Name:"
            }

            Button {
                text: currentSeq.seqName
                Layout.preferredWidth: 100
                onClicked: {
                    keyboardPopup.currentText = currentSeq.seqName
                    keyboardPopup.open()
                }
            }

            Button {
                text: "Save"
                Layout.preferredWidth: 60
                onClicked: {
                    saveSequence()
                }
            }
        }
        

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#E0E0E0"
            clip: true

            ListView {
                anchors.fill: parent
                model: actionSequence.sequence
                width: parent.width

                delegate: Item {
                    width: parent.width
                    height: (model.id === "4" || model.id === "5") ? 250 : 150
                    
                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10
                        anchors.margins: 10
                        width: parent.width
                        height: parent.height
                        
                        Rectangle {
                            width: parent.width
                            height: (model.id === "4" || model.id === "5") ? 200 : 120
                            color: Qt.rgba(255, 255, 255, 0.5)
                            radius: 20
                            border.color: "#000000"


                            RowLayout {
                                anchors.fill: parent
                                spacing: 10
                                anchors.margins: 10

                                ColumnLayout {
                                    Layout.fillHeight: true
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignVCenter
                                    spacing: 10
                                    //anchors.margins: 10
                                    //width: parent.width
                                    //height: parent.height

                                    Text {
                                        text: model.title
                                        font.pixelSize: 20
                                        font.bold: true
                                        Layout.alignment: Qt.AlignVCenter
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.alignment: Qt.AlignVCenter
                                        spacing: 20
                                        anchors.margins: 10
                                        width: parent.width
                                        height: parent.height
                                        opacity: (model.id === "3" || model.id === "6") ? 0 : 1
                                        enabled: model.id !== "3" && model.id !== "6"

                                        ColumnLayout {
                                            Layout.fillHeight: true
                                            Layout.alignment: Qt.AlignVCenter

                                            Text {
                                                text: (model.id === "4" || model.id === "5") ? "W_Length" : "Length"
                                                Layout.preferredWidth: 40
                                            }

                                            Button {
                                                text: model.input1
                                                Layout.preferredWidth: 60
                                                background: Rectangle {
                                                    color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 0) ? "#58ff86" : "white"
                                                }
                                                onClicked: {
                                                    selectedInputField.itemInx = index
                                                    selectedInputField.inputInx = 0
                                                }
                                            }
                                        }

                                        ColumnLayout {
                                            Layout.fillHeight: true
                                            Layout.alignment: Qt.AlignVCenter

                                            Text {
                                                text: (model.id === "4" || model.id === "5") ? "W_Speed" : "Speed"
                                                Layout.preferredWidth: 40
                                            }

                                            Button {
                                                text: model.input2
                                                Layout.preferredWidth: 60
                                                background: Rectangle {
                                                    color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 1) ? "#58ff86" : "white"
                                                }
                                                onClicked: {
                                                    selectedInputField.itemInx = index
                                                    selectedInputField.inputInx = 1
                                                }
                                            }
                                        }
                                    }


                                    RowLayout {
                                        Layout.fillWidth: true
                                        Layout.alignment: Qt.AlignVCenter
                                        spacing: 20
                                        anchors.margins: 10
                                        width: parent.width
                                        height: parent.height
                                        opacity: model.id === "4" || model.id === "5" ? 1 : 0
                                        enabled: model.id === "4" || model.id === "5"

                                        ColumnLayout {
                                            Layout.fillHeight: true
                                            Layout.alignment: Qt.AlignVCenter

                                            Text {
                                                text: "S_Length"
                                                Layout.preferredWidth: 40
                                            }

                                            Button {
                                                text: model.input1
                                                Layout.preferredWidth: 60
                                                background: Rectangle {
                                                    color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 0) ? "#58ff86" : "white"
                                                }
                                                onClicked: {
                                                    selectedInputField.itemInx = index
                                                    selectedInputField.inputInx = 0
                                                }
                                            }
                                        }

                                        ColumnLayout {
                                            Layout.fillHeight: true
                                            Layout.alignment: Qt.AlignVCenter

                                            Text {
                                                text: "S_Speed"
                                                Layout.preferredWidth: 40
                                            }

                                            Button {
                                                text: model.input2
                                                Layout.preferredWidth: 60
                                                background: Rectangle {
                                                    color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 1) ? "#58ff86" : "white"
                                                }
                                                onClicked: {
                                                    selectedInputField.itemInx = index
                                                    selectedInputField.inputInx = 1
                                                }
                                            }
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillHeight: true
                                    Layout.alignment: Qt.AlignVCenter
                                    Layout.preferredWidth: 40

                                    Button {
                                        text: "▲"
                                        Layout.preferredWidth: 40
                                        onClicked: {
                                            selectedInputField.itemInx = -1
                                            selectedInputField.inputInx = -1
                                            if (index > 0) {
                                                actionSequence.sequence.move(index, index - 1, 1)
                                            }
                                        }
                                    }

                                    Button {
                                        text: "▼"
                                        Layout.preferredWidth: 40
                                        onClicked: {
                                            selectedInputField.itemInx = -1
                                            selectedInputField.inputInx = -1
                                            if (index < actionSequence.sequence.count - 1) {
                                                actionSequence.sequence.move(index, index + 1, 1)
                                            }
                                        }
                                    }
                                }

                                Button {
                                    text: "<font color='#ffffff'>X</font>"
                                    Layout.preferredWidth: 40
                                    Layout.preferredHeight: 40
                                    background: Rectangle {
                                        color: "red"
                                        radius: 1
                                    }
                                    onClicked: {
                                        selectedInputField.itemInx = -1
                                        selectedInputField.inputInx = -1
                                        actionSequence.sequence.remove(index)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}