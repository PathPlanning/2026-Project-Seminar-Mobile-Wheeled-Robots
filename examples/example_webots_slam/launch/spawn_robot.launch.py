import os
import math
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
    TimerAction,
)
from launch_ros.event_handlers import OnStateTransition
from launch.conditions import IfCondition
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions.path_join_substitution import PathJoinSubstitution
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
import launch
from ament_index_python.packages import get_package_share_directory
from webots_ros2_driver.webots_launcher import WebotsLauncher
from webots_ros2_driver.webots_controller import WebotsController
from webots_ros2_driver.wait_for_controller_connection import (
    WaitForControllerConnection,
)
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    webots_turtlebot_package_dir = get_package_share_directory(
        "webots_ros2_turtlebot"
    )
    package_dir = get_package_share_directory("example_webots_slam")

    scene = "three_boxes"
    slam_toolbox_dir = get_package_share_directory("slam_toolbox")

    world = PythonExpression(["'", scene, ".wbt'"])
    mode = LaunchConfiguration("mode")
    use_rviz = LaunchConfiguration("use_rviz")
    use_sim_time = LaunchConfiguration("use_sim_time", default=True)

    slam_params_file = os.path.join(
        package_dir, "config", "slam_toolbox_params.yaml"
    )


    webots = WebotsLauncher(
        world=PathJoinSubstitution([package_dir, "worlds", world]),
        mode=mode,
        ros2_supervisor=False,
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", os.path.join(package_dir, "rviz", "config.rviz")],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": '<robot name=""><link name="base_link"/></robot>'
            }
        ],
    )

    footprint_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="screen",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_footprint"],
    )

    world_publisher = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="screen",
        arguments=[
            "1",
            "0",
            "0",
            "1.5707963267948966",
            "0",
            "0",
            "world",
            "map",
        ],
    )

    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "yaml_filename": PathJoinSubstitution(
                    [
                        package_dir,
                        "maps",
                        PythonExpression(["'", scene, ".yaml'"]),
                    ]
                ),
                "topic_name": "reference_map",
                "frame_id": "world",
            }
        ],
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_toolbox_dir, "launch", "online_async_launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "slam_params_file": slam_params_file,
            "use_lifecycle_manager": "true",
        }.items(),
    )

    lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["map_server", "slam_toolbox"],
            }
        ],
    )

    supervisor_driver = WebotsController(
        robot_name="ground_truth_supervisor",
        parameters=[
            {
                "robot_description": os.path.join(
                    package_dir, "urdf", "ground_truth_supervisor.urdf"
                ),
                "use_sim_time": use_sim_time,
            }
        ],
        respawn=True,
    )

    # ROS control spawners
    controller_manager_timeout = ["--controller-manager-timeout", "50"]

    diffdrive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "diffdrive_controller",
            "--controller-ros-args=-p diffdrive_controller:wheel_separation_multiplier:=1.1",
        ]
        + controller_manager_timeout,
    )
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=["joint_state_broadcaster"] + controller_manager_timeout,
    )
    ros_control_spawners = [
        diffdrive_controller_spawner,
        joint_state_broadcaster_spawner,
    ]

    robot_description_path = os.path.join(
        webots_turtlebot_package_dir, "resource", "turtlebot_webots.urdf"
    )
    ros2_control_params = os.path.join(
        webots_turtlebot_package_dir, "resource", "ros2control.yml"
    )
    turtlebot_driver = WebotsController(
        robot_name="TurtleBot3Burger",
        parameters=[
            {
                "robot_description": robot_description_path,
                "use_sim_time": use_sim_time,
                "set_robot_state_publisher": True,
            },
            ros2_control_params,
        ],
        remappings=[
            ("/diffdrive_controller/cmd_vel", "/cmd_vel"),
            ("/diffdrive_controller/odom", "/odom"),
        ],
        respawn=True,
    )

    velocity_publisher = ExecuteProcess(
        cmd=[
            "ros2",
            "topic",
            "pub",
            "--use-sim-time",
            "--rate",
            "10",
            "/cmd_vel",
            "geometry_msgs/msg/TwistStamped",
            "{header: {stamp: now, frame_id: base_link}, "
            "twist: {linear: {x: 0.2}, angular: {z: 0.2}}}",
        ],
        output="screen",
    )

    # Wait for the simulation to be ready to start control nodes
    waiting_nodes = WaitForControllerConnection(
        target_driver=turtlebot_driver, nodes_to_start=ros_control_spawners
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "mode",
                default_value="realtime",
                description="Webots startup mode",
            ),
            DeclareLaunchArgument(
                "use_rviz",
                default_value="true",
                description="Start RViz with the localization configuration",
            ),
            webots,
            robot_state_publisher,
            world_publisher,
            footprint_publisher,
            map_server,
            slam,
            lifecycle,
            supervisor_driver,
            turtlebot_driver,
            velocity_publisher,
            waiting_nodes,
            rviz,
            # This action will kill all nodes once the Webots simulation has exited
            launch.actions.RegisterEventHandler(
                event_handler=launch.event_handlers.OnProcessExit(
                    target_action=webots,
                    on_exit=[
                        launch.actions.EmitEvent(event=launch.events.Shutdown())
                    ],
                )
            ),
        ]
    )

    # return LaunchDescription(
    #     [
    #         DeclareLaunchArgument("mode", default_value="realtime"),
    #         DeclareLaunchArgument("use_sim_time", default_value="true"),
    #         DeclareLaunchArgument("use_rviz", default_value="true"),
    #         webots,
    #         world_to_map,
    #         footprint_publisher,
    #         robot_state_publisher,
    #         reference_map,
    #         reference_map_lifecycle,
    #         supervisor,
    #         turtlebot,
    #         wait_for_robot,
    #         slam,
    #         velocity,
    #         rviz,
    #         RegisterEventHandler(
    #             OnProcessExit(
    #                 target_action=webots,
    #                 on_exit=[EmitEvent(event=Shutdown())],
    #             )
    #         ),
    #     ]
    # )
