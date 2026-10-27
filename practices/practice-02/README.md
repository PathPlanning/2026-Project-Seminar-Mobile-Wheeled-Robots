# Практическая работа 2. TurtleBot3 в Webots

ROS2-пакет `practice_02`: площадка 8 × 8 м с числом 15 в центре (PROTO-файлы `Digit1.proto` и `Digit5.proto`) и робот TurtleBot3 Burger, который едет по окружности вокруг цифр.


## Сборка

Внутри контейнера:

```bash
cd ~/practices_ws
colcon build --packages-select practice_02 --symlink-install
source install/setup.zsh
```

## Запуск симуляции

На Mac предварительно запущен сервер Webots (`python3 local_simulation_server.py`,). Затем внутри контейнера:

```bash
ros2 launch practice_02 spawn_robot.launch.py
```

Откроется Webots со сценой.
