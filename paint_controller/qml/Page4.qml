import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7

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

    Timer {
        id: updateTimer
        interval: 100
        running: true
        repeat: true
        onTriggered: {
            var currentTime = new Date().getTime()
            
            pitchSeries.append(currentTime - startTime, uiData.teensy_imu_pitch)
            rollSeries.append(currentTime - startTime, uiData.teensy_imu_roll)
            yawSeries.append(currentTime - startTime, uiData.teensy_imu_yaw)
            
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

        // Enable Switch and PWM Slider
        Rectangle {
            Layout.fillWidth: true
            height: 80
            color: "#9F9F9F"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 10

                Label { text: "Enable:"; color: "white" ;font.bold: true }
                    
                    RowLayout {
                        TouchSwitch {
                            id: teensyEnableSwitch
                            checked: uiData.teensy_enabled
                            onToggled: backend.setTeensyEnabled(checked)
                        }
                    }

                Label { text: "Relay:"; color: "white" ; font.bold: true }
                    
                    RowLayout {
                        TouchSwitch {
                            id: teensyRelayEnableSwitch
                            checked: uiData.teensy_relay_enabled
                            onToggled: backend.setTeensyRelayEnabled(checked)
                        }
                    }

                Switch {
                    id: enableSwitch
                    text: "Enable Control"
                    checked: uiData.teensy_yaw_enabled
                    onCheckedChanged: backend.setYawControl(checked, uiData.teensy_yaw_command, uiData.teensy_yaw_pid_p, uiData.teensy_yaw_pid_i, uiData.teensy_yaw_pid_d, uiData.teensy_yaw_pwm)
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Label {
                        text: "PWM Value: " + pwmSlider.value
                        color: "black"
                    }

                    Slider {
                        id: pwmSlider
                        Layout.fillWidth: true
                        Layout.preferredHeight: 60  // Make the overall slider taller
                        from: 1100
                        to: 1600
                        value: pwmValue
                        stepSize: 1
                        onValueChanged: pwmValue = value

                        // Customize the handle and background
                        background: Rectangle {
                            x: pwmSlider.leftPadding
                            y: pwmSlider.topPadding + pwmSlider.availableHeight / 2 - height / 2
                            width: pwmSlider.availableWidth
                            height: 20  // Thicker track
                            radius: 10
                            color: "#e0e0e0"

                            Rectangle {
                                width: pwmSlider.visualPosition * parent.width
                                height: parent.height
                                color: "#21be2b"
                                radius: 10
                            }
                        }

                        // Larger handle
                        handle: Rectangle {
                            x: pwmSlider.leftPadding + pwmSlider.visualPosition * (pwmSlider.availableWidth - width)
                            y: pwmSlider.topPadding + pwmSlider.availableHeight / 2 - height / 2
                            width: 40  // Wider handle
                            height: 40 // Taller handle
                            radius: width / 2
                            color: pwmSlider.pressed ? "#f0f0f0" : "#f6f6f6"
                            border.color: "#bdbebf"
                            border.width: 2

                            // Optional: Add a pressed state effect
                            Behavior on color {
                                ColorAnimation { duration: 100 }
                            }
                        }
                    }
                }
            }
        }

        // Y-Axis Range Controls [Previous code remains the same]
        Rectangle {
            Layout.fillWidth: true
            height: 50
            color: "#2a2a2a"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 10

                Label {
                    text: "Y-Axis Range:"
                    color: "white"
                }

                Label {
                    text: "Min:"
                    color: "white"
                }

                TextField {
                    id: yMinInput
                    Layout.preferredWidth: 70
                    text: yAxisMin.toString()
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                    onEditingFinished: {
                        var newMin = parseFloat(text)
                        if (!isNaN(newMin) && newMin < yAxisMax) {
                            yAxisMin = newMin
                            axisY.min = newMin
                        } else {
                            text = yAxisMin.toString()
                        }
                    }
                }

                Label {
                    text: "Max:"
                    color: "white"
                }

                TextField {
                    id: yMaxInput
                    Layout.preferredWidth: 70
                    text: yAxisMax.toString()
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 3
                    }
                    onEditingFinished: {
                        var newMax = parseFloat(text)
                        if (!isNaN(newMax) && newMax > yAxisMin) {
                            yAxisMax = newMax
                            axisY.max = newMax
                        } else {
                            text = yAxisMax.toString()
                        }
                    }
                }

                Button {
                    text: "Reset"
                    onClicked: {
                        yAxisMin = -180
                        yAxisMax = 180
                        yMinInput.text = "-180"
                        yMaxInput.text = "180"
                        axisY.min = -180
                        axisY.max = 180
                    }
                }

                Item { Layout.fillWidth: true }
            }
        }

        // Chart View [Previous code remains the same]
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
                min: yAxisMin
                max: yAxisMax
                tickCount: 7
                titleVisible: true
            }

            LineSeries {
                id: pitchSeries
                name: "Pitch"
                axisX: axisX
                axisY: axisY
                color: "red"
            }

            LineSeries {
                id: rollSeries
                name: "Roll"
                axisX: axisX
                axisY: axisY
                color: "green"
            }

            LineSeries {
                id: yawSeries
                name: "Yaw"
                axisX: axisX
                axisY: axisY
                color: "blue"
            }
        }

        // PID Controls Area
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: parent.height * 0.3
            color: "#2a2a2a"

            GridLayout {
                anchors.fill: parent
                anchors.margins: 20
                columns: 5  // Increased to accommodate the new buttons
                rowSpacing: 15
                columnSpacing: 10

                // P Value Row
                Label {
                    text: "P Value"
                    font.bold: true
                    color: "white"
                }
                Button {
                    text: "-10%"
                    onClicked: {
                        let currentP = uiData.teensy_yaw_pid_p
                        pInput.text = (currentP * 0.9).toFixed(6)
                    }
                }
                TextField {
                    id: pInput
                    Layout.preferredWidth: 100
                    placeholderText: uiData.teensy_yaw_pid_p
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Button {
                    text: "+10%"
                    onClicked: {
                        let currentP = uiData.teensy_yaw_pid_p
                        pInput.text = (currentP * 1.1).toFixed(6)
                    }
                }
                Label {
                    text: "Current P: " + uiData.teensy_yaw_pid_p
                    color: "white"
                }

                // I Value Row
                Label {
                    text: "I Value"
                    font.bold: true
                    color: "white"
                }
                Button {
                    text: "-10%"
                    onClicked: {
                        let currentI = uiData.teensy_yaw_pid_i
                        iInput.text = (currentI * 0.9).toFixed(6)
                    }
                }
                TextField {
                    id: iInput
                    Layout.preferredWidth: 100
                    placeholderText: uiData.teensy_yaw_pid_i
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Button {
                    text: "+10%"
                    onClicked: {
                        let currentI = uiData.teensy_yaw_pid_i
                        iInput.text = (currentI * 1.1).toFixed(6)
                    }
                }
                Label {
                    text: "Current I: " + uiData.teensy_yaw_pid_i
                    color: "white"
                }

                // D Value Row
                Label {
                    text: "D Value"
                    font.bold: true
                    color: "white"
                }
                Button {
                    text: "-10%"
                    onClicked: {
                        let currentD = uiData.teensy_yaw_pid_d
                        dInput.text = (currentD * 0.9).toFixed(6)
                    }
                }
                TextField {
                    id: dInput
                    Layout.preferredWidth: 100
                    placeholderText: uiData.teensy_yaw_pid_d
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Button {
                    text: "+10%"
                    onClicked: {
                        let currentD = uiData.teensy_yaw_pid_d
                        dInput.text = (currentD * 1.1).toFixed(6)
                    }
                }
                Label {
                    text: "Current D: " + uiData.teensy_yaw_pid_d
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
                        let currentTarget = uiData.teensy_yaw_command
                        targetInput.text = (currentTarget * 0.9).toFixed(6)
                    }
                }
                TextField {
                    id: targetInput
                    Layout.preferredWidth: 100
                    placeholderText: uiData.teensy_yaw_command
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Button {
                    text: "+10%"
                    onClicked: {
                        let currentTarget = uiData.teensy_yaw_command
                        targetInput.text = (currentTarget * 1.1).toFixed(6)
                    }
                }
                Label {
                    text: "Target: " + uiData.teensy_yaw_command + "current: " + uiData.teensy_imu_yaw
                    color: "white"
                }

                // Send Button (spanning all columns)
                Rectangle {
                    Layout.columnSpan: 5
                    Layout.alignment: Qt.AlignHCenter
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
                            let p = pInput.text !== "" ? parseFloat(pInput.text) : uiData.teensy_yaw_pid_p
                            let i = iInput.text !== "" ? parseFloat(iInput.text) : uiData.teensy_yaw_pid_i
                            let d = dInput.text !== "" ? parseFloat(dInput.text) : uiData.teensy_yaw_pid_d
                            let target = targetInput.text !== "" ? parseFloat(targetInput.text) : uiData.teensy_yaw_command
                            
                            backend.setYawControl(enableSwitch.checked, target, p, i, d, pwmValue)
                        }
                    }
                }
            }
        }
    }
}