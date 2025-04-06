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

    // Centralized configuration for action types
    property var actionConfig: ({
        "0": { fields: [
            { label: "Distance", key: "input1" },
            { label: "Velocity", key: "input2" }
        ]},
        "1": { fields: [
            { label: "Angle", key: "input1" },
            { label: "Rate", key: "input2" }
        ]},
        "2": { fields: [
            { label: "Time", key: "input1" },
            { label: "Power", key: "input2" }
        ]},
        "4": { fields: [
            { label: "Wait Time", key: "input1" },
            { label: "Wait Speed", key: "input2" },
            { label: "Step Length", key: "input3" },
            { label: "Step Speed", key: "input4" }
        ]},
        "5": { fields: [
            { label: "Delay", key: "input1" },
            { label: "Accel", key: "input2" },
            { label: "Span", key: "input3" },
            { label: "Force", key: "input4" }
        ]}
    })

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
                    height: model ? (70 + (actionConfig[model.id] ? actionConfig[model.id].fields.length * 60 : 0)) : 70
                    
                    // Store the model index
                    property int itemIndex: index

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 10
                        color: Qt.rgba(255, 255, 255, 0.5)
                        radius: 20
                        border.color: "#000000"
                        visible: model !== undefined && model !== null

                        // Local property to store fields for this item
                        property var itemFields: model && actionConfig[model.id] ? actionConfig[model.id].fields : []

                        Text {
                            text: model ? (delegateItem.itemIndex+1).toString() + ") " + model.title : (delegateItem.itemIndex+1).toString() + ") Invalid Item"
                            font.pixelSize: 20
                            font.bold: true
                            anchors.margins: 10
                            anchors.top: parent.top
                            anchors.left: parent.left
                        }

                        ColumnLayout {
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.topMargin: 40
                            anchors.leftMargin: 20
                            spacing: 10
                            visible: parent.itemFields.length > 0

                            Repeater {
                                model: parent.parent.itemFields // Use the local property
                                
                                delegate: RowLayout {
                                    id: rowLayout
                                    spacing: 20
                                    property int fieldIndex: index // Store the field index here

                                    ColumnLayout {
                                        Text {
                                            text: modelData.label
                                            Layout.preferredWidth: 60
                                        }
                                        Button {
                                            id: valueButton
                                            property string currentKey: modelData.key
                                            property int modelIndex: delegateItem.itemIndex
                                            
                                            // This is the most important part - use a timer to force refresh
                                            Timer {
                                                interval: 100
                                                running: true
                                                repeat: true
                                                onTriggered: {
                                                    if (actionSequence.sequence && 
                                                        actionSequence.sequence.count > valueButton.modelIndex) {
                                                        var currentModel = actionSequence.sequence.get(valueButton.modelIndex);
                                                        if (currentModel) {
                                                            var value = currentModel[valueButton.currentKey];
                                                            if (value === undefined || value === null || value === "" || value === "-1") {
                                                                valueButton.text = "0";
                                                            } else {
                                                                valueButton.text = value.toString();
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                            
                                            Layout.preferredWidth: 60
                                            background: Rectangle {
                                                color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                       selectedInputField.inputInx === rowLayout.fieldIndex) ? "#58ff86" : "white"
                                            }
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex
                                                selectedInputField.inputInx = rowLayout.fieldIndex
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + rowLayout.fieldIndex + ", key=" + currentKey)
                                            }
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