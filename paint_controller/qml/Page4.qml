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
            color: "#FFFFFF"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                spacing: 10

                Label { text: "Enable:"; font.bold: true }
                    
                    RowLayout {
                        TouchSwitch {
                            id: teensyEnableSwitch
                            checked: uiData.teensy_enabled
                            onToggled: backend.setTeensyEnabled(checked)
                        }
                    }

                Label { text: "Relay:"; font.bold: true }
                    
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
                    checked: controlEnabled
                    onCheckedChanged: controlEnabled = checked
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 5

                    Label {
                        text: "PWM Value: " + pwmSlider.value
                        color: "white"
                    }

                    Slider {
                        id: pwmSlider
                        Layout.fillWidth: true
                        from: 1000
                        to: 1500
                        value: pwmValue
                        stepSize: 1
                        onValueChanged: pwmValue = value
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
                columns: 3
                rowSpacing: 15
                columnSpacing: 20

                Label {
                    text: "P Value"
                    font.bold: true
                    color: "white"
                }
                TextField {
                    id: pInput
                    Layout.preferredWidth: 100
                    placeholderText: "Enter P"
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Label {
                    text: "Current P: " + uiData.teensy_yaw_pid_p
                    color: "white"
                }

                Label {
                    text: "I Value"
                    font.bold: true
                    color: "white"
                }
                TextField {
                    id: iInput
                    Layout.preferredWidth: 100
                    placeholderText: "Enter I"
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Label {
                    text: "Current I: " + uiData.teensy_yaw_pid_i
                    color: "white"
                }

                Label {
                    text: "D Value"
                    font.bold: true
                    color: "white"
                }
                TextField {
                    id: dInput
                    Layout.preferredWidth: 100
                    placeholderText: "Enter D"
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Label {
                    text: "Current D: " + uiData.teensy_yaw_pid_d
                    color: "white"
                }
                Label {
                    text: "Current Target: " + uiData.teensy_yaw_command
                    color: "white"
                }
                TextField {
                    id: targetInput
                    Layout.preferredWidth: 100
                    placeholderText: "Enter Target"
                    validator: DoubleValidator {}
                    background: Rectangle {
                        color: "#ffffff"
                        radius: 5
                    }
                }
                Label {
                    text: "Current Yaw: " + uiData.teensy_imu_yaw
                    color: "white"
                }
        

                Rectangle {
                    Layout.columnSpan: 3
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
                            if (pInput.text !== "") currentP = parseFloat(pInput.text)
                            if (iInput.text !== "") currentI = parseFloat(iInput.text)
                            if (dInput.text !== "") currentD = parseFloat(dInput.text)
                            if (targetInput.text !== "") currentTarget = parseFloat(targetInput.text)
                            
                            backend.setYawControl(controlEnabled, currentTarget, currentP, currentI, currentD, pwmValue)
                            
                        }
                    }
                }
            }
        }
    }
}