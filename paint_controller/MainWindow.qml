import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import CustomComponents 1.0

ApplicationWindow {
    visible: true
    width: 1280
    height: 720
    title: qsTr("MainWindow")

    Rectangle {
        id: background
        anchors.fill: parent
        color: "#5E5C64"

        RowLayout {
            anchors.fill: parent
            spacing: 10

            // Static Select Bar
            Rectangle {
                id: selectBar
                width: 101
                Layout.fillHeight: true
                color: "#3D3846"

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 10

                    Button {
                        text: "Page 1"
                        onClicked: stackView.replace(page1Component)
                    }

                    Button {
                        text: "Page 2"
                        onClicked: stackView.replace(page2Component)
                    }
                }
            }

            // Main content area
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#5E5C64"

                StackView {
                    id: stackView
                    objectName: "stackView"
                    anchors.fill: parent
                    initialItem: page1Component

                    replaceEnter: Transition {
                        PropertyAnimation {
                            target: enterItem
                            property: "y"
                            from: stackView.height
                            to: 0
                            duration: 400
                            easing.type: Easing.InOutQuad
                        }
                    }

                    replaceExit: Transition {
                        PropertyAnimation {
                            target: exitItem
                            property: "y"
                            from: 0
                            to: -stackView.height
                            duration: 400
                            easing.type: Easing.InOutQuad
                        }
                    }

                    Component {
                        id: page1Component
                        Rectangle {
                            id: page1Rect
                            objectName: "page1"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#E66100"

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 20

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 20

                                    Text {
                                        text: "Page 1"
                                        font.pixelSize: 40
                                        color: "#FFFFFF"
                                        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    spacing: 20

                                    Item {
                                        id: plotContainer
                                        objectName: "plotContainer"
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        Layout.alignment: Qt.AlignHCenter | Qt.AlignTop

                                        property var plotWidget: null

                                        PlotItem {
                                            id: plotItem
                                            Layout.fillWidth: true
                                            Layout.fillHeight: true
                                        }
                                    }

                                    Rectangle {
                                        color: "#DDDDDD"
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 100
                                        Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                                        Text {
                                            text: "Bottom Row"
                                            anchors.centerIn: parent
                                            color: "#000000"
                                        }
                                    }
                                }
                            }
                        }
                    }

                    Component {
                        id: page2Component
                        Rectangle {
                            id: page2Rect
                            objectName: "page2"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#3D3846"

                            ColumnLayout {
                                spacing: 20
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                Text {
                                    text: "Page 2"
                                    font.pixelSize: 40
                                    color: "#FFFFFF"
                                    Layout.alignment: Qt.AlignHCenter | Qt.AlignTop
                                    Layout.topMargin: 20
                                }

                                Rectangle {
                                    width: 200
                                    height: 200
                                    color: "#FFDD00"
                                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                                }

                                Text {
                                    text: "This is the second page."
                                    font.pixelSize: 20
                                    color: "#FFFFFF"
                                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
