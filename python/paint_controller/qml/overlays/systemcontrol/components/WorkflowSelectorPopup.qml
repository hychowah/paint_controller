import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: workflowSelectorPopup

    property var workflowNames: []

    signal workflowSelected(string workflowName)

    width: 400
    height: 300
    x: parent ? (parent.width - width) / 2 : 0
    y: parent ? (parent.height - height) / 2 : 0
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

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
            text: "Select WorkFlow to Load"
            color: "#FFFFFF"
            font.pixelSize: 16
            font.bold: true
        }

        ListView {
            id: workflowList
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: workflowSelectorPopup.workflowNames || []

            delegate: Rectangle {
                width: workflowList.width
                height: 40
                color: delegateMouseArea.containsMouse ? "#3A5A8C" : "#333333"
                radius: 4

                Text {
                    anchors.centerIn: parent
                    text: modelData
                    color: "#FFFFFF"
                    font.pixelSize: 14
                }

                MouseArea {
                    id: delegateMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        workflowSelectorPopup.workflowSelected(modelData)
                        workflowSelectorPopup.close()
                    }
                }
            }
        }

        Button {
            text: "Cancel"
            Layout.alignment: Qt.AlignRight
            onClicked: workflowSelectorPopup.close()
        }
    }
}