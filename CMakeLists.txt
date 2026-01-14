cmake_minimum_required(VERSION 3.8)
project(paint_controller_ros2)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Set environment to avoid snap library conflicts
set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)
set(CMAKE_INSTALL_RPATH "/lib/x86_64-linux-gnu:/usr/lib/x86_64-linux-gnu")

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

# HID API for Steam Deck support
pkg_check_modules(HIDAPI REQUIRED hidapi-libusb)

# Include directories
include_directories(include)
include_directories(${GSTREAMER_INCLUDE_DIRS})
include_directories(${HIDAPI_INCLUDE_DIRS})

# Create executable
add_executable(paint_controller_cpp
  src/paint_controller.cpp
  src/steam_deck_handler.cpp
  include/paint_controller/paint_controller.hpp
  include/paint_controller/steam_deck_handler.hpp
)

# Create Steam Deck test executable
add_executable(steam_deck_test
  src/steam_deck_test.cpp
  src/steam_deck_handler.cpp
  include/paint_controller/steam_deck_handler.hpp
)

# Set up Qt5 for MOC
set_target_properties(paint_controller_cpp PROPERTIES
    AUTOMOC ON
    AUTORCC ON
    AUTOUIC ON
)

set_target_properties(steam_deck_test PROPERTIES
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
  ${HIDAPI_LIBRARIES}
)

target_link_libraries(steam_deck_test
  Qt5::Core
  Qt5::Widgets
  ${HIDAPI_LIBRARIES}
)

# Install targets
install(TARGETS
  paint_controller_cpp
  steam_deck_test
  DESTINATION lib/${PROJECT_NAME}
)

# Install wrapper script
install(PROGRAMS
  scripts/paint_controller_wrapper.sh
  DESTINATION lib/${PROJECT_NAME}
  RENAME paint_controller_cpp_wrapper
)

# Install directories
install(DIRECTORY
  python/paint_controller/qml/
  DESTINATION share/${PROJECT_NAME}/qml
)

install(DIRECTORY
  resource/
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
