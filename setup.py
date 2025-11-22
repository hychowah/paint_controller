from setuptools import setup

package_name = 'paint_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    # data_files=[
    #     ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
    #     ('share/' + package_name, ['package.xml']),
    # ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='c3spray_deck',
    maintainer_email='hychowah@gmail.com',
    description='A ROS 2 package for the paint controller node with a PySide6 UI',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'paint_controller = paint_controller.paint_controller:main',
            'winch_node = paint_controller.winch_node:main',
            'steam_deck_input_node = paint_controller.steam_input_node:main',
            'lidar_logger = paint_controller.lidar_logger:main',
            'network_scanner = network_scanner.network_scanner:main'
        ],
    },
)
