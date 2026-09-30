from launch import LaunchDescription
from launch.actions import ExecuteProcess, LogInfo, RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnProcessStart
from launch_ros.actions import Node

# Вариант 15 -> цифры 1 и 5. (x, y) - стартовая точка цифры: первая вершина
# ломаной в DIGITS (draw_digit.py). Слева цифра 1, справа цифра 5.
TURTLES = [
    {'name': 'digit_1', 'digit': 1, 'x': 2.6, 'y': 7.0},
    {'name': 'digit_5', 'digit': 5, 'x': 9.5, 'y': 8.5},
]


def generate_launch_description():
    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
    )

    # Удаляем стандартную черепаху
    kill_turtle = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/kill', 'turtlesim/srv/Kill',
             '{name: turtle1}'],
        output='screen',
    )

    # Создаём новые черепахи в стартовых точках цифр
    spawns = [
        ExecuteProcess(
            cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn',
                 f"{{x: {t['x']}, y: {t['y']}, theta: 0.0, name: '{t['name']}'}}"],
            output='screen',
        )
        for t in TURTLES
    ]

    # Два экземпляра одной программы с разными параметрами
    drawers = [
        Node(
            package='draw_number',
            executable='draw_digit',
            name=f"draw_digit_{t['digit']}",
            parameters=[{'turtle': t['name'], 'digit': t['digit']}],
            output='screen',
        )
        for t in TURTLES
    ]

    # Цепочка: turtlesim -> kill -> spawn 1 -> spawn 2 -> узлы рисования
    handlers = [
        RegisterEventHandler(OnProcessStart(
            target_action=turtlesim,
            on_start=[LogInfo(msg='turtlesim запущен, убираем turtle1'), kill_turtle],
        )),
    ]
    steps = [kill_turtle] + spawns
    for prev, nxt in zip(steps, steps[1:]):
        handlers.append(RegisterEventHandler(OnProcessExit(
            target_action=prev,
            on_exit=[nxt],
        )))
    handlers.append(RegisterEventHandler(OnProcessExit(
        target_action=spawns[-1],
        on_exit=[LogInfo(msg='Черепахи созданы, запускаем рисование')] + drawers,
    )))

    return LaunchDescription([turtlesim] + handlers)
