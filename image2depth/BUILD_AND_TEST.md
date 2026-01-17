# Image2Depth Module - Build and Test Guide

This guide provides instructions for building, testing, and integrating the image2depth module.

## Prerequisites

### System Requirements
- Ubuntu 22.04 or 24.04
- ROS2 (Humble or Jazzy)
- At least 2GB free disk space for models
- Steam Deck or x86_64 Linux system

### Required Dependencies

```bash
# Update package lists
sudo apt update

# Install OpenCV with DNN module
sudo apt install -y \
    libopencv-dev \
    libopencv-contrib-dev

# Install ROS2 dependencies
sudo apt install -y \
    ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-image-transport

# Verify OpenCV installation
pkg-config --modversion opencv4
# Should output version 4.x.x
```

### Optional Dependencies (Recommended for Performance)

```bash
# ONNX Runtime (for optimized inference)
# Download from: https://github.com/microsoft/onnxruntime/releases
# Example for version 1.16.3:
wget https://github.com/microsoft/onnxruntime/releases/download/v1.16.3/onnxruntime-linux-x64-1.16.3.tgz
tar -xzf onnxruntime-linux-x64-1.16.3.tgz
sudo cp -r onnxruntime-linux-x64-1.16.3/include/* /usr/local/include/
sudo cp -r onnxruntime-linux-x64-1.16.3/lib/* /usr/local/lib/
sudo ldconfig
```

## Building

### Option 1: Build as Standalone Package

```bash
# Navigate to your ROS2 workspace
cd ~/ros2_ws/src

# The image2depth folder should already be in the paint_controller repository
cd paint_controller_ros2

# Build only the image2depth package
cd ~/ros2_ws
colcon build --packages-select image2depth

# Source the workspace
source install/setup.bash
```

### Option 2: Build with Main Package

```bash
# Build all packages including image2depth
cd ~/ros2_ws
colcon build

# Source the workspace
source install/setup.bash
```

### Troubleshooting Build Issues

#### OpenCV Not Found
```
CMake Error: Could not find OpenCV
```
**Solution:**
```bash
sudo apt install libopencv-dev
# Or specify OpenCV path:
export OpenCV_DIR=/usr/lib/x86_64-linux-gnu/cmake/opencv4
```

#### cv_bridge Not Found
```
CMake Error: Could not find cv_bridge
```
**Solution:**
```bash
sudo apt install ros-${ROS_DISTRO}-cv-bridge
source /opt/ros/${ROS_DISTRO}/setup.bash
```

#### Missing DNN Module
```
OpenCV was not built with DNN support
```
**Solution:**
```bash
# Install OpenCV from source with DNN enabled, or use system OpenCV:
sudo apt install libopencv-dev libopencv-contrib-dev
```

## Testing

### Step 1: Download a Test Model

Before testing, you need a depth estimation model in ONNX format.

#### Option A: Use the Download Script (Interactive)
```bash
cd ~/ros2_ws/src/paint_controller_ros2/image2depth
./download_model.sh
```

#### Option B: Manual Download/Conversion

Since pre-converted MiDaS ONNX models may not be readily available, you'll need to convert them yourself:

```bash
# Install PyTorch and dependencies
pip install torch torchvision timm

# Clone MiDaS repository
git clone https://github.com/isl-org/MiDaS.git
cd MiDaS

# Download pretrained model
wget https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.pt

# Create conversion script
cat > export_to_onnx.py << 'EOF'
import torch
import torch.onnx

# Load MiDaS model
model_path = "model-small.pt"
model = torch.load(model_path, map_location='cpu')
model.eval()

# Create dummy input
dummy_input = torch.randn(1, 3, 256, 256)

# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    "midas_small_256.onnx",
    export_params=True,
    opset_version=11,
    do_constant_folding=True,
    input_names=['input'],
    output_names=['output'],
    dynamic_axes={
        'input': {0: 'batch_size'},
        'output': {0: 'batch_size'}
    }
)
print("Model exported to midas_small_256.onnx")
EOF

python export_to_onnx.py

# Move model to standard location
sudo cp midas_small_256.onnx /tmp/midas_small.onnx
```

### Step 2: Test with Standalone Application

The standalone test application doesn't require ROS2 and is useful for quick testing:

#### Test with an Image
```bash
# Download a test image
wget https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1200px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg -O test_image.jpg

# Run depth estimation
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --image test_image.jpg \
    --output depth_output.jpg

# Check the output
display depth_output.jpg  # or use your favorite image viewer
```

#### Test with Webcam
```bash
# Test with webcam (device 0)
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --camera 0

# The application will show two windows:
# - "Input Frame": Original camera feed
# - "Depth Map": Estimated depth map
# 
# Press 'q' to quit
```

#### Test with Video File
```bash
# Download or use your own video
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --video input_video.mp4 \
    --output depth_video.avi
```

#### Performance Testing
```bash
# Test with different input sizes
# Smaller = faster, less accurate
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --camera 0 \
    --width 256 \
    --height 256

# Larger = slower, more accurate
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --camera 0 \
    --width 384 \
    --height 384

# With GPU (if available)
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --camera 0 \
    --gpu

# With bilateral filtering
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model /tmp/midas_small.onnx \
    --camera 0 \
    --filter
```

Expected output:
```
Depth estimator initialized successfully
Model loaded successfully from: /tmp/midas_small.onnx
Input size: 256x256
Using CPU backend for inference
Processing camera stream: 0
Press 'q' to quit
Inference time: 65.3 ms, FPS: 15.32
Inference time: 63.8 ms, FPS: 15.67
...
```

