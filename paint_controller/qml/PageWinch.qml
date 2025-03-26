import QtQuick 6.7
import QtQuick.Controls 6.7
import QtQuick.Layouts 6.7

Item {
    id: winchPageRoot
    objectName: "winchPageRoot"
    Layout.fillWidth: true
    Layout.fillHeight: true
    
    Rectangle {
        id: dataRect
        width: Math.min(parent.width * 0.95, 1200)
        height: Math.min(parent.height * 0.9, 680)
        anchors.centerIn: parent
        color: "#E2E2E2"
        radius: 20
        
        RowLayout {
            anchors.fill: parent
            anchors.margins: 15
            spacing: 15
            
            Rectangle {
                Layout.preferredWidth: parent.width * 0.6
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        color: winchController.available ? "#E3F2FD" : "#FFEBEE"
                        radius: 12
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Rectangle {
                                width: 12
                                height: 12
                                radius: 6
                                color: winchController.available ? "#2196F3" : "#F44336"
                            }
                            
                            Text {
                                text: "Winch Control"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            Item { Layout.fillWidth: true }
                            
                            Text {
                                text: winchController.available ? "Connected" : "Disconnected"
                                color: winchController.available ? "#2196F3" : "#F44336"
                                font.pixelSize: 14
                                font.bold: true
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 56
                        color: winchController.enabled ? "#E3F2FD" : "#F5F5F5"
                        radius: 12
                        border.width: 1
                        border.color: winchController.enabled ? "#90CAF9" : "#E0E0E0"
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            Rectangle {
                                width: 32
                                height: 32
                                radius: 16
                                color: winchController.enabled ? "#2196F3" : "#9E9E9E"
                            }
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                
                                Label {
                                    text: "Winch Power"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                Label {
                                    text: winchController.enabled ? "Enabled - Motor active" : "Disabled - Motor inactive"
                                    font.pixelSize: 13
                                    color: winchController.enabled ? "#2196F3" : "#757575"
                                }
                            }
                            
                            Switch {
                                checked: winchController.enabled
                                onToggled: winchController.setEnabled(checked)
                                enabled: winchController.available
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 56
                        color: winchController.load_detection_enabled ? "#E3F2FD" : "#F5F5F5"
                        radius: 12
                        border.width: 1
                        border.color: winchController.load_detection_enabled ? "#90CAF9" : "#E0E0E0"
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            Rectangle {
                                width: 32
                                height: 32
                                radius: 16
                                color: winchController.load_detection_enabled ? "#2196F3" : "#9E9E9E"
                            }
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                
                                Label {
                                    text: "Load Detection"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                Label {
                                    text: winchController.load_detection_enabled ? "Enabled - Safety active" : "Disabled - No load protection"
                                    font.pixelSize: 13
                                    color: winchController.load_detection_enabled ? "#2196F3" : "#757575"
                                }
                            }
                            
                            Switch {
                                checked: winchController.load_detection_enabled
                                onToggled: winchController.setLoadDetectionEnabled(checked)
                                enabled: winchController.enabled
                            }
                        }
                    }
                    
                    GridLayout {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        columns: 2
                        rowSpacing: 15
                        columnSpacing: 15
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#F5F5F5"
                            radius: 12
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10
                                
                                Text {
                                    text: "Move Increment"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 10
                                    columnSpacing: 10
                                    
                                    Text { 
                                        text: "Length (mm)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    TextField {
                                        id: incrementLengthField
                                        Layout.fillWidth: true
                                        selectByMouse: true
                                        enabled: winchController.enabled
                                        validator: IntValidator { bottom: -10000; top: 10000 }
                                        background: Rectangle {
                                            radius: 6
                                            border.color: "#BDBDBD"
                                            border.width: 1
                                        }
                                    }
                                    
                                    Text { 
                                        text: "Speed (mm/s)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    TextField {
                                        id: incrementSpeedField
                                        Layout.fillWidth: true
                                        selectByMouse: true
                                        text: "500"
                                        enabled: winchController.enabled
                                        validator: IntValidator { bottom: 1; top: 1000 }
                                        background: Rectangle {
                                            radius: 6
                                            border.color: "#BDBDBD"
                                            border.width: 1
                                        }
                                    }
                                }
                                
                                Item { Layout.fillHeight: true }
                                
                                Button {
                                    Layout.fillWidth: true
                                    text: "MOVE INCREMENT"
                                    enabled: winchController.enabled && incrementLengthField.text.length > 0 && incrementSpeedField.text.length > 0
                                    onClicked: {
                                        winchController.moveIncrement(
                                            parseInt(incrementLengthField.text),
                                            parseInt(incrementSpeedField.text)
                                        )
                                    }
                                    
                                    background: Rectangle {
                                        radius: 6
                                        color: parent.enabled ? "#2196F3" : "#BDBDBD"
                                    }
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: "white"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                        
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            color: "#F5F5F5"
                            radius: 12
                            
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10
                                
                                Text {
                                    text: "Move Absolute"
                                    font.pixelSize: 16
                                    font.bold: true
                                    color: "#212121"
                                }
                                
                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    rowSpacing: 10
                                    columnSpacing: 10
                                    
                                    Text { 
                                        text: "Position (mm)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    TextField {
                                        id: absoluteLengthField
                                        Layout.fillWidth: true
                                        selectByMouse: true
                                        enabled: winchController.enabled
                                        validator: IntValidator { bottom: 0; top: 10000 }
                                        background: Rectangle {
                                            radius: 6
                                            border.color: "#BDBDBD"
                                            border.width: 1
                                        }
                                    }
                                    
                                    Text { 
                                        text: "Speed (mm/s)" 
                                        font.pixelSize: 14
                                        color: "#212121"
                                    }
                                    
                                    TextField {
                                        id: absoluteSpeedField
                                        Layout.fillWidth: true
                                        selectByMouse: true
                                        text: "500"
                                        enabled: winchController.enabled
                                        validator: IntValidator { bottom: 1; top: 1000 }
                                        background: Rectangle {
                                            radius: 6
                                            border.color: "#BDBDBD"
                                            border.width: 1
                                        }
                                    }
                                }
                                
                                Item { Layout.fillHeight: true }
                                
                                Button {
                                    Layout.fillWidth: true
                                    text: "GO TO POSITION"
                                    enabled: winchController.enabled && absoluteLengthField.text.length > 0 && absoluteSpeedField.text.length > 0
                                    onClicked: {
                                        winchController.moveAbosulte(
                                            parseInt(absoluteLengthField.text),
                                            parseInt(absoluteSpeedField.text)
                                        )
                                    }
                                    
                                    background: Rectangle {
                                        radius: 6
                                        color: parent.enabled ? "#2196F3" : "#BDBDBD"
                                    }
                                    
                                    contentItem: Text {
                                        text: parent.text
                                        font.pixelSize: 14
                                        font.bold: true
                                        color: "white"
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 60
                        color: "#F5F5F5"
                        radius: 12
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Button {
                                Layout.fillWidth: true
                                text: "Retract Full"
                                enabled: winchController.enabled
                                onClicked: winchController.move_abosulte(0, 500)
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? "#2196F3" : "#BDBDBD"
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            
                            Button {
                                Layout.fillWidth: true
                                text: "STOP"
                                enabled: winchController.enabled
                                onClicked: winchController.move_increment(0, 0)
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? "#F44336" : "#BDBDBD"
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                            
                            Button {
                                Layout.fillWidth: true
                                text: "Extend 1m"
                                enabled: winchController.enabled
                                onClicked: winchController.move_increment(1000, 500)
                                
                                background: Rectangle {
                                    radius: 6
                                    color: parent.enabled ? "#2196F3" : "#BDBDBD"
                                }
                                
                                contentItem: Text {
                                    text: parent.text
                                    font.pixelSize: 14
                                    font.bold: true
                                    color: "white"
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                            }
                        }
                    }
                }
            }
            
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#FFFFFF"
                radius: 15
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 15
                    spacing: 15
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 50
                        visible: winchController.load_detection_enabled && winchController.unusual_load_detected
                        color: "#FFEBEE"
                        radius: 12
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Rectangle {
                                width: 12
                                height: 12
                                radius: 6
                                color: "#F44336"
                            }
                            
                            Text {
                                text: "UNUSUAL LOAD DETECTED"
                                font.bold: true
                                color: "#F44336"
                                font.pixelSize: 14
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        color: "#F5F5F5"
                        radius: 12
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 6
                            
                            Text {
                                text: "Cable Status"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                rowSpacing: 6
                                columnSpacing: 10
                                
                                Text { 
                                    text: "Cable Length:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: Math.round(winchController.cable_length) + " mm"
                                    font.pixelSize: 14
                                    color: "#2196F3"
                                    font.bold: true
                                }
                                
                                Text { 
                                    text: "Cable Speed:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.cable_speed.toFixed(1) + " m/s"
                                    font.pixelSize: 14
                                    color: "#2196F3"
                                    font.bold: true
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 80
                        color: "#F5F5F5"
                        radius: 12
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 6
                            
                            Text {
                                text: "Cable Extension"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            Rectangle {
                                Layout.fillWidth: true
                                height: 20
                                color: "#E0E0E0"
                                radius: 4
                                
                                Rectangle {
                                    width: Math.min(parent.width * (winchController.cable_length / 10000), parent.width)
                                    height: parent.height
                                    color: "#2196F3"
                                    radius: 4
                                }
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: Math.round(winchController.cable_length / 100) + "%"
                                    font.pixelSize: 12
                                    font.bold: true
                                    color: "#212121"
                                }
                            }
                        }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#F5F5F5"
                        radius: 12
                        
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 6
                            
                            Text {
                                text: "Motor Metrics"
                                font.pixelSize: 16
                                font.bold: true
                                color: "#212121"
                            }
                            
                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                rowSpacing: 10
                                columnSpacing: 10
                                
                                Text { 
                                    text: "Torque:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.winch_torque.toFixed(1) + " Nm"
                                    font.pixelSize: 14
                                    color: "#FF5722"
                                    font.bold: true
                                }
                                
                                Text { 
                                    text: "Temperature:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.motor_temperature + " °C"
                                    font.pixelSize: 14
                                    color: "#FF5722"
                                    font.bold: true
                                }
                                
                                Text { 
                                    text: "Voltage:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.motor_voltage + " V"
                                    font.pixelSize: 14
                                    color: "#FF5722"
                                    font.bold: true
                                }
                                
                                Text { 
                                    text: "Brake:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.motor_brake ? "Engaged" : "Released"
                                    font.pixelSize: 14
                                    color: winchController.motor_brake ? "#F44336" : "#4CAF50"
                                    font.bold: true
                                }

                                Text { 
                                    text: "Adnormal Load Detected:" 
                                    font.pixelSize: 14 
                                }
                                
                                Text { 
                                    text: winchController.unusual_load_detected ? "Adnormal" : "Normal"
                                    font.pixelSize: 14
                                    color: winchController.unusual_load_detected ? "#F44336" : "#4CAF50"
                                    font.bold: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}