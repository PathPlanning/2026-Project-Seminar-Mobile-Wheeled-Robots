# SLAM робота в Webots

Пример запускает TurtleBot3 Burger в сцене с тремя коробками. Робот движется по окружности, а `slam_toolbox` строит карту по сканам LiDAR и колёсной одометрии. Супервизор публикует истинную позу робота.

Подготовка, сборка и запуск примера:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch example_webots_slam spawn_robot.launch.py
```

Чтобы запустить пример без RViz:

```bash
ros2 launch example_webots_slam spawn_robot.launch.py use_rviz:=false
```

При запуске используется стандартный `online_async_launch.py` пакета `slam_toolbox` и его стандартные параметры построения карты (скопированные локально). В частности, в примере разрешение карты SLAM отличается от разрешения эталонной карты.  Эталонная карта сцены публикуется узлом `map_server` в топик `/reference_map` в системе координат `world`, построенная SLAM карта публикуется в `/map` в системе координат `map`. Эталон не передаётся в `slam_toolbox`. 

Система координат `world` совпадает с глобальной системой координат сцены. Эталонная карта и трансформ истинной позы `world → base_link_gt` задаются в этой же системе. Таким образом, получается следующее дерево преобразований:

```text
world
├── base_link_gt
└── map
    └── odom
        └── base_link
```