### Step 3: Test with ROS2 Node

#### Start the Depth Estimation Node
```bash
# Source workspace
source ~/ros2_ws/install/setup.bash

# Run the node
ros2 run image2depth depth_estimation_node
```

#### Publish Test Images
In another terminal:
```bash
# Install image publisher if needed
sudo apt install ros-${ROS_DISTRO}-image-publisher

# Publish an image
ros2 run image_publisher image_publisher_node test_image.jpg \
    --ros-args -r image_raw:=/camera/image_raw
```

#### View Depth Output
In another terminal:
```bash
# Install rqt_image_view if needed
sudo apt install ros-${ROS_DISTRO}-rqt-image-view

# View the depth map
ros2 run rqt_image_view rqt_image_view /depth/image
```

#### Test with Camera
```bash
# Install usb_cam if needed
sudo apt install ros-${ROS_DISTRO}-usb-cam

# Start camera node
ros2 run usb_cam usb_cam_node_exe \
    --ros-args -r image_raw:=/camera/image_raw

# In another terminal, start depth estimation
ros2 run image2depth depth_estimation_node

# In another terminal, view results
ros2 run rqt_image_view rqt_image_view /depth/image
```

### Step 4: Test with Launch File

```bash
# Using default parameters
ros2 launch image2depth depth_estimation.launch.py

# With custom parameters
ros2 launch image2depth depth_estimation.launch.py \
    model_path:=/tmp/midas_small.onnx \
    input_topic:=/camera/image_raw \
    output_topic:=/depth/image \
    input_width:=256 \
    input_height:=256 \
    verbose:=true
```

### Step 5: Performance Verification

Monitor the node's performance:

```bash
# Check topics
ros2 topic list
# Should see /depth/image

# Check topic info
ros2 topic info /depth/image

# Monitor publishing rate
ros2 topic hz /depth/image
# Should see ~10-20 Hz on Steam Deck

# View node info
ros2 node info /depth_estimation_node
```

## Performance Expectations

### On Steam Deck (AMD APU)

| Configuration | Input Size | Expected FPS | Notes |
|--------------|------------|--------------|-------|
| Fast | 256x256 | 15-20 FPS | Recommended for real-time |
| Balanced | 384x384 | 10-15 FPS | Good speed/quality tradeoff |
| Quality | 384x384 + filter | 8-12 FPS | Best quality |

### Optimization Tips

1. **Use smaller input size**: 256x256 instead of 384x384
2. **Disable bilateral filter**: Save 2-3 ms per frame
3. **Use ONNX Runtime**: 20-30% performance improvement
4. **Model quantization**: Convert model to INT8 (requires custom conversion)
5. **Reduce input frame rate**: Process every 2nd or 3rd frame

## Integration with Main Package

### Example: Subscribing to Depth in Paint Controller

Add to your main node:

```cpp
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>

class PaintController : public rclcpp::Node {
private:
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr depth_subscription_;
    
    void setupDepthSubscription() {
        depth_subscription_ = this->create_subscription<sensor_msgs::msg::Image>(
            "/depth/image", 10,
            std::bind(&PaintController::depthCallback, this, std::placeholders::_1));
    }
    
    void depthCallback(const sensor_msgs::msg::Image::SharedPtr msg) {
        try {
            // Convert to OpenCV
            cv_bridge::CvImagePtr cv_ptr = cv_bridge::toCvCopy(msg);
            cv::Mat depth_map = cv_ptr->image;
            
            // Use depth information
            // Example: Check if object is within safe distance
            double min_depth;
            cv::minMaxLoc(depth_map, &min_depth, nullptr);
            
            if (min_depth < threshold_) {
                RCLCPP_WARN(this->get_logger(), "Object too close!");
                // Take action...
            }
        } catch (cv_bridge::Exception& e) {
            RCLCPP_ERROR(this->get_logger(), "cv_bridge exception: %s", e.what());
        }
    }
};
```

### Add Dependency to main package.xml

```xml
<depend>image2depth</depend>
```

## Common Issues and Solutions

### Low FPS
**Problem**: Getting less than 10 FPS on Steam Deck  
**Solutions**:
- Reduce input size to 256x256
- Disable bilateral filter
- Check CPU usage (`htop`)
- Ensure no other heavy processes running

### Model Loading Failed
**Problem**: "Failed to load model"  
**Solutions**:
- Verify model path is correct
- Check model is in ONNX format
- Ensure OpenCV is built with DNN support
- Try re-downloading/re-converting the model

### No Depth Output
**Problem**: Node running but no depth images published  
**Solutions**:
- Check input topic has images: `ros2 topic echo /camera/image_raw`
- Verify topic names match
- Check node logs for errors
- Ensure model is initialized correctly

### Poor Depth Quality
**Problem**: Depth maps look noisy or incorrect  
**Solutions**:
- Use larger input size (384x384)
- Enable bilateral filter
- Ensure good lighting conditions
- Try different model (MiDaS v2.1 instead of small)

## Next Steps

1. **Profile performance** on your Steam Deck
2. **Integrate with main application** using depth information
3. **Fine-tune parameters** for your specific use case
4. **Consider model optimization** (quantization, pruning)
5. **Implement temporal filtering** for smoother video results

## Resources

- [MiDaS Repository](https://github.com/isl-org/MiDaS)
- [OpenCV DNN Module](https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html)
- [ONNX Runtime](https://onnxruntime.ai/)
- [ROS2 Image Pipeline](https://index.ros.org/p/image_pipeline/)
