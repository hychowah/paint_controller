import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    visible: true
    visibility: Window.FullScreen
    property var screens: Qt.application.screens
    property var targetScreen: screens.length > 1 ? screens[0] : screens[0]
    
    x: targetScreen.virtualX
    y: targetScreen.virtualY
    width: targetScreen.width
    height: targetScreen.height
    
    Rectangle {
        id: background
        anchors.fill: parent
        color: "#5E5C64"
        
        RowLayout {
            anchors.fill: parent
            spacing: 10
            
            SelectBar {
                id: selectBar
                stackView: stackView
                Layout.fillHeight: true
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#5E5C64"
                
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0
                    
                    // Top bar
                    TopBar {
                        Layout.fillWidth: true
                    }
                    
                    // StackView container
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        
                        // StackView
                        StackView {
                            id: stackView
                            objectName: "stackView"
                            anchors.fill: parent
                            initialItem: page1Component
                            
                            property int currentIndex: 0
                            property int targetIndex: 0
                            
                            replaceEnter: Transition {
                                NumberAnimation {
                                    property: "y"
                                    from: stackView.currentIndex > stackView.targetIndex ? -stackView.height : stackView.height
                                    to: 0
                                    duration: 400
                                    easing.type: Easing.InOutQuad
                                }
                            }
                            
                            replaceExit: Transition {
                                NumberAnimation {
                                    property: "y"
                                    from: 0
                                    to: stackView.currentIndex > stackView.targetIndex ? stackView.height : -stackView.height
                                    duration: 400
                                    easing.type: Easing.InOutQuad
                                }
                            }
                        }
                    }
                }
            }
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
    
    Component {
        id: page3Component
        Page3 {}
    }
}