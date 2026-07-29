#!/usr/bin/env python3
"""
Screen Recorder Service for capturing X11 display using ffmpeg.

Features:
- Records 1280x800 display at 30fps using x11grab
- Saves to ~/Videos/Operation with YYYYMMDD_HHMMSS.mp4 filename format
- Auto-segments recordings at 1 hour
- Monitors disk space (requires 5GB minimum to start/continue)
- Graceful cleanup on application exit
"""

import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, Signal, Slot

logger = logging.getLogger(__name__)


class ScreenRecorder(QObject):
    """
    Screen recording service using ffmpeg x11grab.

    Exposes properties and methods for QML integration to start/stop
    screen recording with automatic segmentation and disk space monitoring.
    """

    # Signals for property changes
    is_recording_changed = Signal()
    free_space_gb_changed = Signal()
    recording_duration_changed = Signal()
    status_message_changed = Signal()

    # Configuration constants
    DISPLAY = ":0.0"
    FRAMERATE = 30
    MIN_FREE_SPACE_GB = 5.0
    MAX_RECORDING_DURATION_SECONDS = 3600  # 1 hour

    def __init__(self, parent: QObject | None = None, screen_manager=None):
        super().__init__(parent)

        # Screen manager for dynamic resolution (optional)
        self._screen_manager = screen_manager

        # Recording state
        self._is_recording = False
        self._ffmpeg_process: subprocess.Popen | None = None
        self._current_recording_file: Path | None = None
        self._recording_start_time: datetime | None = None
        self._recording_duration_seconds = 0

        # Disk space monitoring
        self._free_space_gb = 0.0
        self._status_message = ""

        # Output directory
        self._output_dir = Path.home() / "Videos" / "Operation"
        self._ensure_output_directory()

        # Monitor timer (1 second interval)
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._on_monitor_tick)
        self._monitor_timer.setInterval(1000)

        # Connect to screen manager for dynamic resolution updates
        if self._screen_manager:
            self._screen_manager.screens_changed.connect(self._on_screens_changed)

        # Initial disk space check
        self._update_free_space()

    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Error creating output directory: %s", e)

    def _update_free_space(self) -> None:
        """Update free disk space property."""
        try:
            usage = shutil.disk_usage(self._output_dir)
            new_free_space = usage.free / (1024**3)  # Convert to GB
            if abs(new_free_space - self._free_space_gb) > 0.01:  # Only update if changed significantly
                self._free_space_gb = new_free_space
                self.free_space_gb_changed.emit()
        except Exception as e:
            logger.error("Error checking disk space: %s", e)
            self._free_space_gb = 0.0
            self.free_space_gb_changed.emit()

    def _generate_filename(self) -> Path:
        """Generate filename with YYYYMMDD_HHMMSS format."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self._output_dir / f"{timestamp}.mp4"

    def _start_ffmpeg(self) -> bool:
        """Start ffmpeg recording process."""
        if self._ffmpeg_process is not None:
            logger.warning("ffmpeg process already running")
            return False

        self._current_recording_file = self._generate_filename()

        # Get dynamic resolution from screen manager
        if self._screen_manager:
            width, height = self._screen_manager.get_virtual_desktop_size()
            resolution = f"{width}x{height}"
            screen_count = self._screen_manager.get_screen_count()
        else:
            resolution = "1280x800"  # Fallback to Steam Deck display
            screen_count = 1

        # Build ffmpeg command
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if exists
            "-f",
            "x11grab",
            "-s",
            resolution,
            "-r",
            str(self.FRAMERATE),
            "-i",
            self.DISPLAY,
            "-vcodec",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            str(self._current_recording_file),
        ]

        try:
            # Start ffmpeg with stdin pipe for graceful termination
            self._ffmpeg_process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self._recording_start_time = datetime.now()
            self._recording_duration_seconds = 0

            # Set status message with recording info
            screen_text = "screen" if screen_count == 1 else "screens"
            self._status_message = f"Recording {resolution} ({screen_count} {screen_text})"

            logger.info("Started recording: %s", self._current_recording_file)
            logger.info("Resolution: %s (%d %s)", resolution, screen_count, screen_text)
            return True
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg.")
            self._status_message = "ffmpeg not installed"
            self.status_message_changed.emit()
            return False
        except Exception as e:
            logger.error("Error starting ffmpeg: %s", e)
            self._status_message = f"Error: {str(e)}"
            self.status_message_changed.emit()
            return False

    def _stop_ffmpeg(self) -> bool:
        """Stop ffmpeg recording process gracefully."""
        if self._ffmpeg_process is None:
            return True

        try:
            # Send 'q' to stdin to gracefully stop ffmpeg
            if self._ffmpeg_process.stdin:
                try:
                    self._ffmpeg_process.stdin.write(b"q")
                    self._ffmpeg_process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass  # Process may have already terminated

            # Wait for process to finish (timeout 5 seconds)
            try:
                self._ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force terminate if graceful shutdown fails
                logger.warning("ffmpeg not responding, sending SIGTERM")
                self._ffmpeg_process.terminate()
                try:
                    self._ffmpeg_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning("ffmpeg still not responding, sending SIGKILL")
                    self._ffmpeg_process.kill()
                    self._ffmpeg_process.wait()

            logger.info("Stopped recording: %s", self._current_recording_file)
            return True
        except Exception as e:
            logger.error("Error stopping ffmpeg: %s", e)
            return False
        finally:
            self._ffmpeg_process = None
            self._current_recording_file = None
            self._recording_start_time = None

    def _on_monitor_tick(self) -> None:
        """Called every second to monitor recording state."""
        if not self._is_recording:
            return

        # Update disk space
        self._update_free_space()

        # Update recording duration
        if self._recording_start_time:
            delta = datetime.now() - self._recording_start_time
            self._recording_duration_seconds = int(delta.total_seconds())
            self.recording_duration_changed.emit()

        # Check if we need to segment (1 hour limit)
        if self._recording_duration_seconds >= self.MAX_RECORDING_DURATION_SECONDS:
            logger.info("Max duration reached, segmenting recording")
            self._segment_recording()
            return

        # Check if disk space is too low
        if self._free_space_gb < self.MIN_FREE_SPACE_GB:
            logger.warning("Low disk space, stopping recording")
            self._status_message = "Stopped: Low storage"
            self.status_message_changed.emit()
            self._stop_recording_internal()

    def _segment_recording(self) -> None:
        """Stop current recording and start a new one if space permits."""
        self._stop_ffmpeg()

        # Check if we have enough space for a new segment
        self._update_free_space()
        if self._free_space_gb >= self.MIN_FREE_SPACE_GB:
            if self._start_ffmpeg():
                logger.info("Started new recording segment")
            else:
                self._stop_recording_internal()
        else:
            logger.warning("Not enough space for new segment")
            self._status_message = "Stopped: Low storage"
            self.status_message_changed.emit()
            self._stop_recording_internal()

    def _stop_recording_internal(self) -> None:
        """Internal method to stop recording and update state."""
        self._stop_ffmpeg()
        self._monitor_timer.stop()
        self._is_recording = False
        self._recording_duration_seconds = 0
        self.is_recording_changed.emit()
        self.recording_duration_changed.emit()

    def _on_screens_changed(self) -> None:
        """Handle screen configuration changes during recording.

        When screens are added/removed, segment the recording to start a new
        file with updated resolution matching the new screen configuration.
        """
        if not self._is_recording:
            return

        logger.info("Screen configuration changed, segmenting recording")
        self._segment_recording()

    # ===== QML Properties =====

    @Property(bool, notify=is_recording_changed)
    def is_recording(self) -> bool:
        """Whether screen recording is currently active."""
        return self._is_recording

    @Property(float, notify=free_space_gb_changed)
    def free_space_gb(self) -> float:
        """Free disk space in GB at the output location."""
        return self._free_space_gb

    @Property(int, notify=recording_duration_changed)
    def recording_duration(self) -> int:
        """Current recording duration in seconds."""
        return self._recording_duration_seconds

    @Property(str, notify=status_message_changed)
    def status_message(self) -> str:
        """Status message for errors or notifications."""
        return self._status_message

    @Property(bool, notify=free_space_gb_changed)
    def can_record(self) -> bool:
        """Whether recording can start (enough disk space)."""
        return self._free_space_gb >= self.MIN_FREE_SPACE_GB

    # ===== QML Slots =====

    @Slot()
    def toggleRecording(self) -> None:
        """Toggle screen recording on/off."""
        if self._is_recording:
            self.stopRecording()
        else:
            self.startRecording()

    @Slot()
    def startRecording(self) -> None:
        """Start screen recording if conditions are met."""
        if self._is_recording:
            logger.info("Already recording")
            return

        # Check disk space
        self._update_free_space()
        if self._free_space_gb < self.MIN_FREE_SPACE_GB:
            self._status_message = f"Need {self.MIN_FREE_SPACE_GB}GB free (have {self._free_space_gb:.1f}GB)"
            self.status_message_changed.emit()
            logger.info("%s", self._status_message)
            return

        # Start ffmpeg
        if self._start_ffmpeg():
            self._is_recording = True
            # Keep status message from _start_ffmpeg (shows recording info)
            self.is_recording_changed.emit()
            self.status_message_changed.emit()

            # Start monitor timer
            self._monitor_timer.start()
        else:
            self._status_message = "Failed to start recording"
            self.status_message_changed.emit()

    @Slot()
    def stopRecording(self) -> None:
        """Stop screen recording."""
        if not self._is_recording:
            return

        self._stop_recording_internal()
        self._status_message = ""
        self.status_message_changed.emit()

    def cleanup(self) -> None:
        """
        Cleanup resources on application exit.

        Gracefully stops any active recording to ensure the video file
        is properly finalized.
        """
        logger.info("Cleanup called")
        self._monitor_timer.stop()
        if self._is_recording:
            self._stop_ffmpeg()
            self._is_recording = False
