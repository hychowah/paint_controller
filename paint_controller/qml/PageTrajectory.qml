import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pageTrajRect
    objectName: "pageTrajRect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    StackLayout {
        id: stackLayout
        anchors.fill: parent

        Item {
            id: plannerPage
            width: parent.width
            height: parent.height

            ListModel {
                id: sequenceModel
            }

            QtObject {
                id: selectedInputField
                property int itemInx: -1
                property int inputInx: -1
            }

            QtObject {
                id: currentSeq
                property int seqIndex: -1
                property string seqName: ""
            }

            property var selectedSequence: null

            Rectangle {
                width: parent.width
                height: parent.height
                anchors.bottom: parent.bottom
                anchors.margins: 5
                color: "#9F9F9F"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    anchors.topMargin: 100
                    spacing: 20

                    // Sequence List
                    SequenceList {
                        Layout.preferredWidth: parent.width / 4
                        Layout.fillHeight: true
                        currentSeq: currentSeq

                        onResetSequence: function() {
                            sequenceModel.clear()
                        }

                        onAddAction: function(item) {
                            var action = item.split("_")
                            if(action[0] == "ascent") {
                                sequenceModel.append({id: "0", title: "Ascend", input1: action[1], input2: action[2], input3: -1, input4: -1})
                            }
                            else if(action[0] == "descent") {
                                sequenceModel.append({id: "1", title: "Descend", input1: action[1], input2: action[2], input3: -1, input4: -1})
                            }
                            else if(action[0] == "spray") {
                                sequenceModel.append({id: "2", title: "Spray", input1: action[1], input2: action[2], input3: -1, input4: -1})
                            }
                            else if(action[0] == "stopSpray") {
                                sequenceModel.append({id: "3", title: "Stop Spray", input1: -1, input2: -1, input3: -1, input4: -1})
                            }
                            else if(action[0] == "aNs") {
                                sequenceModel.append({id: "4", title: "Ascend & Spray", input1: action[1], input2: action[2], input3: action[3], input4: action[4]})
                            }
                            else if(action[0] == "dNs") {
                                sequenceModel.append({id: "5", title: "Descend & Spray", input1: action[1], input2: action[2], input3: action[3], input4: action[4]})
                            }
                            else if(action[0] == "resetYaw") {
                                sequenceModel.append({id: "6", title: "Reset Yaw", input1: -1, input2: -1, input3: -1, input4: -1})
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true

                        // action sequence
                        ActionSequence {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            sequence: sequenceModel // pass sequence to ActionSequence
                            selectedInputField: selectedInputField
                            currentSeq: currentSeq

                            onSaveSequence: function() {
                                var seqString = ""
                                for(var i = 0; i < sequenceModel.count; i++) {
                                    if (sequenceModel.get(i).id === "0") {
                                        seqString += "ascent_" + sequenceModel.get(i).input1 + "_" + sequenceModel.get(i).input2 + ","
                                    }
                                    else if (sequenceModel.get(i).id === "1") {
                                        seqString += "descent_" + sequenceModel.get(i).input1 + "_" + sequenceModel.get(i).input2 + ","
                                    }
                                    else if (sequenceModel.get(i).id === "2") {
                                        seqString += "spray_" + sequenceModel.get(i).input1 + "_" + sequenceModel.get(i).input2 + ","
                                    }
                                    else if (sequenceModel.get(i).id === "3") {
                                        seqString += "stopSpray,"
                                    }
                                    else if (sequenceModel.get(i).id === "4") {
                                        seqString += "aNs_" + sequenceModel.get(i).input1 + "_" + sequenceModel.get(i).input2 + "_" + sequenceModel.get(i).input3 + "_" + sequenceModel.get(i).input4 + ","
                                    }
                                    else if (sequenceModel.get(i).id === "5") {
                                        seqString += "dNs_" + sequenceModel.get(i).input1 + "_" + sequenceModel.get(i).input2 + "_" + sequenceModel.get(i).input3 + "_" + sequenceModel.get(i).input4 + ","
                                    }
                                    else if(sequenceModel.get(i).id === "6") {
                                        seqString += "resetYaw,"
                                    }
                                }
                                // remove last comma
                                seqString = seqString.slice(0, -1)
                                trajectoryHandler.saveTrajectory(currentSeq.seqName, seqString)
                            }
                        }

                        TrajNumpad {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 100
                            selectedInputField: selectedInputField
                            sequence: sequenceModel
                        }

                    }

                    // action item
                    ActionItem {
                        Layout.preferredWidth: parent.width / 4
                        Layout.fillHeight: true

                        onAddAscend: function() {
                            // input1: length, input2: speed
                            sequenceModel.append({
                                id: "0", title: "Ascend",
                                input1: "0", input2: "1000",
                                input3: "", input4: ""
                            });
                        }

                        onAddDescend: function() {
                            // input1: length, input2: speed
                            sequenceModel.append({
                                id: "1", title: "Descend",
                                input1: "0", input2: "1000",
                                input3: "", input4: ""
                            });
                        }

                        onAddAscendNSpray: function() {
                            // input1: winch length, input2: winch speed, input3: spray length, input4: spray speed
                            sequenceModel.append({
                                id: "4", title: "Ascend & Spray", 
                                input1: "0", input2: "1000",
                                input3: "0", input4: "1000"
                            });
                        }

                        onAddDescendNSpray: function() {
                            // input1: winch length, input2: winch speed, input3: spray length, input4: spray speed
                            sequenceModel.append({
                                id: "5", title: "Descend & Spray",
                                input1: "0", input2: "1000",
                                input3: "0", input4: "1000"
                            });
                        }

                        onAddSpray: function() {
                            // input1: length, input2: speed
                            sequenceModel.append({
                                id: "2", title: "Spray",
                                input1: "0", input2: "1000",
                                input3: "", input4: ""
                            });
                        }

                        onAddStopSpray: function() {
                            // input1: N/A, input2: N/A
                            sequenceModel.append({
                                id: "3", title: "Stop Spray",
                                input1: "", input2: "",
                                input3: "", input4: ""
                            });
                        }

                        onAddResetYaw: function() {
                            // input1: N/A, input2: N/A
                            sequenceModel.append({
                                id: "6", title: "Reset Yaw",
                                input1: "", input2: "",
                                input3: "", input4: ""
                            });
                        }
                    }
                }
            }
        }

        Item {
            id: executorPage
            width: parent.width
            height: parent.height

            Rectangle {
                width: parent.width
                height: parent.height
                anchors.bottom: parent.bottom
                anchors.margins: 5
                color: "#9F9F9F"
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    anchors.topMargin: 100
                    spacing: 20


                    Rectangle {
                        id: efView
                        objectName: "efView"
                        //anchors.fill: parent
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "transparent"
                        
                        Image {
                            id: efFrame
                            anchors.fill: parent
                            fillMode: Image.PreserveAspectCrop
                            cache: false
                            source: "image://ef_live/frame"
                        }
                    }

                    // action item
                    TrajectoryControl {
                        Layout.preferredWidth: parent.width / 4
                        Layout.fillHeight: true
                    }

                    Connections {
                        target: baseStreamer
                        function onFrame_ready() {
                            efFrame.source = ""
                            efFrame.source = "image://ef_live/frame"
                        }
                    }

                }
            }
        }
    }

    Text {
        id: angleText
        text: "Angle:" //TODO: get angle from py
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: 30
        font.pixelSize: 20
        font.bold: true
    }

    Text {
        text: "Distance:" // TODO: get distance from py
        anchors.top: parent.top
        anchors.left: angleText.right
        anchors.margins: 30
        anchors.leftMargin: 40
        font.pixelSize: 20
        font.bold: true
    }

    RowLayout {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: 20
        height: 50

        Rectangle {
            width: 100
            height: parent.height
            color: stackLayout.currentIndex == 0 ? "#007bff" : "#e0e0e0"
            radius: 20

            Text {
                text: "Planner"
                anchors.centerIn: parent
                anchors.horizontalCenter: parent.horizontalCenter
                color: stackLayout.currentIndex == 0 ? "#ffffff" : "#6c757d"
                font.pixelSize: 15
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stackLayout.currentIndex = 0
                }
            }
        }

        Rectangle {
            width: 100
            height: parent.height
            color: stackLayout.currentIndex == 1 ? "#007bff" : "#e0e0e0"
            radius: 20

            Text {
                text: "Executor"
                anchors.centerIn: parent
                anchors.horizontalCenter: parent.horizontalCenter
                color: stackLayout.currentIndex == 1 ? "#ffffff" : "#6c757d"
                font.pixelSize: 15
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stackLayout.currentIndex = 1
                }
            }
        }
    }
}