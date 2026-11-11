import math
import os

import launch
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions.path_join_substitution import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from webots_ros2_driver.wait_for_controller_connection import WaitForControllerConnection
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher


def default_results_dir():
    source_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if os.path.exists(os.path.join(source_dir, 'setup.py')):
        return os.path.join(source_dir, 'results')
    return os.path.join(os.getcwd(), 'results')


def generate_launch_description():
    webots_turtlebot_package_dir = get_package_share_directory('webots_ros2_turtlebot')
    package_dir = get_package_share_directory('practice_03_odometry')

    world = LaunchConfiguration('world')
    mode = LaunchConfiguration('mode')
    use_sim_time = True

    world_path = PathJoinSubstitution([package_dir, 'worlds', world])

    webots = WebotsLauncher(
        world=world_path,
        mode=mode,
        ros2_supervisor=False
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': '<robot name=""><link name=""/></robot>'
        }],
    )

    footprint_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
    )

    map_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        output='screen',
        arguments=[
            '--x', '1', '--y', '0', '--z', '0',
            '--yaw', str(math.pi / 2), '--pitch', '0', '--roll', '0',
            '--frame-id', 'map', '--child-frame-id', 'odom',
        ],
    )

    supervisor_driver = WebotsController(
        robot_name='ground_truth_supervisor',
        parameters=[{
            'robot_description': os.path.join(
                package_dir, 'resource', 'ground_truth_supervisor.urdf'
            ),
            'use_sim_time': use_sim_time,
        }],
        respawn=True,
    )

    controller_manager_timeout = ['--controller-manager-timeout', '50']

    diffdrive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=[
            'diffdrive_controller',
            [
                '--controller-ros-args=-p '
                'diffdrive_controller:wheel_separation_multiplier:=',
                LaunchConfiguration('wheel_separation_multiplier'),
            ],
        ] + controller_manager_timeout,
    )
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['joint_state_broadcaster'] + controller_manager_timeout,
    )

    robot_description_path = os.path.join(
        webots_turtlebot_package_dir, 'resource', 'turtlebot_webots.urdf')
    ros2_control_params = os.path.join(
        webots_turtlebot_package_dir, 'resource', 'ros2control.yml')
    turtlebot_driver = WebotsController(
        robot_name='TurtleBot3Burger',
        parameters=[
            {'robot_description': robot_description_path,
             'use_sim_time': use_sim_time,
             'set_robot_state_publisher': True},
            ros2_control_params
        ],
        remappings=[
            ('/diffdrive_controller/cmd_vel', '/cmd_vel'),
            ('/diffdrive_controller/odom', '/odom'),
        ],
        respawn=True
    )

    velocity_publisher = Node(
        package='practice_03_odometry',
        executable='cmd_vel_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'linear_x': ParameterValue(LaunchConfiguration('linear_x'), value_type=float),
            'angular_z': ParameterValue(LaunchConfiguration('angular_z'), value_type=float),
            'rate': 10.0,
        }],
    )

    recorder = Node(
        package='practice_03_odometry',
        executable='odometry_recorder',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'duration': ParameterValue(LaunchConfiguration('duration'), value_type=float),
            'sample_period': 0.1,
            'results_dir': ParameterValue(LaunchConfiguration('results_dir'), value_type=str),
            'world_file': ParameterValue(world_path, value_type=str),
        }],
    )

    ros_control_spawners = [diffdrive_controller_spawner, joint_state_broadcaster_spawner]

    waiting_nodes = WaitForControllerConnection(
        target_driver=turtlebot_driver,
        nodes_to_start=ros_control_spawners
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='world_noise_0_1.wbt',
            description='Scene from the worlds directory: world_noise_0.wbt, '
                        'world_noise_0_02.wbt or world_noise_0_1.wbt'
        ),
        DeclareLaunchArgument(
            'mode',
            default_value='realtime',
            description='Webots startup mode'
        ),
        DeclareLaunchArgument(
            'duration',
            default_value='130.0',
            description='Experiment duration in simulation seconds'
        ),
        DeclareLaunchArgument(
            'linear_x',
            default_value='0.2',
            description='Commanded linear velocity, m/s'
        ),
        DeclareLaunchArgument(
            'angular_z',
            default_value='0.2',
            description='Commanded angular velocity, rad/s'
        ),
        DeclareLaunchArgument(
            'wheel_separation_multiplier',
            default_value='1.1',
            description='diffdrive_controller wheel_separation_multiplier'
        ),
        DeclareLaunchArgument(
            'results_dir',
            default_value=default_results_dir(),
            description='Where to save plots and CSV files'
        ),
        webots,
        robot_state_publisher,
        footprint_publisher,
        map_publisher,
        supervisor_driver,
        turtlebot_driver,
        velocity_publisher,
        recorder,
        waiting_nodes,
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=recorder,
                on_exit=[
                    launch.actions.EmitEvent(event=launch.events.Shutdown())
                ],
            )
        ),
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=webots,
                on_exit=[
                    launch.actions.EmitEvent(event=launch.events.Shutdown())
                ],
            )
        ),
    ])

