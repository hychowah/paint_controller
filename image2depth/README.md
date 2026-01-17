# Image to Depth Conversion Module

This module provides real-time monocular depth estimation from RGB images/video, optimized for Steam Deck performance (targeting 10+ FPS).

## Overview

The `image2depth` module converts RGB images or video frames into depth maps using deep learning models like MiDaS. It's designed to run efficiently on Steam Deck hardware with limited computational resources.

## Features

- **Real-time depth estimation** from images and video streams
- **ROS2 integration** for easy integration with robotics applications
- **Standalone mode** for testing without ROS2
- **OpenCV DNN backend** with optional ONNX Runtime support
- **GPU acceleration** support (when available)
- **Configurable input sizes** for performance tuning
- **FPS monitoring** and performance metrics

## Architecture

### Components

1. **DepthEstimator** (`depth_estimator.hpp/cpp`)
   - Core depth estimation class
   - Model loading and inference
   - Pre/post-processing
   - Performance monitoring

2. **depth_estimation_node** (`depth_estimation_node.cpp`)
   - ROS2 node wrapper
   - Subscribes to image topics
   - Publishes depth maps
   - Parameter configuration

3. **depth_estimation_test** (`depth_estimation_test.cpp`)
   - Standalone test application
   - Works with images, videos, or cameras
   - No ROS2 dependency

## Dependencies

### Required
- OpenCV (>= 4.0) with DNN module
- ROS2 (Humble or Jazzy) - for ROS node only
- cv_bridge - for ROS node only

### Optional
- ONNX Runtime - for optimized inference
- CUDA - for GPU acceleration

## Installation

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
    libopencv-dev \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-sensor-msgs
