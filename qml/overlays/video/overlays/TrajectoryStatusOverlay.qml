import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    anchors.fill: parent
    
    // Only visible when trajectory is running
    visible: trajectoryRunner && trajectoryRunner.execution_state === 1
    
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
    
    // Status display at bottom middle (above wall detection)
    Rectangle {
        anchors {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: 150  // Position above wall detection overlay
        }
        width: Math.max(statusLayout.implicitWidth + 40, 300)
        height: statusLayout.implicitHeight + 30
        color: "#CC000000"  // Semi-transparent black
        border.color: "#00FF00"
        border.width: 2
        radius: 8
        
        ColumnLayout {
            id: statusLayout
            anchors.centerIn: parent
            spacing: 8
            
            // Status indicator
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
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
                    text: "TRAJECTORY RUNNING"
                    color: "#00FF00"
                    font.family: "Helvetica"
                    font.pixelSize: 18
                    font.bold: true
                }
            }
            
            // Trajectory name
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: trajectoryRunner ? trajectoryRunner.current_trajectory : ""
                color: "#FFFFFF"
                font.family: "Helvetica"
                font.pixelSize: 14
                visible: trajectoryRunner && trajectoryRunner.current_trajectory !== ""
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                Layout.leftMargin: 20
                Layout.rightMargin: 20
                color: "#444444"
                visible: currentActionText.text !== ""
            }
            
            // Current action display
            ColumnLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 4
                visible: currentActionText.text !== ""
                
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: "Current Action:"
                    color: "#AAAAAA"
                    font.family: "Helvetica"
                    font.pixelSize: 11
                }
                
                Text {
                    id: currentActionText
                    Layout.alignment: Qt.AlignHCenter
                    text: {
                        if (!trajectoryRunner) return ""
                        
                        var actions = trajectoryRunner.get_current_trajectory_actions()
                        var currentIndex = trajectoryRunner.current_action_index
                        
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
                    Layout.alignment: Qt.AlignHCenter
                    text: {
                        if (!trajectoryRunner) return ""
                        
                        var actions = trajectoryRunner.get_current_trajectory_actions()
                        var currentIndex = trajectoryRunner.current_action_index
                        
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
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 4
                spacing: 8
                visible: trajectoryRunner && trajectoryRunner.current_action_index >= 0
                
                Text {
                    text: "Progress:"
                    color: "#AAAAAA"
                    font.family: "Helvetica"
                    font.pixelSize: 11
                }
                
                Text {
                    text: {
                        if (!trajectoryRunner) return ""
                        
                        var actions = trajectoryRunner.get_current_trajectory_actions()
                        var current = trajectoryRunner.current_action_index + 1
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
