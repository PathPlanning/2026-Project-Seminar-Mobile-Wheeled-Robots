# Общая папка для Webots на Mac и Ubuntu в UTM

Инструкция дополняет [установку Ubuntu в UTM](utm_macos.md) и основана на [официальной инструкции ROS 2 для Webots на macOS](https://docs.ros.org/en/foxy/Tutorials/Advanced/Simulators/Webots/Installation-MacOS.html). Этот шаг необходим для запуска Webots на macOS с управлением через ROS2 в Linux VM (UTM). Общая папка необходима для передачи файлов из Linux VM на macOS.


## 1. Создайте папку на Mac

В терминале **macOS** выполните:

```bash
mkdir -p ~/webots-shared
```

Запишите полный путь к папке, например `/Users/username/webots-shared`, где `username` — имя пользователя macOS. Используйте путь без пробелов.

> [!IMPORTANT]
> Выделите для Webots отдельную папку. При завершении симуляции Webots очищает ее содержимое, поэтому не используйте папку репозитория или каталог с личными файлами.

## 2. Подключите папку в UTM

1. Полностью выключите виртуальную машину с Ubuntu.
2. В UTM откройте настройки виртуальной машины (**Edit → Sharing**).
3. Выберите режим общей папки **VirtFS** и укажите созданную папку `webots-shared`.
4. Отключите **Read Only**, чтобы разрешить запись.
5. Сохраните настройки и запустите Ubuntu.

Эти настройки будут работать только если вынастроили виртуальную машину на основе QEMU согласно инструкции из этого репозитория.

## 3. Смонтируйте папку в Ubuntu

Следующие команды выполняются **в Ubuntu внутри UTM**, вне Docker:

```bash
mkdir -p ~/webots-shared
sudo mount -t 9p -o trans=virtio,version=9p2000.L,rw share "$HOME/webots-shared"
```

После монтирования сделайте папку собственностью пользователя Ubuntu:

```bash
sudo chown -R "$(id -u):$(id -g)" "$HOME/webots-shared"
```

Идентификаторы пользователей macOS и Ubuntu отличаются. Без смены владельца папка может быть доступна пользователю виртуальной машины только для чтения, даже если смонтирована с `rw`. Выполняйте `chown` после монтирования: до него команда изменит владельца только локального каталога. Этот способ описан в [документации UTM](https://docs.getutm.app/guest-support/linux/#fixing-permission-errors).

Проверьте запись без `sudo`:

```bash
touch ~/webots-shared/write-test
```

Убедитесь, что файл `write-test` появился в папке на Mac, затем удалите его из Ubuntu:

```bash
rm ~/webots-shared/write-test
```

Если запись не работает, проверьте отключение **Read Only** в UTM и параметры монтирования командой `findmnt "$HOME/webots-shared"`. Смена владельца не снимает режим монтирования `ro`.

## 4. Настройте автоматическое монтирование

Откройте `/etc/fstab` в Ubuntu:

```bash
sudo nano /etc/fstab
```

Добавьте строку, заменив `username` на имя своего пользователя в виртуальной машине:

```text
share /home/username/webots-shared 9p trans=virtio,version=9p2000.L,rw,_netdev,nofail 0 0
```

В `/etc/fstab` требуется полный путь, без `~` и `$HOME`. После сохранения выполните:

```bash
sudo systemctl daemon-reload
```

После перезагрузки Ubuntu повторите проверку создания и удаления файлов. Запускайте контейнер только после монтирования общей папки.

## 5. Заполните `.env.local`

В файл `.env.local` в корне репозитория **в Ubuntu** добавьте переменные, сохранив уже существующие настройки:

```dotenv
MAC_WEBOTS_SHARED_FOLDER=/Users/username/webots-shared
VM_WEBOTS_SHARED_FOLDER=/home/ubuntu/webots-shared
CONTAINER_WEBOTS_SHARED_FOLDER=/tmp/webots-shared
MAC_HOST_IP=192.168.64.1
```

Замените пути на свои. Все три пути обозначают одну общую папку: в macOS, в Ubuntu и внутри контейнера соответственно. Идентификаторы `USER_ID` и `GROUP_ID` в `.env.local` должны совпадать с выводом `id -u` и `id -g` пользователя Ubuntu, которому передана папка.

`192.168.64.1` — пример адреса Mac, доступного из UTM. При использовании **Shared Network** посмотрите адрес шлюза в Ubuntu:

```bash
ip route show default
```

Укажите адрес после `via` в `MAC_HOST_IP`. Файл `docker-compose.webots-mac.yaml` использует его для `host.docker.internal`, монтирует папку Ubuntu в контейнер и задает `WEBOTS_SHARED_FOLDER` в формате `<путь на Mac>:<путь в контейнере>`. Вручную экспортировать эту переменную в Ubuntu не требуется.

Вернитесь к [README](../README.md) для сборки среды, запуска сервера Webots на Mac и запуска примера.