```

### 2. Install ONNX Runtime (Optional, Recommended for Performance)

```bash
# Download ONNX Runtime (adjust version as needed)
wget https://github.com/microsoft/onnxruntime/releases/download/v1.16.3/onnxruntime-linux-x64-1.16.3.tgz
tar -xzf onnxruntime-linux-x64-1.16.3.tgz
sudo cp -r onnxruntime-linux-x64-1.16.3/include/* /usr/local/include/
sudo cp -r onnxruntime-linux-x64-1.16.3/lib/* /usr/local/lib/
sudo ldconfig
```

### 3. Download Depth Model

Download a pre-trained MiDaS model in ONNX format:

```bash
# MiDaS Small (recommended for Steam Deck - good speed/accuracy balance)
wget https://github.com/isl-org/MiDaS/releases/download/v3_1/midas_v21_small_256.onnx -O ~/.local/share/image2depth/models/midas_small.onnx

# Alternative: MiDaS v2.1 Small 384x384 (better accuracy, slower)
# wget <URL_TO_MODEL> -O ~/.local/share/image2depth/models/midas_small.onnx
```

**Note:** You may need to export MiDaS models to ONNX format yourself if pre-converted models are not available. See [MiDaS repository](https://github.com/isl-org/MiDaS) for details.

### 4. Build

From your ROS2 workspace:

```bash
cd ~/ros2_ws
colcon build --packages-select image2depth
source install/setup.bash
```

## Usage

### Standalone Test Application

Test depth estimation without ROS2:

```bash
# Process a single image
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --image input.jpg \
    --output depth_output.jpg

# Process a video file
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --video input.mp4 \
    --output depth_output.avi

# Process camera stream
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --camera 0

# Use GPU acceleration (if available)
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --camera 0 \
    --gpu

# Apply bilateral filtering for smoother results
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --camera 0 \
    --filter
```

### ROS2 Node

Run the depth estimation node:

```bash
# Basic usage
ros2 run image2depth depth_estimation_node

# With custom parameters
ros2 run image2depth depth_estimation_node \
    --ros-args \
    -p model_path:=~/.local/share/image2depth/models/midas_small.onnx \
    -p input_topic:=/camera/image_raw \
    -p output_topic:=/depth/image \
    -p input_width:=384 \
    -p input_height:=384 \
    -p use_gpu:=false
```

### ROS2 Parameters

- `model_path` (string): Path to ONNX model file (default: `~/.local/share/image2depth/models/midas_small.onnx`)
- `input_width` (int): Model input width in pixels (default: 384)
- `input_height` (int): Model input height in pixels (default: 384)
- `max_input_dimension` (int): Max input dimension for auto-scaling (default: 1280, 0=disable)
- `normalize_output` (bool): Normalize depth to 0-255 range (default: true)
- `use_gpu` (bool): Use GPU acceleration if available (default: false)
- `apply_bilateral_filter` (bool): Apply bilateral filter to output (default: false)
- `verbose` (bool): Print performance metrics (default: true)
- `input_topic` (string): Input image topic (default: `/camera/image_raw`)
- `output_topic` (string): Output depth map topic (default: `/depth/image`)

## Performance Optimization

### For Steam Deck

1. **Use smaller input size**: `input_width=256, input_height=256`
2. **Use MiDaS Small model**: Better speed/accuracy tradeoff
3. **Disable GPU**: Steam Deck's CPU may be faster for small models
4. **Disable bilateral filter**: Saves processing time
5. **Enable auto-scaling**: Automatically scales down large images (default: enabled at 1280px)
6. **Use ONNX Runtime**: If available, provides better performance

### Auto-Scaling for High-Resolution Inputs

The module automatically scales down large images/videos before processing to improve performance:

- **Default**: Images larger than 1280px (width or height) are scaled down proportionally
- **Benefits**: Significantly faster processing for 4K, 1080p, or high-resolution images
- **Quality**: Minimal impact on depth estimation accuracy
- **Disable**: Set `max_input_dimension=0` to process at full resolution
- **Adjust**: Set custom max size, e.g., `--max-size 1920` for 1080p sources

Example:
```bash
# Process 4K image with auto-scaling (much faster)
./depth_estimation_test --model model.onnx --image 4k_image.jpg

# Process at full resolution (slower)
./depth_estimation_test --model model.onnx --image 4k_image.jpg --max-size 0

# Custom max size for 1080p videos
./depth_estimation_test --model model.onnx --video 1080p.mp4 --max-size 1920
```

### Expected Performance on Steam Deck

With MiDaS Small (256x256):
- **~15-20 FPS** (CPU only)
- **~25-30 FPS** with ONNX Runtime optimization

With MiDaS Small (384x384):
- **~10-15 FPS** (CPU only)
- **~18-22 FPS** with ONNX Runtime optimization

## Model Options

### MiDaS Models

1. **MiDaS Small (Recommended)**
   - Size: ~10MB
   - Input: 256x256 or 384x384
   - Speed: Fast (15-20 FPS on Steam Deck)
   - Accuracy: Good

2. **MiDaS v2.1**
   - Size: ~100MB
   - Input: 384x384
   - Speed: Slower (5-8 FPS on Steam Deck)
   - Accuracy: Better

3. **MiDaS Large**
   - Size: ~200MB+
   - Input: 384x384 or larger
   - Speed: Very slow (2-3 FPS on Steam Deck)
   - Accuracy: Best

### Alternative Models

- **FastDepth**: Optimized for speed, lower accuracy
- **Depth-Anything**: Recent model with good speed/accuracy balance
- **LapDepth**: Lightweight alternative

## Integration with Main Program

To integrate with the main paint controller:

1. **Add as ROS2 dependency** in the main package
2. **Subscribe to depth topic** in paint controller
3. **Use depth information** for enhanced control (e.g., collision avoidance, 3D painting)

Example integration:
```cpp
// In paint_controller.cpp
auto depth_subscription = create_subscription<sensor_msgs::msg::Image>(
    "/depth/image", 10,
    [this](sensor_msgs::msg::Image::SharedPtr msg) {
        // Process depth information
        // Use for collision detection, path planning, etc.
    });
```

## Troubleshooting

### Model Not Found
```
Error: Model file not found: ~/.local/share/image2depth/models/midas_small.onnx
```
Download the model using instructions in Installation section.

### Low FPS
- Try smaller input size (256x256 instead of 384x384)
- Use MiDaS Small instead of larger models
- Disable bilateral filter
- Install ONNX Runtime for better performance

### OpenCV DNN Error
```
OpenCV(4.x.x) Error: Assertion failed
```
Ensure OpenCV is built with DNN module support:
```bash
opencv_version --build_info | grep -i dnn
```

## Future Improvements

- [ ] ONNX Runtime backend implementation
- [ ] TensorRT support for NVIDIA GPUs
- [ ] Model quantization for INT8 inference
- [ ] Multi-threaded processing pipeline
- [ ] Temporal filtering for video sequences
- [ ] Dynamic model selection based on performance
- [ ] Pre-compiled optimized models for Steam Deck

## References

- [MiDaS: Monocular Depth Estimation](https://github.com/isl-org/MiDaS)
- [Depth-Anything](https://github.com/LiheYoung/Depth-Anything)
- [OpenCV DNN Module](https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html)
- [ONNX Runtime](https://onnxruntime.ai/)
