cmake_minimum_required(VERSION 3.8)
project(paint_controller_ros2)

# find dependencies
find_package(ament_cmake REQUIRED)

# Install directories
install(DIRECTORY
  python/paint_controller/qml/
  DESTINATION share/${PROJECT_NAME}/qml
)

install(DIRECTORY
  resource/
  DESTINATION share/${PROJECT_NAME}/resource
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
