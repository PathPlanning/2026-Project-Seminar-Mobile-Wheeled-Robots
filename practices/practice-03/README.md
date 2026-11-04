# Практическая работа 3. Одометрия и системы координат
## Примечание
**Практическая работа выполнена на macOS**
## Иструкция
**1. Запуск скрипта-сервера Webots в терминале на macOS**

``` bash 
export WEBOTS_HOME=/Applications/Webots.app
python3 local_simulation_server.py
```

**2. Перейти в репозиторий в Ubuntu**

``` bash 
cd 2026-Project-Seminar-Mobile-Wheeled-Robots
```

**3. Сделать сборку среды**

``` bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-mac.yaml build
```
**4. Запустить среду разработки** 

``` bash 
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-mac.yaml up -d
```

``` bash
HOST_XAUTHORITY="$XAUTHORITY" docker compose --env-file .env --env-file .env.local -f docker-compose.yaml -f docker-compose.gpu.yaml -f docker-compose.webots-mac.yaml exec -it ros2-base zsh
```

**5. Собрать рабочее пространство**
``` bash
colcon build
```

**6. Активировать окружение**

```bash
source install/setup.zsh
```
**7. Запустить launch-файл сцены**

```bash
ros2 launch practice_03 spawn_robot.launch.py 
```
**8. Анализ результатов экспериментов**

В ходе работы были проведены три эксперимента с различными значениями шума энкодеров: 0, 0.02 и 0.1.

**Эксперимент 1. Шум 0**

При отсутствии дополнительного шума одометрия по энкодерам достаточно точно повторяет истинную траекторию робота (Ground Truth). Небольшие расхождения могут возникать из-за дискретности измерений и особенностей симуляции.

**Эксперимент 2. Шум 0.02**

При небольшом шуме траектории остаются близкими друг к другу. Однако шум измерений может вызывать дополнительные колебания ошибок положения и угла поворота. На графике траекторий эти различия не всегда хорошо заметны.

**Эксперимент 3. Шум 0.1**

При увеличении шума ожидается более заметный разброс ошибок одометрии по энкодерам. Шум влияет на измерения вращения колёс, которые используются для расчёта положения и ориентации робота.

**Сравнение методов одометрии**

Encoder Odometry рассчитывает положение робота по показаниям энкодеров колёс. Этот способ учитывает измеренное вращение колёс, но чувствителен к шуму датчиков.

Command Odometry рассчитывает положение путём интегрирования заданных линейной и угловой скоростей из /cmd_vel. Этот метод не зависит напрямую от шума энкодеров, однако предполагает, что робот точно выполняет команды движения.

Ground Truth представляет истинное положение робота в симуляции и используется для расчёта ошибок двух остальных методов.