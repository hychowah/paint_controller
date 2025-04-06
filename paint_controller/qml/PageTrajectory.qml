import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: pageTrajRect
    objectName: "pageTrajRect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Create an instance of the ActionConfig
    property var config: ActionConfig {}

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
                                
                                // Use the shared config to determine action properties
                                for (var actionId in pageTrajRect.config.actions) {
                                    var actionConfig = pageTrajRect.config.getAction(actionId);
                                    if (actionConfig && actionConfig.prefix === action[0]) {
                                        // Create a new object for the action
                                        var newAction = {
                                            id: actionId,
                                            title: actionConfig.title
                                        };
                                        
                                        // Fill in the input values from the action string
                                        for (var i = 1; i <= 4; i++) {
                                            if (i <= actionConfig.fields.length && action.length > i) {
                                                newAction["input" + i] = action[i];
                                            } else {
                                                newAction["input" + i] = "-1";
                                            }
                                        }
                                        
                                        sequenceModel.append(newAction);
                                        break;
                                    }
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
                            actionConfig: pageTrajRect.config

                            onSaveSequence: function() {
                                var seqString = ""
                                
                                for(var i = 0; i < sequenceModel.count; i++) {
                                    var item = sequenceModel.get(i);
                                    var actionId = item.id;
                                    var actionConfig = pageTrajRect.config.getAction(actionId);
                                    
                                    if (!actionConfig) {
                                        console.error("Unknown action ID:", actionId);
                                        continue;
                                    }
                                    
                                    // Start with the action prefix
                                    var actionString = actionConfig.prefix;
                                    
                                    // Add input parameters based on fields length
                                    for (var j = 0; j < actionConfig.fields.length; j++) {
                                        var inputKey = actionConfig.fields[j].key;
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
                        actionConfig: pageTrajRect.config // Pass the action config

                        // Connect the new unified action signal
                        onAddAction: function(actionId) {
                            console.log("Adding action with ID:", actionId);
                            sequenceModel.append(pageTrajRect.config.createActionItem(actionId));
                        }

                        // Keep the old signal handlers for backward compatibility
                        onAddMoveWinchTo: function() {
                            console.log("Legacy moveWinchTo signal received");
                        }

                        onAddDescend: function() {
                            console.log("Legacy descend signal received");
                        }

                        onAddAscendNSpray: function() {
                            console.log("Legacy ascendNSpray signal received");
                        }

                        onAddDescendNSpray: function() {
                            console.log("Legacy descendNSpray signal received");
                        }

                        onAddSpray: function() {
                            console.log("Legacy spray signal received");
                        }

                        onAddStopSpray: function() {
                            console.log("Legacy stopSpray signal received");
                        }

                        onAddResetYaw: function() {
                            console.log("Legacy resetYaw signal received");
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