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
    property string selectedButton: "buttonPage1" // Default selected button

    function navigateToPage(index) {
        console.log("Before navigation - currentIndex:", stackView.currentIndex, "depth:", stackView.targetIndex)
        if (index !== stackView.currentIndex) {
            var targetComponent;
            stackView.targetIndex = index
            switch(index) {
                case 0: targetComponent = page1Component; break;
                case 1: targetComponent = page2Component; break;
                case 2: targetComponent = page3Component; break;
            }
            
            console.log("Navigating to page:", index)
            stackView.replace(stackView.currentItem, targetComponent)
            stackView.currentIndex = index
        }
    }

    Column {
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 20

        // Spacer to reserve space at the top
        Rectangle {
            width: parent.width
            height: 20 // Adjust this height to reserve the desired space
            color: "transparent"
        }

        Rectangle {
            id: buttonPage1
            width: selectBar.width * 0.8
            height: selectBar.width * 0.8
            radius: 20
            color: selectBar.selectedButton === "buttonPage1" ? "#E2E2E2" : "#70A3D2"
            Layout.alignment: Qt.AlignHCenter

            Image {
                id: imagePage1
                source: "../resource/base.png"
                anchors.centerIn: parent
                width: selectBar.width * 0.8
                height: selectBar.width * 0.8
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

        Rectangle {
            id: buttonPage2
            width: selectBar.width * 0.8
            height: selectBar.width * 0.8
            radius: 20
            color: selectBar.selectedButton === "buttonPage2" ? "#E2E2E2" : "#70A3D2"
            Layout.alignment: Qt.AlignHCenter

            Image {
                id: imagePage2
                source: "../resource/winch.png"
                anchors.centerIn: parent
                width: selectBar.width * 0.6
                height: selectBar.width * 0.6
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

        // New button for Page 3 with lidar.webp image
        Rectangle {
            id: buttonPage3
            width: selectBar.width * 0.8
            height: selectBar.width * 0.8
            radius: 20
            color: selectBar.selectedButton === "buttonPage3" ? "#E2E2E2" : "#70A3D2"
            Layout.alignment: Qt.AlignHCenter

            Image {
                id: imagePage3
                source: "../resource/lidar.webp"
                anchors.centerIn: parent
                width: selectBar.width * 0.6
                height: selectBar.width * 0.6
                fillMode: Image.PreserveAspectFit
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    if (selectBar.selectedButton !== "buttonPage3") {
                        selectBar.navigateToPage(2)
                        selectBar.selectedButton = "buttonPage3"
                    }
                }
            }
        }
    }

    // Top border for the connection status row
    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: connectionStatusRow.top
    }

    // Connection status row
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

            // Winch status
            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "WINCH"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7 // Adjust this width to ensure alignment
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: backend.winch_available ? "#00e600" : "yellow" // Change color based on status
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // Wheel status
            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "WHEEL"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7 // Adjust this width to ensure alignment
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: backend.wheel_available ? "#00e600" : "yellow"  // Change color based on status
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            // End-effector status
            Row {
                spacing: 5
                width: parent.width

                Text {
                    text: "END-EFFECTOR"
                    color: "white"
                    font.pixelSize: 12
                    font.bold: true
                    anchors.verticalCenter: parent.verticalCenter
                    width: selectBar.width * 0.7 // Adjust this width to ensure alignment
                }
                Rectangle {
                    width: 15
                    height: 15
                    radius: 7.5
                    color: "yellow" // Change color based on status
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

    // Bottom border for the connection status row
    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: connectionStatusRow.bottom
    }

    // Exit button positioned near the bottom
    Rectangle {
        id: buttonExit
        width: selectBar.width * 0.8
        height: selectBar.width * 0.8
        radius: 20
        color: "#FF5733"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20 // Adjust this margin as needed

        Text {
            text: "Exit"
            anchors.centerIn: parent
            color: "#FFFFFF"
            font.pixelSize: 20
        }

        MouseArea {
            anchors.fill: parent
            onClicked: {
                // backend.terminateNodes()
                // Wait a short time to allow nodes to terminate
                exitTimer.start()
            }
        }
    }
    Timer {
        id: exitTimer
        interval: 1000 // 1 second delay
        onTriggered: Qt.quit()
    }
}

