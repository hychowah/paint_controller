// ActionConfig.qml
import QtQuick 2.15

QtObject {
    id: actionConfig
    
    // Centralized configuration for all action types
    readonly property var actions: ({
        "0": { 
            id: "0",
            title: "Move Winch To",
            prefix: "moveWinchTo",
            fields: [
                { label: "Distance", key: "input1" },
                { label: "Velocity", key: "input2" }
            ]
        },
        "1": { 
            id: "1",
            title: "Extend Arm To",
            prefix: "extendArmTo",
            fields: [
                { label: "Extension", key: "input1" }
            ]
        },
        "2": { 
            id: "2",
            title: "Ascend & Spray",
            prefix: "ascendNSpray",
            fields: [
                { label: "Wait Time", key: "input1" },
                { label: "Wait Speed", key: "input2" },
                { label: "Step Length", key: "input3" },
                { label: "Step Speed", key: "input4" }
            ]
        },
        "3": { 
            id: "3",
            title: "Descend & Spray",
            prefix: "descendNSpray",
            fields: [
                { label: "Delay", key: "input1" },
                { label: "Accel", key: "input2" },
                { label: "Span", key: "input3" },
                { label: "Force", key: "input4" }
            ]
        },
        "4": {
            id: "4",
            title: "Reset Yaw",
            prefix: "resetYaw",
            fields: []
        }
    })

    // Helper function to get an action by ID
    function getAction(id) {
        console.log("Getting action for ID:", id);
        var action = actions[id];
        return action || null;
    }

    // Helper function to get field count for an action
    function getFieldCount(id) {
        const action = getAction(id);
        return action ? action.fields.length : 0;
    }

    // Helper function to create default values for a new action
    function createActionItem(id) {
        const action = getAction(id);
        if (!action) {
            console.log("No action found for ID:", id);
            return null;
        }
        
        const item = {
            id: id,
            title: action.title
        };
        
        // Initialize all input fields
        for (let i = 1; i <= 4; i++) {
            const fieldIndex = i - 1;
            const hasField = action.fields.length > fieldIndex;
            
            if (hasField) {
                item["input" + i] = "0";
            } else {
                item["input" + i] = "-1";
            }
        }
        
        return item;
    }
}