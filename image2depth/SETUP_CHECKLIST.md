# Setup and Testing Checklist

Use this checklist to set up and test the image2depth module on your system.

## Prerequisites Setup

### Step 1: Install System Dependencies
- [ ] Ubuntu 22.04 or 24.04 installed
- [ ] ROS2 (Humble or Jazzy) installed and sourced
  ```bash
  source /opt/ros/${ROS_DISTRO}/setup.bash
  ```
- [ ] Install OpenCV
  ```bash
  sudo apt install libopencv-dev
  ```
- [ ] Install ROS2 packages
  ```bash
  sudo apt install ros-${ROS_DISTRO}-cv-bridge ros-${ROS_DISTRO}-sensor-msgs
  ```

### Step 2: Verify Dependencies
- [ ] OpenCV installed correctly
  ```bash
  pkg-config --modversion opencv4  # Should show 4.x.x
  ```
- [ ] ROS2 workspace exists
  ```bash
  ls ~/ros2_ws/src  # Should show paint_controller_ros2
  ```

## Building

### Step 3: Build the Module
- [ ] Navigate to workspace
  ```bash
  cd ~/ros2_ws
  ```
- [ ] Build image2depth
  ```bash
  colcon build --packages-select image2depth
  ```
- [ ] Source the workspace
  ```bash
  source install/setup.bash
  ```
- [ ] Verify executables exist
  ```bash
  ls install/image2depth/lib/image2depth/
  # Should show: depth_estimation_node, depth_estimation_test
  ```

## Model Setup

### Step 4: Get a Depth Model

Choose ONE of these options:

#### Option A: Use Python Conversion Script (Recommended)
- [ ] Install PyTorch
  ```bash
  pip install torch torchvision
  ```
- [ ] Run conversion script
  ```bash
  cd ~/ros2_ws/src/paint_controller_ros2/image2depth
  ./convert_model.py --model small --output ~/.local/share/image2depth/models/midas_small.onnx --size 256
  ```
- [ ] Verify model exists
  ```bash
  ls -lh ~/.local/share/image2depth/models/midas_small.onnx
  ```

#### Option B: Use Bash Download Script
- [ ] Run download script
  ```bash
  cd ~/ros2_ws/src/paint_controller_ros2/image2depth
  ./download_model.sh
  ```
- [ ] Follow prompts to download/specify model URL

#### Option C: Manual Conversion
- [ ] Clone MiDaS repository
  ```bash
  git clone https://github.com/isl-org/MiDaS.git /tmp/MiDaS
  cd /tmp/MiDaS
  ```
- [ ] Follow MiDaS conversion instructions (see BUILD_AND_TEST.md)
- [ ] Copy converted model to `~/.local/share/image2depth/models/midas_small.onnx`

## Testing

### Step 5: Test Standalone Application

#### Test with Static Image
- [ ] Get a test image
  ```bash
  wget -O /tmp/test.jpg https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg
  ```
- [ ] Run depth estimation
  ```bash
  ./install/image2depth/lib/image2depth/depth_estimation_test \
      --model ~/.local/share/image2depth/models/midas_small.onnx \
      --image /tmp/test.jpg \
      --output /tmp/depth_output.jpg
  ```
- [ ] Verify output
  ```bash
  ls -lh /tmp/depth_output.jpg
  # View: xdg-open /tmp/depth_output.jpg
  ```

#### Test with Webcam
- [ ] Connect webcam (if using external camera)
- [ ] Run depth estimation
  ```bash
  ./install/image2depth/lib/image2depth/depth_estimation_test \
      --model ~/.local/share/image2depth/models/midas_small.onnx \
      --camera 0
  ```
- [ ] Verify windows open showing:
  - Input Frame (your camera feed)
  - Depth Map (depth estimation)
- [ ] Check FPS in console output
  - Should see: "Inference time: XX ms, FPS: XX"
  - Target: 10+ FPS
- [ ] Press 'q' to quit

### Step 6: Test ROS2 Node

#### Start Depth Node
- [ ] Open terminal 1
  ```bash
  source ~/ros2_ws/install/setup.bash
  ros2 run image2depth depth_estimation_node
  ```
- [ ] Verify initialization message
  - Should see: "Depth estimator initialized successfully"

#### Publish Test Images
- [ ] Open terminal 2
  ```bash
  source ~/ros2_ws/install/setup.bash
  # Install image publisher if needed
  sudo apt install ros-${ROS_DISTRO}-image-publisher
  
  # Publish test image
  ros2 run image_publisher image_publisher_node /tmp/test.jpg \
      --ros-args -r image_raw:=/camera/image_raw
  ```

