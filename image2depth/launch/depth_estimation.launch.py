from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """
    Launch file for depth estimation node
    
    This launch file starts the depth estimation node with configurable parameters.
    """
    
    # Declare launch arguments
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='~/.local/share/image2depth/models/midas_small.onnx',
        description='Path to ONNX depth estimation model'
    )
    
    input_topic_arg = DeclareLaunchArgument(
        'input_topic',
        default_value='/camera/image_raw',
        description='Input image topic'
    )
    
    output_topic_arg = DeclareLaunchArgument(
        'output_topic',
        default_value='/depth/image',
        description='Output depth map topic'
    )
    
    input_width_arg = DeclareLaunchArgument(
        'input_width',
        default_value='384',
        description='Model input width in pixels'
    )
    
    input_height_arg = DeclareLaunchArgument(
        'input_height',
        default_value='384',
        description='Model input height in pixels'
    )
    
    max_input_dimension_arg = DeclareLaunchArgument(
        'max_input_dimension',
        default_value='1280',
        description='Max input dimension for auto-scaling (0=disable)'
    )
    
    use_gpu_arg = DeclareLaunchArgument(
        'use_gpu',
        default_value='false',
        description='Use GPU acceleration if available'
    )
    
    apply_bilateral_filter_arg = DeclareLaunchArgument(
        'apply_bilateral_filter',
        default_value='false',
        description='Apply bilateral filter for smoother results'
    )
    
    verbose_arg = DeclareLaunchArgument(
        'verbose',
        default_value='true',
        description='Print performance metrics'
    )
    
    # Create depth estimation node
    depth_estimation_node = Node(
        package='image2depth',
        executable='depth_estimation_node',
        name='depth_estimation_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'input_topic': LaunchConfiguration('input_topic'),
            'output_topic': LaunchConfiguration('output_topic'),
            'input_width': LaunchConfiguration('input_width'),
            'input_height': LaunchConfiguration('input_height'),
            'max_input_dimension': LaunchConfiguration('max_input_dimension'),
            'use_gpu': LaunchConfiguration('use_gpu'),
            'apply_bilateral_filter': LaunchConfiguration('apply_bilateral_filter'),
            'verbose': LaunchConfiguration('verbose'),
        }]
    )
    
    return LaunchDescription([
        model_path_arg,
        input_topic_arg,
        output_topic_arg,
        input_width_arg,
        input_height_arg,
        max_input_dimension_arg,
        use_gpu_arg,
        apply_bilateral_filter_arg,
        verbose_arg,
        depth_estimation_node
    ])
