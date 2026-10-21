import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource


LINEAR_X = 0.2
ANGULAR_Z = 0.08


def generate_launch_description():
    package_dir = get_package_share_directory('practice_02')

    spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_dir, 'launch', 'spawn_robot.launch.py')
        )
    )

    use_twist_stamped = os.environ.get('ROS_DISTRO') in ['rolling', 'jazzy', 'kilted']
    if use_twist_stamped:
        msg_type = 'geometry_msgs/msg/TwistStamped'
        msg = ("{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'base_link'}, "
               "twist: {linear: {x: %s}, angular: {z: %s}}}" % (LINEAR_X, ANGULAR_Z))
        extra = []
    else:
        msg_type = 'geometry_msgs/msg/Twist'
        msg = '{linear: {x: %s}, angular: {z: %s}}' % (LINEAR_X, ANGULAR_Z)
        extra = []

    publish_cmd = ExecuteProcess(
        cmd=['ros2', 'topic', 'pub', '-r', '10', *extra, '/cmd_vel', msg_type, msg],
        output='screen',
    )

    return LaunchDescription([
        spawn,
        TimerAction(period=15.0, actions=[publish_cmd]),
    ])
