import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from webots_ros2_driver.wait_for_controller_connection import WaitForControllerConnection
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.webots_launcher import WebotsLauncher


def generate_launch_description():
    package_dir = get_package_share_directory('digits_webots')
    turtlebot_dir = get_package_share_directory('webots_ros2_turtlebot')

    world = LaunchConfiguration('world')
    mode = LaunchConfiguration('mode')
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)

    webots = WebotsLauncher(
        world=PathJoinSubstitution([package_dir, 'worlds', world]),
        mode=mode,
        ros2_supervisor=True,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': '<robot name=""><link name=""/></robot>'}],
    )

    footprint_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        output='screen',
        arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'base_footprint'],
    )

    robot_description_path = os.path.join(turtlebot_dir, 'resource', 'turtlebot_webots.urdf')
    ros2_control_params = os.path.join(turtlebot_dir, 'resource', 'ros2control.yml')

    timeout = ['--controller-manager-timeout', '50', '--param-file', ros2_control_params]
    ros_control_spawners = [
        Node(
            package='controller_manager',
            executable='spawner',
            output='screen',
            arguments=[name] + timeout,
            respawn=True,
            respawn_delay=2.0,
        )
        for name in ('diffdrive_controller', 'joint_state_broadcaster')
    ]

    use_twist_stamped = os.environ.get('ROS_DISTRO') in ('rolling', 'jazzy', 'kilted')
    cmd_vel_topic = 'cmd_vel' if use_twist_stamped else 'cmd_vel_unstamped'
    mappings = [
        ('/diffdrive_controller/' + cmd_vel_topic, '/cmd_vel'),
        ('/diffdrive_controller/odom', '/odom'),
    ]

    turtlebot_driver = WebotsController(
        robot_name='TurtleBot3Burger',
        parameters=[
            {
                'robot_description': robot_description_path,
                'use_sim_time': use_sim_time,
                'set_robot_state_publisher': True,
            },
            ros2_control_params,
        ],
        remappings=mappings,
        respawn=True,
    )

    waiting_nodes = WaitForControllerConnection(
        target_driver=turtlebot_driver,
        nodes_to_start=ros_control_spawners,
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value='digits_world.wbt',
            description='World file from the `worlds` directory of the package',
        ),
        DeclareLaunchArgument(
            'mode',
            default_value='realtime',
            description='Webots startup mode',
        ),
        webots,
        webots._supervisor,
        robot_state_publisher,
        footprint_publisher,
        turtlebot_driver,
        waiting_nodes,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=webots,
                on_exit=[EmitEvent(event=Shutdown())],
            )
        ),
    ])