#### View Depth Output
- [ ] Open terminal 3
  ```bash
  source ~/ros2_ws/install/setup.bash
  # Install image viewer if needed
  sudo apt install ros-${ROS_DISTRO}-rqt-image-view
  
  # View depth map
  ros2 run rqt_image_view rqt_image_view /depth/image
  ```
- [ ] Verify depth map is displayed

#### Test with Camera Stream
- [ ] Install usb_cam
  ```bash
  sudo apt install ros-${ROS_DISTRO}-usb-cam
  ```
- [ ] Start camera node (terminal 2)
  ```bash
  ros2 run usb_cam usb_cam_node_exe \
      --ros-args -r image_raw:=/camera/image_raw
  ```
- [ ] Verify depth node is processing
  - Terminal 1 should show: "FPS: XX, Inference time: XX ms"
- [ ] Verify depth output in rqt_image_view (terminal 3)

### Step 7: Test Launch File
- [ ] Stop all previous nodes (Ctrl+C)
- [ ] Launch with default parameters
  ```bash
  ros2 launch image2depth depth_estimation.launch.py
  ```
- [ ] Launch with custom parameters
  ```bash
  ros2 launch image2depth depth_estimation.launch.py \
      model_path:=~/.local/share/image2depth/models/midas_small.onnx \
      input_width:=256 \
      input_height:=256 \
      verbose:=true
  ```

## Performance Verification

### Step 8: Measure Performance on Steam Deck
- [ ] Run standalone test with FPS monitoring
  ```bash
  ./install/image2depth/lib/image2depth/depth_estimation_test \
      --model ~/.local/share/image2depth/models/midas_small.onnx \
      --camera 0 \
      --width 256 \
      --height 256
  ```
- [ ] Record average FPS (should be 10+)
  - FPS: ______ (target: 15-20 for 256x256)
- [ ] Test with larger input
  ```bash
  ./install/image2depth/lib/image2depth/depth_estimation_test \
      --model ~/.local/share/image2depth/models/midas_small.onnx \
      --camera 0 \
      --width 384 \
      --height 384
  ```
- [ ] Record average FPS
  - FPS: ______ (target: 10-15 for 384x384)

### Step 9: Monitor Resource Usage
- [ ] Install htop if needed
  ```bash
  sudo apt install htop
  ```
- [ ] Run depth estimation in one terminal
- [ ] Run htop in another terminal
- [ ] Record metrics:
  - CPU usage: ______%
  - Memory usage: ______ MB
  - Temperature: ______ °C (if available)

## Troubleshooting

### Common Issues

#### Build Fails
- [ ] OpenCV not found
  - Solution: `sudo apt install libopencv-dev`
- [ ] cv_bridge not found
  - Solution: `sudo apt install ros-${ROS_DISTRO}-cv-bridge`
- [ ] Missing dependencies
  - Solution: See BUILD_AND_TEST.md, "Troubleshooting Build Issues"

#### Model Issues
- [ ] Model not found
  - Solution: Verify path with `ls ~/.local/share/image2depth/models/midas_small.onnx`
- [ ] Model loading fails
  - Solution: Try re-converting or use different model

#### Performance Issues
- [ ] FPS < 10
  - Try: Reduce input size to 256x256
  - Try: Disable bilateral filter
  - Try: Close other applications
  - Check: CPU throttling (Steam Deck power mode)

#### ROS2 Issues
- [ ] No depth output
  - Check: Input topic has data (`ros2 topic echo /camera/image_raw`)
  - Check: Node logs for errors
  - Verify: Topic names match

## Integration Planning

### Step 10: Plan Integration
- [ ] Determine use case for depth information
  - [ ] Collision avoidance
  - [ ] 3D painting
  - [ ] Object detection
  - [ ] Other: _______________
- [ ] Review integration example in IMPLEMENTATION_SUMMARY.md
- [ ] Add dependency to main package.xml if needed
  ```xml
  <depend>image2depth</depend>
  ```
- [ ] Implement depth subscription in main node

## Completion

### Checklist Summary
- [ ] All prerequisites installed
- [ ] Module builds successfully
- [ ] Model obtained and working
- [ ] Standalone test passes
- [ ] ROS2 node works
- [ ] Performance targets met (10+ FPS)
- [ ] Ready for integration

## Notes

Record any issues, observations, or customizations here:

_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________

## Next Steps

After completing this checklist:
1. Review IMPLEMENTATION_SUMMARY.md for integration details
2. Integrate depth estimation into main paint_controller
3. Test integrated system on Steam Deck
4. Optimize parameters for your specific use case

## Support

If you encounter issues:
- Check BUILD_AND_TEST.md for detailed troubleshooting
- Review code comments in source files
- Check GitHub Issues
- Consult MiDaS/OpenCV documentation
