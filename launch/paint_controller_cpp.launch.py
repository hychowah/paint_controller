#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='paint_controller_ros2',
            executable='paint_controller_cpp',
            name='paint_controller_cpp',
            output='screen',
            parameters=[
                {'use_sim_time': False}
            ]
        )
    ])
