import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../../core"

Item {
    id: root
    anchors.fill: parent
    
    // Only visible when workflow is running
    visible: workFlowRunner && workFlowRunner.execution_state === 1
    
    // Timer to update runtime display
    Timer {
        running: root.visible
        interval: 1000  // Update every second
        repeat: true
        onTriggered: {
            // Force property re-evaluation
            runtimeText.text = formatRuntime(workFlowRunner ? workFlowRunner.workflow_runtime : 0)
        }
    }
    
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
                visible: workFlowRunner && workFlowRunner.is_loop_enabled
                
                Rectangle {
                    width: 12
                    height: 12
                    radius: 6
                    color: CommonStyle.videoLoop
                }
                
                Text {
                    text: workFlowRunner && workFlowRunner.loop_iteration > 0 
                          ? "Loop Iteration: " + workFlowRunner.loop_iteration
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
                    text: "Runtime: " + formatRuntime(workFlowRunner ? workFlowRunner.workflow_runtime : 0)
                    color: CommonStyle.videoRuntime
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption + 1
                    font.bold: true
                }
            }
            
            // WorkFlow name
            Text {
                Layout.alignment: Qt.AlignLeft
                text: workFlowRunner ? workFlowRunner.current_workflow : ""
                color: CommonStyle.textPrimary
                font.family: CommonStyle.fontSans
                font.pixelSize: CommonStyle.fontCaption + 1
                visible: workFlowRunner && workFlowRunner.current_workflow !== ""
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: CommonStyle.videoDivider
                visible: currentActionText.text !== ""
            }
            
            // Current action display
            ColumnLayout {
                Layout.alignment: Qt.AlignLeft
                spacing: 4
                visible: currentActionText.text !== ""
                
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
                    text: {
                        if (!workFlowRunner) return ""
                        
                        var actions = workFlowRunner.get_current_workflow_actions()
                        var currentIndex = workFlowRunner.current_action_index
                        
                        if (currentIndex >= 0 && currentIndex < actions.length) {
                            var action = actions[currentIndex]
                            return (currentIndex + 1) + ". " + action.name
                        }
                        return ""
                    }
                    color: CommonStyle.videoAction
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontCaption + 1
                    font.bold: true
                }
                
                // Action description
                Text {
                    Layout.alignment: Qt.AlignLeft
                    text: {
                        if (!workFlowRunner) return ""
                        
                        var actions = workFlowRunner.get_current_workflow_actions()
                        var currentIndex = workFlowRunner.current_action_index
                        
                        if (currentIndex >= 0 && currentIndex < actions.length) {
                            return actions[currentIndex].desc
                        }
                        return ""
                    }
                    color: CommonStyle.textSecondary
                    font.family: CommonStyle.fontSans
                    font.pixelSize: CommonStyle.fontLabel
                    visible: text !== ""
                }
            }
            
            // Progress indicator
            RowLayout {
                Layout.alignment: Qt.AlignLeft
                Layout.topMargin: 4
                spacing: 8
                visible: workFlowRunner && workFlowRunner.current_action_index >= 0
                
                Text {
                    text: "Progress:"
                    color: "#AAAAAA"
                    font.family: "Helvetica"
                    font.pixelSize: 11
                }
                
                Text {
                    text: {
                        if (!workFlowRunner) return ""
                        
                        var actions = workFlowRunner.get_current_workflow_actions()
                        var current = workFlowRunner.current_action_index + 1
                        var total = actions.length
                        
                        return current + " / " + total
                    }
                    color: "#FFFFFF"
                    font.family: "Helvetica"
                    font.pixelSize: 12
                    font.bold: true
                }
            }
        }
    }
}
