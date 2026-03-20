"""
Configuration and default parameters for fisheye unwrapping.
Supports circular fisheye (180° FOV in a circle within rectangular frame).
"""
import numpy as np

# Default image resolution (1080p)
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080

# Circular fisheye parameters
# For circular fisheye, the image is a circle in the center of the frame
DEFAULT_CENTER_X = DEFAULT_WIDTH // 2   # 960
DEFAULT_CENTER_Y = DEFAULT_HEIGHT // 2  # 540
DEFAULT_RADIUS = 500  # Approximate radius of fisheye circle in pixels

# Generic 180° fisheye camera intrinsic parameters
# Focal length for 180° FOV: approximately 0.6 * min(width, height)
DEFAULT_FOCAL_LENGTH = 450.0

# Camera matrix (intrinsics)
def get_camera_matrix(width, height, focal_length=None):
    """Generate camera matrix for given dimensions."""
    if focal_length is None:
        focal_length = DEFAULT_FOCAL_LENGTH
    
    cx = width / 2.0
    cy = height / 2.0
    
    return np.array([
        [focal_length, 0, cx],
        [0, focal_length, cy],
        [0, 0, 1]
    ], dtype=np.float32)

# Generic distortion coefficients for 180° fisheye
# k1: strong negative radial distortion (barrel)
# k2: positive correction at edges
# k3, k4: higher order corrections
DEFAULT_DISTORTION_K1 = -0.35
DEFAULT_DISTORTION_K2 = 0.15
DEFAULT_DISTORTION_K3 = 0.0
DEFAULT_DISTORTION_K4 = 0.0

def get_distortion_coeffs(k1=None, k2=None, k3=None, k4=None):
    """Generate OpenCV fisheye distortion coefficients (4 parameters)."""
    if k1 is None:
        k1 = DEFAULT_DISTORTION_K1
    if k2 is None:
        k2 = DEFAULT_DISTORTION_K2
    if k3 is None:
        k3 = DEFAULT_DISTORTION_K3
    if k4 is None:
        k4 = DEFAULT_DISTORTION_K4
    
    return np.array([k1, k2, k3, k4], dtype=np.float32)

# Unwrapping parameters
DEFAULT_FOV_HORIZONTAL = 90.0   # Degrees (start with narrower view for better quality)
DEFAULT_FOV_VERTICAL = 67.5     # Degrees
DEFAULT_ZOOM = 1.0
DEFAULT_ROTATION = 0.0          # Degrees

# Output resolution for unwrapped image
DEFAULT_OUTPUT_WIDTH = 1920
DEFAULT_OUTPUT_HEIGHT = 1080

# Slider ranges for UI
SLIDER_RANGES = {
    'fov_horizontal': (60, 360, DEFAULT_FOV_HORIZONTAL),
    'fov_vertical': (45, 180, DEFAULT_FOV_VERTICAL),
    'center_x': (0, DEFAULT_WIDTH, DEFAULT_CENTER_X),
    'center_y': (0, DEFAULT_HEIGHT, DEFAULT_CENTER_Y),
    'radius': (100, 1000, DEFAULT_RADIUS),
    'distortion_k1': (-1.0, 0.5, DEFAULT_DISTORTION_K1),
    'distortion_k2': (-0.5, 0.5, DEFAULT_DISTORTION_K2),
    'zoom': (0.5, 3.0, DEFAULT_ZOOM),
    'rotation': (-180, 180, DEFAULT_ROTATION),
    'focal_length': (200, 800, DEFAULT_FOCAL_LENGTH)
}

# Performance settings
PREVIEW_SCALE = 0.5  # Scale factor during slider adjustment (0.5 = half resolution)
DEBOUNCE_MS = 200    # Milliseconds to wait after slider change before full quality update
MAX_FPS = 60         # Maximum target FPS

# Video recording settings
RECORDING_CODEC = 'mp4v'  # 'mp4v', 'XVID', 'H264'
RECORDING_FPS = 30
RECORDING_FORMAT = '.mp4'

# Available camera resolutions
AVAILABLE_RESOLUTIONS = [
    (640, 480),
    (1280, 720),
    (1920, 1080),
    (2560, 1440),
    (3840, 2160)
]

# Default preset configurations
DEFAULT_PRESETS = {
    'front-view-90deg': {
        'name': 'Front View 90°',
        'fov_horizontal': 90.0,
        'fov_vertical': 67.5,
        'zoom': 1.0,
        'rotation': 0.0
    },
    'wide-view-180deg': {
        'name': 'Wide View 180°',
        'fov_horizontal': 180.0,
        'fov_vertical': 135.0,
        'zoom': 1.0,
        'rotation': 0.0
    },
    'panoramic-360deg': {
        'name': 'Panoramic 360°',
        'fov_horizontal': 360.0,
        'fov_vertical': 180.0,
        'zoom': 0.8,
        'rotation': 0.0
    }
}
