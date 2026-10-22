import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_dir = get_package_share_directory('digits_webots')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, 'launch', 'digits_world.launch.py')
        )
    )

    linear = LaunchConfiguration('linear')
    angular = LaunchConfiguration('angular')

    twist = ['linear: {x: ', linear, '}, angular: {z: ', angular, '}']
    if os.environ.get('ROS_DISTRO') in ('rolling', 'jazzy', 'kilted'):
        msg_type = 'geometry_msgs/msg/TwistStamped'
        message = ['{header: auto, twist: {'] + twist + ['}}']
    else:
        msg_type = 'geometry_msgs/msg/Twist'
        message = ['{'] + twist + ['}']

    publisher = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '-r', '10', '/cmd_vel', msg_type, message],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('linear', default_value='0.2',
                              description='Linear velocity, m/s'),
        DeclareLaunchArgument('angular', default_value='0.1',
                              description='Angular velocity, rad/s'),
        simulation,
        publisher,
    ])

