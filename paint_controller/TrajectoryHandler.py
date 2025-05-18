import os.path
import json

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QThread
import time
from rclpy.node import Node
from rclpy.clock import Clock
from paint_interfaces.srv import PaintAction
from ActionConfigPython import ActionConfigPython

import os.path
import json
import time

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QThread
from rclpy.node import Node
from rclpy.clock import Clock
from paint_interfaces.srv import PaintAction
from ActionConfigPython import ActionConfigPython
from UIHeartbeatHandler import HeartbeatStatus


class ActionWorker(QObject):
    """Worker object that performs actions in a separate thread"""
    
    finished = Signal()  # Signal emitted when the work is done
    success = Signal(str)  # Signal emitted with success message
    error = Signal(str)  # Signal emitted with error message.
    
    def __init__(self, robot_controller, cmd_type, params):
        super().__init__()
        self._robot_controller = robot_controller
        self._cmd_type = cmd_type
        self._params = params
        self._abort = False
        self._paint_base_action_client = None
        self._paint_ef_action_client = None
    
    def abort(self):
        """Set abort flag to stop operations"""
        self._abort = True

    def add_time_offset(self, time_msg, seconds=0, nanoseconds=0):
        """Add a time offset to a ROS 2 time message."""
        # Convert any fractional seconds to nanoseconds
        if isinstance(seconds, float):
            extra_ns = int((seconds - int(seconds)) * 1_000_000_000)
            seconds = int(seconds)
            nanoseconds += extra_ns
        
        # Create a new time message to avoid modifying the original
        from builtin_interfaces.msg import Time
        result = Time()
        
        # Add the offset
        result.sec = time_msg.sec + seconds
        result.nanosec = time_msg.nanosec + nanoseconds
        
        # Handle nanosecond overflow
        if result.nanosec >= 1_000_000_000:
            result.sec += result.nanosec // 1_000_000_000
            result.nanosec %= 1_000_000_000
        
        return result
    
    def _check_components_online(self):
        """
        Check if components are online
        
        Returns:
            tuple: (success, message)
        """
        heartbeat_handler = self._robot_controller.heartbeat_handler
        
        # Check if components are online
        if not heartbeat_handler.get_base_online():
            return False, "Base component is offline"
        
        if not heartbeat_handler.get_ef_online():
            return False, "EF component is offline"
        
        return True, "Components are online"
    
    def _check_components_idle(self):
        """
        Check if components are in IDLE state
        
        Returns:
            tuple: (success, message)
        """
        heartbeat_handler = self._robot_controller.heartbeat_handler
        
        # First check if components are online
        online_success, online_message = self._check_components_online()
        if not online_success:
            return False, online_message
            
        # Check for error states
        base_state = heartbeat_handler.get_base_status()
        ef_state = heartbeat_handler.get_ef_status()
        
        if base_state == HeartbeatStatus.ERROR.value:
            return False, "Base component is in ERROR state"
        
        if ef_state == HeartbeatStatus.ERROR.value:
            return False, "EF component is in ERROR state"
        
        # Check for IDLE state
        if base_state != HeartbeatStatus.IDLE.value:
            base_state_str = heartbeat_handler.get_status_string("base")
            return False, f"Base component is not in IDLE state (current: {base_state_str})"
        
        if ef_state != HeartbeatStatus.IDLE.value:
            ef_state_str = heartbeat_handler.get_status_string("ef")
            return False, f"EF component is not in IDLE state (current: {ef_state_str})"
        
        return True, "Components are in IDLE state"
    
    def _are_components_on_task(self):
        """
        Check if at least one component is in ONTASK state
        
        Returns:
            bool: True if at least one component is ONTASK
        """
        heartbeat_handler = self._robot_controller.heartbeat_handler
        
        # Check if components are online first
        online_success, _ = self._check_components_online()
        if not online_success:
            return False
        
        # Get current states
        base_state = heartbeat_handler.get_base_status()
        ef_state = heartbeat_handler.get_ef_status()
        
        # Check if either component is in ONTASK state
        return (base_state == HeartbeatStatus.ONTASK.value or 
                ef_state == HeartbeatStatus.ONTASK.value)
    
    def _ensure_service_clients(self):
        """Ensure service clients are created"""
        if not self._paint_base_action_client:
            self._paint_base_action_client = self._robot_controller.create_client(PaintAction, '/base/execute_action/service')
        if not self._paint_ef_action_client:
            self._paint_ef_action_client = self._robot_controller.create_client(PaintAction, '/ef/execute_action/service')
        
        # Wait for services with timeout
        services_ready = True
        
        if not self._paint_base_action_client.wait_for_service(timeout_sec=2.0):
            error_msg = 'Base Service not available. Timeout waiting for service.'
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
            services_ready = False
        
        if not self._paint_ef_action_client.wait_for_service(timeout_sec=2.0):
            error_msg = 'EF Service not available. Timeout waiting for service.'
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
            services_ready = False
            
        return services_ready
    
    def _execute_service_calls(self, base_action, ef_action, max_wait_time=2.0):
        """Execute service calls to base and EF controllers"""
        # First check if components are in IDLE state
        idle_success, idle_message = self._check_components_idle()
        if not idle_success:
            error_msg = f"Cannot execute service calls: {idle_message}"
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
            return False, error_msg
        
        # Get current time and add offset
        clock = Clock()
        current_time = clock.now().to_msg()
        start_time = self.add_time_offset(current_time, seconds=2.0)
        
        # Create requests
        base_request = PaintAction.Request()
        base_request.start_time = start_time
        base_request.action = base_action
        
        ef_request = PaintAction.Request()
        ef_request.start_time = start_time
        ef_request.action = ef_action
        
        self._robot_controller.get_logger().info(f"Starting service calls: Base={base_action}, EF={ef_action}")
        
        # Send requests asynchronously
        base_future = self._paint_base_action_client.call_async(base_request)
        ef_future = self._paint_ef_action_client.call_async(ef_request)
        
        # Wait for responses with timeout
        wait_increment = 0.1
        elapsed = 0.0
        base_response = None
        ef_response = None
        
        while elapsed < max_wait_time:
            # Check if base request is done
            if base_future.done() and base_response is None:
                try:
                    base_response = base_future.result()
                    self._robot_controller.get_logger().info(f"Base service response received: {base_response}")
                except Exception as e:
                    error_msg = f"Base service call failed: {str(e)}"
                    self._robot_controller.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return False, error_msg
            
            # Check if ef request is done
            if ef_future.done() and ef_response is None:
                try:
                    ef_response = ef_future.result()
                    self._robot_controller.get_logger().info(f"EF service response received: {ef_response}")
                except Exception as e:
                    error_msg = f"EF service call failed: {str(e)}"
                    self._robot_controller.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return False, error_msg
            
            # Both responses received
            if base_response is not None and ef_response is not None:
                break
            
            # Check if worker was asked to abort
            if self._abort:
                self._robot_controller.get_logger().info("Operation aborted")
                return False, "Operation aborted"
            
            # Wait a bit before checking again
            time.sleep(wait_increment)
            elapsed += wait_increment
        
        # Check for timeouts
        if base_response is None:
            error_msg = "Base service call timed out"
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
            return False, error_msg
        
        if ef_response is None:
            error_msg = "EF service call timed out"
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
            return False, error_msg
        
        # Check initial responses
        if not (base_response.success and ef_response.success):
            error_messages = []
            if not base_response.success:
                error_messages.append("Base service failed")
            if not ef_response.success:
                error_messages.append("EF service failed")
            
            error_msg = " and ".join(error_messages)
            self._robot_controller.get_logger().error(f"Service failures: {error_msg}")
            return False, f"Service failures: {error_msg}"
        
        # If we got here, the initial service calls succeeded
        self._robot_controller.get_logger().info("Both service calls succeeded, waiting for completion")
        
        # Wait a short time for components to transition to ONTASK state
        time.sleep(0.1)
        
        # Now continuously check if components are on task and then back to IDLE
        on_task_detected = False
        check_interval = 0.1  # seconds
        
        while True:
            # Check if worker was asked to abort
            if self._abort:
                self._robot_controller.get_logger().info("Operation aborted while waiting for completion")
                return False, "Operation aborted while waiting for completion"
            
            # Check if components are ONTASK
            if not on_task_detected and self._are_components_on_task():
                self._robot_controller.get_logger().info("Components are now ONTASK, waiting for completion")
                on_task_detected = True
            
            # Once we've seen ONTASK state, check if back to IDLE
            if on_task_detected:
                idle_success, _ = self._check_components_idle()
                if idle_success:
                    self._robot_controller.get_logger().info("Components have returned to IDLE state, operation complete")
                    return True, "Operation completed successfully"
            
            # If we haven't detected ONTASK yet, check if components are already back to IDLE
            # This handles very quick operations
            if not on_task_detected:
                idle_success, _ = self._check_components_idle()
                if idle_success:
                    self._robot_controller.get_logger().info("Operation completed (very quick)")
                    return True, "Operation completed successfully"
            
            # Wait before checking again
            time.sleep(check_interval)
    
    def _handle_simple_action(self, action_name, duration):
        """Handle simple actions that just need a sleep to simulate operation"""
        # Check component status before executing
        idle_success, idle_message = self._check_components_idle()
        if not idle_success:
            error_msg = f"Cannot execute {action_name}: {idle_message}"
            self._robot_controller.get_logger().error(error_msg)
            return False, error_msg
            
        self._robot_controller.get_logger().info(f"Starting {action_name} simulation")
        time.sleep(duration)
        if self._abort:
            self._robot_controller.get_logger().info(f"{action_name} aborted")
            return False, f"{action_name} aborted"
        self._robot_controller.get_logger().info(f"Completed {action_name} simulation")
        return True, f"{action_name} completed successfully"
    
    def run(self):
        """Main worker method that will be executed in the thread"""
        try:
            self._robot_controller.get_logger().info(f"Worker executing {self._cmd_type}")
            
            if self._cmd_type == "winch":
                # Simple winch simulation
                success, message = self._handle_simple_action("winch movement", 3.0)
                if success:
                    self.success.emit(message)
                else:
                    self.error.emit(message)
                    
            elif self._cmd_type == "resetYaw":
                # Simple yaw reset simulation
                success, message = self._handle_simple_action("yaw reset", 0.8)
                if success:
                    self.success.emit(message)
                else:
                    self.error.emit(message)
                    
            elif self._cmd_type in ["gimbalSpray", "extendArmTo", "moveWinchTo", "winchNspray"]:
                # All these commands use service calls with different parameters
                
                # Ensure service clients exist and are ready
                if not self._ensure_service_clients():
                    return
                
                # Prepare actions based on command type
                if self._cmd_type == "gimbalSpray":
                    base_action = "none"
                    ef_action = f"gimbalSpray_{self._params[0]}_{self._params[1]}_{self._params[2]}"
                    success_msg = "Winch and spray operation completed"
                
                elif self._cmd_type == "extendArmTo":
                    base_action = "none"
                    ef_action = f"extendArmTo_{self._params[0]}"
                    success_msg = "Extension arm completed"
                
                elif self._cmd_type == "moveWinchTo":
                    self._robot_controller.teensy_controller.extendArm(self._params[2])
                    if len(self._params) == 4:
                        base_action = f"moveWinchTo_{self._params[0]}_{self._params[1]}"
                    else:
                        # Handle different parameter counts if needed
                        base_action = f"moveWinchTo_{self._params[0]}_{self._params[1]}"
                    ef_action = "none"
                    success_msg = "Sending Winch position command"
                
                elif self._cmd_type == "winchNspray":
                    base_action = f"moveWinchTo_{self._params[0]}_{self._params[1]}_{self._params[2]}_{self._params[3]}"
                    ef_action = f"spray_{self._params[0]}_{self._params[1]}_{self._params[2]}_{self._params[3]}"
                    # check if current winch cable is more than target
                    current_cable_length = self._robot_controller.winch_controller.get_cable_length()
                    target_cable_length = abs(float(self._params[0]))
                    if current_cable_length < target_cable_length:
                        # Show error message
                        error_msg = "Current winch cable length is less than target length"
                        self._robot_controller.get_logger().error(error_msg)
                        self._robot_controller.show_popup("Command Error", error_msg, "error")
                        return
                    success_msg = "Sending decent and spray command"
                
                # Execute service calls
                success, message = self._execute_service_calls(base_action, ef_action)
                
                if success:
                    if self._cmd_type == "moveWinchTo":
                        time.sleep(1)  
                        self._robot_controller.teensy_controller.extendArm(self._params[3])
                        time.sleep(2)
                    self._robot_controller.show_popup(success_msg, "Success", "success")
                else:
                    self._robot_controller.show_popup(message, "Error", "error")
            
            else:
                # Unknown command type
                error_msg = f"Unknown command type: {self._cmd_type}"
                self._robot_controller.get_logger().error(error_msg)
                self.error.emit(error_msg)
                
        except Exception as e:
            # Handle any exceptions in the thread
            error_msg = f"Error executing command: {str(e)}"
            self._robot_controller.get_logger().error(error_msg)
            self.error.emit(error_msg)
        finally:
            # Always emit finished signal
            self.finished.emit()

