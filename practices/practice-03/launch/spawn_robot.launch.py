import os
import math
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions.path_join_substitution import PathJoinSubstitution
from launch import LaunchDescription
from launch_ros.actions import Node
import launch
from ament_index_python.packages import get_package_share_directory
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.wait_for_controller_connection import WaitForControllerConnection


def generate_launch_description():
    webots_turtlebot_package_dir = get_package_share_directory('webots_ros2_turtlebot')
    package_dir = get_package_share_directory('practice_03')

    world = LaunchConfiguration('world')
    mode = LaunchConfiguration('mode')
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)

    webots = WebotsLauncher(
        world=PathJoinSubstitution([package_dir, 'worlds', world]),
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

    odometry_statistics = Node(
        package='practice_03',
        executable='odometry_statistics',
        name='odometry_statistics',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    # Match the initial pose of TURTLEBOT in worlds/my_world.wbt.
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

    # ROS control spawners
    controller_manager_timeout = ['--controller-manager-timeout', '50']

    diffdrive_controller_spawner = Node(
    package='controller_manager',
    executable='spawner',
    output='screen',
    arguments=[
        'diffdrive_controller',
        '--controller-ros-args=-p diffdrive_controller:wheel_separation_multiplier:=1.1',
    ] + controller_manager_timeout,
)
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        output='screen',
        arguments=['joint_state_broadcaster'] + controller_manager_timeout,
    )
    ros_control_spawners = [diffdrive_controller_spawner, joint_state_broadcaster_spawner]

    robot_description_path = os.path.join(webots_turtlebot_package_dir, 'resource', 'turtlebot_webots.urdf')
    ros2_control_params = os.path.join(webots_turtlebot_package_dir, 'resource', 'ros2control.yml')
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

    velocity_publisher = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub', '--use-sim-time',
            '--rate', '10', '/cmd_vel', 'geometry_msgs/msg/TwistStamped',
            '{header: {stamp: now, frame_id: base_link}, '
            'twist: {linear: {x: 0.2}, angular: {z: 0.2}}}',
        ],
        output='screen',
    )

    # Wait for the simulation to be ready to start control nodes
    waiting_nodes = WaitForControllerConnection(
        target_driver=turtlebot_driver,
        nodes_to_start=ros_control_spawners
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='my_world.wbt',
            description='Scene file from the package worlds directory'
        ),
        DeclareLaunchArgument(
            'mode',
            default_value='realtime',
            description='Webots startup mode'
        ),
        webots,
        robot_state_publisher,
        footprint_publisher,
        map_publisher,
        supervisor_driver,
        turtlebot_driver,
        velocity_publisher,
        waiting_nodes,
        odometry_statistics,
        # This action will kill all nodes once the Webots simulation has exited
        launch.actions.RegisterEventHandler(
            event_handler=launch.event_handlers.OnProcessExit(
                target_action=webots,
                on_exit=[
                    launch.actions.EmitEvent(event=launch.events.Shutdown())
                ],
            )
        ),
    ])
