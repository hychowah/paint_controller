import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
// import CustomComponents 1.0

ApplicationWindow {
    visible: true
    visibility: Window.FullScreen

    // Get all available screens
    property var screens: Qt.application.screens
    
    // Choose the screen you want (e.g., the second screen)
    property var targetScreen: screens.length > 1 ? screens[1] : screens[0]
    
    // Set the window properties based on the target screen
    x: targetScreen.virtualX
    y: targetScreen.virtualY
    width: targetScreen.width
    height: targetScreen.height
    

    Rectangle {
        id: background
        anchors.fill: parent
        // color: "#FFFFFF"

        // Container to maintain resolution
        // Rectangle {
            // width: 1280
            // height: 720
            // anchors.centerIn: parent
            color: "#5E5C64"

            RowLayout {
                anchors.fill: parent
                spacing: 10

                // Static Select Bar
                SelectBar {
                    id: selectBar
                    stackView: stackView
                    Layout.fillHeight: true
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
                            Page1 {}
                        }

                        Component {
                            id: page2Component
                            Page2 {}
                        }
                    }
                }
            }
        }
    }
// }
