#!/usr/bin/env python3
"""
ROS Bag Recorder Service for remote data recording via SSH.

Features:
- Records all ROS2 topics using 'ros2 bag record -a' on remote End Effector device
- Saves to ~/Documents/OperationData/<timestamp>/ on the remote device
- Compresses bag folder with tar after stopping (blocks new recordings until done)
- Graceful cleanup on application exit
"""

import os
import json
import threading
from datetime import datetime
from typing import Optional, Callable

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer

# Import SSHLauncher from ssh controller
from paint_controller.controllers.ssh import SSHLauncher


class RosBagRecorder(QObject):
    """
    Remote ROS bag recording service using SSH.
    
    Exposes properties and methods for QML integration to start/stop
    ROS bag recording on the remote End Effector device with automatic
    compression after stopping.
    """
    
    # Signals for property changes
    is_bag_recording_changed = Signal()
    bag_recording_duration_changed = Signal()
    is_compressing_changed = Signal()
    bag_status_message_changed = Signal()
    
    # Remote device configuration
    DEVICE_NAME = "END_EFFECTOR"
    REMOTE_OUTPUT_DIR = "~/Documents/OperationData"
    
    def __init__(self, robot_controller, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._robot_controller = robot_controller
        
        # Recording state
        self._is_bag_recording = False
        self._is_compressing = False
        self._bag_recording_duration_seconds = 0
        self._bag_status_message = ""
        self._recording_start_time: Optional[datetime] = None
        self._remote_pid: Optional[int] = None
        self._current_bag_folder: Optional[str] = None
        
        # SSH configuration
        self._ssh_launcher: Optional[SSHLauncher] = None
        self._load_ssh_config()
        
        # Duration update timer (1 second interval)
        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._on_duration_tick)
        self._duration_timer.setInterval(1000)
    
    def _load_ssh_config(self) -> None:
        """Load SSH configuration for the End Effector device."""
        try:
            config_dir = os.path.abspath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "config"
            ))
            ssh_config_path = os.path.join(config_dir, "ssh_config.json")
            
            with open(ssh_config_path, 'r') as f:
                ssh_config = json.load(f)
            
            device_config = ssh_config.get(self.DEVICE_NAME)
            if device_config:
                self._ssh_launcher = SSHLauncher(
                    hostname=device_config.get("hostname"),
                    username=device_config.get("username"),
                    password=device_config.get("password"),
                    key_path=device_config.get("key_path"),
                    port=device_config.get("port", 22)
                )
                print(f"[RosBagRecorder] SSH config loaded for {self.DEVICE_NAME}")
            else:
                print(f"[RosBagRecorder] WARNING: No SSH config found for {self.DEVICE_NAME}")
                self._bag_status_message = "SSH config not found"
                self.bag_status_message_changed.emit()
        except Exception as e:
            print(f"[RosBagRecorder] Error loading SSH config: {e}")
            self._bag_status_message = f"Config error: {e}"
            self.bag_status_message_changed.emit()
    
    def _generate_folder_name(self) -> str:
        """Generate folder name with YYYYMMDD_HHMMSS format."""
        return datetime.now().strftime("rosbag_%Y%m%d_%H%M%S")
    
    def _run_ssh_command(self, command: str, callback: Optional[Callable[[str, str], None]] = None) -> None:
        """Run a command on the remote device via SSH."""
        if not self._ssh_launcher:
            print("[RosBagRecorder] SSH launcher not available")
            if callback:
                callback("", "SSH not configured")
            return
        
        self._ssh_launcher.run_script(command, callback)
    
    def _on_duration_tick(self) -> None:
        """Called every second to update recording duration."""
        if not self._is_bag_recording:
            return
        
        if self._recording_start_time:
            delta = datetime.now() - self._recording_start_time
            self._bag_recording_duration_seconds = int(delta.total_seconds())
            self.bag_recording_duration_changed.emit()
    
    def _start_recording_internal(self) -> None:
        """Internal method to start recording on remote device."""
        self._current_bag_folder = self._generate_folder_name()
        
        # Build command to:
        # 1. Source ROS2 environment
        # 2. Create output directory
        # 3. Start ros2 bag record in background with nohup
        # 4. Echo the PID for tracking
        # Note: We source ROS2 setup and use setsid to create new session for clean signal handling
        start_command = (
            f"bash -c '"
            f"source /opt/ros/humble/setup.bash 2>/dev/null || source /opt/ros/jazzy/setup.bash 2>/dev/null; "
            f"source ~/ros2_ws/install/setup.bash 2>/dev/null; "
            f"export ROS_DOMAIN_ID=2; "
            f"mkdir -p {self.REMOTE_OUTPUT_DIR}/{self._current_bag_folder} && "
            f"cd {self.REMOTE_OUTPUT_DIR}/{self._current_bag_folder} && "
            f"nohup ros2 bag record -a -o bag_data > ros2bag.log 2>&1 & echo $!"
            f"'"
        )
        
        def on_start_complete(stdout: str, stderr: str):
            if stderr and "error" in stderr.lower():
                print(f"[RosBagRecorder] Error starting recording: {stderr}")
                self._bag_status_message = f"Start failed: {stderr[:50]}"
                self.bag_status_message_changed.emit()
                self._is_bag_recording = False
                self.is_bag_recording_changed.emit()
                
                # Show error popup
                if self._robot_controller:
                    self._robot_controller.show_popup(
                        "ROS Bag Recording",
                        f"Failed to start recording: {stderr[:100]}",
                        "error",
                        3000
                    )
                return
            
            # Parse PID from stdout
            try:
                pid_str = stdout.strip()
                if pid_str:
                    self._remote_pid = int(pid_str)
                    print(f"[RosBagRecorder] Recording started with PID: {self._remote_pid}")
                else:
                    print("[RosBagRecorder] Recording started (no PID captured)")
                    self._remote_pid = None
            except ValueError:
                print(f"[RosBagRecorder] Could not parse PID from: {stdout}")
                self._remote_pid = None
            
            # Update state
            self._recording_start_time = datetime.now()
            self._bag_recording_duration_seconds = 0
            self._bag_status_message = ""
            self.bag_status_message_changed.emit()
            self.bag_recording_duration_changed.emit()
            
            # Start duration timer
            self._duration_timer.start()
            
            # Show success popup
            if self._robot_controller:
                self._robot_controller.show_popup(
                    "ROS Bag Recording",
                    f"Recording started: {self._current_bag_folder}",
                    "info",
                    2000
                )
        
        self._run_ssh_command(start_command, on_start_complete)
    
    def _stop_recording_internal(self, compress: bool = True) -> None:
        """Internal method to stop recording on remote device."""
        self._duration_timer.stop()
        
        if not self._is_bag_recording:
            return
        
        # Build stop command - use SIGINT (2) for graceful shutdown of ros2 bag
        # SIGINT allows ros2 bag to flush and close files properly (like Ctrl+C)
        # Then wait a moment for the process to finish writing
        if self._remote_pid:
            stop_command = (
                f"bash -c '"
                f"kill -2 {self._remote_pid} 2>/dev/null || pkill -2 -f \"ros2 bag record\" 2>/dev/null; "
                f"sleep 3; "  # Wait for ros2 bag to finish writing
                f"echo done"
                f"'"
            )
        else:
            stop_command = (
                "bash -c '"
                "pkill -2 -f \"ros2 bag record\" 2>/dev/null; "
                "sleep 3; "  # Wait for ros2 bag to finish writing
                "echo done"
                "'"
            )
        
        def on_stop_complete(stdout: str, stderr: str):
            print(f"[RosBagRecorder] Recording stopped")
            self._remote_pid = None
            
            # Update state
            self._is_bag_recording = False
            self.is_bag_recording_changed.emit()
            
            if compress and self._current_bag_folder:
                # Start compression
                self._compress_bag_folder()
            else:
                self._bag_status_message = ""
                self.bag_status_message_changed.emit()
                self._current_bag_folder = None
        
        self._run_ssh_command(stop_command, on_stop_complete)
    
    def _compress_bag_folder(self) -> None:
        """Compress the bag folder using tar on remote device."""
        if not self._current_bag_folder:
            print("[RosBagRecorder] No bag folder to compress")
            return
        
        self._is_compressing = True
        self.is_compressing_changed.emit()
        self._bag_status_message = "Compressing..."
        self.bag_status_message_changed.emit()
        
        folder_name = self._current_bag_folder
        
        # Build tar command:
        # 1. Navigate to output directory
        # 2. Create tar.gz archive
        # 3. Remove original folder after successful compression
        compress_command = (
            f"bash -c '"
            f"cd {self.REMOTE_OUTPUT_DIR} && "
            f"tar -czf {folder_name}.tar.gz {folder_name} && "
            f"rm -rf {folder_name} && "
            f"echo \"Compressed: {folder_name}.tar.gz\""
            f"'"
        )
        
        def on_compress_complete(stdout: str, stderr: str):
            self._is_compressing = False
            self.is_compressing_changed.emit()
            
            if stderr and "error" in stderr.lower():
                print(f"[RosBagRecorder] Compression error: {stderr}")
                self._bag_status_message = f"Compress failed: {stderr[:50]}"
                self.bag_status_message_changed.emit()
                
                if self._robot_controller:
                    self._robot_controller.show_popup(
                        "ROS Bag Recording",
                        f"Compression failed: {stderr[:100]}",
                        "error",
                        3000
                    )
            else:
                print(f"[RosBagRecorder] Compression complete: {folder_name}.tar.gz")
                self._bag_status_message = ""
                self.bag_status_message_changed.emit()
                
                if self._robot_controller:
                    self._robot_controller.show_popup(
                        "ROS Bag Recording",
                        f"Saved: {folder_name}.tar.gz",
                        "info",
                        2000
                    )
            
            self._current_bag_folder = None
            self._bag_recording_duration_seconds = 0
            self.bag_recording_duration_changed.emit()
        
        self._run_ssh_command(compress_command, on_compress_complete)
    
    # ===== QML Properties =====
    
    @Property(bool, notify=is_bag_recording_changed)
    def is_bag_recording(self) -> bool:
        """Whether ROS bag recording is currently active."""
        return self._is_bag_recording
    
    @Property(int, notify=bag_recording_duration_changed)
    def bag_recording_duration(self) -> int:
        """Current recording duration in seconds."""
        return self._bag_recording_duration_seconds
    
    @Property(bool, notify=is_compressing_changed)
    def is_compressing(self) -> bool:
        """Whether compression is in progress."""
        return self._is_compressing
    
    @Property(str, notify=bag_status_message_changed)
    def bag_status_message(self) -> str:
        """Status message for errors or notifications."""
        return self._bag_status_message
    
    @Property(bool, notify=is_compressing_changed)
    def can_start_bag_recording(self) -> bool:
        """Whether recording can start (not recording and not compressing)."""
        return not self._is_bag_recording and not self._is_compressing
    
    # ===== QML Slots =====
    
    @Slot()
    def toggleBagRecording(self) -> None:
        """Toggle ROS bag recording on/off."""
        if self._is_compressing:
            print("[RosBagRecorder] Cannot toggle - compression in progress")
            if self._robot_controller:
                self._robot_controller.show_popup(
                    "ROS Bag Recording",
                    "Please wait for compression to complete",
                    "warning",
                    2000
                )
            return
        
        if self._is_bag_recording:
            self.stopBagRecording()
        else:
            self.startBagRecording()
    
    @Slot()
    def startBagRecording(self) -> None:
        """Start ROS bag recording if conditions are met."""
        if self._is_bag_recording:
            print("[RosBagRecorder] Already recording")
            return
        
        if self._is_compressing:
            print("[RosBagRecorder] Cannot start - compression in progress")
            self._bag_status_message = "Wait for compression"
            self.bag_status_message_changed.emit()
            return
        
        if not self._ssh_launcher:
            print("[RosBagRecorder] SSH not configured")
            self._bag_status_message = "SSH not configured"
            self.bag_status_message_changed.emit()
            if self._robot_controller:
                self._robot_controller.show_popup(
                    "ROS Bag Recording",
                    "SSH connection not configured for End Effector",
                    "error",
                    3000
                )
            return
        
        # Set recording state first (optimistic update)
        self._is_bag_recording = True
        self.is_bag_recording_changed.emit()
        self._bag_status_message = "Starting..."
        self.bag_status_message_changed.emit()
        
        # Start recording
        self._start_recording_internal()
    
    @Slot()
    def stopBagRecording(self) -> None:
        """Stop ROS bag recording and compress."""
        if not self._is_bag_recording:
            return
        
        self._bag_status_message = "Stopping..."
        self.bag_status_message_changed.emit()
        
        self._stop_recording_internal(compress=True)
    
    def cleanup(self) -> None:
        """
        Cleanup resources on application exit.
        
        Stops any active recording and compresses the bag folder.
        Uses a blocking approach to ensure cleanup completes.
        """
        print("[RosBagRecorder] Cleanup called")
        self._duration_timer.stop()
        
        if self._is_bag_recording:
            print("[RosBagRecorder] Stopping active recording for cleanup...")
            
            # For cleanup, we do a synchronous-style stop
            # Use SIGINT (-2) for graceful shutdown, then wait for ros2 bag to finish
            if self._remote_pid:
                stop_command = (
                    f"bash -c '"
                    f"kill -2 {self._remote_pid} 2>/dev/null || pkill -2 -f \"ros2 bag record\" 2>/dev/null; "
                    f"sleep 3"  # Wait for ros2 bag to finish writing
                    f"'"
                )
            else:
                stop_command = (
                    "bash -c '"
                    "pkill -2 -f \"ros2 bag record\" 2>/dev/null; "
                    "sleep 3"  # Wait for ros2 bag to finish writing
                    "'"
                )
            
            cleanup_done = threading.Event()
            
            def on_cleanup_stop(stdout: str, stderr: str):
                print("[RosBagRecorder] Recording stopped during cleanup")
                
                if self._current_bag_folder:
                    # Compress the folder
                    compress_command = (
                        f"bash -c '"
                        f"cd {self.REMOTE_OUTPUT_DIR} && "
                        f"tar -czf {self._current_bag_folder}.tar.gz {self._current_bag_folder} && "
                        f"rm -rf {self._current_bag_folder}"
                        f"'"
                    )
                    
                    def on_cleanup_compress(stdout: str, stderr: str):
                        print(f"[RosBagRecorder] Cleanup compression complete: {self._current_bag_folder}")
                        cleanup_done.set()
                    
                    self._run_ssh_command(compress_command, on_cleanup_compress)
                else:
                    cleanup_done.set()
            
            self._run_ssh_command(stop_command, on_cleanup_stop)
            
            # Wait for cleanup to complete (max 30 seconds for compression)
            cleanup_done.wait(timeout=30)
            print("[RosBagRecorder] Cleanup complete")
        
        self._is_bag_recording = False
        self._is_compressing = False
        self._remote_pid = None
        self._current_bag_folder = None
