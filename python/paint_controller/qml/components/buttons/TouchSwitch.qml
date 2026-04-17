import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "../../core"

Rectangle {
    id: touchSwitchContainer
    
    // Exposed properties
    property bool checked: false
    property color activeColor: CommonStyle.statusSuccess
    property color inactiveColor: CommonStyle.textDisabled
    property color activeBorderColor: CommonStyle.statusSuccess
    property color inactiveBorderColor: CommonStyle.borderDefault
    
    // Signals
    signal toggled(bool checked)
    
    // Size properties with defaults
    Layout.preferredWidth: Math.round(80 * CommonStyle.scaleFactor)
    Layout.preferredHeight: Math.round(40 * CommonStyle.scaleFactor)
    color: "transparent"
    
    Switch {
        id: switchControl
        anchors.centerIn: parent
        checked: touchSwitchContainer.checked
        
        indicator: Rectangle {
            implicitWidth: Math.round(60 * CommonStyle.scaleFactor)
            implicitHeight: Math.round(30 * CommonStyle.scaleFactor)
            radius: height / 2
            color: switchControl.checked ? activeColor : inactiveColor
            border.color: switchControl.checked ? activeBorderColor : inactiveBorderColor
            
            Rectangle {
                x: switchControl.checked ? parent.width - width - 4 : 4
                width: parent.height - 8
                height: width
                radius: width / 2
                color: CommonStyle.textPrimary
                border.color: switchControl.checked ? activeBorderColor : inactiveBorderColor
                anchors.verticalCenter: parent.verticalCenter
                
                Behavior on x {
                    NumberAnimation { duration: CommonStyle.motionStandard }
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