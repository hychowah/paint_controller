import QtQuick 2.15
import QtQuick.Controls 2.15


Item {
    id: root
    width: 400
    height: 500

    property alias inputValue: inputField.text
    property alias sliderValue: verticalSlider.value
    property Item applicationRoot: null  // New property to reference the application root

    signal arrowAboveClicked()
    signal arrowBelowClicked()

    Text {
        id: sliderValueDisplay
        text: verticalSlider.value.toFixed(0) + " mm/s"
        anchors.bottom: verticalSlider.top
        anchors.horizontalCenter: verticalSlider.horizontalCenter
        font.pixelSize: 16
        color: "#2c3e50"
    }

    Dialog {
        id: warningDialog
        title: "Warning"
        modal: true
        padding: 20
        width: 100
        height: 150
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        parent: applicationRoot  // Add this line
        x: (applicationRoot.width - width) / 2   // Center horizontally
        y: (applicationRoot.height - height) / 2  // Center vertically
        
        background: Rectangle {
            color: "#ffffff"
            radius: 10
            border.color: "#e0e0e0"
            border.width: 1
        }
        
        header: Rectangle {
            color: "transparent"
            height: 40
            
            Label {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: 20
                text: warningDialog.title
                font.bold: true
                font.pixelSize: 16
                color: "#2c3e50"
            }
        }
        
        contentItem: Column {
            spacing: 20
            padding: 20
            
            Row {
                spacing: 10
                
                Text {
                text: "⚠️"
                font.pixelSize: 24
                anchors.verticalCenter: parent.verticalCenter
            }
                
                Label {
                    text: "Please enter both length and speed values"
                    font.pixelSize: 14
                    color: "#2c3e50"
                    wrapMode: Text.WordWrap
                    width: warningDialog.width - 100
                }
            }
        }
        
        footer: Rectangle {
            color: "transparent"
            height: 60
            
            Button {
                anchors.right: parent.right
                anchors.rightMargin: 20
                anchors.verticalCenter: parent.verticalCenter
                text: "OK"
                width: 100
                height: 36
                
                background: Rectangle {
                    color: parent.down ? "#2980b9" : "#3498db"
                    radius: 5
                    
                    Behavior on color {
                        ColorAnimation { duration: 100 }
                    }
                }
                
                contentItem: Text {
                    text: parent.text
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    font.pixelSize: 14
                    font.bold: true
                }
                
                onClicked: warningDialog.close()
            }
        }
    }

    Rectangle {
        width: 100
        height: 100
        anchors.horizontalCenter: inputField.horizontalCenter
        anchors.bottom: inputField.top
        anchors.bottomMargin: 20
        color: "transparent"
        Image {
            id: arrowAbove
            source: "../resource/up_arrow.png"
            anchors.fill: parent
        }
        MouseArea {
            anchors.fill: parent
            onPressed: arrowAbove.opacity = 0.5
            onReleased: {
                arrowAbove.opacity = 1.0
                // Add validation before triggering the backend function
                if (inputField.text.trim() === "" || verticalSlider.value === 0) {
                    warningDialog.open()
                } else {
                    root.arrowAboveClicked()
                    backend.moveWinchIncrement(parseInt(inputField.text), verticalSlider.value)
                }
            }
        }
    }

    TextField {
        id: inputField
        placeholderText: "Enter length"
        font.pixelSize: 20
        width: 160
        height: 40
        verticalAlignment: Text.AlignBottom
        bottomPadding: 5
        rightPadding: 30
        validator: IntValidator {
            bottom: 0
            top: 20000  // Set an appropriate maximum value
            }
        background: Rectangle {
            color: "#9F9F9F"
            border.color: "gray"
            border.width: 1
            radius: 5
            Rectangle {
                width: parent.width
                height: 1
                anchors.bottom: parent.bottom
                color: "gray"
            }
        }
        padding: 10
        anchors.centerIn: parent
        onFocusChanged: {
            if (focus) {
                numpadLoader.active = true
                numpadLoader.item.open()
            } else {
                if (numpadLoader.item) {
                    numpadLoader.item.close()
                }
            }
        }

        Text {
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.rightMargin: 5
            anchors.bottomMargin: 5
            text: "mm"
            font.pixelSize: 14
            color: "gray"
        }
    }

    Rectangle {
        width: 100
        height: 100
        anchors.horizontalCenter: inputField.horizontalCenter
        anchors.top: inputField.bottom
        anchors.topMargin: 20
        color: "transparent"
        Image {
            id: arrowBelow
            source: "../resource/down_arrow.png"
            anchors.fill: parent
        }
        MouseArea {
            anchors.fill: parent
            onPressed: arrowBelow.opacity = 0.5
            onReleased: {
                arrowBelow.opacity = 1.0
                // Add validation before triggering the backend function
                if (inputField.text.trim() === "" || verticalSlider.value === 0) {
                    warningDialog.open()
                } else {
                    root.arrowBelowClicked()
                    backend.moveWinchIncrement(-1 * parseInt(inputField.text), verticalSlider.value)
                }
            }
        }
    }

    Slider {
        id: verticalSlider
        orientation: Qt.Vertical
        anchors.left: inputField.right
        anchors.leftMargin: 5
        anchors.verticalCenter: inputField.verticalCenter
        width: 60
        height: 300
        from: 0
        to: 2000
        stepSize: 1
        value: 1000

        handle: Rectangle {
            x: verticalSlider.leftPadding + verticalSlider.availableWidth / 2 - width / 2
            y: verticalSlider.topPadding + verticalSlider.visualPosition * (verticalSlider.availableHeight - height)
            implicitWidth: 30
            implicitHeight: 30
            radius: 15
            color: verticalSlider.pressed ? "#cccccc" : "#ffffff"
            border.color: "#999999"
            border.width: 2

            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.6
                height: width
                radius: width / 2
                color: "#999999"
            }
        }
    }

    Loader {
        id: numpadLoader
        source: "Numpad.qml"
        active: false
        onLoaded: {
            if (applicationRoot) {
                item.parent = applicationRoot
                positionNumpad()
            } else {
                console.warn("Application root not set for MoveLengthButton")
            }
            item.targetField = inputField
        }
    }

    function positionNumpad() {
        if (numpadLoader.item && applicationRoot) {
            var bottomRight = applicationRoot.mapToItem(null, applicationRoot.width, applicationRoot.height)
            numpadLoader.item.x = bottomRight.x - numpadLoader.item.width - 200
            numpadLoader.item.y = bottomRight.y - numpadLoader.item.height - 100
        }
    }

    Connections {
        target: numpadLoader.item
        function onVisibleChanged() {
            if (!numpadLoader.item.visible) {
                inputField.focus = false
            }
        }
    }

    Component.onCompleted: {
        if (applicationRoot) {
            applicationRoot.widthChanged.connect(positionNumpad)
            applicationRoot.heightChanged.connect(positionNumpad)
        }
    }
}