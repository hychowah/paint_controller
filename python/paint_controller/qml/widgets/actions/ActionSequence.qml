import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../components/buttons"
import "../../components/inputs"

Rectangle {
    id: actionSequence
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1
    clip: true

    property var sequence
    property var selectedInputField: ({ itemInx: -1, inputInx: -1 })
    property var currentSeq: ({ seqName: "Unnamed" })

    signal saveSequence

    // Debug function to log model data safely
    function logModelData() {
        console.log("=== Sequence Model Debug ===");
        console.log("Sequence count:", sequence ? sequence.count : "undefined");
        console.log("==========================");
    }

    KeyboardPopup {
        id: keyboardPopup
        anchors.centerIn: parent
        onTextUpdated: { currentSeq.seqName = newText }
        onClosed: { currentSeq.seqName = keyboardPopup.currentText }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // Header with sequence name and save button
        Rectangle {
            Layout.fillWidth: true
            height: 60
            color: "#f5f5f5"
            radius: 8
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 10
                
                Text { 
                    text: "Sequence"; 
                    font.pixelSize: 20; 
                    font.bold: true; 
                    color: "#333333"
                }
                
                Item { Layout.fillWidth: true }
                
                Text { 
                    text: "Name:"; 
                    font.pixelSize: 16;
                    color: "#555555"
                }
                
                Rectangle {
                    Layout.preferredWidth: 120
                    Layout.preferredHeight: 36
                    color: "#ffffff"
                    border.color: "#dddddd"
                    border.width: 1
                    radius: 6
                    
                    Text {
                        anchors.centerIn: parent
                        text: currentSeq.seqName
                        font.pixelSize: 14
                        color: "#333333"
                    }
                    
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            keyboardPopup.currentText = currentSeq.seqName
                            keyboardPopup.open()
                        }
                    }
                }
                
                Button {
                    id: saveButton
                    text: "Save"
                    Layout.preferredWidth: 80
                    Layout.preferredHeight: 36
                    
                    // Add states for visual feedback
                    states: [
                        State {
                            name: "pressed"
                            when: saveButton.pressed
                            PropertyChanges {
                                target: buttonBackground
                                color: "#388E3C" // Darker green when pressed
                                scale: 0.97 // Slightly smaller when pressed
                            }
                            PropertyChanges {
                                target: buttonText
                                color: "#f0f0f0" // Slightly darker text when pressed
                            }
                        }
                    ]
                    
                    // Add transitions for smooth animation
                    transitions: Transition {
                        PropertyAnimation { 
                            properties: "color, scale"; 
                            duration: 100 
                        }
                    }
                    
                    background: Rectangle {
                        id: buttonBackground
                        radius: 6
                        color: "#4CAF50"
                        border.color: "#388E3C"
                        border.width: 1
                    }
                    
                    contentItem: Text {
                        id: buttonText
                        text: parent.text
                        color: "white"
                        font.pixelSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    
                    onClicked: {
                        saveSequence()
                        notificationPopup.show("Sequence \"" + currentSeq.seqName + "\" saved successfully")
                    }
                }

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
            }
        }

        // Main sequence content with scrollbar
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#f0f0f0"
            radius: 8
            clip: true

            ScrollView {
                id: scrollView
                anchors.fill: parent
                ScrollBar.vertical.policy: ScrollBar.AlwaysOn
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                
                ListView {
                    id: actionListView
                    anchors.margins: 5
                    spacing: 12
                    model: actionSequence.sequence
                    clip: true

                    delegate: Rectangle {
                        id: delegateItem
                        width: actionListView.width - 25 // Account for scrollbar width
                        height: contentColumn.height + 30
                        color: "white"
                        radius: 10
                        border.color: "#dddddd"
                        border.width: 1
                        property int itemIndex: index

                        Component.onCompleted: {
                            console.log("Created delegate for item:", itemIndex);
                        }

                        Column {
                            id: contentColumn
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 15
                            spacing: 10

                            // Action title with number
                            Rectangle {
                                width: parent.width
                                height: 40
                                color: "#f9f9f9"
                                radius: 6
                                
                                Text {
                                    id: actionTitle
                                    text: model && model.title ? 
                                        (delegateItem.itemIndex + 1) + ") " + model.title : 
                                        (delegateItem.itemIndex + 1) + ") Invalid Item"
                                    font.pixelSize: 18
                                    font.bold: true
                                    color: "#333333"
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.left: parent.left
                                    anchors.leftMargin: 10
                                }
                                
                                // Control buttons
                                Row {
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    anchors.rightMargin: 10
                                    spacing: 8

                                    Button {
                                        width: 30
                                        height: 30
                                        text: "▲"
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#f0f0f0"
                                            border.color: "#cccccc"
                                            border.width: 1
                                        }
                                        
                                        onClicked: { 
                                            if (delegateItem.itemIndex > 0) {
                                                actionSequence.sequence.move(delegateItem.itemIndex, delegateItem.itemIndex - 1, 1)
                                                selectedInputField.itemInx = -1
                                                selectedInputField.inputInx = -1
                                            } 
                                        }
                                    }
                                    
                                    Button {
                                        width: 30
                                        height: 30
                                        text: "▼"
                                        
                                        background: Rectangle {
                                            radius: 4
                                            color: "#f0f0f0"
                                            border.color: "#cccccc"
                                            border.width: 1
                                        }
                                        
                                        onClicked: { 
                                            if (delegateItem.itemIndex < actionSequence.sequence.count - 1) {
                                                actionSequence.sequence.move(delegateItem.itemIndex, delegateItem.itemIndex + 1, 1)
                                                selectedInputField.itemInx = -1
                                                selectedInputField.inputInx = -1
                                            } 
                                        }
                                    }

                                    Button {
                                        id: removeButton
                                        width: 30
                                        height: 30
                                        text: "✖"
                                        
                                        background: Rectangle { 
                                            color: "#f44336"
                                            radius: 4
                                        }
                                        
                                        contentItem: Text {
                                            text: "✖"
                                            color: "white"
                                            font.pixelSize: 16
                                            font.bold: true
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                        }
                                        
                                        onClicked: {
                                            selectedInputField.itemInx = -1
                                            selectedInputField.inputInx = -1
                                            actionSequence.sequence.remove(delegateItem.itemIndex)
                                        }
                                    }
                                }
                            }

                            // Fields column
                            Column {
                                id: fieldsList
                                width: parent.width
                                spacing: 12
                                
                                // Field 1
                                Row {
                                    id: field1Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 0
                                    property string inputKey: "input1"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 0;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 1";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length === 0) {
                                                return "Field 1";
                                            }
                                            
                                            return action.fields[0].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field1Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field1Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field1Row.inputKey] !== undefined ? 
                                                  model[field1Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field1Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field1Row.fieldIndex + 
                                                           ", key=" + field1Row.inputKey);
                                            }
                                        }
                                    }
                                }
                                
                                // Field 2
                                Row {
                                    id: field2Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 1
                                    property string inputKey: "input2"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 1;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 2";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length <= 1) {
                                                return "Field 2";
                                            }
                                            
                                            return action.fields[1].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field2Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field2Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field2Row.inputKey] !== undefined ? 
                                                  model[field2Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field2Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field2Row.fieldIndex + 
                                                           ", key=" + field2Row.inputKey);
                                            }
                                        }
                                    }
                                }
                                
                                // Field 3
                                Row {
                                    id: field3Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 2
                                    property string inputKey: "input3"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 2;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 3";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length <= 2) {
                                                return "Field 3";
                                            }
                                            
                                            return action.fields[2].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field3Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field3Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field3Row.inputKey] !== undefined ? 
                                                  model[field3Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field3Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field3Row.fieldIndex + 
                                                           ", key=" + field3Row.inputKey);
                                            }
                                        }
                                    }
                                }
                                
                                // Field 4
                                Row {
                                    id: field4Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 3
                                    property string inputKey: "input4"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 3;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 4";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length <= 3) {
                                                return "Field 4";
                                            }
                                            
                                            return action.fields[3].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field4Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field4Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field4Row.inputKey] !== undefined ? 
                                                  model[field4Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field4Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field4Row.fieldIndex + 
                                                           ", key=" + field4Row.inputKey);
                                            }
                                        }
                                    }
                                }
                                
                                // Field 5 (NEW)
                                Row {
                                    id: field5Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 4
                                    property string inputKey: "input5"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 4;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 5";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length <= 4) {
                                                return "Field 5";
                                            }
                                            
                                            return action.fields[4].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field5Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field5Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field5Row.inputKey] !== undefined ? 
                                                  model[field5Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field5Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field5Row.fieldIndex + 
                                                           ", key=" + field5Row.inputKey);
                                            }
                                        }
                                    }
                                }
                                
                                // Field 6 (NEW)
                                Row {
                                    id: field6Row
                                    spacing: 10
                                    width: parent.width
                                    height: 40
                                    property int fieldIndex: 5
                                    property string inputKey: "input6"
                                    visible: {
                                        if (!model || !model.id || model[inputKey] === "-1") 
                                            return false;
                                        
                                        var action = actionConfig.getAction(model.id);
                                        return action && action.fields && action.fields.length > 5;
                                    }
                                    
                                    Text {
                                        width: 100
                                        height: parent.height
                                        verticalAlignment: Text.AlignVCenter
                                        text: {
                                            if (!model || !model.id) return "Field 6";
                                            
                                            var action = actionConfig.getAction(model.id);
                                            if (!action || !action.fields || action.fields.length <= 5) {
                                                return "Field 6";
                                            }
                                            
                                            return action.fields[5].label;
                                        }
                                        font.pixelSize: 14
                                        color: "#555555"
                                    }
                                    
                                    Rectangle {
                                        width: 120
                                        height: 36
                                        radius: 6
                                        color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                               selectedInputField.inputInx === field6Row.fieldIndex) ? 
                                               "#e3f2fd" : "#ffffff"
                                        border.color: (selectedInputField.itemInx === delegateItem.itemIndex && 
                                                      selectedInputField.inputInx === field6Row.fieldIndex) ? 
                                                      "#2196F3" : "#dddddd"
                                        border.width: 1
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: model && model[field6Row.inputKey] !== undefined ? 
                                                  model[field6Row.inputKey] : "0"
                                            horizontalAlignment: Text.AlignHCenter
                                            verticalAlignment: Text.AlignVCenter
                                            font.pixelSize: 14
                                            color: "#333333"
                                        }
                                        
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                selectedInputField.itemInx = delegateItem.itemIndex;
                                                selectedInputField.inputInx = field6Row.fieldIndex;
                                                console.log("Selected field: item=" + delegateItem.itemIndex + 
                                                           ", field=" + field6Row.fieldIndex + 
                                                           ", key=" + field6Row.inputKey);
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

    Component.onCompleted: {
        console.log("ActionSequence initialized");
        logModelData();
    }
    
    onSequenceChanged: {
        console.log("Sequence model changed");
        logModelData();
    }

    function getDefaultValue(actionId, fieldKey) {
        if (actionId === "0") { // Move Winch To
            if (fieldKey === "input1") return "100"; // Distance
            if (fieldKey === "input2") return "50";  // Velocity
        }
        else if (actionId === "1") { // Descend & Spray
            if (fieldKey === "input1") return "200"; // Target Length
            if (fieldKey === "input2") return "30";  // Speed
            if (fieldKey === "input3") return "0";   // Start Angle
            if (fieldKey === "input4") return "360"; // End Angle
        }
        else if (actionId === "3") { // Extend Arm To
            if (fieldKey === "input1") return "50";  // Distance
        }
        return "0"; // Default fallback
    }
}