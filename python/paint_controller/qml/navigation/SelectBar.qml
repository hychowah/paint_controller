// SelectBar.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../core"

Rectangle {
    id: selectBar
    required property var stackView
    property string selectedButton: "buttonHome"
    property int expandedWidth: CommonStyle.shellSidebarExpandedWidth
    property int collapsedWidth: CommonStyle.shellSidebarCollapsedWidth
    property int buttonSize: expanded ? expandedWidth * 0.8 : collapsedWidth - 10
    property int buttonSpacing: CommonStyle.shellSidebarButtonGap
    property bool expanded: true
    property bool animationInProgress: false

    signal expandedStateChanged(bool isExpanded, int newWidth)
    
    width: expanded ? expandedWidth : collapsedWidth
    Layout.fillHeight: true
    color: CommonStyle.sidebarBackground
    
    // NavigationButton Component Definition
    component NavigationButton: Rectangle {
        id: navigationButton
        
        // Properties that can be customized
        property string buttonId: ""
        property string buttonText: ""
        property string iconSource: ""
        property int pageIndex: 0
        property bool isSelected: false
        property int targetSize: selectBar.buttonSize
        property real iconScale: 0.6
        
        // Button appearance
        width: selectBar.animationInProgress ? width : targetSize
        height: selectBar.animationInProgress ? height : targetSize
        radius: CommonStyle.shellSidebarButtonRadius
        color: isSelected ? CommonStyle.sidebarButtonSelected : CommonStyle.sidebarButton
        anchors.horizontalCenter: parent.horizontalCenter
        
        // Public function to update size
        function updateSize() {
            sizeAnimation.start();
        }
        
        // Size animation
        ParallelAnimation {
            id: sizeAnimation
            NumberAnimation { 
                target: navigationButton
                property: "width" 
                to: selectBar.buttonSize
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad 
            }
            NumberAnimation { 
                target: navigationButton
                property: "height" 
                to: selectBar.buttonSize
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad 
            }
        }

        // Icon
        Image {
            source: iconSource
            anchors.centerIn: parent
            width: parent.width * iconScale
            height: parent.height * iconScale
            fillMode: Image.PreserveAspectFit
            antialiasing: true
            smooth: true
            sourceSize: Qt.size(96, 96)
        }

        // Text label
        Text {
            text: buttonText
            anchors.bottom: parent.bottom
            anchors.bottomMargin: CommonStyle.spacingXs + 1
            anchors.horizontalCenter: parent.horizontalCenter
            color: CommonStyle.textStrong
            font.family: CommonStyle.fontSans
            font.pixelSize: CommonStyle.shellNavLabelFont
            font.bold: true
            visible: selectBar.expanded
            opacity: selectBar.expanded ? 1.0 : 0.0
            
            Behavior on opacity {
                NumberAnimation { duration: CommonStyle.motionFast }
            }
        }

        // Mouse interaction
        MouseArea {
            anchors.fill: parent
            onClicked: {
                if (!isSelected) {
                    selectBar.navigateToPage(pageIndex)
                    selectBar.selectedButton = buttonId
                }
            }
        }
    }
    
    // Add smooth animation for expanding/collapsing
    Behavior on width {
        NumberAnimation { 
            id: widthAnimation
            duration: CommonStyle.motionStandard
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
                case 0: targetComponent = homeComponent; break;
                case 1: targetComponent = wheelPageComponent; break;
                case 2: targetComponent = winchPageComponent; break;
                case 3: targetComponent = statusPageComponent; break;
                case 4: targetComponent = tuningPageComponent; break;
                case 5: targetComponent = launcherPageComponent; break;
                case 8: targetComponent = settingsPageComponent; break;
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
        height: CommonStyle.shellTopSpacerHeight
        color: "transparent"
        anchors.top: parent.top
    }

    // Flickable container for buttons
    Flickable {
        id: buttonFlickable
        width: parent.width
        anchors.top: topSpacer.bottom
        anchors.bottom: connectionStatusPanel.top
        anchors.bottomMargin: CommonStyle.spacingLg
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
                for (var i = 0; i < children.length; i++) {
                    if (children[i].updateSize) {
                        children[i].updateSize();
                    }
                }
            }
            // home button
            NavigationButton {
                id: buttonHome
                buttonId: "buttonHome"
                buttonText: "Home"
                iconSource: "../../resource/homepage.svg"
                pageIndex: 0
                isSelected: selectBar.selectedButton === "buttonHome"
                iconScale: 0.7
            }

            // Page 1 Button - Base
            NavigationButton {
                id: buttonPage1
                buttonId: "buttonPage1"
                buttonText: "Base"
                iconSource: "../../resource/base.png"
                pageIndex: 1
                isSelected: selectBar.selectedButton === "buttonPage1"
                iconScale: 0.7
            }

            // Page 2 Button - Winch
            NavigationButton {
                id: buttonPage2
                buttonId: "buttonPage2"
                buttonText: "Winch"
                iconSource: "../../resource/winch.png"
                pageIndex: 2
                isSelected: selectBar.selectedButton === "buttonPage2"
            }

            // Page 3 Button - Monitor
            NavigationButton {
                id: buttonPage3
                buttonId: "buttonPage3"
                buttonText: "Monitor"
                iconSource: "../../resource/monitor.svg"
                pageIndex: 3
                isSelected: selectBar.selectedButton === "buttonPage3"
            }

            // Page 4 Button - Tuning
            NavigationButton {
                id: buttonPage4
                buttonId: "buttonPage4"
                buttonText: "Tuning"
                iconSource: "../../resource/icon-pid.png"
                pageIndex: 4
                isSelected: selectBar.selectedButton === "buttonPage4"
            }

            // Page 5 Button - Launcher
            NavigationButton {
                id: buttonPage5
                buttonId: "buttonPage5"
                buttonText: "Launcher"
                iconSource: "../../resource/launcher.svg"
                pageIndex: 5
                isSelected: selectBar.selectedButton === "buttonPage5"
                iconScale: 0.7
            }

            // Page Settings Button
            NavigationButton {
                id: buttonPageSettings
                buttonId: "buttonPageSettings"
                buttonText: "Settings"
                iconSource: "../../resource/setting.svg"
                pageIndex: 8
                isSelected: selectBar.selectedButton === "buttonPageSettings"
            }
        }
    }

    // Connection status panel - using the existing component
    Rectangle {
        width: parent.width
        height: 2
        color: CommonStyle.borderDefault
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: connectionStatusPanel.top
    }

    ConnectionStatusPanel {
        id: connectionStatusPanel
        expanded: selectBar.expanded
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: buttonExit.top
        anchors.bottomMargin: selectBar.expanded ? CommonStyle.shellTopSpacerHeight : CommonStyle.spacingLg
    }

    Rectangle {
        width: parent.width
        height: 2
        color: CommonStyle.borderDefault
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: connectionStatusPanel.bottom
    }

    // Exit button
    Rectangle {
        id: buttonExit
        property int targetSize: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
        width: animationInProgress ? width : targetSize
        height: animationInProgress ? height : targetSize
        radius: CommonStyle.shellSidebarButtonRadius
        color: CommonStyle.buttonDanger
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: CommonStyle.spacingLg
        
        function updateSize() {
            exitSizeAnimation.start();
        }
        
        ParallelAnimation {
            id: exitSizeAnimation
            NumberAnimation { 
                target: buttonExit
                property: "width" 
                to: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad 
            }
            NumberAnimation { 
                target: buttonExit
                property: "height" 
                to: selectBar.expanded ? selectBar.width * 0.8 : selectBar.width - 10
                duration: CommonStyle.motionStandard
                easing.type: Easing.InOutQuad 
            }
        }

        Text {
            text: "Exit"
            anchors.centerIn: parent
            color: CommonStyle.textPrimary
            font.family: CommonStyle.fontSans
            font.pixelSize: selectBar.expanded ? CommonStyle.shellExitFont : CommonStyle.shellWarningFont
            font.bold: true
            visible: selectBar.expanded
            opacity: selectBar.expanded ? 1.0 : 0.0
            
            Behavior on opacity {
                NumberAnimation { duration: CommonStyle.motionFast }
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
                    ctx.strokeStyle = CommonStyle.textPrimary;
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
