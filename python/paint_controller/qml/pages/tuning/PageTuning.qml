import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts
import "../../theme"
import "../../components/displays"

Item {
    id: pidTuningPage
    required property var teensyStatus
    required property var tuningActions
    required property var qtBridge

    property int timeWindow: 30000
    property var startTime: new Date().getTime()
    property real yAxisMin: -180
    property real yAxisMax: 180

    // TD-052: form catalog is Python-owned (tuningActions.parameterSets).
    readonly property var parameterSets: tuningActions ? tuningActions.parameterSets : []
    property string selectedParameterSetId: "short_yaw_pid"
    property var selectedSet: null
    property var currentParameters: []
    property var parameterValues: ({})

    function findSetById(setId) {
        for (var i = 0; i < parameterSets.length; i++) {
            if (parameterSets[i].id === setId)
                return parameterSets[i]
        }
        return null
    }

    function selectParameterSet(setId) {
        var entry = findSetById(setId)
        selectedParameterSetId = setId
        selectedSet = entry
        currentParameters = entry ? entry.parameters : []
        parameterValues = ({})
    }

    function statusNumber(statusKey) {
        if (!teensyStatus || !statusKey)
            return 0
        var value = teensyStatus[statusKey]
        if (value === undefined || value === null)
            return 0
        return Number(value)
    }

    function getChartSeries() {
        return selectedSet ? selectedSet.chartSeries : "yaw"
    }

    function getCurrentValue() {
        if (!selectedSet)
            return 0
        return statusNumber(selectedSet.currentStatusKey)
    }

    function getTargetValue() {
        if (!selectedSet)
            return 0
        return statusNumber(selectedSet.targetStatusKey)
    }

    Timer {
        id: updateTimer
        interval: 100
        running: true
        repeat: true
        onTriggered: {
            var currentTime = new Date().getTime()

            pitchSeries.append(currentTime - startTime, pidTuningPage.teensyStatus.imuPitch)
            rollSeries.append(currentTime - startTime, pidTuningPage.teensyStatus.imuRoll)
            yawSeries.append(currentTime - startTime, pidTuningPage.teensyStatus.imuYaw)

            while (pitchSeries.count > 0 &&
                   pitchSeries.at(0).x < currentTime - startTime - timeWindow) {
                pitchSeries.remove(0)
                rollSeries.remove(0)
                yawSeries.remove(0)
            }

            axisX.min = currentTime - startTime - timeWindow
            axisX.max = currentTime - startTime

            if (selectedSet) {
                var targetValue = getTargetValue()
                axisY.min = targetValue - 10
                axisY.max = targetValue + 10
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

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

                ColumnLayout {
                    Layout.fillHeight: true
                    Layout.preferredWidth: parent.width * 0.75
                    spacing: 15

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
                            text: selectedSet ? selectedSet.label : ""
                            color: "#4CAF50"
                            font.pixelSize: 16
                            font.bold: true
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: selectedSet ? selectedSet.description : ""
                        color: "#CCCCCC"
                        font.pixelSize: 13
                        wrapMode: Text.WordWrap
                    }

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
                                            text: "Current: " + statusNumber(modelData.statusKey).toFixed(6)
                                            color: "#CCCCCC"
                                            font.pixelSize: 12
                                            Layout.fillWidth: true
                                        }
                                    }

                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 8

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
                                                    var currentVal = statusNumber(modelData.statusKey)
                                                    var stepPercent = modelData.stepPercent || 5
                                                    var newVal = currentVal * (1 - stepPercent / 100)
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
                                                text: statusNumber(modelData.statusKey).toFixed(6)
                                                color: "#666666"
                                                font.pixelSize: 14
                                                verticalAlignment: Text.AlignVCenter
                                                visible: parameterInput.text === "" && !parameterInput.activeFocus
                                            }
                                        }

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
                                                    var currentVal = statusNumber(modelData.statusKey)
                                                    var stepPercent = modelData.stepPercent || 5
                                                    var newVal = currentVal * (1 + stepPercent / 100)
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

                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true

                            ScrollBar.vertical.policy: ScrollBar.AsNeeded
                            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                            ListView {
                                anchors.fill: parent
                                model: parameterSets
                                spacing: 8

                                delegate: Rectangle {
                                    width: ListView.view.width
                                    height: 60
                                    color: selectedParameterSetId === modelData.id ? "#3A5A8C" : (paramSetMouseArea.containsMouse ? "#2A3040" : "transparent")
                                    border.color: selectedParameterSetId === modelData.id ? "#4CAF50" : "#333333"
                                    border.width: 1
                                    radius: 6

                                    MouseArea {
                                        id: paramSetMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        cursorShape: Qt.PointingHandCursor
                                        onClicked: selectParameterSet(modelData.id)
                                    }

                                    ColumnLayout {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 4

                                        Text {
                                            text: modelData.label
                                            color: selectedParameterSetId === modelData.id ? "#FFFFFF" : "#CCCCCC"
                                            font.bold: selectedParameterSetId === modelData.id
                                            font.pointSize: 11
                                            Layout.fillWidth: true
                                        }

                                        Text {
                                            text: modelData.description
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

    function sendParameters() {
        if (!selectedParameterSetId || !tuningActions)
            return

        var label = selectedSet ? selectedSet.label : selectedParameterSetId
        var success = tuningActions.sendParameterSet(selectedParameterSetId, parameterValues)
        pidTuningPage.qtBridge.show_popup(
            success ? "TUNING" : "TUNING BLOCKED",
            success ? (label + " request sent") : (label + " request rejected"),
            success ? "info" : "error",
            2000
        )
        parameterValues = ({})
    }

    Component.onCompleted: {
        selectParameterSet("short_yaw_pid")
    }
}
