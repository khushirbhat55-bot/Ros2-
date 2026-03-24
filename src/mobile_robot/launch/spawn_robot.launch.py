import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_mobile_robot = get_package_share_directory('mobile_robot')

    world_file  = '/home/khushi/ws_mobile/worlds/my_world.sdf'
    xacro_file  = os.path.join(pkg_mobile_robot, 'model', 'robot.xacro')
    bridge_yaml = os.path.join(pkg_mobile_robot, 'parameters', 'bridge_parameters.yaml')

    x_arg   = DeclareLaunchArgument('x',   default_value='0.0')
    y_arg   = DeclareLaunchArgument('y',   default_value='0.0')
    z_arg   = DeclareLaunchArgument('z',   default_value='0.1')
    yaw_arg = DeclareLaunchArgument('yaw', default_value='0.0')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str
    )

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_file],
        output='screen'
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-name',  'moving_car',
            '-topic', 'robot_description',
            '-x',     LaunchConfiguration('x'),
            '-y',     LaunchConfiguration('y'),
            '-z',     LaunchConfiguration('z'),
            '-Y',     LaunchConfiguration('yaw'),
        ]
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{'config_file': bridge_yaml, 'use_sim_time': True}]
    )

    return LaunchDescription([
        x_arg, y_arg, z_arg, yaw_arg,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        bridge,
    ])
