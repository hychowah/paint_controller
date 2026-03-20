from PySide6.QtCore import QObject, Slot, Signal, Property

class ActionConfigPython(QObject):
    """Python version of ActionConfig.qml for better cross-language consistency"""
    
    configChanged = Signal()  # Signal to notify when config changes
    
    def __init__(self, winch_controller=None):
        super().__init__()
        self._winch_controller = winch_controller
        
        # Centralized configuration for all action types
        self._actions = {
            "0": {
                "id": "0",
                "title": "Move Winch To",
                "prefix": "moveWinchTo",
                "fields": [
                    {"label": "Distance", "key": "input1"},
                    {"label": "Velocity", "key": "input2"},
                    {"label": "Start Arm Position", "key": "input3"},
                    {"label": "End Arm Position", "key": "input4"}
                ]
            },
            "1": {
                "id": "1",
                "title": "Descend & Spray",
                "prefix": "dNs",
                "fields": [
                    {"label": "Target Length", "key": "input1"},
                    {"label": "Speed", "key": "input2"},
                    {"label": "Start Angle", "key": "input3"},
                    {"label": "End Angle", "key": "input4"}
                ]
            },
            "2": {
                "id": "2",
                "title": "Reset Yaw",
                "prefix": "resetYaw",
                "fields": []
            },
            "3": {
                "id": "3",
                "title": "Extend Arm To",
                "prefix": "extendArmTo",
                "fields": [
                    {"label": "Distance", "key": "input1"}
                ]
            },
            "4": {
                "id": "4",
                "title": "Pitch Spray",
                "prefix": "pitchSpray",
                "fields": [
                    {"label": "Start Angle", "key": "input1"},
                    {"label": "End Angle", "key": "input2"},
                    {"label": "Speed", "key": "input3"},
                ]
            },

        }
    
    @Property(dict, notify=configChanged)
    def actions(self):
        """Expose actions as a QML property"""
        return self._actions
    
    @Slot(str, result=dict)
    def getAction(self, action_id):
        """Get action configuration by ID (QML callable)"""
        return self.get_action(action_id)
    
    @Slot(str, result=int)
    def getFieldCount(self, action_id):
        """Get number of fields for an action (QML callable)"""
        return self.get_field_count(action_id)
    
    @Slot(str, result=dict)
    def getActionByPrefix(self, prefix):
        """Find an action by its prefix string (QML callable)"""
        return self.get_action_by_prefix(prefix)
    
    @Slot(str, result=str)
    def getActionIdByPrefix(self, prefix):
        """Find an action ID by its prefix string (QML callable)"""
        action_id = self.get_action_id_by_prefix(prefix)
        return action_id if action_id is not None else ""
    
    @Slot(str, result=dict)
    def createActionItem(self, action_id):
        """Create a default action item for QML with appropriate default values"""
        return self.create_action_item(action_id)
    
    # Python-style methods for use from Python code
    def get_action(self, action_id):
        """Get action configuration by ID (Python style)"""
        return self._actions.get(action_id)
    
    def get_field_count(self, action_id):
        """Get number of fields for an action (Python style)"""
        action = self.get_action(action_id)
        return len(action["fields"]) if action else 0
    
    def get_action_by_prefix(self, prefix):
        """Find an action by its prefix string (Python style)"""
        for action_id, action in self._actions.items():
            if action["prefix"] == prefix:
                return action
        return None
    
    def get_action_id_by_prefix(self, prefix):
        """Find an action ID by its prefix string (Python style)"""
        for action_id, action in self._actions.items():
            if action["prefix"] == prefix:
                return action_id
        return None
    
    def create_action_item(self, action_id):
        """Create a default action item with appropriate default values (Python style)"""
        action = self.get_action(action_id)
        if not action:
            return {}
            
        item = {
            "id": action_id,
            "title": action["title"]
        }
        
        # Set default values based on action type
        if action_id == "0":  # Move Winch To
            item["input1"] = str(int(self._winch_controller.get_cable_length()))  # Default distance
            item["input2"] = "350"  # Default velocity
            item["input3"] = "200"
            item["input4"] = "800"
            item["input5"] = "-1"
            item["input6"] = "-1"
        elif action_id == "1":  # Descend & Spray
            item["input1"] = str(int(self._winch_controller.get_cable_length()))  # Default target length
            item["input2"] = "550"  # Default speed
            item["input3"] = "55"  # Default start angle
            item["input4"] = "55"  # Default end angle
            item["input5"] = "-1"
            item["input6"] = "-1"
        elif action_id == "2":  # Reset Yaw
            item["input1"] = "-1"
            item["input2"] = "-1"
            item["input3"] = "-1"
            item["input4"] = "-1"
            item["input5"] = "-1"
            item["input6"] = "-1"
        elif action_id == "3":  # Extend Arm To
            item["input1"] = "350"  # Default distance
            item["input2"] = "-1"
            item["input3"] = "-1"
            item["input4"] = "-1"
            item["input5"] = "-1"
            item["input6"] = "-1"
        elif action_id == "4":  # Pitch Spray
            item["input1"] = "55"
            item["input2"] = "55"
            item["input3"] = "10"
        else:
            # For any other action types, initialize inputs
            for i in range(1, 7):  # input1 through input6
                field_index = i - 1
                if field_index < len(action["fields"]):
                    item[f"input{i}"] = "0"
                else:
                    item[f"input{i}"] = "-1"
                    
        return item