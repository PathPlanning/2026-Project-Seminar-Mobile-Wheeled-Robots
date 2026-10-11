## Сборка среды


Для установки Webots внутрь контейнера добавьте файл `docker-compose.webots-linux.yaml` во время сборки образа:

```bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml [-f docker-compose.nvidia.yaml] build
```

## Запуск среды


Для запуска контейнера с установленным Webots выполните:

```bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml [-f docker-compose.nvidia.yaml] up -d

HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-linux.yaml [-f docker-compose.nvidia.yaml] exec -it ros2-base zsh
```

## Запуск робота

```bash
cd ~/practices_ws
colcon build --symlink-install
source install/setup.zsh
```

На Linux откройте терминал контейнера. На Mac сначала запустите сервер Webots в macOS, затем откройте терминал контейнера, как описано выше.

Внутри контейнера запустите файл из репозитория:

```bash
ros2 launch webbots spawn_robot.launch.py
```

Launch-файл открывает мир `home.wbt` с роботом TurtleBot3 Burger и препятствием, запускает драйвер робота и контроллеры колес. На Linux окно симулятора открывается на рабочем столе Linux-хоста, на Mac — в macOS.

Дождитесь загрузки мира и запуска контроллеров. Во втором терминале контейнера выполните:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/TwistStamped "{header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'base_link'}, twist: {linear: {x: 0.1, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.2}}}"
```

