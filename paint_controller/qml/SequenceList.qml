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
    
    // Add a subtle gradient background instead of drop shadow
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#ffffff" }
        GradientStop { position: 1.0; color: "#f7f7f7" }
    }
    
    property var currentSeq

    signal resetSequence // signal to clear sequence
    signal addAction(string item) // signal to add action to sequence

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 10

        Text {
            Layout.fillWidth: true
            text: "Saved Sequences"
            font.pixelSize: 18
            font.bold: true
            color: "#333333"
            Layout.bottomMargin: 5
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            clip: true
            
            ScrollView {
                anchors.fill: parent
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                
                ListView {
                    id: sequenceListView
                    width: parent.width
                    height: parent.height
                    spacing: 8
                    model: trajectoryHandler.trajectory
                    
                    delegate: Rectangle {
                        id: itemRect
                        width: sequenceListView.width
                        height: 64
                        radius: 8
                        
                        // Use a gradient for selected item
                        gradient: Gradient {
                            GradientStop { 
                                position: 0.0
                                color: currentSeq.seqIndex === index ? "#a8f9b9" : "#f9f9f9" 
                            }
                            GradientStop { 
                                position: 1.0
                                color: currentSeq.seqIndex === index ? "#8be99e" : "#f0f0f0" 
                            }
                        }
                        
                        border.color: currentSeq.seqIndex === index ? "#64d87b" : "#e0e0e0"
                        border.width: 1
                        
                        // Add a transition animation
                        Behavior on gradient {
                            ColorAnimation { duration: 150 }
                        }
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 15
                            spacing: 12
                            
                            Rectangle {
                                width: 28
                                height: 28
                                radius: 14
                                color: currentSeq.seqIndex === index ? "#4caf50" : "#e0e0e0"
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    color: "white"
                                    font.pixelSize: 16
                                    visible: currentSeq.seqIndex === index
                                }
                            }
                            
                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                elide: Text.ElideRight
                                font.pixelSize: 16
                                font.bold: true
                                color: currentSeq.seqIndex === index ? "#2e7d32" : "#333333"
                            }
                            
                            Text {
                                text: modelData.sequence.split(",").length
                                color: "#777777"
                                font.pixelSize: 14
                            }
                            
                            Text {
                                text: "steps"
                                color: "#777777"
                                font.pixelSize: 14
                            }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            
                            onClicked: {
                                sequenceList.currentSeq.seqIndex = index
                                sequenceList.currentSeq.seqName = modelData.name
                                sequenceList.resetSequence()

                                modelData.sequence.split(",").forEach(function(item) {
                                    sequenceList.addAction(item)
                                })
                            }
                            
                            // Add hover effect
                            hoverEnabled: true
                            onEntered: {
                                if (currentSeq.seqIndex !== index) {
                                    itemRect.border.color = "#c0c0c0"
                                }
                            }
                            onExited: {
                                if (currentSeq.seqIndex !== index) {
                                    itemRect.border.color = "#e0e0e0"
                                }
                            }
                        }
                    }
                }
            }
        }

        Button {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            
            enabled: currentSeq.seqIndex !== -1
            
            contentItem: Text {
                text: "Delete Selected Sequence"
                color: "white"
                font.pixelSize: 14
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            
            background: Rectangle {
                id: deleteButton
                color: enabled ? 
                       deleteButtonMouseArea.pressed ? "#d32f2f" : 
                       deleteButtonMouseArea.containsMouse ? "#f44336" : "#ff4637" 
                       : "#e0e0e0"
                radius: 8
                
                // Transition animation
                Behavior on color {
                    ColorAnimation { duration: 150 }
                }
            }
            
            MouseArea {
                id: deleteButtonMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                onClicked: {
                    if (enabled) {
                        trajectoryHandler.deleteTrajectory(currentSeq.seqIndex)
                        currentSeq.seqIndex = -1
                        currentSeq.seqName = ""
                    }
                }
            }
        }
    }
}