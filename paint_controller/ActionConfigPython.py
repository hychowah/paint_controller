from PySide6.QtCore import QObject, Slot, Signal, Property

class ActionConfigPython(QObject):
    """Python version of ActionConfig.qml for better cross-language consistency"""
    
    configChanged = Signal()  # Signal to notify when config changes
    
    def __init__(self):
        super().__init__()  # Initialize QObject
        
        # Centralized configuration for all action types
        self._actions = {
            "0": {
                "id": "0",
                "title": "Move Winch To",
                "prefix": "moveWinchTo",
                "fields": [
                    {"label": "Distance", "key": "input1"},
                    {"label": "Velocity", "key": "input2"}
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
            }

        }
    
    @Property(dict, notify=configChanged)
    def actions(self):
        """Expose actions as a QML property"""
        return self._actions
    
    @Slot(str, result=dict)
    def getAction(self, action_id):
        """Get action configuration by ID (QML callable)"""
        return self._actions.get(action_id)
    
    @Slot(str, result=int)
    def getFieldCount(self, action_id):
        """Get number of fields for an action (QML callable)"""
        action = self.getAction(action_id)
        return len(action["fields"]) if action else 0
    
    @Slot(str, result=dict)
    def getActionByPrefix(self, prefix):
        """Find an action by its prefix string (QML callable)"""
        for action_id, action in self._actions.items():
            if action["prefix"] == prefix:
                return action
        return None
    
    @Slot(str, result=str)
    def getActionIdByPrefix(self, prefix):
        """Find an action ID by its prefix string (QML callable)"""
        for action_id, action in self._actions.items():
            if action["prefix"] == prefix:
                return action_id
        return ""
    
    @Slot(str, result=dict)
    def createActionItem(self, action_id):
        """Create a default action item for QML"""
        action = self.getAction(action_id)
        if not action:
            return {}
            
        item = {
            "id": action_id,
            "title": action["title"]
        }
        
        # Initialize all input fields
        for i in range(1, 5):  # input1 through input4
            field_index = i - 1
            if field_index < len(action["fields"]):
                item[f"input{i}"] = "0"
            else:
                item[f"input{i}"] = "-1"
                
        return item
    
    # Keep the Python-style methods for use from Python code
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