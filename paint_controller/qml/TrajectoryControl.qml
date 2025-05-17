// TrajectoryControl.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: control
    color: "#f5f7fa"  // Light background color
    radius: 8
    border.color: "#e0e5ec"
    border.width: 1

    property bool selected: false
    property var currentActions: []
    property int currentActionIndex: -1
    
    // Use a bound property to stay in sync with Python's execution state
    property bool isExecuting: trajectoryHandler.isExecuting
    
    // Connect to the Python signals
    Connections {
        target: trajectoryHandler
        
        // Handle the showMessage signal from Python
        function onShowMessage(message, isSuccess) {
            showMessage(message, isSuccess)
        }
        
        // Handle the executingChanged signal
        function onExecutingChanged(executing) {
            // When execution completes and was successful, prepare to move to next action after a delay
            if (!executing && control.currentActionIndex < control.currentActions.length - 1) {
                executionTimer.start()
            }
        }

        function onSequenceSaved(sequenceName) {
            // If this is the currently selected sequence, reload its actions
            if (control.selected) {
                // Find the index of the sequence
                for (let i = 0; i < trajectoryHandler.trajectory.length; i++) {
                    if (trajectoryHandler.trajectory[i].name === sequenceName) {
                        // Reload the current sequence data
                        trajectoryHandler.selectTrajectory(i)
                        control.currentActions = trajectoryHandler.getSelectedActions()
                        break
                    }
                }
            }
        }
    }
    
    // Helper functions for button appearance
    function getButtonColor() {
        if (control.isExecuting) {
            return "#51aef3"  // Blue when executing
        } else if (control.currentActionIndex >= 0) {
            return "#a1f9c6"  // Green when ready
        } else {
            return "#e0e5ec"  // Gray when disabled
        }
    }
    
    function getButtonTextColor() {
        if (control.isExecuting) {
            return "#ffffff"  // White text on blue background
        } else if (control.currentActionIndex >= 0) {
            return "#2d3436"  // Dark text on green background
        } else {
            return "#95a5a6"  // Light gray text on gray background
        }
    }
    
    // Use a timer to delay moving to the next action for better UI experience
    Timer {
        id: executionTimer
        interval: 1000 // ms
        repeat: false
        onTriggered: {
            control.currentActionIndex++
        }
    }

    // Add popup component
    Popup {
        id: messagePopup
        x: (parent.width - width) / 2
        y: (parent.height - height) / 2
        width: 300
        height: 150
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        property string message: ""
        property bool isSuccess: true
        
        background: Rectangle {
            color: messagePopup.isSuccess ? "#a1f9c6" : "#ff6b6b"
            radius: 8
            border.color: messagePopup.isSuccess ? "#7ae5ad" : "#e85757"
            border.width: 1
        }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 20
            
            Text {
                text: messagePopup.message
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                font.pixelSize: 16
                font.bold: true
                color: messagePopup.isSuccess ? "#2d3436" : "#ffffff"
            }
            
            Button {
                text: "OK"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 100
                Layout.preferredHeight: 36
                background: Rectangle {
                    radius: 6
                    color: messagePopup.isSuccess ? "#7ae5ad" : "#e85757"
                    border.width: 1
                    border.color: messagePopup.isSuccess ? "#65c295" : "#d44747"
                }
                
                contentItem: Text {
                    text: "OK"
                    color: "#ffffff"
                    font.pixelSize: 14
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                onClicked: messagePopup.close()
            }
        }
    }

    // Sequence List View
    Rectangle {
        anchors.fill: parent
        color: "transparent"
        visible: !selected
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 0
            spacing: 0
            
            // Header area
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                color: "#ffffff"
                radius: 8
                
                Text {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.leftMargin: 16
                    text: "Available Sequences"
                    font.pixelSize: 18
                    font.bold: true
                    color: "#2d3436"
                }
                
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: "#e0e5ec"
                }
            }
            
            // Sequences list
            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                ScrollBar.vertical.policy: ScrollBar.AsNeeded
                
                ListView {
                    anchors.fill: parent
                    model: trajectoryHandler.trajectory
                    spacing: 1
                    
                    delegate: Rectangle {
                        width: ListView.view.width
                        height: 60
                        color: "#ffffff"
                        
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: 8
                            radius: 6
                            color: "#ffffff"
                            border.color: "#e0e5ec"
                            border.width: 1
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12
                                
                                Rectangle {
                                    width: 32
                                    height: 32
                                    radius: 16
                                    color: "#1e88e5"
                                    
                                    Text {
                                        anchors.centerIn: parent
                                        text: (index + 1).toString()
                                        color: "#ffffff"
                                        font.pixelSize: 14
                                        font.bold: true
                                    }
                                }
                                
                                Text {
                                    Layout.fillWidth: true
                                    text: modelData.name
                                    elide: Text.ElideRight
                                    verticalAlignment: Text.AlignVCenter
                                    font.pixelSize: 16
                                    color: "#2d3436"
                                }
                                
                                // Arrow icon
                                Text {
                                    text: "›"
                                    font.pixelSize: 22
                                    font.bold: true
                                    color: "#1e88e5"
                                }
                            }
                            
                            MouseArea {
                                anchors.fill: parent
                                onClicked: {
                                    trajectoryHandler.selectTrajectory(index)
                                    control.currentActions = trajectoryHandler.getSelectedActions()
                                    control.selected = true
                                    control.currentActionIndex = 0
                                }
                                
                                // Hover effect
                                hoverEnabled: true
                                onEntered: parent.color = "#f0f5ff"
                                onExited: parent.color = "#ffffff"
                            }
                        }
                    }
                }
            }
        }
    }

    // Action Details View
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0
        visible: selected

        // Header with back button
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: "#ffffff"
            radius: 8
            
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                spacing: 8
                
                // Back button
                Rectangle {
                    width: 120
                    height: 36
                    color: "#f0f5ff"
                    border.color: "#e0e5ec"
                    border.width: 1
                    radius: 6
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 4
                        
                        // Back arrow
                        Text {
                            text: "←"
                            font.pixelSize: 18
                            font.bold: true
                            color: "#1e88e5"
                        }
                        
                        Text {
                            text: "Back"
                            font.pixelSize: 14
                            color: "#2d3436"
                        }
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            if (control.isExecuting) {
                                // Ask for confirmation if there's an action running
                                showMessage("Please wait for the current action to complete or use E-Stop to cancel.", false)
                            } else {
                                control.selected = false
                                control.currentActionIndex = -1
                            }
                        }
                        
                        // Hover effect
                        hoverEnabled: true
                        onEntered: parent.color = "#e1e9fd"
                        onExited: parent.color = "#f0f5ff"
                    }
                }
                
                Text {
                    text: "Sequence Actions"
                    font.pixelSize: 18
                    font.bold: true
                    color: "#2d3436"
                    Layout.fillWidth: true
                }
            }
            
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#e0e5ec"
            }
        }

        // Action list container
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 8
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            clip: true
            ScrollBar.vertical.policy: ScrollBar.AsNeeded
            
            ListView {
                anchors.fill: parent
                model: control.currentActions
                spacing: 8
                
                delegate: Rectangle {
                    width: ListView.view.width
                    height: Math.max(60, actionTextMetrics.height + 24)  // Dynamic height based on content
                    color: control.isExecuting && index === control.currentActionIndex ? 
                          "#e1e9fd" : "#ffffff"
                    border.color: control.isExecuting && index === control.currentActionIndex ? 
                                "#1e88e5" : "#e0e5ec"
                    border.width: 1
                    radius: 6

                    // Used to measure text height
                    TextMetrics {
                        id: actionTextMetrics
                        font.pixelSize: 14
                        text: modelData
                        elide: Text.ElideNone
                        elideWidth: parent.width - 80  // Leave space for indicators
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 12

                        // Indicator circle
                        Item {
                            width: 24
                            height: 24
                            Layout.alignment: Qt.AlignTop

                            Rectangle {
                                anchors.fill: parent
                                radius: 12
                                color: index === control.currentActionIndex ? 
                                       (control.isExecuting ? "#1e88e5" : "#1e88e5") : 
                                       "#f0f5ff"
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: control.isExecuting && index === control.currentActionIndex ? "▶" : "➔"
                                    color: index === control.currentActionIndex ? 
                                         (control.isExecuting ? "#ffffff" : "#ffffff") : 
                                         "#1e88e5"
                                    font.pixelSize: 12
                                    visible: index === control.currentActionIndex
                                }
                            }
                        }

                        // Action description text
                        Text {
                            text: modelData
                            Layout.fillWidth: true
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.Wrap
                            font.pixelSize: 14
                            color: "#2d3436"
                        }
                    }

                    MouseArea {
                        enabled: !control.isExecuting
                        anchors.fill: parent
                        onClicked: control.currentActionIndex = index
                        
                        // Hover effect
                        hoverEnabled: true
                        onEntered: {
                            if (index !== control.currentActionIndex) {
                                parent.color = "#f7f9fc"
                            }
                        }
                        onExited: {
                            if (index !== control.currentActionIndex) {
                                parent.color = "#ffffff"
                            }
                        }
                    }
                }
            }
        }

        // Control Buttons
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 70
            Layout.bottomMargin: 8
            Layout.leftMargin: 8
            Layout.rightMargin: 8
            color: "transparent"
            
            RowLayout {
                anchors.fill: parent
                spacing: 12
            

                // Start Next Action / Executing Button
                Rectangle {
                    id: executionButton
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: getButtonColor()
                    radius: 6
                    border.color: !control.isExecuting && control.currentActionIndex >= 0 ? "#7ae5ad" : "#d1d6e0"
                    border.width: 1

                    // Animation for pulsing during execution
                    SequentialAnimation {
                        id: pulseAnimation
                        running: control.isExecuting
                        loops: Animation.Infinite
                        
                        PropertyAnimation {
                            target: executionButton
                            property: "opacity"
                            from: 1.0
                            to: 0.7
                            duration: 800
                        }
                        
                        PropertyAnimation {
                            target: executionButton
                            property: "opacity"
                            from: 0.7
                            to: 1.0
                            duration: 800
                        }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: control.isExecuting ? "Executing..." : "Execute"
                        font.pixelSize: 16
                        font.bold: true
                        color: getButtonTextColor()
                    }

                    MouseArea {
                        enabled: !control.isExecuting && control.currentActionIndex >= 0
                        anchors.fill: parent
                        onClicked: {
                            // overlayController.avoidAutoRunOverwrite()
                            trajectoryHandler.startExecution(control.currentActionIndex)

                        }
                        
                        // Hover effect
                        hoverEnabled: true
                        onEntered: {
                            if (!control.isExecuting && control.currentActionIndex >= 0) {
                                parent.color = "#8cf0b6"
                            }
                        }
                        onExited: {
                            if (!control.isExecuting && control.currentActionIndex >= 0) {
                                parent.color = "#a1f9c6"
                            }
                        }
                        onPressed: {
                            if (!control.isExecuting && control.currentActionIndex >= 0) {
                                parent.color = "#7ae5ad"
                            }
                        }
                        onReleased: {
                            if (!control.isExecuting && control.currentActionIndex >= 0) {
                                parent.color = "#8cf0b6"
                            }
                        }
                    }
                }
            }
        }
    }
    
    function showMessage(message, isSuccess) {
        messagePopup.message = message
        messagePopup.isSuccess = isSuccess
        messagePopup.open()
    }
}