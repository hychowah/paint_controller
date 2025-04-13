import os.path
import json

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QThread
import time
from rclpy.node import Node
from rclpy.clock import Clock
from paint_interfaces.srv import PaintAction
from ActionConfigPython import ActionConfigPython

class ActionWorker(QObject):
    """Worker object that performs actions in a separate thread"""
    
    finished = Signal()  # Signal emitted when the work is done
    success = Signal(str)  # Signal emitted with success message
    error = Signal(str)  # Signal emitted with error message
    
    def __init__(self, node, cmd_type, params):
        super().__init__()
        self._node = node
        self._cmd_type = cmd_type
        self._params = params
        self._abort = False
        
    def abort(self):
        """Set abort flag to stop operations"""
        self._abort = True

    def add_time_offset(self, time_msg, seconds=0, nanoseconds=0):
        """
        Add a time offset to a ROS 2 time message.
        
        Args:
            time_msg: A ROS 2 Time message (builtin_interfaces.msg.Time)
            seconds: Number of seconds to add (int or float)
            nanoseconds: Number of nanoseconds to add (int)
            
        Returns:
            A new Time message with the offset added
        """
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
    
    def run(self):
        """Main worker method that will be executed in the thread"""
        try:
            # In a real implementation, you would call actual hardware functions here
            # This is just a simulation with time.sleep
            self._node.get_logger().info(f"Worker executing {self._cmd_type}")
            
            if self._cmd_type == "winch":
                # Simulate winch movement (takes longer)
                self._node.get_logger().info("Starting winch movement simulation")
                time.sleep(3)  # This sleep won't block the UI anymore
                if self._abort:
                    self._node.get_logger().info("Winch movement aborted")
                    return
                self._node.get_logger().info("Completed winch movement simulation")
                self.success.emit("Winch movement completed successfully!")
            elif self._cmd_type == "moveGun":
                # Simulate gun movement
                self._node.get_logger().info("Starting gun movement simulation")
                time.sleep(1.5)
                if self._abort:
                    return
                self._node.get_logger().info("Completed gun movement simulation")
                self.success.emit("Gun moved to target position")
            elif self._cmd_type == "extendArmTo":
                self._node.get_logger().info("Starting arm extension")
                clock = Clock()
                current_time = clock.now().to_msg()  # This creates a Time message

                start_time_offset = 2.0  # 2 seconds offset for the start time
                start_time = self.add_time_offset(current_time, seconds=start_time_offset)

                if not hasattr(self, '_paint_base_action_client'):
                    self._paint_base_action_client = self._node.create_client(PaintAction, '/base/execute_action/service')
                if not hasattr(self, '_paint_ef_action_client'):
                    self._paint_ef_action_client = self._node.create_client(PaintAction, '/ef/execute_action/service')

                if not self._paint_base_action_client.wait_for_service(timeout_sec=1.0):
                    error_msg = 'Base Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                if not self._paint_ef_action_client.wait_for_service(timeout_sec=1.0):
                    error_msg = 'EF Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                # Create and send the Base request
                base_request = PaintAction.Request()
                base_request.start_time = start_time
                # winch action in format {action}_{distance}_{speed}
                base_request.action = f"none"
                
                # Create and send the EF request (with "none" action)
                ef_request = PaintAction.Request()
                ef_request.start_time = start_time
                ef_request.action = f"extendArmTo_{self._params[0]}" 
                
                self._node.get_logger().info("Starting moveWinchTo service calls")
                
                # Send the requests asynchronously
                base_future = self._paint_base_action_client.call_async(base_request)
                ef_future = self._paint_ef_action_client.call_async(ef_request)
                
                # Wait for responses with timeout (using a combination of sleep and check to allow abortion)
                max_wait_time = 2.0  # 2 seconds max wait for service responses
                wait_increment = 0.1  # Check every 0.1 seconds
                elapsed = 0.0
                
                base_response = None
                ef_response = None
                
                while elapsed < max_wait_time:
                    # Check if base request is done
                    if base_future.done() and base_response is None:
                        try:
                            base_response = base_future.result()
                            self._node.get_logger().info(f"Base service response received: {base_response}")
                        except Exception as e:
                            error_msg = f"Base service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Check if ef request is done
                    if ef_future.done() and ef_response is None:
                        try:
                            ef_response = ef_future.result()
                            self._node.get_logger().info(f"EF service response received: {ef_response}")
                        except Exception as e:
                            error_msg = f"EF service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Both responses received
                    if base_response is not None and ef_response is not None:
                        break
                    
                    # Check if worker was asked to abort
                    if self._abort:
                        self._node.get_logger().info("Winch positioning aborted")
                        return
                    
                    # Wait a bit before checking again
                    time.sleep(wait_increment)
                    elapsed += wait_increment
                
                # Check for timeouts
                if base_response is None:
                    self._node.get_logger().error("Base service call timed out")
                    self.error.emit("Base service call timed out")
                    return
                
                if ef_response is None:
                    self._node.get_logger().error("EF service call timed out")
                    self.error.emit("EF service call timed out")
                    return
                
                # Check responses
                if base_response.success and ef_response.success:
                    self._node.get_logger().info("Both service calls succeeded")
                    self.success.emit("Winch positioned successfully")
                else:
                    error_messages = []
                    if not base_response.success:
                        error_messages.append("Base service failed")
                    if not ef_response.success:
                        error_messages.append("EF service failed")
                    
                    error_msg = " and ".join(error_messages)
                    self._node.get_logger().error(f"Service failures: {error_msg}")
                    self.error.emit(f"Service failures: {error_msg}")
                if self._abort:
                    return
                self._node.get_logger().info("Completed extending arm ")
                self.success.emit("Extention arm completed")
            elif self._cmd_type == "winchNspray":
                # Simulate positioning - would be a hardware call in real implementation
                clock = Clock()
                current_time = clock.now().to_msg()  # This creates a Time message

                start_time_offset = 2.0  # 2 seconds offset for the start time
                start_time = self.add_time_offset(current_time, seconds=start_time_offset)
                
                # Create service client if it doesn't exist
                if not hasattr(self, '_paint_base_action_client'):
                    self._paint_base_action_client = self._node.create_client(PaintAction, '/base/execute_action/service')
                if not hasattr(self, '_paint_ef_action_client'):
                    self._paint_ef_action_client = self._node.create_client(PaintAction, '/ef/execute_action/service')
                
                # Wait for services with timeout
                if not self._paint_base_action_client.wait_for_service(timeout_sec=2.0):
                    error_msg = 'Base Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                if not self._paint_ef_action_client.wait_for_service(timeout_sec=2.0):
                    error_msg = 'EF Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                # Create and send the Base request
                base_request = PaintAction.Request()
                base_request.start_time = start_time
                # winch action in format {action}_{distance}_{speed}
                base_request.action = f"moveWinchTo_{self._params[0]}_{self._params[1]}_{self._params[2]}_{self._params[3]}"
                
                # Create and send the EF request (with "none" action)
                ef_request = PaintAction.Request()
                ef_request.start_time = start_time
                ef_request.action = f"spray_{self._params[0]}_{self._params[1]}_{self._params[2]}_{self._params[3]}" 
                
                self._node.get_logger().info("Starting moveWinchTo service calls")
                
                # Send the requests asynchronously
                base_future = self._paint_base_action_client.call_async(base_request)
                ef_future = self._paint_ef_action_client.call_async(ef_request)
                
                # Wait for responses with timeout (using a combination of sleep and check to allow abortion)
                max_wait_time = 2.0  # 2 seconds max wait for service responses
                wait_increment = 0.1  # Check every 0.1 seconds
                elapsed = 0.0
                
                base_response = None
                ef_response = None
                
                while elapsed < max_wait_time:
                    # Check if base request is done
                    if base_future.done() and base_response is None:
                        try:
                            base_response = base_future.result()
                            self._node.get_logger().info(f"Base service response received: {base_response}")
                        except Exception as e:
                            error_msg = f"Base service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Check if ef request is done
                    if ef_future.done() and ef_response is None:
                        try:
                            ef_response = ef_future.result()
                            self._node.get_logger().info(f"EF service response received: {ef_response}")
                        except Exception as e:
                            error_msg = f"EF service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Both responses received
                    if base_response is not None and ef_response is not None:
                        break
                    
                    # Check if worker was asked to abort
                    if self._abort:
                        self._node.get_logger().info("Winch positioning aborted")
                        return
                    
                    # Wait a bit before checking again
                    time.sleep(wait_increment)
                    elapsed += wait_increment
                
                # Check for timeouts
                if base_response is None:
                    self._node.get_logger().error("Base service call timed out")
                    self.error.emit("Base service call timed out")
                    return
                
                if ef_response is None:
                    self._node.get_logger().error("EF service call timed out")
                    self.error.emit("EF service call timed out")
                    return
                
                # Check responses
                if base_response.success and ef_response.success:
                    self._node.get_logger().info("Both service calls succeeded")
                    self.success.emit("Winch positioned successfully")
                else:
                    error_messages = []
                    if not base_response.success:
                        error_messages.append("Base service failed")
                    if not ef_response.success:
                        error_messages.append("EF service failed")
                    
                    error_msg = " and ".join(error_messages)
                    self._node.get_logger().error(f"Service failures: {error_msg}")
                    self.error.emit(f"Service failures: {error_msg}")
                if self._abort:
                    return
                self._node.get_logger().info("Completed winch and spray simulation")
                self.success.emit("Winch and spray operation completed")
            elif self._cmd_type == "resetYaw":
                # Simulate yaw reset
                self._node.get_logger().info("Starting yaw reset simulation")
                time.sleep(0.8)
                if self._abort:
                    return
                self._node.get_logger().info("Completed yaw reset simulation")
                self.success.emit("Yaw reset successful")

            elif self._cmd_type == "moveWinchTo":
                # Simulate positioning - would be a hardware call in real implementation
                clock = Clock()
                current_time = clock.now().to_msg()  # This creates a Time message
                start_time = self.add_time_offset(current_time, seconds=2)
                
                # Create service client if it doesn't exist
                if not hasattr(self, '_paint_base_action_client'):
                    self._paint_base_action_client = self._node.create_client(PaintAction, '/base/execute_action/service')
                if not hasattr(self, '_paint_ef_action_client'):
                    self._paint_ef_action_client = self._node.create_client(PaintAction, '/ef/execute_action/service')
                
                # Wait for services with timeout
                if not self._paint_base_action_client.wait_for_service(timeout_sec=2.0):
                    error_msg = 'Base Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                if not self._paint_ef_action_client.wait_for_service(timeout_sec=2.0):
                    error_msg = 'EF Service not available. Timeout waiting for service.'
                    self._node.get_logger().error(error_msg)
                    self.error.emit(error_msg)
                    return
                
                # Create and send the Base request
                base_request = PaintAction.Request()
                base_request.start_time = start_time
                base_request.action = self._cmd_type
                
                # Create and send the EF request (with "none" action)
                ef_request = PaintAction.Request()
                ef_request.start_time = start_time
                ef_request.action = "none"  # Special action to keep EF in ONTASK state
                
                self._node.get_logger().info("Starting moveWinchTo service calls")
                
                # Send the requests asynchronously
                base_future = self._paint_base_action_client.call_async(base_request)
                ef_future = self._paint_ef_action_client.call_async(ef_request)
                
                # Wait for responses with timeout (using a combination of sleep and check to allow abortion)
                max_wait_time = 2.0  # 2 seconds max wait for service responses
                wait_increment = 0.1  # Check every 0.1 seconds
                elapsed = 0.0
                
                base_response = None
                ef_response = None
                
                while elapsed < max_wait_time:
                    # Check if base request is done
                    if base_future.done() and base_response is None:
                        try:
                            base_response = base_future.result()
                            self._node.get_logger().info(f"Base service response received: {base_response}")
                        except Exception as e:
                            error_msg = f"Base service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Check if ef request is done
                    if ef_future.done() and ef_response is None:
                        try:
                            ef_response = ef_future.result()
                            self._node.get_logger().info(f"EF service response received: {ef_response}")
                        except Exception as e:
                            error_msg = f"EF service call failed: {str(e)}"
                            self._node.get_logger().error(error_msg)
                            self.error.emit(error_msg)
                            return
                    
                    # Both responses received
                    if base_response is not None and ef_response is not None:
                        break
                    
                    # Check if worker was asked to abort
                    if self._abort:
                        self._node.get_logger().info("Winch positioning aborted")
                        return
                    
                    # Wait a bit before checking again
                    time.sleep(wait_increment)
                    elapsed += wait_increment
                
                # Check for timeouts
                if base_response is None:
                    self._node.get_logger().error("Base service call timed out")
                    self.error.emit("Base service call timed out")
                    return
                
                if ef_response is None:
                    self._node.get_logger().error("EF service call timed out")
                    self.error.emit("EF service call timed out")
                    return
                
                # Check responses
                if base_response.success and ef_response.success:
                    self._node.get_logger().info("Both service calls succeeded")
                    self.success.emit("Winch positioned successfully")
                else:
                    error_messages = []
                    if not base_response.success:
                        error_messages.append("Base service failed")
                    if not ef_response.success:
                        error_messages.append("EF service failed")
                    
                    error_msg = " and ".join(error_messages)
                    self._node.get_logger().error(f"Service failures: {error_msg}")
                    self.error.emit(f"Service failures: {error_msg}")
            else:
                # Unknown command type (shouldn't reach here)
                self._node.get_logger().error(f"Unknown command type: {self._cmd_type}")
                self.error.emit(f"Unknown command type: {self._cmd_type}")
                
        except Exception as e:
            # Handle any exceptions in the thread
            error_msg = f"Error executing command: {str(e)}"
            self._node.get_logger().error(error_msg)
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

    def __init__(self, node: Node):
        super().__init__()
        self._trajectory = []
        self._currentTrajDescription = []
        self._currentTrajCmd = []
        self._isExecuting = False  # Track execution state
        
        # Thread and worker for actions
        self._thread = None
        self._worker = None

        self._node = node
        self.filePath = os.path.join(os.path.dirname(__file__), 'resource', 'trajectory.json')      
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
            'resetYaw': self._handle_reset_yaw,
            'extendArmTo': self._handle_extend_arm_to,
        }
        
        self.readTrajectoryFromJSONFile()

    @Property(bool, notify=executingChanged)
    def isExecuting(self):
        """Get execution state"""
        return self._isExecuting
        
    def _setExecuting(self, executing):
        """Set execution state and emit signal"""
        self._node.get_logger().info(f"Setting executing state to: {executing}")
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
        command = ["moveWinchTo", params[0], params[1]]
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
            f"Ascent {params[0]}mm with speed {params[1]}mm/s and spray with speed {params[3]}mm/s"
        ]
        commands = [
            ["winchNspray", params[0], params[1], params[3]]
        ]
        return descriptions, commands
        
    def _handle_descend_and_spray(self, params):
        """Handle dNs (descend and spray) action"""
        descriptions = [
            f"Descent {params[0]}mm with speed {params[1]}mm/s and spray with speed {params[3]}mm/s"
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
    
    def _handle_worker_success(self, message):
        """Handle success signal from worker"""
        self._node.get_logger().info(f"Worker success: {message}")
        self.showMessage.emit(message, True)
    
    def _handle_worker_error(self, message):
        """Handle error signal from worker"""
        self._node.get_logger().error(f"Worker error: {message}")
        self.showMessage.emit(message, False)
    
    def _handle_worker_finished(self):
        """Handle finished signal from worker"""
        self._node.get_logger().info("Worker finished")
        
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
            self._node.get_logger().warning("Thread is still running, cannot start new execution")
            self.showMessage.emit("Another action thread is still running", False)
            return False
            
        # Check if valid index
        if 0 <= index < len(self._currentTrajCmd):
            cmd_type = self._currentTrajCmd[index][0]
            cmd_params = self._currentTrajCmd[index][1:]
            self._node.get_logger().info(f"Starting execution of {cmd_type} command")
            
            # Set executing state to true
            self._setExecuting(True)
            
            try:
                # Create a new thread
                self._thread = QThread()
                
                # Create the worker and move it to the thread
                self._worker = ActionWorker(self._node, cmd_type, cmd_params)
                self._worker.moveToThread(self._thread)
                
                # Connect signals and slots
                self._thread.started.connect(self._worker.run)
                self._worker.finished.connect(self._handle_worker_finished)
                self._worker.success.connect(self._handle_worker_success)
                self._worker.error.connect(self._handle_worker_error)
                
                # Start the thread
                self._thread.start()
                
                self._node.get_logger().info(f"Started thread for {cmd_type} command")
                return True
            except Exception as e:
                error_msg = f"Error starting execution thread: {str(e)}"
                self._node.get_logger().error(error_msg)
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
            self._node.get_logger().info(f"Thread is running: {is_running}")
            return is_running
        return False
        
    # Directly reset execution state for debugging
    @Slot()
    def forceResetExecution(self):
        """Force reset the execution state (for debugging)"""
        self._node.get_logger().info("Forcing execution state reset")
        
        # Clean up thread if it exists
        if self._thread and self._thread.isRunning():
            if self._worker:
                self._worker.abort()
                
            self._thread.quit()
            self._thread.wait(1000)  # Wait up to 1 second
            
            # If thread is still running, terminate it (harsh)
            if self._thread.isRunning():
                self._node.get_logger().warning("Thread did not quit, terminating")
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