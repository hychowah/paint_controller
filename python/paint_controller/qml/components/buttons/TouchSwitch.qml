import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../theme"

Rectangle {
    id: touchSwitchContainer
    
    required property bool checked
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
            // Request only: the visual follows the external `checked` binding,
            // so a rejected request needs no revert and the binding survives.
            touchSwitchContainer.toggled(!touchSwitchContainer.checked)
        }
    }
}