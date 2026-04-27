import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Item {
    id: root
    anchors.fill: parent
    required property var workflowRunner
    readonly property bool hasWorkflowRunner: workflowRunner !== null && workflowRunner !== undefined
    readonly property bool isWorkflowRunning: hasWorkflowRunner ? workflowRunner.execution_state === 1 : false
    readonly property bool hasCurrentWorkflow: hasWorkflowRunner ? workflowRunner.current_workflow !== "" : false
    readonly property bool hasCurrentAction: currentActionText.text !== undefined && currentActionText.text !== ""
    readonly property bool hasActionDescription: actionDescriptionText.text !== undefined && actionDescriptionText.text !== ""
    readonly property bool hasWorkflowProgress: hasWorkflowRunner ? workflowRunner.current_action_index >= 0 : false
    
    // Only visible when workflow is running
    visible: isWorkflowRunning
    
    // Runtime formatter function
    function formatRuntime(seconds) {
        var hrs = Math.floor(seconds / 3600)
        var mins = Math.floor((seconds % 3600) / 60)
        var secs = seconds % 60
        
        if (hrs > 0) {
            return hrs + "h " + mins + "m " + secs + "s"
        } else if (mins > 0) {
            return mins + "m " + secs + "s"
        } else {
            return secs + "s"
        }
    }
    
    // Blinking border animation
    Rectangle {
        id: blinkingBorder
        anchors.fill: parent
        color: "transparent"
        border.width: 4
        border.color: CommonStyle.videoBorderEnabled
        radius: 0
        
        SequentialAnimation on opacity {
            running: root.visible
            loops: Animation.Infinite
            
            NumberAnimation {
                from: 1.0
                to: 0.3
                duration: 800
                easing.type: Easing.InOutQuad
            }
            
            NumberAnimation {
                from: 0.3
                to: 1.0
                duration: 800
                easing.type: Easing.InOutQuad
            }
        }
    }
    
    // Status display at left middle side
    Rectangle {
        anchors {
            left: parent.left
            verticalCenter: parent.verticalCenter
            leftMargin: CommonStyle.videoPanelSideMargin
        }
        width: Math.max(statusLayout.implicitWidth + 40, 300)
        height: statusLayout.implicitHeight + 30
        color: CommonStyle.videoSurfaceStrong
        border.color: CommonStyle.videoBorderEnabled
        border.width: 2
        radius: CommonStyle.radiusSm
        
        ColumnLayout {
            id: statusLayout
            anchors {
                left: parent.left
                right: parent.right
                verticalCenter: parent.verticalCenter
                leftMargin: 20
                rightMargin: 20
            }
            spacing: 8
            
            // Status indicator
            RowLayout {
                Layout.alignment: Qt.AlignLeft
                spacing: CommonStyle.spacingSm + 2
                
                // Animated indicator
                Rectangle {
                    width: 16
                    height: 16
                    radius: 8
                    color: CommonStyle.videoBorderEnabled
                    
                    SequentialAnimation on scale {
                        running: root.visible
                        loops: Animation.Infinite
                        
                        NumberAnimation {
                            from: 1.0
                            to: 1.3
                            duration: 600
                        }
                        
                        NumberAnimation {
                            from: 1.3
                            to: 1.0
                            duration: 600
                        }
                    }
                }
                
                Text {
                    text: "WORKFLOW RUNNING"
                    color: CommonStyle.videoBorderEnabled
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontBody + 2
                    font.bold: true
                }
            }
            
            // Loop iteration indicator (only shown when looping)
            RowLayout {
                Layout.alignment: Qt.AlignLeft
                spacing: 8
                visible: hasWorkflowRunner ? workflowRunner.is_loop_enabled : false
                
                Rectangle {
                    width: 12
                    height: 12
                    radius: 6
                    color: CommonStyle.videoLoop
                }
                
                Text {
                      text: workflowRunner && workflowRunner.loop_iteration > 0 
                          ? "Loop Iteration: " + workflowRunner.loop_iteration
                          : "Loop: Enabled"
                    color: CommonStyle.videoLoop
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption + 1
                    font.bold: true
                }
            }
            
            // Runtime display
            RowLayout {
                Layout.alignment: Qt.AlignLeft
                spacing: 8
                
                Rectangle {
                    width: 12
                    height: 12
                    radius: 6
                    color: CommonStyle.videoRuntime
                }
                
                Text {
                    id: runtimeText
                    text: "Runtime: " + formatRuntime(workflowRunner ? workflowRunner.workflow_runtime : 0)
                    color: CommonStyle.videoRuntime
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption + 1
                    font.bold: true
                }
            }
            
            // WorkFlow name
            Text {
                Layout.alignment: Qt.AlignLeft
                text: hasWorkflowRunner ? workflowRunner.current_workflow : ""
                color: CommonStyle.textPrimary
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption + 1
                visible: hasCurrentWorkflow
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: CommonStyle.videoDivider
                visible: hasCurrentAction
            }
            
            // Current action display
            ColumnLayout {
                Layout.alignment: Qt.AlignLeft
                spacing: 4
                visible: hasCurrentAction
                
                Text {
                    Layout.alignment: Qt.AlignLeft
                    text: "Current Action:"
                    color: CommonStyle.textSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontLabel
                }
                
                Text {
                    id: currentActionText
                    Layout.alignment: Qt.AlignLeft
                    text: workflowRunner ? workflowRunner.current_action_display : ""
                    color: CommonStyle.videoAction
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption + 1
                    font.bold: true
                }
                
                // Action description
                Text {
                    id: actionDescriptionText
                    Layout.alignment: Qt.AlignLeft
                    text: hasWorkflowRunner ? workflowRunner.current_action_description : ""
                    color: CommonStyle.textSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontLabel
                    visible: hasActionDescription
                }
            }
            
            // Progress indicator
            RowLayout {
                Layout.alignment: Qt.AlignLeft
                Layout.topMargin: 4
                spacing: 8
                visible: hasWorkflowProgress
                
                Text {
                    text: "Progress:"
                    color: "#AAAAAA"
                    font.family: "Helvetica"
                    font.pixelSize: 11
                }
                
                Text {
                    text: workflowRunner ? workflowRunner.workflow_progress_text : ""
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 12
                    font.bold: true
                }
            }
        }
    }
}
