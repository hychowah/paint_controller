import os.path
import json

from PySide6.QtCore import QObject, Signal, Property, Slot
import time
from rclpy.node import Node
from paint_interfaces.srv import PaintAction
from ActionConfigPython import ActionConfigPython

class TrajectoryHandler(QObject):
    """Handles trajectory management and execution"""

    trajectoryChanged = Signal()
    actionConfigChanged = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self._trajectory = []
        self._currentTrajDescription = []
        self._currentTrajCmd = []

        self._node = node
        self.filePath = os.path.join(os.path.dirname(__file__), 'resource', 'trajectory.json')
        base_client = self._node.create_client(PaintAction, '/winch/execute_action')
        
        # Create action config instance
        self._action_config = ActionConfigPython()
        
        # Register action handlers
        self._action_handlers = {
            'moveWinchTo': self._handle_move_winch_to,
            'descent': self._handle_descent,
            'spray': self._handle_spray,
            'stopSpray': self._handle_stop_spray,
            'aNs': self._handle_ascend_and_spray,
            'dNs': self._handle_descend_and_spray,
            'resetYaw': self._handle_reset_yaw
        }
        
        self.readTrajectoryFromJSONFile()

    def readTrajectoryFromJSONFile(self):
        # check if file exists
        # if not, create it
        # if it does, read it
        if os.path.exists(self.filePath):
            with open(self.filePath, 'r') as file:
                self._trajectory = json.load(file)
        else:
            self._trajectory = []
            self._saveTrajectory()

        self.trajectoryChanged.emit()

    def _saveTrajectory(self):
        """Internal method to save data"""
        with open(self.filePath, 'w') as file:
            json.dump(self._trajectory, file, indent=2)

    # Action handler methods
    def _handle_move_winch_to(self, params):
        """Handle moveWinchTo action"""
        description = f"Move winch to {params[0]}mm with speed {params[1]}mm/s"
        command = ["moveWinchTo", params[0], params[1]]
        return description, command
        
    def _handle_descent(self, params):
        """Handle descent action"""
        description = f"Descent {params[0]}mm with speed {params[1]}mm/s"
        command = ["winch", f"-{params[0]}", params[1]]
        return description, command
        
    def _handle_spray(self, params):
        """Handle spray action"""
        descriptions = [
            f"Move gun to {params[0]}mm",
            f"Spray with speed {params[1]}mm/s"
        ]
        commands = [
            ["moveGun", params[0]],
            ["spray", params[1]]
        ]
        return descriptions, commands
        
    def _handle_stop_spray(self, params):
        """Handle stopSpray action"""
        descriptions = [
            "Stop spraying",
            "Retract gun"
        ]
        commands = [
            ["moveGun", "0"],
            ["spray", "0"]
        ]
        return descriptions, commands
        
    def _handle_ascend_and_spray(self, params):
        """Handle aNs (ascend and spray) action"""
        descriptions = [
            f"Move gun to {params[2]}mm",
            f"Ascent {params[0]}mm with speed {params[1]}mm/s and spray with speed {params[3]}mm/s"
        ]
        commands = [
            ["moveGun", params[2]],
            ["winchNspray", params[0], params[1], params[3]]
        ]
        return descriptions, commands
        
    def _handle_descend_and_spray(self, params):
        """Handle dNs (descend and spray) action"""
        descriptions = [
            f"Move gun to {params[2]}mm",
            f"Descent {params[0]}mm with speed {params[1]}mm/s and spray with speed {params[3]}mm/s"
        ]
        commands = [
            ["moveGun", params[2]],
            ["winchNspray", f"-{params[0]}", params[1], params[3]]
        ]
        return descriptions, commands
        
    def _handle_reset_yaw(self, params):
        """Handle resetYaw action"""
        description = "Reset yaw"
        command = ["resetYaw"]
        return description, command

    @Property(list, notify=trajectoryChanged)
    def trajectory(self):
        return self._trajectory

    @Slot(int)
    def deleteTrajectory(self, index):
        if 0 <= index < len(self._trajectory):
            del self._trajectory[index]
            self._saveTrajectory()
            self.trajectoryChanged.emit()

    @Slot(str, str)
    def saveTrajectory(self, name, sequence):
        added = True
        for item in self._trajectory:
            if item["name"] == name:
                item["sequence"] = sequence
                added = False
                break
        if added:
            self._trajectory.append({"name": name, "sequence": sequence})

        self._saveTrajectory()
        self.trajectoryChanged.emit()

    @Slot(int)
    def selectTrajectory(self, index):
        if 0 <= index < len(self._trajectory):
            # Reset current trajectory
            self._currentTrajCmd = []
            self._currentTrajDescription = []

            trajStr = self._trajectory[index]["sequence"]
            actions = trajStr.split(',')
            
            for action in actions:
                parts = action.split('_')
                action_prefix = parts[0]
                params = parts[1:] if len(parts) > 1 else []
                
                # Use the action handler if available
                if action_prefix in self._action_handlers:
                    handler = self._action_handlers[action_prefix]
                    result = handler(params)
                    
                    # Handle single description/command pair
                    if isinstance(result[0], str):
                        self._currentTrajDescription.append(result[0])
                        self._currentTrajCmd.append(result[1])
                    # Handle multiple description/command pairs
                    else:
                        descriptions, commands = result
                        for i in range(len(descriptions)):
                            self._currentTrajDescription.append(descriptions[i])
                            self._currentTrajCmd.append(commands[i])
                else:
                    # Handle unknown action types
                    self._node.get_logger().warning(f"Unknown action: {action_prefix}")
                    self._currentTrajDescription.append(f"Unknown action: {action_prefix}")
                    self._currentTrajCmd.append(["unknown", action_prefix])

    @Slot(result=list)
    def getSelectedActions(self):
        return self._currentTrajDescription
    
    @Slot(int)
    def startExecution(self, index):
        if 0 <= index < len(self._currentTrajCmd):
            cmd_type = self._currentTrajCmd[index][0]
            self._node.get_logger().info(f"Executing {cmd_type} command")
            
            if cmd_type == "winch":
                print("Winch command")
                time.sleep(10)
            elif cmd_type == "moveGun":
                pass # TODO
            elif cmd_type == "spray":
                pass # TODO
            elif cmd_type == "winchNspray":
                pass # TODO
            elif cmd_type == "resetYaw":
                pass # TODO
            elif cmd_type == "moveWinchTo":
                print("Move winch to command")

    @Slot()
    def stopAll(self):
        pass # TODO
        
    # Expose action config to QML
    @Property('QVariant', notify=actionConfigChanged)
    def actionConfig(self):
        """Expose the entire action config to QML"""
        return self._action_config.actions
        
    @Slot(str, result='QVariant')
    def getAction(self, action_id):
        """Get action configuration by ID for QML"""
        return self._action_config.get_action(action_id)
        
    @Slot(str, result=int)
    def getFieldCount(self, action_id):
        """Get field count for an action for QML"""
        return self._action_config.get_field_count(action_id)
        
    @Slot(str, result=str)
    def getActionIdByPrefix(self, prefix):
        """Find action ID by prefix for QML"""
        return self._action_config.get_action_id_by_prefix(prefix) or ""
        
    @Slot(str, result='QVariant')
    def createActionItem(self, action_id):
        """Create a new action item with default values"""
        action = self._action_config.get_action(action_id)
        if not action:
            return {}
            
        item = {
            "id": action_id,
            "title": action["title"]
        }
        
        # Initialize all input fields
        for i in range(1, 5):  # input1 through input4
            if i <= len(action["fields"]):
                item[f"input{i}"] = "0"
            else:
                item[f"input{i}"] = "-1"
                
        return item