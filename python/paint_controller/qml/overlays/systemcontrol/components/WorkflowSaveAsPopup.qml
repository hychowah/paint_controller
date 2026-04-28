import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: workflowSaveAsPopup

    property string workflowName: ""

    signal saveRequested(string workflowName)

    width: 400
    height: 150
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    modal: true
    focus: true

    onOpened: saveAsNameField.text = workflowName

    background: Rectangle {
        color: "#2A2A2A"
        radius: 8
        border.color: "#404040"
        border.width: 1
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10

        Text {
            text: "Save WorkFlow As"
            color: "#FFFFFF"
            font.pixelSize: 16
            font.bold: true
        }

        TextField {
            id: saveAsNameField
            Layout.fillWidth: true
            placeholderText: "Enter workflow name"
            text: workflowSaveAsPopup.workflowName
        }

        RowLayout {
            Layout.alignment: Qt.AlignRight
            spacing: 10

            Button {
                text: "Cancel"
                onClicked: workflowSaveAsPopup.close()
            }

            Button {
                text: "Save"
                onClicked: {
                    var trimmedName = saveAsNameField.text.trim()
                    if (trimmedName !== "") {
                        workflowSaveAsPopup.saveRequested(trimmedName)
                        workflowSaveAsPopup.close()
                    }
                }
            }
        }
    }
}