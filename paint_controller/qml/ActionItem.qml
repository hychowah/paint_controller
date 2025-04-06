// ActionItem.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: actionItem
    color: "#FFFFFF"
    radius: 15
    border.color: "#E0E0E0"
    border.width: 1

    // Define signals for all possible actions
    signal addAction(string actionId)
    
    // Define backward compatibility signals
    signal addAscend 
    signal addDescend
    signal addMoveWinchTo
    signal addAscendNSpray
    signal addDescendNSpray
    signal addSpray
    signal addStopSpray
    signal addResetYaw

    // Connect old signals to new unified signal
    onAddMoveWinchTo: addAction("0")
    onAddDescend: addAction("1")
    onAddSpray: addAction("2")
    onAddStopSpray: addAction("3")
    onAddAscendNSpray: addAction("4")
    onAddDescendNSpray: addAction("5")
    onAddResetYaw: addAction("6")

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // Action item title
        Text {
            text: "Actions"
            font.pixelSize: 20
            font.bold: true
        }

        // Action item content
        Rectangle {
            id: actionContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#E0E0E0"

            // Use a ColumnLayout for reliable vertical stacking
            ColumnLayout {
                id: actionsLayout
                anchors.fill: parent
                anchors.margins: 10
                spacing: 10

                // Dynamic action buttons created from actionConfig
                Repeater {
                    model: {
                        if (!actionConfig || !actionConfig.actions) {
                            console.log("ActionConfig not properly initialized");
                            return [];
                        }
                        return Object.keys(actionConfig.actions).sort();
                    }
                    
                    delegate: Rectangle {
                        property var action: actionConfig.getAction(modelData)
                        
                        Layout.fillWidth: true
                        Layout.preferredHeight: 70
                        color: Qt.rgba(255, 255, 255, 0.5)
                        border.color: "#E0E0E0"
                        border.width: 1
                        radius: 15

                        Text {
                            anchors.left: parent.left
                            anchors.margins: 10
                            anchors.leftMargin: 20
                            anchors.verticalCenter: parent.verticalCenter
                            text: action ? action.title : "Unknown Action"
                            font.pixelSize: 20
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            onClicked: {
                                actionItem.addAction(modelData)
                            }
                        }
                    }
                }

                // Add spacer item to push everything to the top
                Item {
                    Layout.fillHeight: true
                }
            }
        }
    }

    Component.onCompleted: {
        console.log("actionConfig:", JSON.stringify(actionConfig));
        console.log("actionConfig.actions:", JSON.stringify(actionConfig.actions));
        console.log("Model data:", JSON.stringify(Object.keys(actionConfig.actions)));
    }
}