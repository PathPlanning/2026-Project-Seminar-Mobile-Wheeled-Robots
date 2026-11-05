# Локализация робота в Webots с помощью AMCL

Пример демонстрирует локализацию TurtleBot3 Burger по карте и данным лидара. Робот движется по кругу с постоянными линейной и угловой скоростями. В RViz можно наблюдать карту, сканы лидара, частицы AMCL, оценку и истинную позу робота.

Перед запуском соберите пакет из корня рабочего пространства и подключите окружение:

```bash
colcon build --packages-select example_webots_localization
source install/setup.bash
```

## Запуск

```bash
ros2 launch example_webots_localization spawn_robot.launch.py [scene:=scene_name] [localization_mode:=mode_name] [error_x:= ... error_y:= ... ey error_yaw:= ...][use_rviz:=true/false]
```

Параметры:

- **`scene`** — сцена и соответствующая карта. Значение по умолчанию: `three_boxes`.
  - `three_boxes` — три кубика в центре арены.
  - `one_box` — один центральный кубик, грани которого параллельны стенам. Симметрия сцены может приводить к нескольким похожим гипотезам при глобальной локализации.
- **`localization_mode`** — способ инициализации AMCL. Значение по умолчанию: `global`.
  - `global` — начальная поза неизвестна, частицы распределяются по свободному пространству карты.
  - `initial` — используется начальная оценка: стартовая поза робота плюс ошибка. Стартовая поза робота в сцене: $x = 1\;м$, $y = 0\;м$, $yaw = \pi/2 \; рад$
- **`error_x`**, **`error_y`**, **`error_yaw`** — ошибки начальной оценки по осям X и Y в метрах и начальной оценки угла в радианах. По умолчанию: `0.0`. Ошибки применяются только в режиме `initial`. .
- **`use_rviz`** — запуск RViz: `true` или `false`. По умолчанию: `true`.

## Примеры

Запуск со стандартными параметрами: три кубика, глобальная локализация и RViz:

```bash
ros2 launch example_webots_localization spawn_robot.launch.py
```

Глобальная локализация в симметричной сцене с одним кубиком:

```bash
ros2 launch example_webots_localization spawn_robot.launch.py scene:=one_box
```

Локализация с начальной догадкой и заданными ошибками:

```bash
ros2 launch example_webots_localization spawn_robot.launch.py \
  localization_mode:=initial error_x:=0.2 error_y:=-0.1 error_yaw:=0.3
```

Запуск без RViz:

```bash
ros2 launch example_webots_localization spawn_robot.launch.py use_rviz:=false
```
