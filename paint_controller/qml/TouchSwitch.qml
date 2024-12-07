import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: touchSwitchContainer
    
    // Exposed properties
    property bool checked: false
    property color activeColor: "#4CAF50"
    property color inactiveColor: "#cccccc"
    property color activeBorderColor: "#43A047"
    property color inactiveBorderColor: "#bbbbbb"
    
    // Signals
    signal toggled(bool checked)
    
    // Size properties with defaults
    Layout.preferredWidth: 80
    Layout.preferredHeight: 40
    color: "transparent"
    
    Switch {
        id: switchControl
        anchors.centerIn: parent
        checked: touchSwitchContainer.checked
        
        indicator: Rectangle {
            implicitWidth: 60
            implicitHeight: 30
            radius: height / 2
            color: switchControl.checked ? activeColor : inactiveColor
            border.color: switchControl.checked ? activeBorderColor : inactiveBorderColor
            
            Rectangle {
                x: switchControl.checked ? parent.width - width - 4 : 4
                width: parent.height - 8
                height: width
                radius: width / 2
                color: "white"
                border.color: switchControl.checked ? activeBorderColor : inactiveBorderColor
                anchors.verticalCenter: parent.verticalCenter
                
                Behavior on x {
                    NumberAnimation { duration: 200 }
                }
            }
        }
    }
    
    MouseArea {
        anchors.fill: parent
        onClicked: {
            touchSwitchContainer.checked = !touchSwitchContainer.checked
            touchSwitchContainer.toggled(touchSwitchContainer.checked)
        }
    }
}