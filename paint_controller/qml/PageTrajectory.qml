import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pageTrajRect
    objectName: "pageTrajRect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Use the context property directly - no need for a proxy
    // actionConfig is now a global context property

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
                                var actionPrefix = action[0]
                                var actionId = actionConfig.getActionIdByPrefix(actionPrefix)
                                
                                if (actionId !== "") {
                                    // Create a new object for the action
                                    var newAction = {
                                        id: actionId,
                                        title: actionConfig.getAction(actionId).title
                                    };
                                    
                                    // Fill in the input values from the action string
                                    var fields = actionConfig.getAction(actionId).fields;
                                    for (var i = 0; i < fields.length; i++) {
                                        var fieldIndex = i + 1;
                                        var actionValueIndex = i + 1;
                                        
                                        if (actionValueIndex < action.length) {
                                            newAction["input" + fieldIndex] = action[actionValueIndex];
                                        } else {
                                            newAction["input" + fieldIndex] = "0";
                                        }
                                    }
                                    
                                    // Set unused inputs to -1
                                    for (var j = fields.length + 1; j <= 4; j++) {
                                        newAction["input" + j] = "-1";
                                    }
                                    
                                    sequenceModel.append(newAction);
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
                                    var config = actionConfig.getAction(actionId);
                                    
                                    if (!config) {
                                        console.error("Unknown action ID:", actionId);
                                        continue;
                                    }
                                    
                                    // Start with the action prefix
                                    var actionString = config.prefix;
                                    
                                    // Add input parameters based on fields length
                                    for (var j = 0; j < config.fields.length; j++) {
                                        var inputKey = config.fields[j].key;
                                        var inputValue = item[inputKey];
                                        
                                        // Skip if undefined or -1 for actions that don't use all inputs
                                        if (inputValue !== undefined && inputValue !== "-1") {
                                            actionString += "_" + inputValue;
                                        } else {
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

                        // onAddAction: function(actionId) {
                        //     console.log("Adding action with ID:", actionId);
                        //     sequenceModel.append(actionConfig.createActionItem(actionId));
                        // }
                        onAddAction: {
                            var actionItem = actionConfig.createActionItem(actionId);
                            console.log("Action item to append: " + JSON.stringify(actionItem));
                            sequenceModel.append(actionItem);
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