"""
Processing thread for unwrapping fisheye frames without blocking GUI.
"""
from PyQt5.QtCore import QThread, pyqtSignal
import queue
import time


class ProcessingThread(QThread):
    """Thread for processing fisheye frames asynchronously."""
    
    frame_processed = pyqtSignal(object, object)  # Emits (original_display, unwrapped)
    processing_fps = pyqtSignal(float)
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.running = False
        
        # Input queue from camera
        self.input_queue = queue.Queue(maxsize=2)
        
        # Performance tracking
        self.fps = 0.0
        self.frame_count = 0
        self.fps_start_time = None
        
        # Display settings
        self.show_circle_overlay = True
        
    def run(self):
        """Main processing loop."""
        self.running = True
        self.fps_start_time = time.time()
        
        while self.running:
            try:
                # Get frame from queue (with timeout to allow thread checking)
                frame = self.input_queue.get(timeout=0.1)
                
                # Process frame
                unwrapped = self.processor.process_frame(frame, fast_mode=False)
                
                # Prepare display frame
                if self.show_circle_overlay:
                    display_original = self.processor.draw_circle_overlay(frame)
                else:
                    display_original = frame
                    
                # Emit processed frames
                self.frame_processed.emit(display_original, unwrapped)
                
                # Update FPS
                self.frame_count += 1
                elapsed = time.time() - self.fps_start_time
                if elapsed >= 1.0:
                    self.fps = self.frame_count / elapsed
                    self.processing_fps.emit(self.fps)
                    self.frame_count = 0
                    self.fps_start_time = time.time()
                    
            except queue.Empty:
                # No frame available, continue
                continue
            except Exception as e:
                print(f"Processing error: {e}")
                
    def add_frame(self, frame):
        """Add frame to processing queue (drops old frames if full)."""
        try:
            self.input_queue.put_nowait(frame)
        except queue.Full:
            # Queue full, drop oldest and add new
            try:
                self.input_queue.get_nowait()
                self.input_queue.put_nowait(frame)
            except:
                pass
                
    def set_show_overlay(self, show):
        """Update circle overlay setting."""
        self.show_circle_overlay = show
        
    def stop(self):
        """Stop the processing thread."""
        self.running = False
        self.wait()
