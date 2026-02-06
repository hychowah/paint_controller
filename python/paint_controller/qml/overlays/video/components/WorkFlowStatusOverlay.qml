import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    anchors.fill: parent
    
    // Only visible when workflow is running
    visible: workFlowRunner && workFlowRunner.execution_state === 1
    
    // Blinking border animation
    Rectangle {
        id: blinkingBorder
        anchors.fill: parent
        color: "transparent"
        border.width: 4
        border.color: "#00FF00"  // Green border
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
            leftMargin: 20
        }
        width: Math.max(statusLayout.implicitWidth + 40, 300)
        height: statusLayout.implicitHeight + 30
        color: "#CC000000"  // Semi-transparent black
        border.color: "#00FF00"
        border.width: 2
        radius: 8
        
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
                spacing: 10
                
                // Animated indicator
                Rectangle {
                    width: 16
                    height: 16
                    radius: 8
                    color: "#00FF00"
                    
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
                    color: "#00FF00"
                    font.family: "Helvetica"
                    font.pixelSize: 18
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
                    color: "#FFD700"  // Gold color for loop indicator
                }
                
                Text {
                    text: workFlowRunner && workFlowRunner.loop_iteration > 0 
                          ? "Loop Iteration: " + workFlowRunner.loop_iteration
                          : "Loop: Enabled"
                    color: "#FFD700"
                    font.family: "Helvetica"
                    font.pixelSize: 14
                    font.bold: true
                }
            }
            
            // WorkFlow name
            Text {
                Layout.alignment: Qt.AlignLeft
                text: workFlowRunner ? workFlowRunner.current_workflow : ""
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 14
                visible: workFlowRunner && workFlowRunner.current_workflow !== ""
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: "#444444"
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
                    color: "#AAAAAA"
                    font.family: "Helvetica"
                    font.pixelSize: 11
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
                    color: "#FFFF00"  // Yellow for current action
                    font.family: "Helvetica"
                    font.pixelSize: 14
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
                    color: "#CCCCCC"
                    font.family: "Helvetica"
                    font.pixelSize: 11
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
