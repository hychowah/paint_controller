import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: workFlowTab
    color: "transparent"
    required property var workflowRunner

    ColumnLayout {
        anchors {
            fill: parent
            margins: 15
        }
        spacing: 15

        // WorkFlow Selection
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: "WorkFlow"
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 14
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 60
                color: "#2A2A2A"
                border.color: "#3A5A8C"
                border.width: 1
                radius: 6

                ComboBox {
                    anchors {
                        fill: parent
                        margins: 6
                    }
                    model: workFlowRunner ? workFlowRunner.workflow_list : []
                    currentIndex: -1
                    
                    onCurrentIndexChanged: {
                        if (currentIndex >= 0 && workFlowRunner) {
                            workFlowRunner.load_workflow(model[currentIndex])
                        }
                    }

                    delegate: ItemDelegate {
                        width: parent.width
                        height: 60
                        text: modelData
                        highlighted: ListView.isCurrentItem
                        background: Rectangle {
                            color: highlighted ? "#3A5A8C" : "#2A2A2A"
                        }
                        contentItem: Text {
                            text: modelData
                            color: highlighted ? "#FFFFFF" : "#CCCCCC"
                            font.family: "Helvetica"
                            font.pixelSize: 14
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    contentItem: Text {
                        text: workFlowRunner && workFlowRunner.current_workflow 
                              ? workFlowRunner.current_workflow 
                              : "Select workflow..."
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 14
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 10
                    }

                    background: Rectangle {
                        color: "#2A2A2A"
                        border.color: "#3A5A8C"
                        border.width: 1
                        radius: 6
                    }
                }
            }
        }

        // Status Display
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: "Status"
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 14
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 40
                color: "#2A2A2A"
                border.color: "#333333"
                border.width: 1
                radius: 6

                Text {
                    anchors {
                        fill: parent
                        margins: 10
                    }
                    text: {
                        if (!workFlowRunner) return "No runner"
                        switch (workFlowRunner.execution_state) {
                            case 0: return "Idle"
                            case 1: return "Running"
                            case 2: return "Paused"
                            case 3: return "Completed"
                            case 4: return "Error"
                            default: return "Unknown"
                        }
                    }
                    color: {
                        if (!workFlowRunner) return "#CCCCCC"
                        switch (workFlowRunner.execution_state) {
                            case 0: return "#CCCCCC"  // Idle - gray
                            case 1: return "#00FF00"  // Running - green
                            case 2: return "#FFFF00"  // Paused - yellow
                            case 3: return "#00FFFF"  // Completed - cyan
                            case 4: return "#FF0000"  // Error - red
                            default: return "#CCCCCC"
                        }
                    }
                    font.family: "Helvetica"
                    font.pixelSize: 14
                    font.bold: true
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        // Two-column layout for Actions and Control Buttons
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 15

            // Left Column - Actions List
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 60
                spacing: 8

                Text {
                    text: "Actions"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 14
                    font.bold: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "#2A2A2A"
                    border.color: "#333333"
                    border.width: 1
                    radius: 6

                    ScrollView {
                        anchors {
                            fill: parent
                            margins: 8
                        }
                        clip: true
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        ColumnLayout {
                            width: parent.parent.width - 16
                            spacing: 4

                            // Instructions if no workflow loaded
                            Text {
                                visible: !workFlowRunner || !workFlowRunner.current_workflow
                                text: "Load a workflow to see actions"
                                color: "#888888"
                                font.family: "Helvetica"
                                font.pixelSize: 12
                                font.italic: true
                                Layout.fillWidth: true
                            }

                            // Action items (loaded from YAML)
                            Repeater {
                                model: workFlowRunner ? workFlowRunner.workflow_actions : []

                                delegate: Rectangle {
                                    Layout.fillWidth: true
                                    height: 50
                                    color: (workFlowRunner && workFlowRunner.current_action_index === index) 
                                           ? "#3A5A8C"  // Highlight current action
                                           : "#1A1A1A"
                                    border.color: (workFlowRunner && workFlowRunner.current_action_index === index)
                                                  ? "#00FF00"  // Green border for current
                                                  : "#333333"
                                    border.width: 1
                                    radius: 4

                                    Behavior on color {
                                        ColorAnimation { duration: 200 }
                                    }

                                    ColumnLayout {
                                        anchors {
                                            fill: parent
                                            margins: 8
                                        }
                                        spacing: 2

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 10

                                            Text {
                                                text: (index + 1) + "."
                                                color: "#3A5A8C"
                                                font.family: "Helvetica"
                                                font.pixelSize: 12
                                                font.bold: true
                                            }

                                            Text {
                                                text: modelData.name
                                                color: "#FFFFFF"
                                                font.family: "Helvetica"
                                                font.pixelSize: 12
                                                font.bold: true
                                                Layout.fillWidth: true
                                            }

                                            Rectangle {
                                                width: 60
                                                height: 20
                                                color: "#2A3040"
                                                radius: 3
                                                border.color: "#3A5A8C"
                                                border.width: 1

                                                Text {
                                                    anchors.centerIn: parent
                                                    text: modelData.type.replace("teensy_", "").replace("winch_", "")
                                                    color: "#AAAAAA"
                                                    font.family: "Helvetica"
                                                    font.pixelSize: 10
                                                }
                                            }
                                        }

                                        Text {
                                            text: modelData.description
                                            color: "#888888"
                                            font.family: "Helvetica"
                                            font.pixelSize: 10
                                            Layout.fillWidth: true
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Right Column - Control Buttons
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 35
                spacing: 10

                Text {
                    text: "Controls"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 14
                    font.bold: true
                }

                // Play Button
                Rectangle {
                    Layout.fillWidth: true
                    height: 70
                    color: playMouseArea.containsMouse ? "#2E7D32" : "#1B5E20"
                    border.color: "#66BB6A"
                    border.width: 2
                    radius: 8

                    Text {
                        anchors.centerIn: parent
                        text: "▶ Play"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    MouseArea {
                        id: playMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (workFlowRunner && workFlowRunner.current_workflow) {
                                workFlowRunner.play()
                            }
                        }
                    }

                    Behavior on color {
                        ColorAnimation { duration: 150 }
                    }
                }

                // Stop Button
                Rectangle {
                    Layout.fillWidth: true
                    height: 70
                    color: stopMouseArea.containsMouse ? "#D32F2F" : "#B71C1C"
                    border.color: "#EF5350"
                    border.width: 2
                    radius: 8

                    Text {
                        anchors.centerIn: parent
                        text: "⏹ Stop"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    MouseArea {
                        id: stopMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (workFlowRunner) {
                                workFlowRunner.stop()
                            }
                        }
                    }

                    Behavior on color {
                        ColorAnimation { duration: 150 }
                    }
                }

                // Spacer to push buttons to top
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }
}

