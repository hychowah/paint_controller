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
    onAddMoveWinchTo: {
        console.log("Legacy signal: addMoveWinchTo -> addAction(0)");
        addAction("0");
    }
    onAddDescend: {
        console.log("Legacy signal: addDescend -> addAction(1)");
        addAction("1");
    }
    onAddSpray: {
        console.log("Legacy signal: addSpray -> addAction(2)");
        addAction("2");
    }
    onAddStopSpray: {
        console.log("Legacy signal: addStopSpray -> addAction(3)");
        addAction("3");
    }
    onAddAscendNSpray: {
        console.log("Legacy signal: addAscendNSpray -> addAction(4)");
        addAction("4");
    }
    onAddDescendNSpray: {
        console.log("Legacy signal: addDescendNSpray -> addAction(5)");
        addAction("5");
    }
    onAddResetYaw: {
        console.log("Legacy signal: addResetYaw -> addAction(6)");
        addAction("6");
    }

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
                            console.error("ActionConfig not properly initialized");
                            return [];
                        }
                        
                        var keys = Object.keys(actionConfig.actions).sort();
                        console.log("Action keys:", JSON.stringify(keys));
                        return keys;
                    }
                    
                    delegate: Rectangle {
                        property var action: {
                            var act = actionConfig.getAction(modelData);
                            // console.log("Action for ID " + modelData + ":", JSON.stringify(act));
                            return act;
                        }
                        
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
                                console.log("Action clicked: " + modelData + " - " + (action ? action.title : "Unknown"));
                                actionItem.addAction(modelData);
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

    // Component.onCompleted: {
    //     // console.log("ActionItem initialized");
    //     if (actionConfig) {
    //         console.log("actionConfig available:", typeof actionConfig);
    //         if (actionConfig.actions) {
    //             console.log("actionConfig.actions available");
    //             try {
    //                 console.log("actionConfig.actions:", JSON.stringify(actionConfig.actions));
    //             } catch (e) {
    //                 console.error("Error stringifying actionConfig.actions:", e);
    //             }
    //         } else {
    //             console.error("actionConfig.actions is not available");
    //         }
    //     } else {
    //         console.error("actionConfig is not available");
    //     }
    // }
}