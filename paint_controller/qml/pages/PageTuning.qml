import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import "../"
import "../components"

Item {
    id: pidTuningPage
    
    property int timeWindow: 30000
    property var startTime: new Date().getTime()
    property real yAxisMin: -180
    property real yAxisMax: 180
    
    // Parameter set definitions with their parameters
    property var parameterSetDefinitions: {
        "Short Yaw PID": {
            description: "Tune yaw axis PID parameters",
            chartSeries: "yaw",
            currentValueGetter: () => teensyController.all_status.imu_yaw,
            targetValueGetter: () => teensyController.all_status.yaw_command,
            parameters: [
                { 
                    name: "P Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_p,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "I Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_i,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "D Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_d,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "Target", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_command,
                    unit: "degrees",
                    stepPercent: 10 
                }
            ],
            sendFunction: (params) => {
                teensyController.setShortParams(
                    params["P Value"] !== undefined ? params["P Value"] : teensyController.all_status.yaw_pid_p,
                    params["I Value"] !== undefined ? params["I Value"] : teensyController.all_status.yaw_pid_i,
                    params["D Value"] !== undefined ? params["D Value"] : teensyController.all_status.yaw_pid_d
                )
            }
        },
        "Long Yaw PID": {
            description: "Tune long yaw axis PID parameters",
            chartSeries: "yaw",
            currentValueGetter: () => teensyController.all_status.imu_yaw,
            targetValueGetter: () => teensyController.all_status.yaw_command,
            parameters: [
                { 
                    name: "P Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_p,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "I Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_i,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "D Value", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_pid_d,
                    unit: "",
                    stepPercent: 5 
                },
                { 
                    name: "Target", 
                    type: "number", 
                    currentGetter: () => teensyController.all_status.yaw_command,
                    unit: "degrees",
                    stepPercent: 10 
                }
            ],
            sendFunction: (params) => {
                teensyController.setLongParams(
                    params["P Value"] !== undefined ? params["P Value"] : teensyController.all_status.yaw_pid_p,
                    params["I Value"] !== undefined ? params["I Value"] : teensyController.all_status.yaw_pid_i,
                    params["D Value"] !== undefined ? params["D Value"] : teensyController.all_status.yaw_pid_d
                )
            }
        }
    }

    property string selectedParameterSet: "Short Yaw PID"
    property var currentParameters: []
    property var parameterValues: ({})

    Timer {
        id: updateTimer
        interval: 100
        running: true
        repeat: true
        onTriggered: {
            var currentTime = new Date().getTime()
            
            pitchSeries.append(currentTime - startTime, teensyController.all_status.imu_pitch)
            rollSeries.append(currentTime - startTime, teensyController.all_status.imu_roll)
            yawSeries.append(currentTime - startTime, teensyController.all_status.imu_yaw)
            
            while (pitchSeries.count > 0 && 
                   pitchSeries.at(0).x < currentTime - startTime - timeWindow) {
                pitchSeries.remove(0)
                rollSeries.remove(0)
                yawSeries.remove(0)
            }
            
            axisX.min = currentTime - startTime - timeWindow
            axisX.max = currentTime - startTime
            
            // Update Y axis based on current values
            if (selectedParameterSet && parameterSetDefinitions[selectedParameterSet]) {
                let targetValue = parameterSetDefinitions[selectedParameterSet].targetValueGetter()
                axisY.min = targetValue - 10
                axisY.max = targetValue + 10
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Chart View
        ChartView {
            id: chartView
            Layout.fillWidth: true
            Layout.fillHeight: true
            antialiasing: true
            legend.visible: true
            theme: ChartView.ChartThemeDark

            ValueAxis {
                id: axisX
                titleText: "Time (s)"
                labelsVisible: true
                tickCount: 6
                labelFormat: "%.1f"
                titleVisible: true
            }

            ValueAxis {
                id: axisY
                titleText: "Degrees"
                min: -10
                max: 10
                tickCount: 7
                titleVisible: true
            }

            LineSeries {
                id: pitchSeries
                name: "Pitch"
                axisX: axisX
                axisY: axisY
                color: "red"
                visible: getChartSeries() === "pitch"
            }

            LineSeries {
                id: rollSeries
                name: "Roll"
                axisX: axisX
                axisY: axisY
                color: "green"
                visible: getChartSeries() === "roll"
            }

            LineSeries {
                id: yawSeries
                name: "Yaw"
                axisX: axisX
                axisY: axisY
                color: "blue"
                visible: getChartSeries() === "yaw"
            }
        }

        // Tuning Controls Area
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.4
            color: "#252A36"
            border.color: "#3A5A8C"
            border.width: 1
            radius: 10

            RowLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20

                // Parameter Controls (Left Side - 3/4 of the space)
                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: parent.width * 0.75
                    spacing: 15

                    // Header
                    RowLayout {
                        Layout.fillWidth: true
                        
                        Text {
                            text: "Tuning Parameters"
                            color: "#FFFFFF"
                            font.family: "Helvetica"
                            font.pixelSize: 18
                            font.bold: true
                        }
                        
                        Item { Layout.fillWidth: true }
                        
                        Text {
                            text: selectedParameterSet
                            color: "#4CAF50"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: parameterSetDefinitions[selectedParameterSet]?.description || ""
                        color: "#CCCCCC"
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }

                    // Parameters Section
                    ScrollView {
                        id: scrollView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        
                        ScrollBar.vertical.policy: ScrollBar.AsNeeded
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                        
                        ColumnLayout {
                            width: scrollView.width
                            spacing: 15
                            
                            // Dynamic parameter inputs
                            Repeater {
                                model: currentParameters
                                
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 8
                                    
                                    RowLayout {
                                        Layout.fillWidth: true
                                        
                                        Text {
                                            text: modelData.name + (modelData.unit ? " (" + modelData.unit + ")" : "")
                                            color: "#FFFFFF"
                                            font.pixelSize: 14
                                            font.bold: true
                                            Layout.preferredWidth: 140
                                        }
                                        
                                        Text {
                                            text: "Current: " + (modelData.currentGetter ? modelData.currentGetter().toFixed(6) : "N/A")
                                            color: "#CCCCCC"
                                            font.pixelSize: 12
                                            Layout.fillWidth: true
                                        }
                                    }
                                    
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8
                                        
                                        // Decrease button
                                        Rectangle {
                                            width: 80
                                            height: 40
                                            color: decreaseArea.containsMouse ? "#d32f2f" : "#f44336"
                                            radius: 4
                                            
                                            MouseArea {
                                                id: decreaseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    let currentVal = modelData.currentGetter ? modelData.currentGetter() : 0
                                                    let stepPercent = modelData.stepPercent || 5
                                                    let newVal = currentVal * (1 - stepPercent / 100)
                                                    parameterInput.text = newVal.toFixed(6)
                                                    parameterValues[modelData.name] = newVal
                                                }
                                            }
                                            
                                            Text {
                                                anchors.centerIn: parent
                                                text: "-" + (modelData.stepPercent || 5) + "%"
                                                color: "white"
                                                font.pixelSize: 12
                                                font.bold: true
                                            }
                                        }
                                        
                                        // Input field
                                        Rectangle {
                                            Layout.fillWidth: true
                                            height: 40
                                            color: "#1A1A1A"
                                            border.color: parameterInput.activeFocus ? "#3A5A8C" : "#333333"
                                            border.width: 1
                                            radius: 4
                                            
                                            TextInput {
                                                id: parameterInput
                                                anchors.fill: parent
                                                anchors.margins: 10
                                                text: ""
                                                color: "#FFFFFF"
                                                font.pixelSize: 14
                                                verticalAlignment: TextInput.AlignVCenter
                                                validator: DoubleValidator { bottom: -999999; top: 999999; decimals: 6 }
                                                
                                                onTextChanged: {
                                                    if (text !== "") {
                                                        parameterValues[modelData.name] = parseFloat(text)
                                                    } else {
                                                        delete parameterValues[modelData.name]
                                                    }
                                                }
                                            }
                                            
                                            Text {
                                                anchors.fill: parameterInput
                                                anchors.margins: 10
                                                text: modelData.currentGetter ? modelData.currentGetter().toFixed(6) : "0.000000"
                                                color: "#666666"
                                                font.pixelSize: 14
                                                verticalAlignment: Text.AlignVCenter
                                                visible: parameterInput.text === "" && !parameterInput.activeFocus
                                            }
                                        }
                                        
                                        // Increase button
                                        Rectangle {
                                            width: 80
                                            height: 40
                                            color: increaseArea.containsMouse ? "#2e7d32" : "#4caf50"
                                            radius: 4
                                            
                                            MouseArea {
                                                id: increaseArea
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                onClicked: {
                                                    let currentVal = modelData.currentGetter ? modelData.currentGetter() : 0
                                                    let stepPercent = modelData.stepPercent || 5
                                                    let newVal = currentVal * (1 + stepPercent / 100)
                                                    parameterInput.text = newVal.toFixed(6)
                                                    parameterValues[modelData.name] = newVal
                                                }
                                            }
                                            
                                            Text {
                                                anchors.centerIn: parent
                                                text: "+" + (modelData.stepPercent || 5) + "%"
                                                color: "white"
                                                font.pixelSize: 12
                                                font.bold: true
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Send Button
                    Rectangle {
                        id: sendButton
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 10
                        width: 140
                        height: 50
                        radius: 8
                        color: sendButtonArea.containsMouse ? "#4CAF50" : "#3A8F3A"
                        border.color: "#4CAF50"
                        border.width: 1
                        
                        MouseArea {
                            id: sendButtonArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: sendParameters()
                        }
                        
                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            Text {
                                text: "▶"
                                color: "#FFFFFF"
                                font.pixelSize: 14
                            }
                            
                            Text {
                                text: "SEND"
                                color: "#FFFFFF"
                                font.pixelSize: 16
                                font.bold: true
                            }
                        }
                    }
                }

                // Parameter Set Selection (Right Side - 1/4 of the space)
                Rectangle {
                    Layout.preferredWidth: parent.width * 0.25
                    Layout.fillHeight: true
                    color: "#1A1A1A"
                    border.color: "#333333"
                    border.width: 1
                    radius: 8

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 10

                        Text {
                            text: "Parameter Sets"
                            font.bold: true
                            font.pointSize: 12
                            color: "white"
                            Layout.alignment: Qt.AlignHCenter
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 1
                            color: "#333333"
                        }

                        // Scrollable parameter set list
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            
                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                            ListView {
                                anchors.fill: parent
                                model: Object.keys(parameterSetDefinitions)
                                spacing: 8

                                delegate: Rectangle {
                                    width: ListView.view.width
                                    height: 60
                                    color: selectedParameterSet === modelData ? "#3A5A8C" : (paramSetMouseArea.containsMouse ? "#2A3040" : "transparent")
                                    border.color: selectedParameterSet === modelData ? "#4CAF50" : "#333333"
                                    border.width: 1
                                    radius: 6

                                    MouseArea {
                                        id: paramSetMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: {
                                            selectedParameterSet = modelData
                                            currentParameters = parameterSetDefinitions[selectedParameterSet]?.parameters || []
                                            parameterValues = {}
                                        }
                                    }

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 4

                                        Text {
                                            text: modelData
                                            color: selectedParameterSet === modelData ? "#FFFFFF" : "#CCCCCC"
                                            font.bold: selectedParameterSet === modelData
                                            font.pointSize: 11
                                            Layout.fillWidth: true
                                        }

                                        Text {
                                            text: parameterSetDefinitions[modelData]?.description || ""
                                            color: "#999999"
                                            font.pointSize: 9
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                            maximumLineCount: 2
                                            elide: Text.ElideRight
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

    // Helper functions
    function getChartSeries() {
        return parameterSetDefinitions[selectedParameterSet]?.chartSeries || "yaw"
    }

    function getCurrentValue() {
        let getter = parameterSetDefinitions[selectedParameterSet]?.currentValueGetter
        return getter ? getter() : 0
    }

    function getTargetValue() {
        let getter = parameterSetDefinitions[selectedParameterSet]?.targetValueGetter
        return getter ? getter() : 0
    }

    function sendParameters() {
        if (!selectedParameterSet || !parameterSetDefinitions[selectedParameterSet]) return
        
        console.log("Sending parameters for:", selectedParameterSet)
        console.log("Parameters:", JSON.stringify(parameterValues))
        
        let sendFunc = parameterSetDefinitions[selectedParameterSet].sendFunction
        if (sendFunc) {
            sendFunc(parameterValues)
        }
        
        // Clear inputs after sending
        parameterValues = {}
    }

    // Initialize with default selection
    Component.onCompleted: {
        selectedParameterSet = "Short Yaw PID"
        currentParameters = parameterSetDefinitions[selectedParameterSet].parameters
        parameterValues = {}
    }
}