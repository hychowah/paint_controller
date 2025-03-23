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

    property var showInputField1: ["0", "1", "2", "4", "5"]
    property var showInputField2: ["4", "5"]

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
                id: actionListView
                anchors.fill: parent
                model: actionSequence.sequence
                // Removed redundant width property that was causing the error

                delegate: Item {
                    width: actionListView.width
                    height: (model.id === "4" || model.id === "5") ? 180 : 130

                    Rectangle {
                            anchors.fill: parent
                            anchors.margins: 10
                            height: (model.id === "4" || model.id === "5") ? 130 : 100
                            color: Qt.rgba(255, 255, 255, 0.5)
                            radius: 20
                            border.color: "#000000"
                    
                        Text {
                            text: (index+1).toString() + ") " + model.title
                            font.pixelSize: 20
                            font.bold: true
                            anchors.margins: 10
                            anchors.top: parent.top
                            anchors.left: parent.left
                            Layout.alignment: Qt.AlignVCenter
                        }

                        RowLayout {
                            id: inputRowLayout1
                            anchors.top: parent.top
                            anchors.left: parent.left
                            spacing: 20
                            anchors.leftMargin: 20
                            anchors.topMargin: 40
                            Layout.fillWidth: true
                            opacity: showInputField1.indexOf(model.id) !== -1
                            enabled: showInputField1.indexOf(model.id) !== -1

                            ColumnLayout {
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
                            anchors.top: inputRowLayout1.bottom
                            anchors.left: parent.left
                            spacing: 20
                            anchors.leftMargin: 20
                            anchors.topMargin: 5
                            Layout.fillWidth: true
                            opacity: showInputField2.indexOf(model.id) !== -1
                            enabled: showInputField2.indexOf(model.id) !== -1

                            ColumnLayout {
                                Text {
                                    text: "S_Length"
                                    Layout.preferredWidth: 40
                                }

                                Button {
                                    text: model.input3
                                    Layout.preferredWidth: 60
                                    background: Rectangle {
                                        color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 2) ? "#58ff86" : "white"
                                    }
                                    onClicked: {
                                        selectedInputField.itemInx = index
                                        selectedInputField.inputInx = 2
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
                                    text: model.input4
                                    Layout.preferredWidth: 60
                                    background: Rectangle {
                                        color: (selectedInputField.itemInx === index && selectedInputField.inputInx === 3) ? "#58ff86" : "white"
                                    }
                                    onClicked: {
                                        selectedInputField.itemInx = index
                                        selectedInputField.inputInx = 3
                                    }
                                }
                            }
                        }

                        Button {
                            id: removeButton
                            text: "<font color='#ffffff'>X</font>"
                            width: 40
                            height: 40
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.right
                            anchors.margins: 40
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

                        ColumnLayout {
                            anchors.right: removeButton.left
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.margins: 30

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
                    }
                }
            }
        }
    }
}