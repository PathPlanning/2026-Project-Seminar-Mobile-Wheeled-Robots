# Практическая работа №1 — Introduction to ROS2

## Вариант

07

## Описание

ROS2-пакет `digit_drawer` управляет двумя черепахами в `turtlesim` и рисует цифры варианта - `0` и `7`.

Для управления используется одна универсальная программа `digit_drawer.py`, которая запускается два раза с разными параметрами:

* `turtle_0` — рисует цифру `0`;
* `turtle_7` — рисует цифру `7`.

Положение черепахи отслеживается через топик `/turtle_name/pose`, а управление движением выполняется через `/turtle_name/cmd_vel`.

Завершение поворотов и прямолинейных участков определяется по данным о положении черепахи, а не по времени.

## Сборка

Из корня ROS2 workspace:

```bash
cd ~/practices_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select digit_drawer
source install/setup.bash
```

## Запуск

Запустить практическую работу:

```bash
ros2 launch digit_drawer digit_drawer.launch.py
```

После запуска автоматически:

1. запускается `turtlesim`;
2. удаляется стандартная `turtle1`;
3. создаются `turtle_0` и `turtle_7`;
4. запускаются два экземпляра контроллера;
5. черепахи рисуют цифры `0` и `7`.

После завершения рисования контроллеры продолжают работать и публикуют нулевую скорость.

## Диагностика ROS2

Список узлов:

```bash
ros2 node list
```

Список топиков:

```bash
ros2 topic list
```

Список сервисов:

```bash
ros2 service list
```

Для визуализации связей между узлами:

```bash
rqt_graph
```

## Структура пакета

```text
digit_drawer/
├── digit_drawer/
│   ├── __init__.py
│   └── digit_drawer.py
├── launch/
│   └── digit_drawer.launch.py
├── resource/
│   └── digit_drawer
├── test/
│   ├── test_copyright.py
│   ├── test_flake8.py
│   └── test_pep257.py
├── package.xml
├── setup.cfg
└── setup.py
```
