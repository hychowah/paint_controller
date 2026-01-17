# Image2Depth Quick Start Guide

Get started with depth estimation in 5 minutes!

## Quick Install (Ubuntu 22.04/24.04 + ROS2)

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y libopencv-dev ros-${ROS_DISTRO}-cv-bridge

# 2. Build the package
cd ~/ros2_ws
colcon build --packages-select image2depth
source install/setup.bash

# 3. Get a model (requires manual conversion - see BUILD_AND_TEST.md)
# For now, we'll create a placeholder
echo "Model needs to be downloaded/converted - see BUILD_AND_TEST.md for instructions"
```

## Option 1: Quick Test with Image (No ROS2 required)

```bash
# Test with a static image
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --image your_image.jpg \
    --output depth_output.jpg
```

## Option 2: Quick Test with Camera (No ROS2 required)

```bash
# Test with webcam
./install/image2depth/lib/image2depth/depth_estimation_test \
    --model ~/.local/share/image2depth/models/midas_small.onnx \
    --camera 0
```

## Option 3: Run as ROS2 Node

```bash
# Terminal 1: Start depth estimation node
ros2 run image2depth depth_estimation_node

# Terminal 2: Publish test images or start camera
ros2 run usb_cam usb_cam_node_exe --ros-args -r image_raw:=/camera/image_raw

# Terminal 3: View depth output
ros2 run rqt_image_view rqt_image_view /depth/image
```

## Getting the Model

You need a MiDaS ONNX model. See `BUILD_AND_TEST.md` for detailed instructions on:
1. Converting PyTorch models to ONNX
2. Finding pre-converted models
3. Alternative models (Depth-Anything, FastDepth)

## Expected Performance on Steam Deck

- **256x256 input**: ~15-20 FPS ✓ Recommended
- **384x384 input**: ~10-15 FPS
- **With filtering**: -2-3 FPS

## Need Help?

- See `README.md` for feature overview
- See `BUILD_AND_TEST.md` for detailed build/test instructions
- Check Issues on GitHub
