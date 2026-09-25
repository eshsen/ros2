# ПР02 — команды терминала и наблюдения

## Рабочая среда

Корень workspace и репозитория:

```text
/home/anastasiia/ros2
```

Системный установленный пакет turtlesim:

```text
/opt/ros/jazzy
```

Рабочий DDS-домен:

```text
ROS_DOMAIN_ID=16
```

Путь `pwd` относится к текущему каталогу workspace. Команда `ros2 pkg prefix turtlesim` показывает путь установки ROS-пакета. Это разные пути и разные сущности.

## Три команды Linux

### 1. `pwd`

Точная команда:

```bash
pwd
```

Назначение: выводит абсолютный путь текущего рабочего каталога.

Мой результат:

```text
/home/anastasiia/ros2
```

### 2. `mkdir -p`

Точная команда:

```bash
mkdir -p src evidence/pr02
```

Назначение: создаёт каталоги `src` и `evidence/pr02`; флаг `-p` также создаёт отсутствующие родительские каталоги и не сообщает ошибку, если каталог уже существует.

Мой результат: созданы каталоги workspace `src` и evidence для ПР02.

### 3. `ros2 pkg prefix turtlesim`

Точная команда:

```bash
ros2 pkg prefix turtlesim
```

Назначение: показывает каталог установки найденного ROS-пакета.

Мой результат:

```text
/opt/ros/jazzy
```

## Операторы перенаправления и конвейера

### `>` и `2>&1`

Пример:

```bash
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
```

Оператор `>` перенаправляет стандартный вывод команды в файл и заменяет предыдущее содержимое файла. Конструкция `2>&1` направляет стандартный поток ошибок в то же место, куда направлен стандартный вывод. В результате stdout и stderr сохраняются в одном файле.

### `|` и `tee`

Пример:

```bash
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build.txt
```

Оператор `|` передаёт stdout одной команды на stdin следующей. Команда `tee` одновременно показывает переданный вывод в терминале и записывает его в файл. В работе лог сборки был виден в терминале и сохранён в `evidence/pr02/build.txt`.

Различие: `>` перенаправляет вывод непосредственно в файл, а `|` передаёт вывод другой команде. `tee` является этой второй командой и позволяет одновременно видеть и сохранять вывод.

### `source` и запуск новой программы

Команда:

```bash
source /opt/ros/jazzy/setup.bash
```

`source` выполняет содержимое файла `setup.bash` в текущем процессе Bash. Поэтому переменные окружения ROS 2, пути и команды становятся доступны в текущем терминале.

Запуск программы, например:

```bash
ros2 launch turtle_bringup sim.launch.py
```

создаёт отдельный процесс launch и дочерний процесс `turtlesim_node`. Когда процесс заканчивается, изменения его окружения не переносятся обратно в текущий Bash. Поэтому `source install/setup.bash` нужен перед `ros2 launch`, чтобы текущий терминал мог найти пакет из workspace.

## Создание и сборка пустого пакета

Команда создания:

```bash
cd src
ros2 pkg create --build-type ament_python --license Apache-2.0 \
  turtle_bringup --dependencies launch launch_ros turtlesim
```

После создания пакет расположен в:

```text
src/turtle_bringup
```

Пустая сборка:

```bash
set -o pipefail
colcon build --symlink-install --packages-select turtle_bringup \
  2>&1 | tee evidence/pr02/build-empty.txt
```

Фактический результат:

```text
Starting >>> turtle_bringup
Finished <<< turtle_bringup [2.63s]

Summary: 1 package finished [2.87s]
```

`set -o pipefail` делает статус конвейера ошибочным, если упала команда `colcon build`, а не только `tee`.

После сборки и подключения overlay:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 pkg prefix turtle_bringup
ros2 pkg executables turtle_bringup
```

Результат `ros2 pkg prefix turtle_bringup`:

```text
/home/anastasiia/ros2/install/turtle_bringup
```

Команда `ros2 pkg executables turtle_bringup` не вывела executable. Это ожидаемо: пакет установлен, но собственной ноды и `console_scripts` в нём ещё нет.

## Launch-файл

Исходный файл на диске:

```text
src/turtle_bringup/launch/sim.launch.py
```

После сборки установленный файл:

```text
install/turtle_bringup/share/turtle_bringup/launch/sim.launch.py
```

Проверка установленного launch-файла:

```bash
ls "$(ros2 pkg prefix turtle_bringup)/share/turtle_bringup/launch"
```

Результат:

```text
sim.launch.py
```

Запуск:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py
```

Результат: открылось одно окно turtlesim; в графе обнаружена нода:

```text
/turtlesim
```

Остановка launch через `Ctrl+C` завершает процесс turtlesim, запущенный launch-файлом.

## Исправная доставка команды

Начальная поза:

```yaml
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
***
```

Команда:

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Ожидаемое направление: движение вперёд и поворот вокруг оси Z.

Фактическая поза после команды:

```yaml
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
***
```

Наблюдение: черепаха переместилась и повернулась. Разовая публикация не задаёт бесконечное движение, поэтому скорости в позднее полученном сообщении pose снова равны нулю.

## Сбой: неправильное полное имя топика

Команда:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Параметры домена, типа и скорости не менялись. Изменено только имя топика с `/turtle1/cmd_vel` на `/cmd_vel`.

Проверка:

```bash
ros2 topic info /cmd_vel --verbose
```

Наблюдение:

```text
Publisher count: 1
Subscription count: 0
```

Publisher CLI с именем `_ros2cli_6663` существует, но `/turtlesim` не подписан на `/cmd_vel`.

Сравнение с правильным топиком до исправления:

```bash
ros2 topic info /turtle1/cmd_vel --verbose
```

Наблюдение:

```text
Publisher count: 0
Subscription count: 1
Node name: turtlesim
Endpoint type: SUBSCRIPTION
```

Поза во время ошибочной публикации:

```yaml
x: 6.509308815002441
y: 5.796990871429443
theta: 0.5040000081062317
linear_velocity: 0.0
angular_velocity: 0.0
***
```

Черепаха не двигалась.

## Исправление

Неправильный publisher был остановлен через `Ctrl+C`. Затем изменено только полное имя топика:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Проверка endpoints:

```bash
ros2 topic info /turtle1/cmd_vel --verbose
```

Результат:

```text
Publisher count: 1
Node name: _ros2cli_6772
Endpoint type: PUBLISHER

Subscription count: 1
Node name: turtlesim
Endpoint type: SUBSCRIPTION
```

Поза после исправления:

```yaml
x: 3.6989803314208984
y: 8.334210395812988
theta: -1.9807411432266235
linear_velocity: 1.0
angular_velocity: 0.5
***
```

Черепаха двигалась.

## Вывод

Файл `sim.launch.py` на диске не является работающей нодой. После сборки он становится установленным ресурсом пакета, доступным команде `ros2 launch`. Launch запускает отдельный процесс `turtlesim_node`, который создаёт ноду `/turtlesim` в ROS-графе.

Тип `geometry_msgs/msg/Twist` был одинаковым в исправном и ошибочном опытах, но сообщения доставлялись только в `/turtle1/cmd_vel`. `/cmd_vel` и `/turtle1/cmd_vel` — разные полные имена топиков. В ошибочном случае discovery обнаружил publisher `/cmd_vel`, но не создал связь доставки, потому что для него не было subscriber. После изменения только имени на `/turtle1/cmd_vel` publisher и subscriber `/turtlesim` были сопоставлены, и черепаха начала двигаться.
