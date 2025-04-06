import QtQuick 2.15

QtObject {
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
            title: "Descend",
            prefix: "descent",
            fields: [
                { label: "Angle", key: "input1" },
                { label: "Rate", key: "input2" }
            ]
        },
        "2": { 
            id: "2",
            title: "Spray",
            prefix: "spray",
            fields: [
                { label: "Time", key: "input1" },
                { label: "Power", key: "input2" }
            ]
        },
        "3": {
            id: "3",
            title: "Stop Spray",
            prefix: "stopSpray",
            fields: []
        },
        "4": { 
            id: "4",
            title: "Ascend & Spray",
            prefix: "aNs",
            fields: [
                { label: "Wait Time", key: "input1" },
                { label: "Wait Speed", key: "input2" },
                { label: "Step Length", key: "input3" },
                { label: "Step Speed", key: "input4" }
            ]
        },
        "5": { 
            id: "5",
            title: "Descend & Spray",
            prefix: "dNs",
            fields: [
                { label: "Delay", key: "input1" },
                { label: "Accel", key: "input2" },
                { label: "Span", key: "input3" },
                { label: "Force", key: "input4" }
            ]
        },
        "6": {
            id: "6",
            title: "Reset Yaw",
            prefix: "resetYaw",
            fields: []
        }
    })

    // Helper function to get an action by ID
    function getAction(id) {
        return actions[id] || null;
    }

    // Helper function to get field count for an action
    function getFieldCount(id) {
        const action = getAction(id);
        return action ? action.fields.length : 0;
    }

    // Helper function to create default values for a new action
    function createActionItem(id) {
        const action = getAction(id);
        if (!action) return null;
        
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