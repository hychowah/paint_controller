#!/bin/bash

# Source ROS2 environment
source /opt/ros/humble/setup.bash

# Export ROS domain ID if you're using one
# export ROS_DOMAIN_ID=<your_domain_id>

# Run with sudo while preserving environment
sudo --preserve-env=PYTHONPATH,LD_LIBRARY_PATH,ROS_DISTRO,ROS_VERSION,ROS_PYTHON_VERSION,ROS_PACKAGE_PATH,AMENT_PREFIX_PATH,CMAKE_PREFIX_PATH,COLCON_PREFIX_PATH,ROS_ETC_DIR,ROS_ROOT,ROS_LOCALHOST_ONLY,ROS_NAMESPACE,ROS_DOMAIN_ID \
    python3 network_scanner.py  