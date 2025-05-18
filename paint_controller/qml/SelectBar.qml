// SelectBar.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: selectBar
    property var stackView
    property string selectedButton: "buttonPage1"
    property int expandedWidth: 150
    property int collapsedWidth: 50
    property int buttonSize: expanded ? expandedWidth * 0.8 : collapsedWidth - 10
    property int buttonSpacing: 20
    property bool expanded: true
    property bool animationInProgress: false

    signal expandedStateChanged(bool isExpanded, int newWidth)
    
    width: expanded ? expandedWidth : collapsedWidth
    Layout.fillHeight: true
    color: "#4374A2"
    
    // Add smooth animation for expanding/collapsing
    Behavior on width {
        NumberAnimation { 
            id: widthAnimation
            duration: 250
            easing.type: Easing.InOutQuad
            onRunningChanged: {
                if (running) {
                    // Animation started
                    animationInProgress = true;
                } else {
                    // Animation completed - now update button sizes
                    animationInProgress = false;
                    // Emit signal when animation completes
                    expandedStateChanged(expanded, width);
                    // Trigger button size changes after width animation completes
                    buttonSizeTimer.start();
                }
            }
        }
    }
    
    Timer {
        id: buttonSizeTimer
        interval: 10 // Short delay
        repeat: false
        onTriggered: {
            // Force update of button sizes after width animation completes
            buttonColumn.updateButtonSizes();
        }
    }
    
    // Expose a function to toggle sidebar state from external controllers
    function toggleSidebar() {
        if (!animationInProgress) {
            expanded = !expanded;
        }
    }
    
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
        height: 50
        color: "transparent"
        anchors.top: parent.top
    }

    // Flickable container for buttons
    Flickable {
        id: buttonFlickable
        width: parent.width
        anchors.top: topSpacer.bottom
        anchors.bottom: connectionStatusPanel.top
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
            
            // Function to update button sizes
            function updateButtonSizes() {
                // Notify all buttons to update their sizes
                buttonPage1.updateSize();
                buttonPage2.updateSize();
                buttonPage3.updateSize();
                buttonPage4.updateSize();
                buttonPage7.updateSize();
                buttonExit.updateSize();
            }

            // Page 1 Button - Base
            Rectangle {
                id: buttonPage1
                property int targetSize: selectBar.buttonSize
                width: animationInProgress ? width : targetSize
                height: animationInProgress ? height : targetSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage1" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter
                
                function updateSize() {
                    sizeAnimation.start();
                }
                
                ParallelAnimation {
                    id: sizeAnimation
                    NumberAnimation { 
                        target: buttonPage1
                        property: "width" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                    NumberAnimation { 
                        target: buttonPage1
                        property: "height" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                }

                Image {
                    source: "../resource/base.png"
                    anchors.centerIn: parent
                    width: parent.width * 0.7
                    height: parent.height * 0.7
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
                    visible: selectBar.expanded
                    opacity: selectBar.expanded ? 1.0 : 0.0
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
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

            // Page 2 Button - Winch
            Rectangle {
                id: buttonPage2
                property int targetSize: selectBar.buttonSize
                width: animationInProgress ? width : targetSize
                height: animationInProgress ? height : targetSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage2" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter
                
                function updateSize() {
                    sizeAnimation2.start();
                }
                
                ParallelAnimation {
                    id: sizeAnimation2
                    NumberAnimation { 
                        target: buttonPage2
                        property: "width" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                    NumberAnimation { 
                        target: buttonPage2
                        property: "height" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                }

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
                    visible: selectBar.expanded
                    opacity: selectBar.expanded ? 1.0 : 0.0
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
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

            // Page 3 Button - Monitor
            Rectangle {
                id: buttonPage3
                property int targetSize: selectBar.buttonSize
                width: animationInProgress ? width : targetSize
                height: animationInProgress ? height : targetSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage3" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter
                
                function updateSize() {
                    sizeAnimation3.start();
                }
                
                ParallelAnimation {
                    id: sizeAnimation3
                    NumberAnimation { 
                        target: buttonPage3
                        property: "width" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                    NumberAnimation { 
                        target: buttonPage3
                        property: "height" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                }

                Image {
                    source: "../resource/monitor.svg"
                    anchors.centerIn: parent
                    width: parent.width * 0.6
                    height: parent.height * 0.6
                    fillMode: Image.PreserveAspectFit
                    antialiasing: true
                    smooth: true
                    sourceSize: Qt.size(96, 96)
                }

                Text {
                    text: "Monitor"
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: "black"
                    font.pixelSize: 15
                    font.bold: true
                    visible: selectBar.expanded
                    opacity: selectBar.expanded ? 1.0 : 0.0
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
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

            // Page 4 Button - Tuning
            Rectangle {
                id: buttonPage4
                property int targetSize: selectBar.buttonSize
                width: animationInProgress ? width : targetSize
                height: animationInProgress ? height : targetSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage4" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter
                
                function updateSize() {
                    sizeAnimation4.start();
                }
                
                ParallelAnimation {
                    id: sizeAnimation4
                    NumberAnimation { 
                        target: buttonPage4
                        property: "width" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                    NumberAnimation { 
                        target: buttonPage4
                        property: "height" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                }

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
                    visible: selectBar.expanded
                    opacity: selectBar.expanded ? 1.0 : 0.0
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
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

            // Page 7 Button - Spray
            Rectangle {
                id: buttonPage7
                property int targetSize: selectBar.buttonSize
                width: animationInProgress ? width : targetSize
                height: animationInProgress ? height : targetSize
                radius: 20
                color: selectBar.selectedButton === "buttonPage7" ? "#E2E2E2" : "#70A3D2"
                anchors.horizontalCenter: parent.horizontalCenter
                
                function updateSize() {
                    sizeAnimation7.start();
                }
                
                ParallelAnimation {
                    id: sizeAnimation7
                    NumberAnimation { 
                        target: buttonPage7
                        property: "width" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                    NumberAnimation { 
                        target: buttonPage7
                        property: "height" 
                        to: selectBar.buttonSize
                        duration: 250
                        easing.type: Easing.InOutQuad 
                    }
                }

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
                    visible: selectBar.expanded
                    opacity: selectBar.expanded ? 1.0 : 0.0
                    
                    Behavior on opacity {
                        NumberAnimation { duration: 150 }
                    }
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
        }
    }

    // Connection status panel - using the existing component
    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: connectionStatusPanel.top
    }

    ConnectionStatusPanel {
        id: connectionStatusPanel
        expanded: selectBar.expanded
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: buttonExit.top
        anchors.bottomMargin: selectBar.expanded ? 50 : 20
    }

    Rectangle {
        width: parent.width
        height: 2
        color: "white"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: connectionStatusPanel.bottom
    }

    // Exit button
    Rectangle {
        id: buttonExit
        property int targetSize: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
        width: animationInProgress ? width : targetSize
        height: animationInProgress ? height : targetSize
        radius: 20
        color: "#FF5733"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        
        function updateSize() {
            exitSizeAnimation.start();
        }
        
        ParallelAnimation {
            id: exitSizeAnimation
            NumberAnimation { 
                target: buttonExit
                property: "width" 
                to: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
                duration: 250
                easing.type: Easing.InOutQuad 
            }
            NumberAnimation { 
                target: buttonExit
                property: "height" 
                to: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
                duration: 250
                easing.type: Easing.InOutQuad 
            }
        }

        Text {
            text: "Exit"
            anchors.centerIn: parent
            color: "#FFFFFF"
            font.pixelSize: selectBar.expanded ? 20 : 14
            font.bold: true
            visible: selectBar.expanded
            opacity: selectBar.expanded ? 1.0 : 0.0
            
            Behavior on opacity {
                NumberAnimation { duration: 150 }
            }
        }

        // Exit icon for collapsed state
        Rectangle {
            visible: !selectBar.expanded
            anchors.centerIn: parent
            width: parent.width * 0.6
            height: width
            radius: width / 2
            color: "transparent"
            
            Canvas {
                anchors.fill: parent
                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = "white";
                    ctx.lineWidth = width * 0.1;
                    
                    // Draw an X
                    ctx.beginPath();
                    ctx.moveTo(width * 0.2, height * 0.2);
                    ctx.lineTo(width * 0.8, height * 0.8);
                    ctx.stroke();
                    
                    ctx.beginPath();
                    ctx.moveTo(width * 0.8, height * 0.2);
                    ctx.lineTo(width * 0.2, height * 0.8);
                    ctx.stroke();
                }
            }
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