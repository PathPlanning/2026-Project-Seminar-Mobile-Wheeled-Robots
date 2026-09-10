from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    TimerAction,
    LogInfo,
    RegisterEventHandler,
)
from launch_ros.actions import Node
from launch.event_handlers import OnProcessStart


def generate_launch_description():

    turtlesim = Node(
        package="turtlesim", executable="turtlesim_node", name="turtlesim"
    )

    kill_turtle = ExecuteProcess(
        cmd=[
            "ros2",
            "service",
            "call",
            "/kill",
            "turtlesim/srv/Kill",
            "{name: turtle1}",
        ],
        output="screen",
    )

    spawn_turtle = ExecuteProcess(
        cmd=[
            "ros2",
            "service",
            "call",
            "/spawn",
            "turtlesim/srv/Spawn",
            "{x: 2, y: 2, theta: 0.2, name: 'turtle2'}",
        ],
        output="screen",
    )

    nav = Node(
        package="example_turtlesim",
        executable="nav2goal",
        name="nav2goal",
        output="screen",
    )

    pub_goal = ExecuteProcess(
        cmd=[
            'ros2', 'topic', 'pub',
            '--once', 
            '-w', '1',
            '/turtle2/goal',
            'geometry_msgs/msg/Point',
            '{x: 2.0, y: 8.0, z: 0.0}',
        ],
        output='screen'
    )

    return LaunchDescription(
        [
            turtlesim,
            RegisterEventHandler(
                OnProcessStart(
                    target_action=turtlesim,
                    on_start=[
                        LogInfo(msg="Turtlesim started, spawning turtle"),
                        kill_turtle,
                        spawn_turtle,
                        nav
                    ],
                )
            ),
            TimerAction(period=1.0, actions=[LogInfo(msg="Publish goal"), pub_goal]),
        ]
    )