import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "./components"

Item {
    id: editWorkFlowTab
    required property var workflowEditor

    // Properties for workflow editing
    property var currentWorkflow: null
    property string workflowName: ""
    property bool workflowLoop: false
    property var actions: []
    property int selectedActionIndex: -1
    property var actionIdList: []
    readonly property int paramFieldHeight: 55

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Top toolbar
        Rectangle {
            Layout.fillWidth: true
            height: 65
            color: "#252525"
            radius: 8
            border.color: "#333333"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "Edit WorkFlow: " + (workflowName || "None")
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }

                    RowLayout {
                        spacing: 10

                        CheckBox {
                            id: loopCheckbox
                            checked: workflowLoop
                            onCheckedChanged: workflowLoop = checked

                            contentItem: Text {
                                text: "Enable Loop"
                                color: "#FFFFFF"
                                font.pixelSize: 13
                                leftPadding: loopCheckbox.indicator.width + 8
                                verticalAlignment: Text.AlignVCenter
                            }

                            indicator: Rectangle {
                                width: 20
                                height: 20
                                x: loopCheckbox.leftPadding
                                y: parent.height / 2 - height / 2
                                radius: 3
                                color: loopCheckbox.checked ? "#3A5A8C" : "#2A2A2A"
                                border.color: "#3A5A8C"
                                border.width: 1

                                Text {
                                    anchors.centerIn: parent
                                    text: "✓"
                                    color: "#FFFFFF"
                                    font.pixelSize: 14
                                    font.bold: true
                                    visible: loopCheckbox.checked
                                }
                            }
                        }

                        Text {
                            text: "(Workflow will restart after completion)"
                            color: workflowLoop ? "#AAFFAA" : "#777777"
                            font.pixelSize: 11
                            font.italic: true
                        }
                    }
                }

                WorkflowCustomButton {
                    text: "Load"
                    buttonWidth: 100
                    buttonHeight: 50
                    onClicked: workflowSelector.open()
                }

                WorkflowCustomButton {
                    text: "Save"
                    buttonWidth: 100
                    buttonHeight: 50
                    enabled: workflowName !== "" && actions.length > 0
                    onClicked: saveWorkflow()
                }
            }
        }

        // Main content area
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // Left panel - Action list
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: "#1E1E1E"
                radius: 8
                border.color: "#333333"
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 5

                    RowLayout {
                        Layout.fillWidth: true
                        
                        Text {
                            text: "Actions"
                            color: "#FFFFFF"
                            font.pixelSize: 14
                            font.bold: true
                            Layout.fillWidth: true
                        }

                        Text {
                            text: "(" + actions.length + " actions)"
                            color: "#AAAAAA"
                            font.pixelSize: 12
                        }
                    }

                    // Actions list
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#2A2A2A"
                        radius: 4
                        border.color: "#404040"
                        border.width: 1

                        ListView {
                            id: actionsList
                            anchors.fill: parent
                            anchors.margins: 5
                            spacing: 2
                            clip: true
                            model: actions

                            ScrollBar.vertical: ScrollBar {
                                policy: ScrollBar.AsNeeded
                            }

                            delegate: Rectangle {
                                width: actionsList.width - 10
                                height: 60
                                color: selectedActionIndex === index ? "#3A5A8C" : "#333333"
                                radius: 4
                                border.color: selectedActionIndex === index ? "#5A7AAC" : "#444444"
                                border.width: 1

                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        selectedActionIndex = index
                                        loadActionToEditor(index)
                                    }
                                }

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    spacing: 2

                                    RowLayout {
                                        Layout.fillWidth: true
                                        
                                        Text {
                                            text: (index + 1) + ". " + (modelData.name || "Unnamed")
                                            color: "#FFFFFF"
                                            font.pixelSize: 13
                                            font.bold: true
                                            Layout.fillWidth: true
                                            elide: Text.ElideRight
                                        }

                                        Text {
                                            text: modelData.type || "Unknown"
                                            color: "#AAAAAA"
                                            font.pixelSize: 11
                                            font.italic: true
                                        }
                                    }

                                    Text {
                                        text: getActionSummary(modelData)
                                        color: "#CCCCCC"
                                        font.pixelSize: 11
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                        wrapMode: Text.NoWrap
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Right panel - Action editor
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: "#1E1E1E"
                radius: 8
                border.color: "#333333"
                border.width: 1

                ScrollView {
                    anchors.fill: parent
                    anchors.margins: 10
                    clip: true
                    
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded

                    ColumnLayout {
                        width: parent.width - 20
                        spacing: 10

                        Text {
                            text: selectedActionIndex >= 0 ? "Edit Parameters" : "Select an action to edit parameters"
                            color: "#FFFFFF"
                            font.pixelSize: 14
                            font.bold: true
                        }

                        // Action info (read-only)
                        Rectangle {
                            width: 300
                            Layout.preferredHeight: 80
                            color: "#252525"
                            radius: 6
                            border.color: "#404040"
                            border.width: 1
                            visible: selectedActionIndex >= 0

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 5

                                Text {
                                    text: "Action: " + (selectedActionIndex >= 0 && actions[selectedActionIndex] ? actions[selectedActionIndex].name : "")
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                Text {
                                    text: "Type: " + (selectedActionIndex >= 0 && actions[selectedActionIndex] ? actions[selectedActionIndex].type : "")
                                    color: "#AAAAAA"
                                    font.pixelSize: 12
                                }

                                Text {
                                    text: "ID: " + (selectedActionIndex >= 0 && actions[selectedActionIndex] ? actions[selectedActionIndex].id : "")
                                    color: "#AAAAAA"
                                    font.pixelSize: 11
                                }
                            }
                        }

                        // Parameters section
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: paramsLayout.implicitHeight + 80
                            color: "#252525"
                            radius: 6
                            border.color: "#404040"
                            border.width: 1
                            visible: selectedActionIndex >= 0

                            ColumnLayout {
                                id: paramsLayout
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text {
                                    text: "Parameters"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                // Dynamic parameter fields based on action type
                                Loader {
                                    id: paramFieldsLoader
                                    Layout.fillWidth: true
                                    Layout.preferredHeight: item ? item.implicitHeight + 40 : 100
                                    sourceComponent: null
                                }
                            }
                        }

                        // Timing section
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: timingLayout.implicitHeight + 80
                            color: "#252525"
                            radius: 6
                            border.color: "#404040"
                            border.width: 1
                            visible: selectedActionIndex >= 0

                            ColumnLayout {
                                id: timingLayout
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 8

                                Text {
                                    text: "Timing"
                                    color: "#FFFFFF"
                                    font.pixelSize: 13
                                    font.bold: true
                                }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: 10
                                    rowSpacing: 8

                                    Text { 
                                        text: "Estimated Duration (ms):"
                                        color: "#CCCCCC"
                                        font.pixelSize: 12
                                        Layout.preferredWidth: 150
                                    }
                                    TextField {
                                        id: estimatedDurationField
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: 200
                                        Layout.preferredHeight: paramFieldHeight
                                        readOnly: true
                                        color: "#FFFFFF"
                                        background: Rectangle {
                                            color: "#2A2A2A"
                                            border.color: "#3A5A8C"
                                            border.width: 1
                                            radius: 4
                                        }
                                        Component.onCompleted: {
                                            text = (selectedActionIndex >= 0 && actions[selectedActionIndex]) ? 
                                                   (actions[selectedActionIndex].estimated_duration || "").toString() : ""
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                numpad.targetField = estimatedDurationField
                                                numpad.open()
                                            }
                                        }
                                        onTextChanged: {
                                            if (text !== "") {
                                                var val = parseInt(text)
                                                if (!isNaN(val)) updateActionProperty("estimated_duration", val)
                                            }
                                        }
                                    }

                                    Text { 
                                        text: "Offset (ms):"
                                        color: "#CCCCCC"
                                        font.pixelSize: 12
                                        Layout.preferredWidth: 150
                                        visible: selectedActionIndex >= 0 && actions[selectedActionIndex] && actions[selectedActionIndex].trigger
                                    }
                                    TextField {
                                        id: offsetMsField
                                        Layout.fillWidth: true
                                        Layout.preferredWidth: 200
                                        Layout.preferredHeight: paramFieldHeight
                                        readOnly: true
                                        color: "#FFFFFF"
                                        visible: selectedActionIndex >= 0 && actions[selectedActionIndex] && actions[selectedActionIndex].trigger
                                        background: Rectangle {
                                            color: "#2A2A2A"
                                            border.color: "#3A5A8C"
                                            border.width: 1
                                            radius: 4
                                        }
                                        Component.onCompleted: {
                                            if (selectedActionIndex >= 0 && actions[selectedActionIndex] && actions[selectedActionIndex].trigger) {
                                                text = (actions[selectedActionIndex].trigger.offset_ms || "").toString()
                                            }
                                        }
                                        MouseArea {
                                            anchors.fill: parent
                                            onClicked: {
                                                numpad.targetField = offsetMsField
                                                numpad.open()
                                            }
                                        }
                                        onTextChanged: {
                                            if (visible && text !== "") {
                                                var val = parseInt(text)
                                                if (!isNaN(val)) updateTriggerProperty("offset_ms", val)
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

    // Custom Button Component
    component WorkflowCustomButton: Rectangle {
        property string text: ""
        property bool enabled: true
        property int buttonWidth: text.length > 3 ? 80 : 40
        property int buttonHeight: 32
        signal clicked()

        width: buttonWidth
        height: buttonHeight
        color: enabled ? (buttonMouseArea.containsMouse ? "#3A5A8C" : "#2A3040") : "#1A1A1A"
        border.color: enabled ? "#3A5A8C" : "#333333"
        border.width: 1
        radius: 6
        opacity: enabled ? 1.0 : 0.5

        Text {
            anchors.centerIn: parent
            text: parent.text
            color: parent.enabled ? "#FFFFFF" : "#666666"
            font.pixelSize: 13
        }

        MouseArea {
            id: buttonMouseArea
            anchors.fill: parent
            hoverEnabled: true
            enabled: parent.enabled
            cursorShape: Qt.PointingHandCursor
            onClicked: parent.clicked()
        }
    }

    WorkflowSelectorPopup {
        id: workflowSelector
        workflowNames: workflowEditor ? workflowEditor.workflow_list : []
        onWorkflowSelected: function(selectedWorkflowName) {
            loadWorkflowFile(selectedWorkflowName)
        }
    }

    WorkflowSaveAsPopup {
        id: saveAsDialog
        workflowName: editWorkFlowTab.workflowName
        onSaveRequested: function(savedWorkflowName) {
            workflowName = savedWorkflowName
            saveWorkflow()
        }
    }

    // JavaScript functions
    function getParameterComponent() {
        if (selectedActionIndex < 0 || !actions[selectedActionIndex]) {
            return null
        }

        var actionType = actions[selectedActionIndex].type || ""

        switch (actionType) {
            case "winch_absolute":
            case "winch_increment":
                return winchParamsComponent
            case "valve_turn":
                return valveParamsComponent
            case "spray_gimbal":
                return gimbalParamsComponent
            case "arm_extend":
                return armParamsComponent
            case "ef_force":
                return forceParamsComponent
            default:
                return genericParamsComponent
        }
    }

    function updateParameterFields() {
        paramFieldsLoader.sourceComponent = null
        paramFieldsLoader.sourceComponent = getParameterComponent()
    }

    // Numpad popup
    NumpadNew {
        id: numpad
    }

    // Parameter components
    Component {
        id: winchParamsComponent
        GridLayout {
            id: winchGrid
            width: parent ? parent.width : 0
            columns: 2
            columnSpacing: 10
            rowSpacing: 8
            
            property bool ignoreChanges: false

            Text { text: "Length (mm):"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: lengthField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    winchGrid.ignoreChanges = true
                    text = getParam("length", 0).toString()
                    winchGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = lengthField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!winchGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("length", val)
                    }
                }
            }

            Text { text: "Speed (mm/s):"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: speedField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    winchGrid.ignoreChanges = true
                    text = getParam("speed", 100).toString()
                    winchGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = speedField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!winchGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("speed", val)
                    }
                }
            }
        }
    }

    Component {
        id: valveParamsComponent
        GridLayout {
            id: valveGrid
            width: 200
            columns: 2
            columnSpacing: 10
            rowSpacing: 8
            
            property bool ignoreChanges: false

            Text { text: "Turn Value:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: turnValueField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    valveGrid.ignoreChanges = true
                    text = getParam("turn_value", 0).toString()
                    valveGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = turnValueField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!valveGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("turn_value", val)
                    }
                }
            }
        }
    }

    Component {
        id: gimbalParamsComponent
        GridLayout {
            id: gimbalGrid
            width: parent ? parent.width : 0
            columns: 2
            columnSpacing: 10
            rowSpacing: 8
            
            property bool ignoreChanges: false

            Text { text: "Angle (°):"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: angleField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    gimbalGrid.ignoreChanges = true
                    text = getParam("angle", 0).toString()
                    gimbalGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = angleField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!gimbalGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("angle", val)
                    }
                }
            }

            Text { text: "Speed (°/s):"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: gimbalSpeedField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    gimbalGrid.ignoreChanges = true
                    text = getParam("speed", 10).toString()
                    gimbalGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = gimbalSpeedField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!gimbalGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("speed", val)
                    }
                }
            }
        }
    }

    Component {
        id: armParamsComponent
        GridLayout {
            id: armGrid
            width: parent ? parent.width : 0
            columns: 2
            columnSpacing: 10
            rowSpacing: 8
            
            property bool ignoreChanges: false

            Text { text: "Distance (mm):"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: distanceField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    armGrid.ignoreChanges = true
                    text = getParam("distance", 0).toString()
                    armGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = distanceField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!armGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("distance", val)
                    }
                }
            }
        }
    }

    Component {
        id: forceParamsComponent
        GridLayout {
            id: forceGrid
            width: parent ? parent.width : 0
            columns: 2
            columnSpacing: 10
            rowSpacing: 8
            
            property bool ignoreChanges: false

            Text { text: "Force X:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: fxField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    forceGrid.ignoreChanges = true
                    text = getParam("fx", 0).toString()
                    forceGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = fxField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!forceGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("fx", val)
                    }
                }
            }

            Text { text: "Force Y:"; color: "#CCCCCC"; font.pixelSize: 12; Layout.preferredWidth: 100 }
            TextField {
                id: fyField
                Layout.fillWidth: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: editWorkFlowTab.paramFieldHeight
                readOnly: true
                color: "#FFFFFF"
                background: Rectangle {
                    color: "#2A2A2A"
                    border.color: "#3A5A8C"
                    border.width: 1
                    radius: 4
                }
                Component.onCompleted: {
                    forceGrid.ignoreChanges = true
                    text = getParam("fy", 0).toString()
                    forceGrid.ignoreChanges = false
                }
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        numpad.targetField = fyField
                        numpad.open()
                    }
                }
                onTextChanged: {
                    if (!forceGrid.ignoreChanges) {
                        var val = parseFloat(text)
                        if (!isNaN(val)) updateParam("fy", val)
                    }
                }
            }
        }
    }

    Component {
        id: genericParamsComponent
        Text {
            text: "No parameters for this action type"
            color: "#AAAAAA"
            font.pixelSize: 12
            font.italic: true
        }
    }

    // Helper functions
    function getParam(key, defaultValue) {
        if (selectedActionIndex < 0 || !actions[selectedActionIndex]) {
            return defaultValue
        }
        var params = actions[selectedActionIndex].params || {}
        return params[key] !== undefined ? params[key] : defaultValue
    }

    function updateParam(key, value) {
        if (selectedActionIndex < 0) return
        
        var action = actions[selectedActionIndex]
        if (!action.params) {
            action.params = {}
        }
        action.params[key] = value
        actions[selectedActionIndex] = action
        refreshActionsList()
    }

    function updateActionProperty(key, value) {
        if (selectedActionIndex < 0) return
        
        var action = actions[selectedActionIndex]
        action[key] = value
        actions[selectedActionIndex] = action
        refreshActionsList()
    }

    function updateTriggerProperty(key, value) {
        if (selectedActionIndex < 0) return
        
        var action = actions[selectedActionIndex]
        if (!action.trigger) {
            action.trigger = {}
        }
        action.trigger[key] = value
        actions[selectedActionIndex] = action
        refreshActionsList()
    }

    function getActionSummary(action) {
        var summary = ""
        if (action.params) {
            var params = action.params
            switch (action.type) {
                case "winch_absolute":
                case "winch_increment":
                    summary = "length=" + (params.length || 0) + "mm, speed=" + (params.speed || 0) + "mm/s"
                    break
                case "valve_turn":
                    summary = "turn=" + (params.turn_value || 0)
                    break
                case "spray_gimbal":
                    summary = "angle=" + (params.angle || 0) + "°, speed=" + (params.speed || 0) + "°/s"
                    break
                case "arm_extend":
                    summary = "distance=" + (params.distance || 0) + "mm"
                    break
                case "ef_force":
                    summary = "fx=" + (params.fx || 0) + ", fy=" + (params.fy || 0)
                    break
            }
        }
        return summary || "No parameters"
    }

    function loadActionToEditor(index) {
        if (index < 0 || index >= actions.length) return
        
        // Update parameter fields to show current action's parameters
        updateParameterFields()
        
        // Update timing fields
        var action = actions[index]
        if (estimatedDurationField) {
            estimatedDurationField.text = (action.estimated_duration || "").toString()
        }
        if (offsetMsField && action.trigger) {
            offsetMsField.text = (action.trigger.offset_ms || "").toString()
        }
    }

    function refreshActionsList() {
        // Force ListView to update
        var temp = actions
        actions = []
        actions = temp
    }

    function loadWorkflowFile(name) {
        console.log("Loading workflow:", name)
        if (!workflowEditor) {
            console.log("WorkflowEditor not available")
            return
        }
        
        // Get full workflow data from Python
        var workflowJson = workflowEditor.get_workflow_data(name)
        if (workflowJson === "") {
            console.log("Failed to load workflow data")
            return
        }
        
        try {
            var workflow = JSON.parse(workflowJson)
            workflowName = workflow.name || name
            currentWorkflow = workflow
            actions = workflow.actions || []
            workflowLoop = workflow.loop === true
            selectedActionIndex = -1
            
            console.log("Loaded workflow with", actions.length, "actions, loop:", workflowLoop)
        } catch (e) {
            console.log("Error parsing workflow JSON:", e)
        }
    }

    function saveWorkflow() {
        if (workflowName === "") {
            console.log("No workflow name specified")
            return
        }
        
        if (!workflowEditor) {
            console.log("WorkflowEditor not available")
            return
        }
        
        // Build workflow structure
        var workflow = {
            "name": workflowName,
            "description": currentWorkflow ? (currentWorkflow.description || "") : "",
            "loop": workflowLoop,
            "actions": actions
        }
        
        // Convert to JSON and save via Python
        var workflowJson = JSON.stringify(workflow)
        var success = workflowEditor.save_workflow_data(workflowName, workflowJson)
        
        if (success) {
            console.log("Successfully saved workflow:", workflowName)
            // Show success message (could add a popup here)
        } else {
            console.log("Failed to save workflow:", workflowName)
            // Show error message (could add a popup here)
        }
    }
}
