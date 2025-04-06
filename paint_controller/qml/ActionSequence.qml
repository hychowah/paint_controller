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
    property var selectedInputField: ({ itemInx: -1, inputInx: -1 })
    property var currentSeq: ({ seqName: "Unnamed" })
    property var actionConfig: null

    signal saveSequence

    KeyboardPopup {
        id: keyboardPopup
        anchors.centerIn: parent
        onTextUpdated: { currentSeq.seqName = newText }
        onClosed: { currentSeq.seqName = keyboardPopup.currentText }
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
            Text { text: "Sequence"; font.pixelSize: 20; font.bold: true; Layout.rightMargin: 40 }
            Text { text: "Name:" }
            Button { text: currentSeq.seqName; Layout.preferredWidth: 100; onClicked: { keyboardPopup.currentText = currentSeq.seqName; keyboardPopup.open() } }
            Button { text: "Save"; Layout.preferredWidth: 60; onClicked: saveSequence() }
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

                delegate: Item {
                    id: delegateItem
                    width: actionListView.width
                    height: model ? (70 + (model.id === "4" || model.id === "5" ? 240 : 120)) : 70
                    
                    // Store the model index
                    property int itemIndex: index

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 10
                        color: Qt.rgba(255, 255, 255, 0.5)
                        radius: 20
                        border.color: "#000000"
                        visible: model !== undefined && model !== null

                        Text {
                            text: model ? (delegateItem.itemIndex+1).toString() + ") " + model.title : (delegateItem.itemIndex+1).toString() + ") Invalid Item"
                            font.pixelSize: 20
                            font.bold: true
                            anchors.margins: 10
                            anchors.top: parent.top
                            anchors.left: parent.left
                        }

                        // First row of input fields (always show input1 and input2)
                        ColumnLayout {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.topMargin: 40
                            anchors.leftMargin: 20
                            spacing: 10
                            
                            // Input 1
                            RowLayout {
                                spacing: 20
                                visible: model.id !== "3" && model.id !== "6" // Hide for actions with no fields
                                
                                ColumnLayout {
                                    Text {
                                        text: {
                                            if (model.id === "0") return "Distance";
                                            if (model.id === "1") return "Angle";
                                            if (model.id === "2") return "Time";
                                            if (model.id === "4") return "Wait Time";
                                            if (model.id === "5") return "Delay";
                                            return "Input 1";
                                        }
                                        Layout.preferredWidth: 60
                                    }
                                    Button {
                                        text: model.input1 || "0"
                                        Layout.preferredWidth: 60
                                        background: Rectangle {
                                            color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                  selectedInputField.inputInx === 0) ? "#58ff86" : "white"
                                        }
                                        onClicked: {
                                            selectedInputField.itemInx = delegateItem.itemIndex
                                            selectedInputField.inputInx = 0
                                        }
                                    }
                                }
                            }
                            
                            // Input 2
                            RowLayout {
                                spacing: 20
                                visible: model.id !== "3" && model.id !== "6" // Hide for actions with no fields
                                
                                ColumnLayout {
                                    Text {
                                        text: {
                                            if (model.id === "0") return "Velocity";
                                            if (model.id === "1") return "Rate";
                                            if (model.id === "2") return "Power";
                                            if (model.id === "4") return "Wait Speed";
                                            if (model.id === "5") return "Accel";
                                            return "Input 2";
                                        }
                                        Layout.preferredWidth: 60
                                    }
                                    Button {
                                        text: model.input2 || "0"
                                        Layout.preferredWidth: 60
                                        background: Rectangle {
                                            color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                  selectedInputField.inputInx === 1) ? "#58ff86" : "white"
                                        }
                                        onClicked: {
                                            selectedInputField.itemInx = delegateItem.itemIndex
                                            selectedInputField.inputInx = 1
                                        }
                                    }
                                }
                            }
                            
                            // Input 3 (only for actions 4 and 5)
                            RowLayout {
                                spacing: 20
                                visible: model.id === "4" || model.id === "5"
                                
                                ColumnLayout {
                                    Text {
                                        text: model.id === "4" ? "Step Length" : "Span"
                                        Layout.preferredWidth: 60
                                    }
                                    Button {
                                        text: model.input3 || "0"
                                        Layout.preferredWidth: 60
                                        background: Rectangle {
                                            color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                  selectedInputField.inputInx === 2) ? "#58ff86" : "white"
                                        }
                                        onClicked: {
                                            selectedInputField.itemInx = delegateItem.itemIndex
                                            selectedInputField.inputInx = 2
                                        }
                                    }
                                }
                            }
                            
                            // Input 4 (only for actions 4 and 5)
                            RowLayout {
                                spacing: 20
                                visible: model.id === "4" || model.id === "5"
                                
                                ColumnLayout {
                                    Text {
                                        text: model.id === "4" ? "Step Speed" : "Force"
                                        Layout.preferredWidth: 60
                                    }
                                    Button {
                                        text: model.input4 || "0"
                                        Layout.preferredWidth: 60
                                        background: Rectangle {
                                            color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                  selectedInputField.inputInx === 3) ? "#58ff86" : "white"
                                        }
                                        onClicked: {
                                            selectedInputField.itemInx = delegateItem.itemIndex
                                            selectedInputField.inputInx = 3
                                        }
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
                            background: Rectangle { color: "red"; radius: 1 }
                            onClicked: {
                                selectedInputField.itemInx = -1
                                selectedInputField.inputInx = -1
                                actionSequence.sequence.remove(delegateItem.itemIndex)
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
                                    if (delegateItem.itemIndex > 0) {
                                        actionSequence.sequence.move(delegateItem.itemIndex, delegateItem.itemIndex - 1, 1)
                                        selectedInputField.itemInx = -1
                                        selectedInputField.inputInx = -1
                                    } 
                                } 
                            }
                            Button { 
                                text: "▼"
                                Layout.preferredWidth: 40
                                onClicked: { 
                                    if (delegateItem.itemIndex < actionSequence.sequence.count - 1) {
                                        actionSequence.sequence.move(delegateItem.itemIndex, delegateItem.itemIndex + 1, 1)
                                        selectedInputField.itemInx = -1
                                        selectedInputField.inputInx = -1
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