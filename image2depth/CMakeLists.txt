cmake_minimum_required(VERSION 3.8)
project(image2depth)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Set environment to avoid snap library conflicts
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu")

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(cv_bridge REQUIRED)

# OpenCV
find_package(OpenCV REQUIRED)

# ONNX Runtime
find_package(PkgConfig REQUIRED)
pkg_check_modules(ONNXRUNTIME onnxruntime)

# Include directories
include_directories(
  include
  ${OpenCV_INCLUDE_DIRS}
)

if(ONNXRUNTIME_FOUND)
  include_directories(${ONNXRUNTIME_INCLUDE_DIRS})
  add_definitions(-DUSE_ONNXRUNTIME)
  message(STATUS "ONNX Runtime found - will use for optimized inference")
else()
  message(WARNING "ONNX Runtime not found - will use OpenCV DNN (may be slower)")
endif()

# Depth estimation node library
add_library(depth_estimator_lib
  src/depth_estimator.cpp
)

ament_target_dependencies(depth_estimator_lib
  rclcpp
  sensor_msgs
  std_msgs
  cv_bridge
)

target_link_libraries(depth_estimator_lib
  ${OpenCV_LIBRARIES}
)

if(ONNXRUNTIME_FOUND)
  target_link_libraries(depth_estimator_lib ${ONNXRUNTIME_LIBRARIES})
endif()

# Depth estimation ROS2 node
add_executable(depth_estimation_node
  src/depth_estimation_node.cpp
)

ament_target_dependencies(depth_estimation_node
  rclcpp
  sensor_msgs
  std_msgs
  cv_bridge
)

target_link_libraries(depth_estimation_node
  depth_estimator_lib
  ${OpenCV_LIBRARIES}
)

if(ONNXRUNTIME_FOUND)
  target_link_libraries(depth_estimation_node ${ONNXRUNTIME_LIBRARIES})
endif()

# Standalone test executable (for testing without ROS)
add_executable(depth_estimation_test
  src/depth_estimation_test.cpp
)

target_link_libraries(depth_estimation_test
  depth_estimator_lib
  ${OpenCV_LIBRARIES}
)

if(ONNXRUNTIME_FOUND)
  target_link_libraries(depth_estimation_test ${ONNXRUNTIME_LIBRARIES})
endif()

# Install targets
install(TARGETS
  depth_estimator_lib
  depth_estimation_node
  depth_estimation_test
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

# Install header files
install(DIRECTORY include/
  DESTINATION include
)

# Install config and launch files
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
