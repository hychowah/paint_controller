import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import "../"
import "../components"

Item {
    id: pidTuningPage
    
    property real currentP: 0.0
    property real currentI: 0.0
    property real currentD: 0.0
    property real currentTarget: 0.0
    property int pwmValue: 1000
    property bool controlEnabled: false
    
    property int timeWindow: 30000
    property var startTime: new Date().getTime()
    property real yAxisMin: -180
    property real yAxisMax: 180
    
    // Parameter selection
    property string selectedParameter: "yaw"

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
                min: getCommandValue() - 5
                max: getCommandValue() + 5
                tickCount: 7
                titleVisible: true
            }

            LineSeries {
                id: pitchSeries
                name: "Pitch"
                axisX: axisX
                axisY: axisY
                color: "red"
                visible: selectedParameter === "pitch"
            }

            LineSeries {
                id: rollSeries
                name: "Roll"
                axisX: axisX
                axisY: axisY
                color: "green"
                visible: selectedParameter === "roll"
            }

            LineSeries {
                id: yawSeries
                name: "Yaw"
                axisX: axisX
                axisY: axisY
                color: "blue"
                visible: selectedParameter === "yaw"
            }
        }

        // PID Controls Area with Parameter Selection
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.35
            color: "#2a2a2a"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 15

                // PID Controls (Left Side) - Make it scrollable
                Rectangle {
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    color: "transparent"

                    ScrollView {
                        anchors.fill: parent
                        contentWidth: availableWidth
                        clip: true

                        GridLayout {
                            width: parent.parent.width
                            columns: 5
                            rowSpacing: 12
                            columnSpacing: 8

                        // Header showing selected parameter
                        Label {
                            Layout.columnSpan: 5
                            Layout.alignment: Qt.AlignHCenter
                            text: "Tuning " + selectedParameter.toUpperCase() + " Parameters"
                            font.bold: true
                            font.pointSize: 14
                            color: "#4CAF50"
                        }

                        // P Value Row
                        Label {
                            text: "P Value"
                            font.bold: true
                            color: "white"
                        }
                        Button {
                            text: "-5%"
                            onClicked: {
                                let currentP = getCurrentP()
                                pInput.text = (currentP * 0.95).toFixed(6)
                            }
                        }
                        TextField {
                            id: pInput
                            Layout.preferredWidth: 100
                            placeholderText: getCurrentP().toString()
                            validator: DoubleValidator {}
                            background: Rectangle {
                                color: "#ffffff"
                                radius: 5
                            }
                        }
                        Button {
                            text: "+5%"
                            onClicked: {
                                let currentP = getCurrentP()
                                pInput.text = (currentP * 1.05).toFixed(6)
                            }
                        }
                        Label {
                            text: "Current P: " + getCurrentP()
                            color: "white"
                        }

                        // I Value Row
                        Label {
                            text: "I Value"
                            font.bold: true
                            color: "white"
                        }
                        Button {
                            text: "-5%"
                            onClicked: {
                                let currentI = getCurrentI()
                                iInput.text = (currentI * 0.95).toFixed(6)
                            }
                        }
                        TextField {
                            id: iInput
                            Layout.preferredWidth: 100
                            placeholderText: getCurrentI().toString()
                            validator: DoubleValidator {}
                            background: Rectangle {
                                color: "#ffffff"
                                radius: 5
                            }
                        }
                        Button {
                            text: "+5%"
                            onClicked: {
                                let currentI = getCurrentI()
                                iInput.text = (currentI * 1.05).toFixed(6)
                            }
                        }
                        Label {
                            text: "Current I: " + getCurrentI()
                            color: "white"
                        }

                        // D Value Row
                        Label {
                            text: "D Value"
                            font.bold: true
                            color: "white"
                        }
                        Button {
                            text: "-5%"
                            onClicked: {
                                let currentD = getCurrentD()
                                dInput.text = (currentD * 0.95).toFixed(6)
                            }
                        }
                        TextField {
                            id: dInput
                            Layout.preferredWidth: 100
                            placeholderText: getCurrentD().toString()
                            validator: DoubleValidator {}
                            background: Rectangle {
                                color: "#ffffff"
                                radius: 5
                            }
                        }
                        Button {
                            text: "+5%"
                            onClicked: {
                                let currentD = getCurrentD()
                                dInput.text = (currentD * 1.05).toFixed(6)
                            }
                        }
                        Label {
                            text: "Current D: " + getCurrentD()
                            color: "white"
                        }

                        // Target Value Row
                        Label {
                            text: "Target"
                            font.bold: true
                            color: "white"
                        }
                        Button {
                            text: "-10%"
                            onClicked: {
                                let currentTarget = getCommandValue()
                                targetInput.text = (currentTarget * 0.9).toFixed(6)
                            }
                        }
                        TextField {
                            id: targetInput
                            Layout.preferredWidth: 100
                            placeholderText: getCommandValue().toString()
                            validator: DoubleValidator {}
                            background: Rectangle {
                                color: "#ffffff"
                                radius: 5
                            }
                        }
                        Button {
                            text: "+10%"
                            onClicked: {
                                let currentTarget = getCommandValue()
                                targetInput.text = (currentTarget * 1.1).toFixed(6)
                            }
                        }
                        Label {
                            text: "Target: " + getCommandValue() + " Current: " + getCurrentValue()
                            color: "white"
                        }

                            // Send Button (spanning all columns)
                            Rectangle {
                                Layout.columnSpan: 5
                                Layout.alignment: Qt.AlignHCenter
                                Layout.topMargin: 10
                                Layout.bottomMargin: 10
                                width: 120
                                height: 40
                                color: sendMouseArea.pressed ? "#2196F3" : "#1976D2"
                                radius: 5

                                Text {
                                    anchors.centerIn: parent
                                    text: "SEND"
                                    color: "white"
                                    font.bold: true
                                }

                                MouseArea {
                                    id: sendMouseArea
                                    anchors.fill: parent
                                    onClicked: {
                                        let p = pInput.text !== "" ? parseFloat(pInput.text) : getCurrentP()
                                        let i = iInput.text !== "" ? parseFloat(iInput.text) : getCurrentI()
                                        let d = dInput.text !== "" ? parseFloat(dInput.text) : getCurrentD()
                                        let target = targetInput.text !== "" ? parseFloat(targetInput.text) : getCommandValue()
                                        
                                        if (selectedParameter === "yaw") {
                                            teensyController.setYawParams(p, i, d)
                                        } else if (selectedParameter === "pitch") {
                                            teensyController.setPitchParams(p, i, d)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Parameter Selection (Right Side)
                Rectangle {
                    Layout.preferredWidth: 180
                    Layout.fillHeight: true
                    color: "#3a3a3a"
                    radius: 10

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8

                        Label {
                            text: "Select Parameter"
                            font.bold: true
                            font.pointSize: 11
                            color: "white"
                            Layout.alignment: Qt.AlignHCenter
                        }

                        ScrollView {
                            id: scrollView
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ColumnLayout {
                                width: scrollView.availableWidth
                                spacing: 6

                                // Yaw Parameter Button
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 50
                                    color: selectedParameter === "yaw" ? "#4CAF50" : "#555555"
                                    radius: 6
                                    border.color: selectedParameter === "yaw" ? "#66BB6A" : "#777777"
                                    border.width: 1

                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            selectedParameter = "yaw"
                                            clearInputs()
                                        }
                                    }

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 2

                                        Text {
                                            text: "YAW"
                                            color: "white"
                                            font.bold: true
                                            font.pointSize: 11
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                        Text {
                                            text: "Current: " + teensyController.all_status.imu_yaw.toFixed(1) + "°"
                                            color: "#CCCCCC"
                                            font.pointSize: 9
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }
                                }

                                // Pitch Parameter Button
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 50
                                    color: selectedParameter === "pitch" ? "#4CAF50" : "#555555"
                                    radius: 6
                                    border.color: selectedParameter === "pitch" ? "#66BB6A" : "#777777"
                                    border.width: 1

                                    MouseArea {
                                        anchors.fill: parent
                                        onClicked: {
                                            selectedParameter = "pitch"
                                            clearInputs()
                                        }
                                    }

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 2

                                        Text {
                                            text: "PITCH"
                                            color: "white"
                                            font.bold: true
                                            font.pointSize: 11
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                        Text {
                                            text: "Current: " + teensyController.all_status.imu_pitch.toFixed(1) + "°"
                                            color: "#CCCCCC"
                                            font.pointSize: 9
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                    }
                                }

                                // Add more parameters here as needed
                                // Pitch Parameter Button (example for future expansion)
                                Rectangle {
                                    Layout.fillWidth: true
                                    height: 50
                                    color: selectedParameter === "pitch" ? "#4CAF50" : "#555555"
                                    radius: 6
                                    border.color: selectedParameter === "pitch" ? "#66BB6A" : "#777777"
                                    border.width: 1
                                    opacity: 0.5  // Disabled for now

                                    ColumnLayout {
                                        anchors.centerIn: parent
                                        spacing: 2

                                        Text {
                                            text: "PITCH"
                                            color: "white"
                                            font.bold: true
                                            font.pointSize: 11
                                            Layout.alignment: Qt.AlignHCenter
                                        }
                                        Text {
                                            text: "(Coming Soon)"
                                            color: "#888888"
                                            font.pointSize: 8
                                            Layout.alignment: Qt.AlignHCenter
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

    // Helper functions to get current values based on selected parameter
    function getCurrentP() {
        if (selectedParameter === "yaw") {
            return teensyController.all_status.yaw_pid_p
        } else if (selectedParameter === "pitch") {
            return teensyController.all_status.pitch_pid_p || 0
        }
        return 0
    }

    function getCurrentI() {
        if (selectedParameter === "yaw") {
            return teensyController.all_status.yaw_pid_i
        } else if (selectedParameter === "pitch") {
            return teensyController.all_status.pitch_pid_i || 0
        }
        return 0
    }

    function getCurrentD() {
        if (selectedParameter === "yaw") {
            return teensyController.all_status.yaw_pid_d
        } else if (selectedParameter === "pitch") {
            return teensyController.all_status.pitch_pid_d || 0
        }
        return 0
    }

    function getCommandValue() {
        if (selectedParameter === "yaw") {
            return teensyController.all_status.yaw_command
        } else if (selectedParameter === "pitch") {
            return teensyController.all_status.pitch_command || 0
        }
        return 0
    }

    function getCurrentValue() {
        if (selectedParameter === "yaw") {
            return teensyController.all_status.imu_yaw
        } else if (selectedParameter === "pitch") {
            return teensyController.all_status.imu_pitch
        }
        return 0
    }

    function clearInputs() {
        pInput.text = ""
        iInput.text = ""
        dInput.text = ""
        targetInput.text = ""
    }
}