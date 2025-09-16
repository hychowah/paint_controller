cmake_minimum_required(VERSION 3.8)
project(paint_controller_ros2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)

# Qt5 dependencies
find_package(Qt5 REQUIRED COMPONENTS Core Widgets Quick Qml)

# GStreamer dependencies
find_package(PkgConfig REQUIRED)
pkg_check_modules(GSTREAMER REQUIRED gstreamer-1.0)
pkg_check_modules(GSTREAMER_APP REQUIRED gstreamer-app-1.0)

# Include directories
include_directories(include)
include_directories(${GSTREAMER_INCLUDE_DIRS})

# Create executable
add_executable(paint_controller_cpp
  src/paint_controller.cpp
  include/paint_controller/paint_controller.hpp
)

# Set up Qt5 for MOC
set_target_properties(paint_controller_cpp PROPERTIES
    AUTOMOC ON
    AUTORCC ON
    AUTOUIC ON
)

# Target dependencies
ament_target_dependencies(paint_controller_cpp
  rclcpp
  std_msgs
  sensor_msgs
)

# Link Qt5 libraries
target_link_libraries(paint_controller_cpp
  Qt5::Core
  Qt5::Widgets
  Qt5::Quick
  Qt5::Qml
  ${GSTREAMER_LIBRARIES}
  ${GSTREAMER_APP_LIBRARIES}
)

# Install targets
install(TARGETS
  paint_controller_cpp
  DESTINATION lib/${PROJECT_NAME}
)

# Install directories
install(DIRECTORY
  paint_controller/qml/
  DESTINATION share/${PROJECT_NAME}/qml
)

install(DIRECTORY
  paint_controller/resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
