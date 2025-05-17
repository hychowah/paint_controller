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
                case 4: targetComponent = page5Component; break;
                case 5: targetComponent = page6Component; break;
                case 6: targetComponent = page7Component; break;
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

                Text {
                    text: "Base"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
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

                Text {
                    text: "Winch"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
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
                    source: "../resource/monitor.svg" 
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                    antialiasing: true  
                    smooth: true 
                    sourceSize: Qt.size(96, 96)  // Force higher resolution rendering     
                }

                Text {
                    text: "Monitor"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
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

            // Page 4 Button
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

                Text {
                    text: "Tuning"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
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


            // Page 6 Button
            Rectangle {
                id: buttonPage7
                width: buttonSize
                height: buttonSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage7" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "../resource/spray.png"
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                }

                Text {
                    text: "Spray"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        if (selectBar.selectedButton !== "buttonPage7") {
                            selectBar.navigateToPage(6)
                            selectBar.selectedButton = "buttonPage7"
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
        height: 100
        color: "#A4A589"  
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: buttonExit.top 
        anchors.bottomMargin: 50

        // Add state property to track which view is shown
        property bool showDeviceStatus: true

        // Define natural-looking colors as properties
        property color availableColor: "#7ED957"  // Softer green
        property color idleColor: "#4CD964"       // Natural green
        property color onTaskColor: "#4A90E2"     // Soft blue
        property color warningColor: "#FFCC00"    // Amber yellow
        property color errorColor: "#FF5E3A"      // Soft red
        property color offlineColor: "#8E8E93"    // Medium gray

        // Make the rectangle clickable
        MouseArea {
            anchors.fill: parent
            onClicked: parent.showDeviceStatus = !parent.showDeviceStatus
        }

        Column {
            anchors.fill: parent
            spacing: 8  // Increased spacing for better readability
            anchors.margins: 12  // Increased margins

            // Device Status View
            Column {
                visible: parent.parent.showDeviceStatus
                width: parent.width
                spacing: parent.spacing

                Row {
                    spacing: 8  // Increased spacing
                    width: parent.width

                    Text {
                        text: "WINCH"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: selectBar.width * 0.45  // Adjusted for alignment
                    }
                    
                    // Status lights container for better alignment
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: winchController.available ? connectionStatusRow.availableColor : connectionStatusRow.warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // Base heartbeat status indicator with SWAPPED colors (idle = green, onTask = blue)
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: {
                                if (!heartbeatHandler.base_online) return connectionStatusRow.offlineColor;
                                switch(heartbeatHandler.base_status) {
                                    case 0x00: return connectionStatusRow.idleColor;     // IDLE - NOW GREEN
                                    case 0x01: return connectionStatusRow.onTaskColor;   // ONTASK - NOW BLUE
                                    case 0x02: return connectionStatusRow.warningColor;  // WARNING
                                    case 0x03: return connectionStatusRow.errorColor;    // ERROR
                                    default: return connectionStatusRow.offlineColor;
                                }
                            }
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                            
                            ToolTip.visible: baseHeartbeatMouseArea.containsMouse
                            ToolTip.text: {
                                let statusText = "Unknown";
                                if (!heartbeatHandler.base_online) {
                                    statusText = "OFFLINE";
                                } else {
                                    switch(heartbeatHandler.base_status) {
                                        case 0x00: statusText = "IDLE"; break;
                                        case 0x01: statusText = "ONTASK"; break;
                                        case 0x02: statusText = "WARNING"; break;
                                        case 0x03: statusText = "ERROR"; break;
                                        case 0x04: statusText = "CLEAR_ERROR"; break;
                                    }
                                }
                                return "Base heartbeat: " + statusText;
                            }
                            
                            MouseArea {
                                id: baseHeartbeatMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                        }
                    }
                }

                Row {
                    spacing: 8
                    width: parent.width

                    Text {
                        text: "WHEEL"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: selectBar.width * 0.45
                    }
                    
                    // Status lights container for better alignment
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: wheelController.available ? connectionStatusRow.availableColor : connectionStatusRow.warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // Base heartbeat status indicator with SWAPPED colors (idle = green, onTask = blue)
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: {
                                if (!heartbeatHandler.base_online) return connectionStatusRow.offlineColor;
                                switch(heartbeatHandler.base_status) {
                                    case 0x00: return connectionStatusRow.idleColor;     // IDLE - NOW GREEN
                                    case 0x01: return connectionStatusRow.onTaskColor;   // ONTASK - NOW BLUE
                                    case 0x02: return connectionStatusRow.warningColor;  // WARNING
                                    case 0x03: return connectionStatusRow.errorColor;    // ERROR
                                    default: return connectionStatusRow.offlineColor;
                                }
                            }
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                            
                            ToolTip.visible: baseHeartbeatMouseArea2.containsMouse
                            ToolTip.text: {
                                let statusText = "Unknown";
                                if (!heartbeatHandler.base_online) {
                                    statusText = "OFFLINE";
                                } else {
                                    switch(heartbeatHandler.base_status) {
                                        case 0x00: statusText = "IDLE"; break;
                                        case 0x01: statusText = "ONTASK"; break;
                                        case 0x02: statusText = "WARNING"; break;
                                        case 0x03: statusText = "ERROR"; break;
                                        case 0x04: statusText = "CLEAR_ERROR"; break;
                                    }
                                }
                                return "Base heartbeat: " + statusText;
                            }
                            
                            MouseArea {
                                id: baseHeartbeatMouseArea2
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                        }
                    }
                }

                Row {
                    spacing: 8
                    width: parent.width

                    Text {
                        text: "EF"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        anchors.verticalCenter: parent.verticalCenter
                        width: selectBar.width * 0.45
                    }
                    
                    // Status lights container for better alignment
                    Row {
                        spacing: 8
                        anchors.verticalCenter: parent.verticalCenter
                        
                        // Controller availability indicator
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: teensyController.available ? connectionStatusRow.availableColor : connectionStatusRow.warningColor
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                        }
                        
                        // EF heartbeat status indicator with SWAPPED colors (idle = green, onTask = blue)
                        Rectangle {
                            width: 14
                            height: 14
                            radius: 7
                            color: {
                                if (!heartbeatHandler.ef_online) return connectionStatusRow.offlineColor;
                                switch(heartbeatHandler.ef_status) {
                                    case 0x00: return connectionStatusRow.idleColor;     // IDLE - NOW GREEN
                                    case 0x01: return connectionStatusRow.onTaskColor;   // ONTASK - NOW BLUE
                                    case 0x02: return connectionStatusRow.warningColor;  // WARNING
                                    case 0x03: return connectionStatusRow.errorColor;    // ERROR
                                    default: return connectionStatusRow.offlineColor;
                                }
                            }
                            anchors.verticalCenter: parent.verticalCenter
                            
                            // Add a subtle glow effect
                            Rectangle {
                                anchors.fill: parent
                                radius: parent.radius
                                color: "transparent"
                                border.width: 1
                                border.color: Qt.rgba(parent.color.r, parent.color.g, parent.color.b, 0.5)
                            }
                            
                            ToolTip.visible: efHeartbeatMouseArea.containsMouse
                            ToolTip.text: {
                                let statusText = "Unknown";
                                if (!heartbeatHandler.ef_online) {
                                    statusText = "OFFLINE";
                                } else {
                                    switch(heartbeatHandler.ef_status) {
                                        case 0x00: statusText = "IDLE"; break;
                                        case 0x01: statusText = "ONTASK"; break;
                                        case 0x02: statusText = "WARNING"; break;
                                        case 0x03: statusText = "ERROR"; break;
                                        case 0x04: statusText = "CLEAR_ERROR"; break;
                                    }
                                }
                                return "EF heartbeat: " + statusText;
                            }
                            
                            MouseArea {
                                id: efHeartbeatMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                        }
                    }
                }
            }

            // IP Status View
            Column {
                visible: !parent.parent.showDeviceStatus
                width: parent.width
                spacing: parent.spacing

                Row {
                    spacing: 5
                    width: parent.width

                    Text {
                        text: "EF IP:"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        width: selectBar.width * 0.7
                    }
                    Text {
                        text: uiData.ef_ip
                        color: "white"  // Changed to white for better contrast
                        font.bold: true
                        font.pixelSize: 10
                        Layout.fillWidth: true
                        anchors.right: parent.right
                    }
                }

                Row {
                    spacing: 5
                    width: parent.width

                    Text {
                        text: "BASE IP:"
                        color: "white"
                        font.pixelSize: 12
                        font.bold: true
                        width: selectBar.width * 0.7
                    }
                    Text {
                        text: uiData.base_ip
                        color: "white"  // Changed to white for better contrast
                        font.bold: true
                        font.pixelSize: 10
                        Layout.fillWidth: true
                        anchors.right: parent.right
                    }
                }
            }

            // Optional: Add an indicator to show which view is currently displayed
            Text {
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                text: parent.parent.showDeviceStatus ? "Touch to show IP" : "Touch to show Device Status"
                color: "white"
                font.pixelSize: 10
                font.italic: true
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