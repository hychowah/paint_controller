"""
Video recorder for saving original and unwrapped video streams.
"""
import cv2
import os
from datetime import datetime
from pathlib import Path
from utils.config import RECORDING_CODEC, RECORDING_FPS, RECORDING_FORMAT


class VideoRecorder:
    """Record video streams to file."""
    
    def __init__(self, output_dir="recordings"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.is_recording = False
        self.original_writer = None
        self.unwrapped_writer = None
        
        self.original_path = None
        self.unwrapped_path = None
        
        self.frame_count = 0
        
    def start_recording(self, width, height, record_both=True):
        """
        Start recording video.
        
        Args:
            width: Frame width
            height: Frame height
            record_both: If True, record both original and unwrapped streams
            
        Returns:
            Tuple of (original_path, unwrapped_path)
        """
        if self.is_recording:
            print("Already recording")
            return None, None
            
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup codec
        fourcc = cv2.VideoWriter_fourcc(*RECORDING_CODEC)
        
        # Create original video writer
        if record_both:
            self.original_path = self.output_dir / f"fisheye_original_{timestamp}{RECORDING_FORMAT}"
            self.original_writer = cv2.VideoWriter(
                str(self.original_path),
                fourcc,
                RECORDING_FPS,
                (width, height)
            )
            
            if not self.original_writer.isOpened():
                print(f"Failed to create video writer for original: {self.original_path}")
                self.original_writer = None
                self.original_path = None
        
        # Create unwrapped video writer
        self.unwrapped_path = self.output_dir / f"fisheye_unwrapped_{timestamp}{RECORDING_FORMAT}"
        self.unwrapped_writer = cv2.VideoWriter(
            str(self.unwrapped_path),
            fourcc,
            RECORDING_FPS,
            (width, height)
        )
        
        if not self.unwrapped_writer.isOpened():
            print(f"Failed to create video writer for unwrapped: {self.unwrapped_path}")
            self.unwrapped_writer = None
            self.unwrapped_path = None
            # Clean up original writer if unwrapped failed
            if self.original_writer:
                self.original_writer.release()
                self.original_writer = None
                self.original_path = None
            return None, None
            
        self.is_recording = True
        self.frame_count = 0
        
        print(f"Started recording:")
        if self.original_path:
            print(f"  Original: {self.original_path}")
        print(f"  Unwrapped: {self.unwrapped_path}")
        
        return self.original_path, self.unwrapped_path
        
    def write_frame(self, original_frame=None, unwrapped_frame=None):
        """
        Write frames to video files.
        
        Args:
            original_frame: Original fisheye frame (numpy array)
            unwrapped_frame: Unwrapped frame (numpy array)
        """
        if not self.is_recording:
            return
            
        try:
            if original_frame is not None and self.original_writer is not None:
                self.original_writer.write(original_frame)
                
            if unwrapped_frame is not None and self.unwrapped_writer is not None:
                self.unwrapped_writer.write(unwrapped_frame)
                
            self.frame_count += 1
        except Exception as e:
            print(f"Error writing frame: {e}")
            
    def stop_recording(self):
        """Stop recording and close video files."""
        if not self.is_recording:
            return
            
        self.is_recording = False
        
        # Release video writers
        if self.original_writer is not None:
            self.original_writer.release()
            self.original_writer = None
            
        if self.unwrapped_writer is not None:
            self.unwrapped_writer.release()
            self.unwrapped_writer = None
            
        duration = self.frame_count / RECORDING_FPS
        print(f"Stopped recording. Frames: {self.frame_count}, Duration: {duration:.1f}s")
        
        if self.original_path:
            print(f"  Saved original: {self.original_path}")
        if self.unwrapped_path:
            print(f"  Saved unwrapped: {self.unwrapped_path}")
            
        result = (self.original_path, self.unwrapped_path)
        
        self.original_path = None
        self.unwrapped_path = None
        self.frame_count = 0
        
        return result
        
    def is_recording_active(self):
        """Check if currently recording."""
        return self.is_recording
        
    def get_frame_count(self):
        """Get number of frames recorded."""
        return self.frame_count
        
    def get_duration(self):
        """Get recording duration in seconds."""
        if self.frame_count == 0:
            return 0.0
        return self.frame_count / RECORDING_FPS
        
    def save_snapshot(self, frame, prefix="snapshot"):
        """
        Save a single frame as an image.
        
        Args:
            frame: Frame to save (numpy array)
            prefix: Filename prefix
            
        Returns:
            Path to saved image or None on error
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"{prefix}_{timestamp}.png"
        
        try:
            cv2.imwrite(str(filename), frame)
            print(f"Saved snapshot: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return None
            
    def __del__(self):
        """Cleanup on deletion."""
        if self.is_recording:
            self.stop_recording()
