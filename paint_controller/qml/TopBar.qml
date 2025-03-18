// TopBar.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: topBar
    height: 50
    color: "#28445E"
    z: 1  // Ensure top bar is above the StackView

    // Add property but mark it as required to prevent binding loops
    // required property var uiData

    // White bottom border
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "white"
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 10

        Text {
            text: uiData ? uiData.display_message || "" : ""
            color: "white"
            font.family: "Roboto"  // Modern sans-serif font
            font.pixelSize: 18
            font.weight: Font.Medium
        }

        Item { Layout.fillWidth: true } // Spacer

        Button {
            id: warningButton
            text: "⚠️ Warnings (" + warningHandler.warnings.length + ")"
            background: Rectangle {
                color: warningHandler.warnings.length === 0 ? "#ffffff" : "#ff4444"
                radius: 5
            }
            onClicked: warningPopup.open()
        }

        Text {
            text: Qt.formatDateTime(new Date(), "hh:mm:ss")
            color: "white"
            font.family: "Roboto"  // Modern sans-serif font
            font.pixelSize: 24
            font.weight: Font.Medium

            Timer {
                interval: 1000
                running: true
                repeat: true
                onTriggered: parent.text = Qt.formatDateTime(new Date(), "hh:mm:ss")
            }
        }
    }

    // Warning popup
    Popup {
        id: warningPopup
        parent: Overlay.overlay // Make relative to the app window
        width: Math.min(Overlay.overlay.width * 0.8, 600)
        height: Math.min(Overlay.overlay.height * 0.8, 400)
        x: (Overlay.overlay.width - width) / 2
        y: (Overlay.overlay.height - height) / 2
        padding: 15
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            Text {
                text: "Warnings:"
                font.pixelSize: 16
                font.bold: true
                //Layout.alignment: Qt.AlignHLeft
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                
                ListView {
                    id: listView
                    model: warningHandler.warnings
                    spacing: 8
                    boundsBehavior: Flickable.StopAtBounds
                    //implicitHeight: contentHeight

                    delegate: RowLayout {
                        width: listView.width - 20
                        spacing: 15

                        Text {
                            text: modelData
                            color: "red"
                            wrapMode: Text.Wrap
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "Clear"
                            onClicked: {
                                if(warningHandler.warnings.length == 1) {
                                    warningPopup.close()
                                }
                                warningHandler.remove_warning(index)
                            }
                            //Layout.alignment: Qt.AlignRight
                        }
                    }
                }
            }

            Button {
                text: "Clear All"
                Layout.alignment: Qt.AlignRight
                onClicked: {
                    warningHandler.clear()
                    warningPopup.close()
                }
            }
        }
    }
}