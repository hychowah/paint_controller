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

    signal saveSequence

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

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
                    height: {
                        if (!model || !model.id) return 70;
                        var action = actionConfig.getAction(model.id);
                        return action ? 70 + (action.fields.length * 60) : 70;
                    }
                    property int itemIndex: index

                    Component.onCompleted: {
                        console.log("Raw model for item " + itemIndex + ": " + JSON.stringify(model));
                    }

                    Rectangle {
                        width: parent.width - 20
                        height: parent.height - 20
                        x: 10
                        y: 10
                        color: Qt.rgba(255, 255, 255, 0.5)
                        radius: 20
                        border.color: "#000000"
                        visible: model !== undefined && model !== null

                        Text {
                            text: model && model.title ? (delegateItem.itemIndex+1) + ") " + model.title : (delegateItem.itemIndex+1) + ") Invalid Item"
                            font.pixelSize: 20
                            font.bold: true
                            x: 10
                            y: 10
                        }

                        ColumnLayout {
                            x: 20
                            y: 40
                            spacing: 10
                            width: 200
                            height: model && actionConfig.getAction(model.id) ? actionConfig.getAction(model.id).fields.length * 60 : 0
                            Rectangle {
                                anchors.fill: parent
                                color: "yellow"
                            }

                            Repeater {
                                model: {
                                    if (!delegateItem.model || !delegateItem.model.id) {
                                        console.log("Invalid model for item " + delegateItem.itemIndex);
                                        return [];
                                    }
                                    var action = actionConfig.getAction(delegateItem.model.id);
                                    if (!action) {
                                        console.log("No action found for ID " + delegateItem.model.id);
                                        return [];
                                    }
                                    console.log("Fields for " + delegateItem.model.id + ": " + JSON.stringify(action.fields));
                                    return action.fields;
                                }

                                delegate: RowLayout {
                                    id: rowLayout
                                    spacing: 20
                                    property int fieldIndex: index

                                    Text {
                                        text: modelData.label
                                        Layout.preferredWidth: 60
                                    }
                                    Button {
                                        id: valueButton
                                        property string currentKey: modelData.key
                                        property int modelIndex: delegateItem.itemIndex

                                        text: delegateItem.model[currentKey] || "0"
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
                }
            }
        }
    }

    Component.onCompleted: {
        console.log("Initial sequence: " + (sequence ? sequence.count : "undefined") + " items");
    }
    onSequenceChanged: {
        console.log("Sequence updated: " + (sequence ? sequence.count : "undefined") + " items");
    }
}