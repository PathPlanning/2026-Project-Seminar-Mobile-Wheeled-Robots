from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim'
    )

    kill_turtle = ExecuteProcess(
        cmd=[
            'ros2', 'service', 'call',
            '/kill',
            'turtlesim/srv/Kill',
            '{name: turtle1}'
        ],
        output='screen'
    )

    spawn_zero = ExecuteProcess(
        cmd=[
            'ros2', 'service', 'call',
            '/spawn',
            'turtlesim/srv/Spawn',
            '{x: 3.0, y: 3.0, theta: 0.0, name: turtle_0}'
        ],
        output='screen'
    )

    spawn_seven = ExecuteProcess(
        cmd=[
            'ros2', 'service', 'call',
            '/spawn',
            'turtlesim/srv/Spawn',
            '{x: 7.0, y: 7.0, theta: 0.0, name: turtle_7}'
        ],
        output='screen'
    )

    zero_controller = Node(
        package='digit_drawer',
        executable='digit_drawer',
        name='digit_drawer_0',
        parameters=[
            {
                'turtle_name': 'turtle_0',
                'digit': 0
            }
        ]
    )

    seven_controller = Node(
        package='digit_drawer',
        executable='digit_drawer',
        name='digit_drawer_7',
        parameters=[
            {
                'turtle_name': 'turtle_7',
                'digit': 7
            }
        ]
    )

    return LaunchDescription([
        turtlesim,

        TimerAction(
            period=2.0,
            actions=[kill_turtle]
        ),

        TimerAction(
            period=3.0,
            actions=[spawn_zero, spawn_seven]
        ),

        TimerAction(
            period=4.0,
            actions=[
                zero_controller,
                seven_controller
            ]
        )
    ])

