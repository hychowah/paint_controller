from setuptools import setup

package_name = 'paint_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='A ROS 2 package for the paint controller node with a PySide6 UI',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'paint_controller = paint_controller.paint_controller:main',
            'winch_node = paint_controller.winch_node:main',
            'joystick_node = paint_controller.joystick_control_node:main',
            'lidar_logger = paint_controller.lidar_logger:main'
        ],
    },
)
