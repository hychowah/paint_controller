import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7
import Qt5Compat.GraphicalEffects

Rectangle {
    id: page5Rect
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "#9F9F9F"

    Rectangle {
        id: dataRect
        Layout.fillWidth: true  
        width: 1050
        height: 700
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 30

        RowLayout {  // Add this RowLayout
            anchors.fill: parent
            anchors.margins: 20

            Rectangle {
                id: efView
                objectName: "efView"
                color: "transparent"
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                layer.enabled: true
                layer.effect: OpacityMask {
                    maskSource: Item {
                        width: efView.width
                        height: efView.height
                        Rectangle {
                            anchors.centerIn: parent
                            width: parent.width
                            height: parent.height
                            radius: 20
                        }
                    }
                }

                Image {
                    id: efFrame
                    anchors.fill: parent
                    fillMode: Image.PreserveAspectCrop
                    cache: false
                    source: "image://ef_live/frame"
                }
            }
        }

        Connections {
            target: baseStreamer
            function onFrame_ready() {
                efFrame.source = ""
                efFrame.source = "image://ef_live/frame"
            }
        }
    }
}