import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pageTrajRect
    objectName: "pageTrajRect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Action configuration that defines input fields for each action type
    property var actionConfig: ({
        "0": { prefix: "moveWinchTo", inputCount: 2 },
        "1": { prefix: "descent", inputCount: 2 },
        "2": { prefix: "spray", inputCount: 2 },
        "3": { prefix: "stopSpray", inputCount: 0 },
        "4": { prefix: "aNs", inputCount: 4 },
        "5": { prefix: "dNs", inputCount: 4 },
        "6": { prefix: "resetYaw", inputCount: 0 }
    })

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

                    ColumnLayout {
                        Layout.preferredWidth: parent.width / 4
                        Layout.fillHeight: true

                        PlannerPageStatus {
                            Layout.preferredWidth: parent.width
                            Layout.fillHeight: true
                        }

                        // Sequence List
                        SequenceList {
                            Layout.preferredWidth: parent.width
                            Layout.preferredHeight: parent.height / 2
                            currentSeq: currentSeq

                            onResetSequence: function() {
                                sequenceModel.clear()
                            }

                            onAddAction: function(item) {
                                var action = item.split("_")
                                if(action[0] == "moveWinchTo") {
                                    sequenceModel.append({id: "0", title: "Move Winch To", input1: action[1], input2: action[2], input3: "-1", input4: "-1"})
                                }
                                else if(action[0] == "spray") {
                                    sequenceModel.append({id: "2", title: "Spray", input1: action[1], input2: action[2], input3: "-1", input4: "-1"})
                                }
                                else if(action[0] == "stopSpray") {
                                    sequenceModel.append({id: "3", title: "Stop Spray", input1: "-1", input2: "-1", input3: "-1", input4: "-1"})
                                }
                                else if(action[0] == "aNs") {
                                    sequenceModel.append({id: "4", title: "Ascend & Spray", input1: action[1], input2: action[2], input3: action[3], input4: action[4]})
                                }
                                else if(action[0] == "dNs") {
                                    sequenceModel.append({id: "5", title: "Descend & Spray", input1: action[1], input2: action[2], input3: action[3], input4: action[4]})
                                }
                                else if(action[0] == "resetYaw") {
                                    sequenceModel.append({id: "6", title: "Reset Yaw", input1: "-1", input2: "-1", input3: "-1", input4: "-1"})
                                }
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
                                    var item = sequenceModel.get(i);
                                    var actionId = item.id;
                                    var actionConfig = pageTrajRect.actionConfig[actionId];
                                    
                                    if (!actionConfig) {
                                        console.error("Unknown action ID:", actionId);
                                        continue;
                                    }
                                    
                                    // Start with the action prefix
                                    var actionString = actionConfig.prefix;
                                    
                                    // Add input parameters based on inputCount
                                    for (var j = 1; j <= actionConfig.inputCount; j++) {
                                        var inputKey = "input" + j;
                                        var inputValue = item[inputKey];
                                        
                                        // Skip if undefined or -1 for actions that don't use all inputs
                                        if (inputValue !== undefined && inputValue !== "-1") {
                                            actionString += "_" + inputValue;
                                        } else if (j <= actionConfig.inputCount) {
                                            // Add placeholder for required inputs
                                            actionString += "_0";
                                        }
                                    }
                                    
                                    seqString += actionString + ",";
                                }
                                
                                // remove last comma
                                if (seqString.length > 0) {
                                    seqString = seqString.slice(0, -1);
                                }
                                
                                console.log("Saving trajectory:", seqString);
                                trajectoryHandler.saveTrajectory(currentSeq.seqName, seqString);
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


                        onAddMoveWinchTo: function() {
                            // input1: length, input2: speed
                            sequenceModel.append({
                                id: "0", title: "Move Winch To",
                                input1: "0", input2: "1000",
                                input3: "-1", input4: "-1"
                            });
                        }

                        onAddDescend: function() {
                            // input1: length, input2: speed
                            sequenceModel.append({
                                id: "1", title: "Descend",
                                input1: "0", input2: "1000",
                                input3: "-1", input4: "-1"
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
                                input3: "-1", input4: "-1"
                            });
                        }

                        onAddStopSpray: function() {
                            // input1: N/A, input2: N/A
                            sequenceModel.append({
                                id: "3", title: "Stop Spray",
                                input1: "-1", input2: "-1",
                                input3: "-1", input4: "-1"
                            });
                        }

                        onAddResetYaw: function() {
                            // input1: N/A, input2: N/A
                            sequenceModel.append({
                                id: "6", title: "Reset Yaw",
                                input1: "-1", input2: "-1",
                                input3: "-1", input4: "-1"
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

                        ExecutorPageStatus {
                            anchors {
                                top: parent.top
                                left: parent.left
                                right: parent.right
                            }
                            height: 100
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