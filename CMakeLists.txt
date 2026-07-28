cmake_minimum_required(VERSION 3.8)
project(paint_controller_ros2)

# find dependencies
find_package(ament_cmake REQUIRED)

# Intentionally installs no payload: the app runs from the source tree
# (bash launcher + venv), and nothing reads share/${PROJECT_NAME}/.
# Do not re-add install() stanzas without a real install-space consumer.

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
