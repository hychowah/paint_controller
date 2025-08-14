import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import "../"
import "../components"

Item {
    id: winchPageRoot
    objectName: "winchPageRoot"
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    // Added: Constants for reusable styling
    property color primaryColor: "#2196F3"
    property color dangerColor: "#F44336"
    property color successColor: "#4CAF50"
    property color warningColor: "#FF9800"
    property color disabledColor: "#BDBDBD"
    
    // Added: Notification component
    Popup {
        id: notificationPopup
        width: 300
        height: 60
        x: (parent.width - width) / 2
        y: parent.height - height - 20
        modal: false
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        
        background: Rectangle {
            color: "#323232"
            radius: 8
        }
        
        contentItem: Text {
            id: notificationText
            color: "white"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            font.pixelSize: 14
        }
        
        function show(message, duration) {
            notificationText.text = message;
            open();
            closeTimer.interval = duration || 3000;
            closeTimer.restart();
        }
        
        Timer {
            id: closeTimer
            onTriggered: notificationPopup.close()
        }
    }
    
    Rectangle {
        id: dataRect
        width: Math.min(parent.width * 0.95, 1200)
        height: Math.min(parent.height * 0.9, 680)
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 20
        
        // Added: Border for better depth perception
        border.width: 1
        border.color: "#CCCCCC"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 15
            
            Rectangle {
                Layout.preferredWidth: parent.width * 0.6
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                
                // Added: Subtle border for visual depth
                border.width: 1
                border.color: "#E0E0E0"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        color: winchController.available ? "#E3F2FD" : "#FFEBEE"
                        radius: 12
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Rectangle {
                                width: 12
                                height: 12
                                radius: 6
                                color: winchController.available ? primaryColor : dangerColor
                                
                                // Added: Pulsing animation for status indicator
                                SequentialAnimation on opacity {
                                    running: winchController.available
                                    loops: Animation.Infinite
                                    PropertyAnimation { to: 0.6; duration: 1000 }
                                    PropertyAnimation { to: 1.0; duration: 1000 }
                                }
                            }
                            
                            Text {
                                text: "Winch Control"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                text: winchController.available ? "Connected" : "Disconnected"
                                color: winchController.available ? primaryColor : dangerColor
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }
                    
                    // Winch Power control with relative sizing and aligned switches
                    // Winch Power control with fixed layout to avoid recursive rearrangement
                    Rectangle {
                        id: winchPowerControl
                        Layout.fillWidth: true
                        height: 50  // Base height - can be adjusted as needed
                        color: winchController.enabled ? "#E3F2FD" : "#F5F5F5"
                        radius: 12
                        border.width: 1
                        border.color: winchController.enabled ? "#90CAF9" : "#E0E0E0"
                        
                        // Use Row instead of RowLayout to avoid recursive layout issues
                        Row {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            // Status indicator with fixed size
                            Rectangle {
                                id: powerIndicator
                                width: parent.height * 1
                                height: parent.height * 1
                                anchors.verticalCenter: parent.verticalCenter
                                radius: width / 2
                                color: winchController.enabled ? primaryColor : disabledColor
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "⚡"  // Power symbol
                                    color: "white"
                                    font.pixelSize: 24
                                    font.bold: true
                                }
                            }
                            
                            // Text content with fixed width calculated from parent
                            Column {
                                id: powerTextColumn
                                width: parent.width - powerIndicator.width - powerToggleContainer.width - parent.spacing * 2
                                height: parent.height
                                spacing: 4
                                anchors.verticalCenter: parent.verticalCenter
                                
                                Text {
                                    width: parent.width
                                    text: "Winch Power"
                                    font.pixelSize: parent.height * 0.6
                                    font.bold: true
                                    color: "#212121"
                                    elide: Text.ElideRight
                                }
                                
                                Text {
                                    width: parent.width
                                    text: winchController.enabled ? "Enabled - Motor active" : "Disabled - Motor inactive"
                                    font.pixelSize: parent.height * 0.4
                                    color: winchController.enabled ? primaryColor : "#757575"
                                    elide: Text.ElideRight
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                }
                            }
                            
                            // Fixed size container for switch to ensure alignment
                            Item {
                                id: powerToggleContainer
                                width: 88  // Fixed width
                                height: parent.height
                                
                                Rectangle {
                                    id: switchTrack
                                    width: parent.height * 2
                                    height: parent.height * 1
                                    radius: height / 2
                                    anchors.centerIn: parent
                                    color: winchController.enabled ? primaryColor : "#E0E0E0"
                                    
                                    Behavior on color {
                                        ColorAnimation { duration: 200 }
                                    }
                                }
                                
                                Rectangle {
                                    id: switchHandle
                                    width: parent.height * 1
                                    height: parent.height * 1
                                    radius: width / 2
                                    color: "white"
                                    border.width: 2
                                    border.color: winchController.enabled ? primaryColor : "#BDBDBD"
                                    anchors.verticalCenter: switchTrack.verticalCenter
                                    x: powerToggleContainer.width/2 - width/2 + (winchController.enabled ? 15 : -15)
                                    
                                    Behavior on x {
                                        NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
                                    }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        winchController.setEnabled(!winchController.enabled);
                                        notificationPopup.show(winchController.enabled ? 
                                            "Winch power enabled" : "Winch power disabled", 2000);
                                    }
                                    enabled: winchController.available
                                    
                                    onPressed: switchHandle.opacity = 0.8
                                    onReleased: switchHandle.opacity = 1.0
                                }
                            }
                        }
                    }

                    // Load Detection Switch with fixed layout
                    Rectangle {
                        id: loadDetectionControl
                        Layout.fillWidth: true
                        height: 50  // Same height as winch power control for consistency
                        color: winchController.load_detection_enabled ? "#E3F2FD" : "#F5F5F5"
                        radius: 12
                        border.width: 1
                        border.color: winchController.load_detection_enabled ? "#90CAF9" : "#E0E0E0"
                        
                        // Use Row instead of RowLayout to avoid recursive layout issues
                        Row {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            Rectangle {
                                id: loadIndicator
                                width: parent.height * 1
                                height: parent.height * 1
                                anchors.verticalCenter: parent.verticalCenter
                                radius: width / 2
                                color: winchController.load_detection_enabled ? primaryColor : disabledColor
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "⚖"  // Scale/balance symbol
                                    color: "white"
                                    font.pixelSize: 24
                                    font.bold: true
                                }
                            }
                            
                            Column {
                                id: loadTextColumn
                                width: parent.width - loadIndicator.width - loadToggleContainer.width - parent.spacing * 2
                                height: parent.height
                                spacing: 4
                                anchors.verticalCenter: parent.verticalCenter
                                
                                Text {
                                    width: parent.width
                                    text: "Load Detection"
                                    font.pixelSize: parent.height * 0.6
                                    font.bold: true
                                    color: "#212121"
                                    elide: Text.ElideRight
                                }
                                
                                Text {
                                    width: parent.width
                                    text: winchController.load_detection_enabled ? 
                                        "Enabled - Safety active" : 
                                        "Disabled - No load protection"
                                    font.pixelSize: parent.height * 0.4
                                    color: winchController.load_detection_enabled ? primaryColor : "#757575"
                                    elide: Text.ElideRight
                                    wrapMode: Text.Wrap
                                    maximumLineCount: 2
                                }
                            }
                            
                            Item {
                                id: loadToggleContainer
                                width: 88  // Same fixed width as power toggle
                                height: parent.height
                                
                                Rectangle {
                                    id: loadSwitchTrack
                                    width: parent.height * 2
                                    height: parent.height * 1
                                    radius: height / 2
                                    anchors.centerIn: parent
                                    color: winchController.load_detection_enabled ? primaryColor : "#E0E0E0"
                                    
                                    Behavior on color {
                                        ColorAnimation { duration: 200 }
                                    }
                                }
                                
                                Rectangle {
                                    id: loadSwitchHandle
                                    width: parent.height * 1
                                    height: parent.height * 1
                                    radius: width / 2
                                    color: "white"
                                    border.width: 2
                                    border.color: winchController.load_detection_enabled ? primaryColor : "#BDBDBD"
                                    anchors.verticalCenter: loadSwitchTrack.verticalCenter
                                    x: loadToggleContainer.width/2 - width/2 + (winchController.load_detection_enabled ? 15 : -15)
                                    
                                    Behavior on x {
                                        NumberAnimation { duration: 200; easing.type: Easing.InOutQuad }
                                    }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        winchController.setLoadDetectionEnabled(!winchController.load_detection_enabled);
                                        notificationPopup.show(winchController.load_detection_enabled ? 
                                            "Load detection enabled" : 
                                            "Load detection disabled", 2000);
                                    }
                                    enabled: winchController.enabled
                                    
                                    onPressed: loadSwitchHandle.opacity = 0.8
                                    onReleased: loadSwitchHandle.opacity = 1.0
                                }
                            }
                        }
                    }
                                        
                    // Added: History log component
                    Rectangle {
                        id: historyLog
                        Layout.fillWidth: true
                        height: 80
                        color: "#F5F5F5"
                        radius: 12
                        visible: winchController.enabled
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 5
                            
                            Text {
                                text: "Recent Activity"
                                font.pixelSize: 14
                                font.bold: true
                                color: "#212121"
                            }
                            
                            ListView {
                                id: activityListView
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: ListModel { id: activityModel }
                                delegate: Text {
                                    text: timestamp + ": " + activity
                                    font.pixelSize: 12
                                    color: "#424242"
                                }
                                
                                // Sample data - in real app, would be populated from controller
                                Component.onCompleted: {
                                    activityModel.append({timestamp: "10:42:15", activity: "Cable extended to 1800mm"})
                                    activityModel.append({timestamp: "10:40:03", activity: "System initialized"})
                                }
                            }
                        }
                    }
                    
                    GridLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        columns: 2
                        rowSpacing: 15
                        columnSpacing: 15
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#F5F5F5"
                            radius: 12
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10
                                
                                Text {
                                    text: "Move Increment"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 10
                                    columnSpacing: 10
                                    
                                    Text { 
                                        text: "Length (mm)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    // Improved: Input field with units and validation feedback
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        
                                        TextField {
                                            id: incrementLengthField
                                            Layout.fillWidth: true
                                            selectByMouse: true
                                            placeholderText: "Enter length"
                                            enabled: winchController.enabled
                                            validator: IntValidator { bottom: -10000; top: 10000 }
                                            
                                            background: Rectangle {
                                                radius: 6
                                                border.color: incrementLengthField.acceptableInput ? "#BDBDBD" : dangerColor
                                                border.width: 1
                                            }
                                            
                                            onTextChanged: {
                                                if (text && !acceptableInput) {
                                                    errorToolTip.text = "Enter a value between -10000 and 10000"
                                                    errorToolTip.visible = true
                                                } else {
                                                    errorToolTip.visible = false
                                                }
                                            }
                                            
                                            ToolTip {
                                                id: errorToolTip
                                                visible: false
                                                delay: 500
                                                timeout: 5000
                                                contentItem: Text {
                                                    color: "white"
                                                    text: errorToolTip.text
                                                }
                                                
                                                background: Rectangle {
                                                    color: dangerColor
                                                    radius: 4
                                                }
                                            }
                                        }
                                    }
                                    
                                    Text { 
                                        text: "Speed (mm/s)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    // Improved: Added a slider for speed selection
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        
                                        TextField {
                                            id: incrementSpeedField
                                            Layout.fillWidth: true
                                            selectByMouse: true
                                            text: "500"
                                            enabled: winchController.enabled
                                            validator: IntValidator { bottom: 1; top: 1000 }
                                            
                                            background: Rectangle {
                                                radius: 6
                                                border.color: incrementSpeedField.acceptableInput ? "#BDBDBD" : dangerColor
                                                border.width: 1
                                            }
                                            
                                            onTextChanged: {
                                                if (text && parseInt(text) > 0 && parseInt(text) <= 1000) {
                                                    incrementSpeedSlider.value = parseInt(text)
                                                }
                                            }
                                        }
                                        
                                        Slider {
                                            id: incrementSpeedSlider
                                            Layout.fillWidth: true
                                            from: 1
                                            to: 1000
                                            stepSize: 10
                                            value: 500
                                            enabled: winchController.enabled
                                            
                                            onValueChanged: {
                                                incrementSpeedField.text = Math.round(value).toString()
                                            }
                                        }
                                    }
                                }
                                
                                // Added: Quick preset buttons
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 5
                                    
                                    Button {
                                        text: "10mm"
                                        enabled: winchController.enabled
                                        onClicked: incrementLengthField.text = "10"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                    
                                    Button {
                                        text: "100mm"
                                        enabled: winchController.enabled
                                        onClicked: incrementLengthField.text = "100"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                    
                                    Button {
                                        text: "500mm"
                                        enabled: winchController.enabled
                                        onClicked: incrementLengthField.text = "500"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                }
                                
                                Item { Layout.fillHeight: true }
                                
                                Button {
                                    Layout.fillWidth: true
                                    text: "MOVE INCREMENT"
                                    enabled: winchController.enabled && incrementLengthField.text.length > 0 && incrementSpeedField.text.length > 0 && incrementLengthField.acceptableInput && incrementSpeedField.acceptableInput
                                    onClicked: {
                                        winchController.moveIncrement(
                                            parseInt(incrementLengthField.text),
                                            parseInt(incrementSpeedField.text)
                                        );
                                        // Added: Feedback and logging
                                        notificationPopup.show("Moving increment: " + incrementLengthField.text + "mm", 2000);
                                        activityModel.insert(0, {
                                            timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
                                            activity: "Increment move: " + incrementLengthField.text + "mm"
                                        });
                                    }
                                    
                                    background: Rectangle {
                                        radius: 6
                                        color: parent.enabled ? primaryColor : disabledColor
                                    }
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: "white"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#F5F5F5"
                            radius: 12
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10
                                
                                Text {
                                    text: "Move Absolute"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 10
                                    columnSpacing: 10
                                    
                                    Text { 
                                        text: "Position (mm)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 0
                                        
                                        TextField {
                                            id: absoluteLengthField
                                            Layout.fillWidth: true
                                            selectByMouse: true
                                            placeholderText: "Enter position"
                                            enabled: winchController.enabled
                                            validator: IntValidator { bottom: 0; top: 10000 }
                                            
                                            background: Rectangle {
                                                radius: 6
                                                border.color: absoluteLengthField.acceptableInput ? "#BDBDBD" : dangerColor
                                                border.width: 1
                                            }
                                        }
                                    }
                                    
                                    Text { 
                                        text: "Speed (mm/s)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 5
                                        
                                        TextField {
                                            id: absoluteSpeedField
                                            Layout.fillWidth: true
                                            selectByMouse: true
                                            text: "500"
                                            enabled: winchController.enabled
                                            validator: IntValidator { bottom: 1; top: 1000 }
                                            
                                            background: Rectangle {
                                                radius: 6
                                                border.color: absoluteSpeedField.acceptableInput ? "#BDBDBD" : dangerColor
                                                border.width: 1
                                            }
                                            
                                            onTextChanged: {
                                                if (text && parseInt(text) > 0 && parseInt(text) <= 1000) {
                                                    absoluteSpeedSlider.value = parseInt(text)
                                                }
                                            }
                                        }
                                        
                                        Slider {
                                            id: absoluteSpeedSlider
                                            Layout.fillWidth: true
                                            from: 1
                                            to: 1000
                                            stepSize: 10
                                            value: 500
                                            enabled: winchController.enabled
                                            
                                            onValueChanged: {
                                                absoluteSpeedField.text = Math.round(value).toString()
                                            }
                                        }
                                    }
                                }
                                
                                // Added: Position presets
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 5
                                    
                                    Button {
                                        text: "Home"
                                        enabled: winchController.enabled
                                        onClicked: absoluteLengthField.text = "0"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                    
                                    Button {
                                        text: "Mid"
                                        enabled: winchController.enabled
                                        onClicked: absoluteLengthField.text = "5000"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                    
                                    Button {
                                        text: "Max"
                                        enabled: winchController.enabled
                                        onClicked: absoluteLengthField.text = "10000"
                                        
                                        contentItem: Text {
                                            text: parent.text
                                            font.pixelSize: 12
                                            color: primaryColor
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#E3F2FD"
                                            border.color: primaryColor
                                            border.width: 1
                                        }
                                    }
                                }
                                
                                Item { Layout.fillHeight: true }
                                
                                Button {
                                    Layout.fillWidth: true
                                    text: "GO TO POSITION"
                                    enabled: winchController.enabled && absoluteLengthField.text.length > 0 && absoluteSpeedField.text.length > 0 // && absoluteLengthField.acceptableInput && absoluteSpeedField.acceptableInput
                                    onClicked: {
                                        winchController.moveAbsolute(
                                            parseInt(absoluteLengthField.text),
                                            parseInt(absoluteSpeedField.text)
                                        );
                                        // Added: Feedback and logging
                                        notificationPopup.show("Moving to position: " + absoluteLengthField.text + "mm", 2000);
                                        activityModel.insert(0, {
                                            timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
                                            activity: "Absolute move to: " + absoluteLengthField.text + "mm"
                                        });
                                    }
                                    
                                    background: Rectangle {
                                        radius: 6
                                        color: parent.enabled ? primaryColor : disabledColor
                                    }
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: "white"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 60
                        color: "#F5F5F5"
                        radius: 12
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Button {
                                Layout.fillWidth: true
                                text: "Retract Full"
                                enabled: winchController.enabled
                                onClicked: {
                                    winchController.move_abosulte(0, 500);
                                    // Added: Feedback and logging
                                    notificationPopup.show("Retracting cable fully", 2000);
                                    activityModel.insert(0, {
                                        timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
                                        activity: "Full retraction initiated"
                                    });
                                }
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? primaryColor : disabledColor
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            
                            // Improved: Emergency stop button
                            Button {
                                Layout.fillWidth: true
                                Layout.preferredWidth: parent.width * 1.2
                                text: "EMERGENCY STOP"
                                enabled: winchController.enabled
                                onClicked: {
                                    winchController.move_increment(0, 0);
                                    // Added: Feedback and logging
                                    notificationPopup.show("EMERGENCY STOP ACTIVATED", 3000);
                                    activityModel.insert(0, {
                                        timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
                                        activity: "Emergency stop activated"
                                    });
                                }
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? dangerColor : disabledColor
                                    
                                    // Added: Pulsing animation for emergency button
                                    SequentialAnimation on opacity {
                                        running: winchController.enabled
                                        loops: Animation.Infinite
                                        PropertyAnimation { to: 0.8; duration: 800 }
                                        PropertyAnimation { to: 1.0; duration: 800 }
                                    }
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            
                            Button {
                                Layout.fillWidth: true
                                text: "Extend 1m"
                                enabled: winchController.enabled
                                onClicked: {
                                    winchController.move_increment(1000, 500);
                                    // Added: Feedback and logging
                                    notificationPopup.show("Extending cable by 1m", 2000);
                                    activityModel.insert(0, {
                                        timestamp: new Date().toLocaleTimeString(Qt.locale(), "hh:mm:ss"),
                                        activity: "1m extension initiated"
                                    });
                                }
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? primaryColor : disabledColor
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                
                // Added: Subtle border for visual depth
                border.width: 1
                border.color: "#E0E0E0"
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15
                    
                    // Improved: More prominent abnormal load warning
                    Rectangle {
                        Layout.fillWidth: true
                        height: 60
                        visible: winchController.load_detection_enabled && winchController.unusual_load_detected
                        color: "#FFEBEE"
                        radius: 12
                        
                        // Added: Pulsing animation for warning
                        SequentialAnimation on opacity {
                            running: winchController.load_detection_enabled && winchController.unusual_load_detected
                            loops: Animation.Infinite
                            PropertyAnimation { to: 0.7; duration: 500 }
                            PropertyAnimation { to: 1.0; duration: 500 }
                        }
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Rectangle {
                                width: 24
                                height: 24
                                radius: 12
                                color: dangerColor
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "!"
                                    color: "white"
                                    font.bold: true
                                    font.pixelSize: 16
                                }
                            }
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                
                                Text {
                                    text: "UNUSUAL LOAD DETECTED"
                                    font.bold: true
                                    color: dangerColor
                                    font.pixelSize: 16
                                }
                                
                                Text {
                                    text: "Immediate attention required"
                                    color: "#D32F2F"
                                    font.pixelSize: 12
                                }
                            }
                            
                            Button {
                                text: "RESET"
                                onClicked: {
                                    // Reset would be handled by controller
                                    notificationPopup.show("Load alarm acknowledged", 2000);
                                }
                                
                                background: Rectangle {
                                    radius: 4
                                    color: "#FFCDD2"
                                    border.color: dangerColor
                                    border.width: 1
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: dangerColor
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                    
                    // Cable Status Section
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 220
                        color: "#F5F5F5"
                        radius: 12
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10
                            
                            Text {
                                text: "Cable Status"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            // Card-based layout for cable metrics
                            Flow {
                                Layout.fillWidth: true
                                spacing: 10
                                
                                // Cable Length card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 110
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: "#E0E0E0"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        Text { 
                                            text: "Cable Length" 
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        Text { 
                                            text: Math.round(winchController.cable_length)
                                            font.pixelSize: 36
                                            font.bold: true
                                            color: "#2196F3"
                                        }
                                        
                                        Text { 
                                            text: "mm"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        // Visual indicator of how close to max length
                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 4
                                            color: "#E0E0E0"
                                            radius: 2
                                            
                                            Rectangle {
                                                width: Math.min(parent.width * (winchController.cable_length / 10000), parent.width)
                                                height: parent.height
                                                radius: 2
                                                color: {
                                                    const percent = winchController.cable_length / 100;
                                                    if (percent < 70) return "#2196F3";
                                                    else if (percent < 90) return "#FF9800";
                                                    else return "#F44336";
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                // Cable Speed card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 110
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: "#E0E0E0"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        Text { 
                                            text: "Cable Speed" 
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        RowLayout {
                                            spacing: 4
                                            
                                            Text { 
                                                text: winchController.cable_speed.toFixed(1)
                                                font.pixelSize: 36
                                                font.bold: true
                                                color: Math.abs(winchController.cable_speed) > 0.5 ? "#FF9800" : "#2196F3"
                                            }
                                            
                                            // Direction indicators
                                            Text {
                                                visible: Math.abs(winchController.cable_speed) > 0.05
                                                text: winchController.cable_speed > 0 ? "▶" : "◀"
                                                font.pixelSize: 24
                                                color: "#FF9800"
                                                Layout.alignment: Qt.AlignBottom
                                                Layout.bottomMargin: 6
                                            }
                                        }
                                        
                                        Text { 
                                            text: "mm/s"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        // Speed indicator
                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 4
                                            color: "#E0E0E0"
                                            radius: 2
                                            visible: Math.abs(winchController.cable_speed) > 0
                                            
                                            Rectangle {
                                                property real maxSpeed: 500 // Maximum expected speed in m/s
                                                width: Math.min(parent.width * (Math.abs(winchController.cable_speed) / maxSpeed), parent.width)
                                                height: parent.height
                                                radius: 2
                                                color: Math.abs(winchController.cable_speed) > 1.5 ? "#FF9800" : "#2196F3"
                                            }
                                        }
                                    }
                                }
                            }
                            
                            // Cable Extension visual indicator
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 60
                                color: "#FFFFFF"
                                radius: 8
                                border.width: 1
                                border.color: "#E0E0E0"
                                
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 6
                                    
                                    RowLayout {
                                        Layout.fillWidth: true
                                        
                                        Text {
                                            text: "Cable Extension"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        Item { Layout.fillWidth: true }
                                        
                                        Text {
                                            text: Math.round(winchController.cable_length / 100) + "%"
                                            font.pixelSize: 16
                                            font.bold: true
                                            color: {
                                                const percent = winchController.cable_length / 100;
                                                if (percent < 70) return "#2196F3";
                                                else if (percent < 90) return "#FF9800";
                                                else return "#F44336";
                                            }
                                        }
                                    }
                                    
                                    Rectangle {
                                        Layout.fillWidth: true
                                        height: 20
                                        color: "#E0E0E0"
                                        radius: 4
                                        
                                        Rectangle {
                                            id: extensionBar
                                            width: Math.min(parent.width * (winchController.cable_length / 10000), parent.width)
                                            height: parent.height
                                            radius: 4
                                            color: {
                                                const percent = winchController.cable_length / 100;
                                                if (percent < 70) return "#2196F3";
                                                else if (percent < 90) return "#FF9800";
                                                else return "#F44336";
                                            }
                                        }
                                        
                                        // Extension markers
                                        Row {
                                            anchors.fill: parent
                                            spacing: 0
                                            
                                            Repeater {
                                                model: 10
                                                
                                                Rectangle {
                                                    width: 1
                                                    height: parent.height
                                                    x: (index + 1) * (parent.width / 10)
                                                    color: "#9E9E9E"
                                                    visible: index > 0 && index < 9  // Skip first and last
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#F5F5F5"
                        radius: 12
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 10
                            
                            Text {
                                text: "Motor Metrics"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            // More visually engaging display with cards
                            Flow {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 10
                                
                                // Torque card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 90
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: winchController.winch_torque > 50 ? "#F44336" : "#E0E0E0"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        RowLayout {
                                            Layout.fillWidth: true
                                            
                                            Text { 
                                                text: "Torque" 
                                                font.pixelSize: 14
                                                color: "#757575"
                                            }
                                            
                                            Item { Layout.fillWidth: true }
                                            
                                            Rectangle {
                                                visible: winchController.winch_torque > 50
                                                width: 16
                                                height: 16
                                                radius: 8
                                                color: "#F44336"
                                                
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "!"
                                                    color: "white"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                }
                                            }
                                        }
                                        
                                        Text { 
                                            text: winchController.winch_torque.toFixed(1)
                                            font.pixelSize: 32
                                            font.bold: true
                                            color: {
                                                const torque = winchController.winch_torque;
                                                if (torque < 30) return "#2196F3"; 
                                                else if (torque < 50) return "#FF9800";
                                                else return "#F44336";
                                            }
                                        }
                                        
                                        Text { 
                                            text: "Nm"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                    }
                                }
                                
                                // Temperature card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 90
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: winchController.motor_temperature > 60 ? "#F44336" : "#E0E0E0"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        RowLayout {
                                            Layout.fillWidth: true
                                            
                                            Text { 
                                                text: "Temperature" 
                                                font.pixelSize: 14
                                                color: "#757575"
                                            }
                                            
                                            Item { Layout.fillWidth: true }
                                            
                                            Rectangle {
                                                visible: winchController.motor_temperature > 50
                                                width: 16
                                                height: 16
                                                radius: 8
                                                color: winchController.motor_temperature > 60 ? "#F44336" : "#FF9800"
                                                
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "!"
                                                    color: "white"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                }
                                            }
                                        }
                                        
                                        Text { 
                                            text: winchController.motor_temperature.toFixed(1)
                                            font.pixelSize: 32
                                            font.bold: true
                                            color: {
                                                const temp = winchController.motor_temperature;
                                                if (temp < 40) return "#2196F3";
                                                else if (temp < 60) return "#FF9800";
                                                else return "#F44336";
                                            }
                                        }
                                        
                                        Text { 
                                            text: "°C"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                    }
                                }
                                
                                // Voltage card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 90
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: (winchController.motor_voltage < 22 || winchController.motor_voltage > 25) ? "#F44336" : "#E0E0E0"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        RowLayout {
                                            Layout.fillWidth: true
                                            
                                            Text { 
                                                text: "Voltage" 
                                                font.pixelSize: 14
                                                color: "#757575"
                                            }
                                            
                                            Item { Layout.fillWidth: true }
                                            
                                            Rectangle {
                                                visible: winchController.motor_voltage < 22 || winchController.motor_voltage > 25
                                                width: 16
                                                height: 16
                                                radius: 8
                                                color: "#F44336"
                                                
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "!"
                                                    color: "white"
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                }
                                            }
                                        }
                                        
                                        Text { 
                                            text: winchController.motor_voltage.toFixed(1)
                                            font.pixelSize: 32
                                            font.bold: true
                                            color: {
                                                const voltage = winchController.motor_voltage;
                                                if (voltage > 22 && voltage < 25) return "#2196F3";
                                                else return "#F44336";
                                            }
                                        }
                                        
                                        Text { 
                                            text: "V"
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                    }
                                }
                                
                                // Brake status card
                                Rectangle {
                                    width: parent.width / 2 - 5
                                    height: 90
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: winchController.motor_brake ? "#F44336" : "#4CAF50"
                                    
                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 4
                                        
                                        Text { 
                                            text: "Brake" 
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        RowLayout {
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                            
                                            Rectangle {
                                                width: 16
                                                height: 16
                                                radius: 8
                                                color: winchController.motor_brake ? "#F44336" : "#4CAF50"
                                            }
                                            
                                            Text { 
                                                text: winchController.motor_brake ? "ENGAGED" : "RELEASED"
                                                font.pixelSize: 24
                                                font.bold: true
                                                color: winchController.motor_brake ? "#F44336" : "#4CAF50"
                                            }
                                        }
                                    }
                                }
                                
                                // Abnormal load card
                                Rectangle {
                                    width: parent.width - 0
                                    height: 60
                                    color: "#FFFFFF"
                                    radius: 8
                                    border.width: 1
                                    border.color: winchController.unusual_load_detected ? "#F44336" : "#4CAF50"
                                    
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        spacing: 10
                                        
                                        Text { 
                                            text: "Load Status:" 
                                            font.pixelSize: 14
                                            color: "#757575"
                                        }
                                        
                                        Rectangle {
                                            width: 16
                                            height: 16
                                            radius: 8
                                            color: winchController.unusual_load_detected ? "#F44336" : "#4CAF50"
                                        }
                                        
                                        Text { 
                                            text: winchController.unusual_load_detected ? "ABNORMAL" : "NORMAL"
                                            font.pixelSize: 24
                                            font.bold: true
                                            color: winchController.unusual_load_detected ? "#F44336" : "#4CAF50"
                                        }
                                        
                                        Item { Layout.fillWidth: true }
                                        
                                        Button {
                                            visible: winchController.unusual_load_detected
                                            text: "RESET"
                                            enabled: winchController.unusual_load_detected
                                            
                                            contentItem: Text {
                                                text: parent.text
                                                font.pixelSize: 12
                                                font.bold: true
                                                color: "#F44336"
                                                horizontalAlignment: Text.AlignHCenter
                                                verticalAlignment: Text.AlignVCenter
                                            }
                                            
                                            background: Rectangle {
                                                radius: 4
                                                color: "#FFEBEE"
                                                border.color: "#F44336"
                                                border.width: 1
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                }
            }
        }
    }
}