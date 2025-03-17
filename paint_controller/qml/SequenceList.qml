// SequenceList.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: sequenceList
    color: "#ffffff"
    radius: 15
    border.color: "#e0e0e0"
    border.width: 1
    property var currentSeq

    signal resetSequence // signal to clear sequence
    signal addAction(string item) // signal to add action to sequence

    ColumnLayout {
        anchors.fill: parent
        spacing: 5

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                id: repeaterLayout
                width: parent.width
                spacing: 5

                Repeater {
                    model: trajectoryHandler.trajectory
                    
                    Rectangle {
                        id: itemRect
                        Layout.fillWidth: true
                        height: 50
                        color: currentSeq.seqIndex === index ? "#a8f9b9" : "#ffffff"
                        border.color: "#e0e0e0"
                        border.width: 1
                        radius: 5
                        
                        Text {
                            anchors {
                                left: parent.left
                                right: parent.right
                                verticalCenter: parent.verticalCenter
                                margins: 10
                            }
                            text: modelData.name
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignLeft
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 16
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                sequenceList.currentSeq.seqIndex = index
                                sequenceList.currentSeq.seqName = modelData.name
                                //trajectoryHandler.selectTrajectory(index)
                                sequenceList.resetSequence()

                                modelData.sequence.split(",").forEach(function(item) {
                                    //var action = item.split("_")
                                    sequenceList.addAction(item)
                                })

                            }
                        }
                    }
                }
            }
        }

        Button {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            text: "<font color=\"white\">Delete Selected Sequence</font>"
            enabled: currentSeq.seqIndex !== -1
            background: Rectangle {
                color: enabled ? "#ff4637" : "#e0e0e0"
            }
            onClicked: {
                trajectoryHandler.deleteTrajectory(currentSeq.seqIndex)
                currentSeq.seqIndex = -1
                currentSeq.seqName = ""
            }
        }
    }
}