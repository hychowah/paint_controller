import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../"
import "../components"

Rectangle {
    id: pageTrajRect
    objectName: "pageTrajRect"
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Store the last known valid page index
    property int lastKnownPageIndex: 0

    // Initialize the current page explicitly when the component is created
    Component.onCompleted: {
        var currentPage = trajectoryHandler.currentPage;
        console.log("PageTrajectory completed, handler page:", currentPage);
        
        // Only update if we have a valid value
        if (currentPage !== undefined && currentPage !== null) {
            stackLayout.currentIndex = currentPage;
            lastKnownPageIndex = currentPage;
        } else {
            // Otherwise, directly query the handler for the latest state
            console.log("Requesting current page from trajectoryHandler...");
            trajectoryHandler.requestCurrentPage();
        }
    }

    // Also ensure the correct page is shown when this component becomes visible again
    onVisibleChanged: {
        if (visible) {
            var currentPage = trajectoryHandler.currentPage;
            console.log("PageTrajectory visible again, handler page:", currentPage);
            
            // Use the valid value or fall back to last known state
            if (currentPage !== undefined && currentPage !== null) {
                stackLayout.currentIndex = currentPage;
                lastKnownPageIndex = currentPage;
            } else {
                // Request current page again, but use lastKnownPageIndex as fallback
                stackLayout.currentIndex = lastKnownPageIndex;
                console.log("Using last known page index:", lastKnownPageIndex);
                trajectoryHandler.requestCurrentPage();
            }
        }
    }

    StackLayout {
        id: stackLayout
        anchors.fill: parent
        
        // Keep the binding to the property for ongoing updates
        currentIndex: trajectoryHandler.currentPage
        
        // Debug log for index changes
        onCurrentIndexChanged: {
            console.log("StackLayout index changed to:", currentIndex);
            // Update our last known good index
            lastKnownPageIndex = currentIndex;
        }

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
                    anchors.topMargin: 20
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

                        onAddAction: function(actionId) {
                            console.log("Adding action with ID:", actionId);
                            
                            // Use the createActionItem method to get a properly initialized item with defaults
                            var newItem = actionConfig.createActionItem(actionId);
                            if (!newItem || Object.keys(newItem).length === 0) {
                                console.error("Failed to create action item for ID:", actionId);
                                return;
                            }
                            
                            // console.log("Created action item:", JSON.stringify(newItem));
                            
                            // Add the item to the sequence model
                            sequenceModel.append(newItem);
                            // console.log("Sequence model now has", sequenceModel.count, "items");
                        }
                    }
                }
            }
        }

        Item {
            id: executorPage
            width: parent.width
            height: parent.height
            
            property bool videoFullscreen: false

            Rectangle {
                width: parent.width
                height: parent.height
                anchors.bottom: parent.bottom
                anchors.margins: 5
                color: "#9F9F9F"
                
                // Fullscreen video overlay
                Rectangle {
                    id: fullscreenVideoOverlay
                    anchors.fill: parent
                    color: "black"
                    visible: executorPage.videoFullscreen
                    z: 100
                    
                    Image {
                        id: fullscreenFrame
                        anchors.fill: parent
                        fillMode: Image.PreserveAspectFit
                        cache: false
                        source: efFrame.source
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            executorPage.videoFullscreen = false
                        }
                    }
                }
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    anchors.topMargin: 20
                    spacing: 20
                    visible: !executorPage.videoFullscreen

                    ColumnLayout {
                        id: efView
                        objectName: "efView"
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 0
                        
                        ExecutorPageStatus {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 110
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "transparent"
                            
                            // Bind image source to control mode
                            property string imageSource: backend.control_mode === "ef" ? 
                                                    "image://ef_live/frame" : 
                                                    "image://base_front_live/frame"
                            
                            Image {
                                id: efFrame
                                anchors.fill: parent
                                fillMode: Image.PreserveAspectCrop
                                cache: false
                                source: parent.imageSource
                            }
                            
                            // Tap to fullscreen
                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    executorPage.videoFullscreen = true
                                }
                            }
                        }
                    }

                    // action item
                    TrajectoryControl {
                        Layout.preferredWidth: parent.width / 4
                        Layout.fillHeight: true
                    }

                    Connections {
                        target: baseStreamHandler
                        function onEndEffectorFrameReady() {
                            if (backend.control_mode === "ef") {
                                efFrame.source = ""
                                efFrame.source = "image://ef_live/frame"
                            }
                        }
                        function onBaseFrontFrameReady() {
                            if (backend.control_mode !== "ef") {
                                efFrame.source = ""
                                efFrame.source = "image://base_front_live/frame"
                            }
                        }
                    }
                }
            }
        }
    }

    // Minimal mode indicator - position in top right corner
    Rectangle {
        id: modeIndicator
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        width: 8  // Very small
        height: 8
        radius: 4  // Makes it a small circle
        // Different color for each mode
        color: stackLayout.currentIndex == 0 ? "#4CAF50" : "#2196F3"  // Green for Planner, Blue for Executor
        opacity: 0.7
    }

    // Connect to the pageChanged signal
    Connections {
        target: trajectoryHandler
        function onPageChanged(page) {
            console.log("Page change signal received: " + page);
            stackLayout.currentIndex = page;
            lastKnownPageIndex = page; // Update the last known page
        }
    }
}