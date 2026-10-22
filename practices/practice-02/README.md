## Сборка (внутри докера)
cd practices_ws
colcon build --packages-select digits_webots
source install/setup.zsh

## Запуск
ros2 launch digits_webots drive_circle.launch.py
