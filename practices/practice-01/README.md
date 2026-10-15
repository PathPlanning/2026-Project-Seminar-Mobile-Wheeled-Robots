# Практическая работа 1. Знакомство с ROS 2

Автор: Сорокина Анастасия
Вариант: 15 

# Сборка
cd ~/practices_ws
colcon build --symlink-install --packages-select draw_number
source install/setup.zsh

## Запуск
ros2 launch draw_number draw_number.launch.py

Ручная подготовка сцены не требуется. Launch-файл последовательно:
1. запускает turtlesim;
2. удаляет стандартную черепаху turtle1 (сервис /kill);
3. создаёт две черепахи digit_1 и digit_5 в стартовых точках цифр (сервис /spawn);
4. запускает два экземпляра узла draw_digit: draw_digit_1 и draw_digit_5.