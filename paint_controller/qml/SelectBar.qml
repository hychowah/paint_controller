import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7
import QtCharts 6.7
import QtMultimedia 6.7

Rectangle {
    id: selectBar
    stackView: stackView
    width: 150
    Layout.fillHeight: true
    color: "#4374A2"

    property var stackView
    property string selectedButton: "buttonPage1"
    property int buttonSize: width * 0.8
    property int buttonSpacing: 20

    function navigateToPage(index) {
        console.log("Before navigation - currentIndex:", stackView.currentIndex, "depth:", stackView.targetIndex)
        if (index !== stackView.currentIndex) {
            var targetComponent;
            stackView.targetIndex = index
            switch(index) {
                case 0: targetComponent = page1Component; break;
                case 1: targetComponent = page2Component; break;
                case 2: targetComponent = page3Component; break;
                case 3: targetComponent = page4Component; break;
                // Add more cases for additional pages
            }
            
            console.log("Navigating to page:", index)
            stackView.replace(stackView.currentItem, targetComponent)
            stackView.currentIndex = index
        }
    }

    // Top spacer
    Rectangle {
        id: topSpacer
        width: parent.width
        height: 20
        color: "transparent"
        anchors.top: parent.top
    }

    // Flickable container for buttons
    Flickable {
        id: buttonFlickable
        width: parent.width
        anchors.top: topSpacer.bottom
        anchors.bottom: connectionStatusRow.top
        anchors.bottomMargin: 20
        contentWidth: width
        contentHeight: buttonColumn.height
        clip: true
        
        // Show scrollbar when content exceeds visible area
        ScrollBar.vertical: ScrollBar {
            active: buttonFlickable.contentHeight > buttonFlickable.height
            policy: ScrollBar.AsNeeded
        }

        Column {
            id: buttonColumn
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: buttonSpacing
            width: parent.width

            // Page 1 Button
            Rectangle {
                id: buttonPage1
                width: buttonSize
                height: buttonSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage1" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "../resource/base.png"
                    anchors.centerIn: parent
                    width: parent.width * 0.8
                    height: parent.height * 0.8
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (selectBar.selectedButton !== "buttonPage1") {
                            selectBar.navigateToPage(0)
                            selectBar.selectedButton = "buttonPage1"
                        }
                    }
                }
            }

            // Page 2 Button
            Rectangle {
                id: buttonPage2
                width: buttonSize
                height: buttonSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage2" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "../resource/winch.png"
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (selectBar.selectedButton !== "buttonPage2") {
                            selectBar.navigateToPage(1)
                            selectBar.selectedButton = "buttonPage2"
                        }
                    }
                }
            }

            // Page 3 Button
            Rectangle {
                id: buttonPage3
                width: buttonSize
                height: buttonSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage3" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "../resource/lidar.webp"
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (selectBar.selectedButton !== "butonPage3") {
                            selectBar.navigateToPage(2)
                            selectBar.selectedButton = "buttonPage3"
                        }
                    }
                }
            }

            // Page 3 Button
            Rectangle {
                id: buttonPage4
                width: buttonSize
                height: buttonSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage4" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "../resource/icon-pid.png"
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (selectBar.selectedButton !== "buttonPage4") {
                            selectBar.navigateToPage(3)
                            selectBar.selectedButton = "buttonPage4"
                        }
                    }
                }
            }

            // Template for additional buttons
            // Copy and modify this structure for new pages
            // Rectangle {
            //     id: buttonPageX
            //     width: buttonSize
            //     height: buttonSize
            //     radius: 20
            //     color: selectBar.selectedButton === "buttonPageX" ? "#E2E2E2" : "#70A3D2"
            //     anchors.horizontalCenter: parent.horizontalCenter
            //     
            //     Image {
            //         source: "../resource/your-image.png"
            //         anchors.centerIn: parent
            //         width: parent.width * 0.6
            //         height: parent.height * 0.6
            //         fillMode: Image.PreserveAspectFit
            //     }
            //     
            //     MouseArea {
            //         anchors.fill: parent
            //         onClicked: {
            //             if (selectBar.selectedButton !== "buttonPageX") {
            //                 selectBar.navigateToPage(X)
            //                 selectBar.selectedButton = "buttonPageX"
            //             }
            //         }
            //     }
            // }
        }
    }

    // Connection status section remains the same
    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: connectionStatusRow.top
    }

    Rectangle {
        id: connectionStatusRow
        width: parent.width
        height: 80
        color: "#A4A589"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: buttonExit.top 
        anchors.bottomMargin: 50

        Column {
            anchors.fill: parent
            spacing: 5
            anchors.margins: 10

            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "WINCH"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: uiData.winch_available ? "#00e600" : "yellow"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "WHEEL"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: uiData.wheel_available ? "#00e600" : "yellow"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "END-EFFECTOR"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: "yellow"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: connectionStatusRow.bottom
    }

    Rectangle {
        id: buttonExit
        width: selectBar.width * 0.8
        height: selectBar.width * 0.8
        radius: 20
        color: "#FF5733"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20

        Text {
            text: "Exit"
            anchors.centerIn: parent
            color: "#FFFFFF"
            font.pixelSize: 20
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                exitTimer.start()
            }
        }
    }

    Timer {
        id: exitTimer
        interval: 1000
        onTriggered: Qt.quit()
    }
}