class TrajectoryHandler(QObject):
    """Handles trajectory management and execution"""

    trajectoryChanged = Signal()
    actionConfigChanged = Signal()
    showMessage = Signal(str, bool)  # message text, isSuccess
    executingChanged = Signal(bool)  # isExecuting
    sequenceSaved = Signal(str) 
    pageChanged = Signal(int) 

    def __init__(self, robot_controller):
        super().__init__()
        self._trajectory = []
        self._robot_controller = robot_controller
        self._currentTrajDescription = []
        self._currentTrajCmd = []
        self._isExecuting = False  # Track execution state
        self._current_page = 0
        
        # Thread and worker for actions
        self._thread = None
        self._worker = None

        self.filePath = os.path.join(os.path.dirname(__file__), 'resource', 'trajectory.json')      
        # Create action config instance
        self._action_config = ActionConfigPython(self._robot_controller)
        
        # Register action handlers
        self._action_handlers = {
            'moveWinchTo': self._handle_move_winch_to,
            'descent': self._handle_descent,
            'stopSpray': self._handle_stop_spray,
            'dNs': self._handle_descend_and_spray,
            'resetYaw': self._handle_reset_yaw,
            'extendArmTo': self._handle_extend_arm_to,
            'gimbalSpray': self._handle_gimbal_spray,
        }
        
        self.readTrajectoryFromJSONFile()

    @Property(bool, notify=executingChanged)
    def isExecuting(self):
        """Get execution state"""
        return self._isExecuting
        
    def _setExecuting(self, executing):
        """Set execution state and emit signal"""
        self._robot_controller.get_logger().info(f"Setting executing state to: {executing}")
        if self._isExecuting != executing:
            self._isExecuting = executing
            self.executingChanged.emit(executing)

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
        command = ["moveWinchTo", params[0], params[1], params[2], params[3]]
        return description, command
    
    def _handle_extend_arm_to(self, params):
        """Handle extendArmTo action"""
        description = f"Extend arm to {params[0]}mm"
        command = ["extendArmTo", params[0]]
        return description, command
        
    def _handle_descent(self, params):
        """Handle descent action"""
        description = f"Descent {params[0]}mm with speed {params[1]}mm/s"
        command = ["winch", f"-{params[0]}", params[1]]
        return description, command
        
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

    def _handle_gimbal_spray(self, params):
        """Handle gimbalSpray action"""
        descriptions = [
            f"Start gimbal spray from {params[0]} to - {params[1]} degrees"
        ]
        commands = [
            ["gimbalSpray", params[0], params[1], params[2]]
        ]
        return descriptions, commands

        
    def _handle_descend_and_spray(self, params):
        """Handle dNs (descend and spray) action"""
        descriptions = [
            f"Descent {params[0]}mm with speed {params[1]}mm/s and spray from {params[2]} to {params[3]}"
        ]
        commands = [
            ["winchNspray", f"-{params[0]}", params[1], params[2], params[3]]
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

        # Emit the sequence saved signal with the name
        self.sequenceSaved.emit(name)

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
                    self._robot_controller.get_logger().warning(f"Unknown action: {action_prefix}")
                    self._currentTrajDescription.append(f"Unknown action: {action_prefix}")
                    self._currentTrajCmd.append(["unknown", action_prefix])

    @Slot(result=list)
    def getSelectedActions(self):
        return self._currentTrajDescription
    
    def _handle_worker_success(self, message):
        """Handle success signal from worker"""
        self._robot_controller.get_logger().info(f"Worker success: {message}")
        self.showMessage.emit(message, True)
    
    def _handle_worker_error(self, message):
        """Handle error signal from worker"""
        self._robot_controller.get_logger().error(f"Worker error: {message}")
        self.showMessage.emit(message, False)
    
    def _handle_worker_finished(self):
        """Handle finished signal from worker"""
        self._robot_controller.get_logger().info("Worker finished")
        
        # Clean up thread and worker
        if self._thread:
            if self._worker:
                self._worker = None
                
            self._thread.quit()
            self._thread.wait()  # Wait for thread to finish
            self._thread = None
        
        # Reset executing state
        self._setExecuting(False)
    
    @Slot(int, result=bool)
    def startExecution(self, index):
        # Check if already executing something
        if self._isExecuting:
            self.showMessage.emit("Another action is already in progress", False)
            return False
            
        # Check if thread is still running
        if self._thread and self._thread.isRunning():
            self._robot_controller.get_logger().warning("Thread is still running, cannot start new execution")
            self.showMessage.emit("Another action thread is still running", False)
            return False
            
        # Check if valid index
        if 0 <= index < len(self._currentTrajCmd):
            cmd_type = self._currentTrajCmd[index][0]
            cmd_params = self._currentTrajCmd[index][1:]
            self._robot_controller.get_logger().info(f"Starting execution of {cmd_type} command")
            
            # Set executing state to true
            self._setExecuting(True)
            
            try:
                # Create a new thread
                self._thread = QThread()
                
                # Create the worker and move it to the thread
                self._worker = ActionWorker(self._robot_controller, cmd_type, cmd_params)
                self._worker.moveToThread(self._thread)
                
                # Connect signals and slots
                self._thread.started.connect(self._worker.run)
                self._worker.finished.connect(self._handle_worker_finished)
                self._worker.success.connect(self._handle_worker_success)
                self._worker.error.connect(self._handle_worker_error)
                
                # Start the thread
                self._thread.start()
                
                self._robot_controller.get_logger().info(f"Started thread for {cmd_type} command")
                return True
            except Exception as e:
                error_msg = f"Error starting execution thread: {str(e)}"
                self._robot_controller.get_logger().error(error_msg)
                self.showMessage.emit(error_msg, False)
                self._setExecuting(False)
                
                # Clean up in case of error
                if self._thread and self._thread.isRunning():
                    self._thread.quit()
                    self._thread.wait()
                self._thread = None
                self._worker = None
                
                return False
        else:
            self.showMessage.emit("Invalid action index", False)
            return False

    @Slot()
    def stopAll(self):
        # Set abort flag if worker exists
        if self._worker:
            self._worker.abort()
        
        # Reset executing state
        self._setExecuting(False)
        self.showMessage.emit("Emergency stop activated. All operations halted.", False)

    # Debug method to check thread status
    @Slot(result=bool)
    def isThreadRunning(self):
        """Check if the action thread is still running"""
        if self._thread:
            is_running = self._thread.isRunning()
            self._robot_controller.get_logger().info(f"Thread is running: {is_running}")
            return is_running
        return False
        
    # Directly reset execution state for debugging
    @Slot()
    def forceResetExecution(self):
        """Force reset the execution state (for debugging)"""
        self._robot_controller.get_logger().info("Forcing execution state reset")
        
        # Clean up thread if it exists
        if self._thread and self._thread.isRunning():
            if self._worker:
                self._worker.abort()
                
            self._thread.quit()
            self._thread.wait(1000)  # Wait up to 1 second
            
            # If thread is still running, terminate it (harsh)
            if self._thread.isRunning():
                self._robot_controller.get_logger().warning("Thread did not quit, terminating")
                self._thread.terminate()
                self._thread.wait()
                
        self._thread = None
        self._worker = None
        
        self._setExecuting(False)
        self.showMessage.emit("Execution state manually reset", True)
        return True

    # New method to trigger messages from Python
    @Slot(str, bool)
    def triggerMessage(self, message, isSuccess):
        """Method to trigger a message popup from Python code"""
        self.showMessage.emit(message, isSuccess)
        
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
    
    @Slot(int)
    def switch_to_page(self, page_index):
        """
        Switch to the specified page index.
        
        Args:
            page_index: 0 for Planner, 1 for Executor
        """
        if page_index in [0, 1] and page_index != self._current_page:
            self._current_page = page_index
            self.pageChanged.emit(page_index)  # Changed from page_changed to pageChanged
            page_name = "Planner" if page_index == 0 else "Executor"
            self._robot_controller.show_popup("Page Changed", f"Switched to {page_name} mode", "info", 1500)

    @Slot()
    def switchPage(self):
        """
        Direct method to toggle between pages.
        Can be called directly from QML for testing.
        """
        # Toggle between 0 and 1
        new_page = 1 if self._current_page == 0 else 0
        
        # Print debug info
        print(f"Direct page switch from {self._current_page} to {new_page}")
        
        # Set the page without using signals (for testing)
        self._current_page = new_page
        
        # Emit signal for normal operation
        self.pageChanged.emit(new_page)
        
        # Show popup
        page_name = "Planner" if new_page == 0 else "Executor"
        self._robot_controller.show_popup("Page Changed", f"Directly switched to {page_name} mode", "info", 1500)
        
        # Return the new page index for immediate use in QML if needed
        return new_page

    @Slot()
    def next_page(self):
        """Switch to the next page (cycling if needed)"""
        next_index = (self._current_page + 1) % 2
        self.switch_to_page(next_index)

    @Slot()
    def previous_page(self):
        """Switch to the previous page (cycling if needed)"""
        prev_index = (self._current_page - 1) % 2
        self.switch_to_page(prev_index)

    @Property(int)
    def current_page(self):
        """Get the current page index"""
        return self._current_page
    
    @Slot()
    def requestCurrentPage(self):
        """Request the current page state and emit the pageChanged signal."""
        current_page = self._current_page 
        self.pageChanged.emit(current_page)


