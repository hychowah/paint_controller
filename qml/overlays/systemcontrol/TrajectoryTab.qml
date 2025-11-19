import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: trajectoryTab
    color: "transparent"

    ColumnLayout {
        anchors {
            fill: parent
            margins: 15
        }
        spacing: 15

        // Trajectory Selection
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: "Trajectory"
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
                    model: trajectoryRunner ? trajectoryRunner.trajectory_list : []
                    currentIndex: -1
                    
                    onCurrentIndexChanged: {
                        if (currentIndex >= 0 && trajectoryRunner) {
                            trajectoryRunner.load_trajectory(model[currentIndex])
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
                        text: trajectoryRunner && trajectoryRunner.current_trajectory 
                              ? trajectoryRunner.current_trajectory 
                              : "Select trajectory..."
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
                        if (!trajectoryRunner) return "No runner"
                        switch (trajectoryRunner.execution_state) {
                            case 0: return "Idle"
                            case 1: return "Running"
                            case 2: return "Paused"
                            case 3: return "Completed"
                            case 4: return "Error"
                            default: return "Unknown"
                        }
                    }
                    color: {
                        if (!trajectoryRunner) return "#CCCCCC"
                        switch (trajectoryRunner.execution_state) {
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

        // Control Buttons
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 10

            // Play / Pause / Resume Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Play Button
                Rectangle {
                    Layout.fillWidth: true
                    height: 45
                    color: playMouseArea.containsMouse ? "#3A5A8C" : "#2A3040"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 6

                    Text {
                        anchors.centerIn: parent
                        text: "Play"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    MouseArea {
                        id: playMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (trajectoryRunner && trajectoryRunner.current_trajectory) {
                                trajectoryRunner.play()
                            }
                        }
                    }
                }

                // Pause Button
                Rectangle {
                    Layout.fillWidth: true
                    height: 45
                    color: pauseMouseArea.containsMouse ? "#3A5A8C" : "#2A3040"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 6

                    Text {
                        anchors.centerIn: parent
                        text: "Pause"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    MouseArea {
                        id: pauseMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (trajectoryRunner) {
                                trajectoryRunner.pause()
                            }
                        }
                    }
                }

                // Resume Button
                Rectangle {
                    Layout.fillWidth: true
                    height: 45
                    color: resumeMouseArea.containsMouse ? "#3A5A8C" : "#2A3040"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 6

                    Text {
                        anchors.centerIn: parent
                        text: "Resume"
                        color: "#FFFFFF"
                        font.family: "Helvetica"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    MouseArea {
                        id: resumeMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (trajectoryRunner) {
                                trajectoryRunner.resume()
                            }
                        }
                    }
                }
            }

            // Stop Button (full width)
            Rectangle {
                Layout.fillWidth: true
                height: 45
                color: stopMouseArea.containsMouse ? "#CC4444" : "#992222"
                border.color: "#FF6666"
                border.width: 1
                radius: 6

                Text {
                    anchors.centerIn: parent
                    text: "Stop"
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 16
                    font.bold: true
                }

                MouseArea {
                    id: stopMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        if (trajectoryRunner) {
                            trajectoryRunner.stop()
                        }
                    }
                }
            }
        }

        // Actions List
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
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

                    ColumnLayout {
                        width: 350
                        height: 150
                        spacing: 4

                        // Instructions if no trajectory loaded
                        Text {
                            visible: !trajectoryRunner || !trajectoryRunner.current_trajectory
                            text: "Load a trajectory to see actions"
                            color: "#888888"
                            font.family: "Helvetica"
                            font.pixelSize: 12
                            font.italic: true
                            Layout.fillWidth: true
                        }

                        // Action items (loaded from YAML)
                        Repeater {
                            model: {
                                // Dynamically load actions from current trajectory
                                if (!trajectoryRunner || !trajectoryRunner.current_trajectory) {
                                    return []
                                }
                                
                                return trajectoryRunner.get_current_trajectory_actions()
                            }

                            delegate: Rectangle {
                                width: parent.width
                                height: 50
                                color: (trajectoryRunner && trajectoryRunner.current_action_index === index) 
                                       ? "#3A5A8C"  // Highlight current action
                                       : "#1A1A1A"
                                border.color: (trajectoryRunner && trajectoryRunner.current_action_index === index)
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
                                        text: modelData.desc
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
    }
}

