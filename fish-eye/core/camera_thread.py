"""
Threaded camera capture for non-blocking video streaming.
"""
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import queue
import time


class CameraThread(QThread):
    """Thread for capturing frames from camera without blocking GUI."""
    
    frame_ready = pyqtSignal(object)  # Emits numpy array (frame)
    fps_update = pyqtSignal(float)    # Emits current FPS
    error_occurred = pyqtSignal(str)   # Emits error message
    
    def __init__(self, camera_index=0, width=1920, height=1080):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        
        self.capture = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=2)  # Limit queue to prevent lag
        
        # FPS calculation
        self.fps = 0.0
        self.frame_count = 0
        self.fps_start_time = None
        
    def run(self):
        """Main thread loop for capturing frames."""
        self.running = True
        
        # Open camera
        self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self.capture.isOpened():
            self.error_occurred.emit(f"Failed to open camera {self.camera_index}")
            return
            
        # Set resolution
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        # Verify actual resolution
        actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if actual_width != self.width or actual_height != self.height:
            print(f"Warning: Requested {self.width}x{self.height}, got {actual_width}x{actual_height}")
            
        self.fps_start_time = time.time()
        
        while self.running:
            ret, frame = self.capture.read()
            
            if not ret:
                self.error_occurred.emit("Failed to read frame from camera")
                break
                
            # Update FPS
            self.frame_count += 1
            elapsed = time.time() - self.fps_start_time
            if elapsed >= 1.0:  # Update FPS every second
                self.fps = self.frame_count / elapsed
                self.fps_update.emit(self.fps)
                self.frame_count = 0
                self.fps_start_time = time.time()
                
            # Emit frame (will drop if queue is full - prevents lag)
            try:
                self.frame_queue.put_nowait(frame)
                # Emit the latest frame
                self.frame_ready.emit(frame)
            except queue.Full:
                # Queue full, drop oldest frame and add new one
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put_nowait(frame)
                    self.frame_ready.emit(frame)
                except:
                    pass
                    
        # Clean up
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            
    def stop(self):
        """Stop the capture thread."""
        self.running = False
        self.wait()  # Wait for thread to finish
        
    def get_frame_dimensions(self):
        """Get actual frame dimensions."""
        if self.capture is not None and self.capture.isOpened():
            width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return width, height
        return self.width, self.height
