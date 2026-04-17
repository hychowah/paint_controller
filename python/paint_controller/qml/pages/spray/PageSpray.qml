import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtCharts 2.15
import QtMultimedia 5.15
import QtGraphicalEffects 1.15
import "../../core"
import "../../components/buttons"
import "../../components/inputs"
import "../../components/displays"
import "../../components/panels"

Rectangle {
    id: page5Rect
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    // Video stream view now fills the entire page5Rect
    Rectangle {
        id: efView
        objectName: "efView"
        anchors.fill: parent
        color: "transparent"
        
        Image {
            id: efFrame
            anchors.fill: parent
            fillMode: Image.PreserveAspectFit
            cache: false
            source: "image://ef_live/frame"
        }
    }

    // Overlay controls on top of the video stream
    Rectangle {
        id: bottomOverlay
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 200
        color: "transparent"
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 20

            Button {
                text: "Settings"
                Layout.preferredWidth: 100
                anchors.bottom: parent.bottom
            }

            Label {
                text: uiData.winch_available ? "Winch Connected" : "Winch Disconnected"
                color: "white"
                Layout.fillWidth: true
                anchors.bottom: parent.bottom
            }

            DigitalGauge {
                width: 150
                height: 150
                torque: Math.abs(uiData.winch_torque)
                speed: uiData.winch_speed
                maxTorque: 1000
                units: "Nm"
                speedUnits: "RPM"
                Layout.rightMargin: 20
            }
        }
    }

    // Side overlay
    Rectangle {
        id: sideOverlay
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: bottomOverlay.top
        width: 200
        color: Qt.rgba(0, 0, 0, 0.3)
        visible: false

        Column {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 10

            Label {
                text: "Statistics"
                color: "white"
                font.bold: true
            }
        }
    }



    Connections {
        target: backend
        function onFrame_ready() {
            efFrame.source = ""
            efFrame.source = "image://ef_live/frame"
        }
    }
}