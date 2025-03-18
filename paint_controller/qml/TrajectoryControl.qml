// TrajectoryControl.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: control
    color: "#ffffff"
    radius: 15
    border.color: "#e0e0e0"
    border.width: 1

    property bool selected: false
    property var currentActions: []
    property int currentActionIndex: -1
    property bool isExecuting: false

    ColumnLayout {
        width: parent.width
        spacing: 5
        visible: !selected

        Repeater {
            model: trajectoryHandler.trajectory
            
            Rectangle {
                id: itemRect
                Layout.fillWidth: true
                height: 50
                color: "#d1eafc"
                border.color: "#e0e0e0"
                border.width: 1
                radius: 5
                
                Text {
                    anchors.fill: parent
                    anchors.margins: 10
                    text: modelData.name
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 16
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        trajectoryHandler.selectTrajectory(index)
                        control.currentActions = trajectoryHandler.getSelectedActions()
                        control.selected = true
                        control.currentActionIndex = 0
                    }
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 5
        visible: selected

        // Back button
        Rectangle {
            Layout.alignment: Qt.AlignTop | Qt.AlignLeft  // Force top position
            Layout.fillWidth: true  // Match parent width
            Layout.preferredHeight: 50  // Maintain fixed height
            //width: 100
            //height: 50
            color: "#e0e0e0"
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
                text: "← Back to Sequences"
                elide: Text.ElideRight
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 16
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    control.selected = false
                    control.currentActionIndex = -1
                    control.isExecuting = false
                }
            }
        }

        // Action list
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ColumnLayout {
                width: parent.width
                spacing: 2

                Repeater {
                    model: control.currentActions

                    Rectangle {
                        id: actionItem
                        width: parent.width
                        height: 60
                        color: control.isExecuting && index === control.currentActionIndex ? 
                               "#51aef3" : "#d1eafc"
                        border.color: "#e0e0e0"
                        radius: 3

                        RowLayout {
                            anchors.fill: parent
                            spacing: 10

                            Button {
                                visible: !control.isExecuting
                                text: index === control.currentActionIndex ? "➔" : ""
                                onClicked: control.currentActionIndex = index
                                flat: true
                                background: Rectangle { color: "transparent" }
                            }

                            Text {
                                text: modelData
                                Layout.fillWidth: true
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 16
                                font.bold: true
                            }
                        }

                        MouseArea {
                            enabled: !control.isExecuting
                            anchors.fill: parent
                            onClicked: control.currentActionIndex = index
                        }
                    }
                }
            }
        }

        // Control Panel
        Rectangle {
            id: eStopButton
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            color: "#ec3939"
            border.color: "#e0e0e0"
            radius: 3

            Text {
                text: "E-Stop"
                anchors.centerIn: parent
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 16
                font.bold: true
            }


            MouseArea {
                enabled: !control.isExecuting
                anchors.fill: parent
                onClicked: {
                    control.isExecuting = false
                    trajectoryHandler.stopAll()
                }
            }
        }

        Rectangle {
            id: executionButton
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            color: !control.isExecuting && control.currentActionIndex >= 0 ? "#a1f9c6" : "#e6e7e7"
            border.color: "#e0e0e0"
            radius: 3

            Text {
                text: control.isExecuting ? "Executing..." : "Start Next Action"
                anchors.centerIn: parent
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 16
                font.bold: true
            }


            MouseArea {
                enabled: !control.isExecuting
                anchors.fill: parent
                onClicked: {
                    control.isExecuting = true
                    control.startNextAction()
                }
            }
        }
    }

    Timer {
        id: executionTimer
        interval: 500 // ms
        repeat: false
        onTriggered: {
            if(control.currentActionIndex < control.currentActions.length - 1) {
                control.currentActionIndex++
            }
            control.isExecuting = false
        }
    }

    function startNextAction() {
        trajectoryHandler.startExecution(control.currentActionIndex) // send action index to python
        executionTimer.start()
    }
}