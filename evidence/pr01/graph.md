# ПР01 — Окружение и граф ROS 2

## Среда опыта

- Способ запуска: native Ubuntu.
- Операционная система: Ubuntu 24.04.5 LTS.
- Дистрибутив ROS 2: Jazzy.
- Исходный рабочий DDS-домен: `16`.
- DDS-домен для воспроизведения сбоя: `17`.
- DDS-домен после исправления: `16`.
- Измерение частоты `/turtle1/pose` выполнялось примерно 15 секунд; финальное окно содержало 946 сообщений.

## Исправный граф

### Команды запуска

Терминал A — симулятор:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtlesim_node
```

Терминал B — управление с клавиатуры:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key
```

Терминал C — наблюдение:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2
ros2 topic list -t
ros2 node info /turtlesim
ros2 topic type /turtle1/pose
POSE_TYPE=$(ros2 topic type /turtle1/pose)
ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose
```

### Ноды и роли

| Нода | Роль |
|---|---|
| `/turtlesim` | Симулятор: принимает команды движения, публикует положение и данные сенсора черепахи |
| `/teleop_turtle` | Управление с клавиатуры: публикует команды линейной и угловой скорости |

### Список нод в домене 16

Команда:

```bash
ros2 node list --no-daemon --spin-time 2
```

Вывод:

```text
/teleop_turtle
/turtlesim
```

### Топики и типы

Команда:

```bash
ros2 topic list -t
```

Вывод:

```text
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim/msg/Color]
/turtle1/pose [turtlesim/msg/Pose]
```

Ключевые топики:

| Топик | Тип | Назначение |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда линейной и угловой скорости от teleop к симулятору |
| `/turtle1/pose` | `turtlesim/msg/Pose` | Положение, ориентация, линейная и угловая скорости черепахи |
| `/turtle1/color_sensor` | `turtlesim/msg/Color` | Цвет точки поля под черепахой |

### Информация о ноде `/turtlesim`

Команда:

```bash
ros2 node info /turtlesim
```

Наблюдение:

- Нода подписана на `/turtle1/cmd_vel` типа `geometry_msgs/msg/Twist`.
- Нода публикует `/turtle1/pose` типа `turtlesim/msg/Pose`.
- Нода публикует `/turtle1/color_sensor` типа `turtlesim/msg/Color`.
- Нода предоставляет сервисы `/clear`, `/kill`, `/reset`, `/spawn`, `/turtle1/set_pen`, `/turtle1/teleport_absolute` и `/turtle1/teleport_relative`.
- Нода предоставляет action server `/turtle1/rotate_absolute`.

### Однократное сообщение позы

Команда:

```bash
ros2 topic echo /turtle1/pose --once
```

Вывод:

```yaml
x: 5.544444561004639
y: 5.544444561004639
theta: 0.0
linear_velocity: 0.0
angular_velocity: 0.0
***
```

### Частота `/turtle1/pose`

Команда:

```bash
ros2 topic hz /turtle1/pose
```

Команда работала около 15 секунд. Финальное наблюдение:

```text
average rate: 62.501
min: 0.015s max: 0.017s std dev: 0.00044s window: 946
```

Измеренная средняя частота: `62.501 Гц`.

## Разрыв связи

### Условия

Симулятор `/turtlesim` всё время продолжал работать в DDS-домене `16`. Нода `/teleop_turtle` была остановлена и повторно запущена в DDS-домене `17`. Наблюдающий CLI также был запущен в домене `17`.

Перед сменой домена был сохранён тип:

```bash
POSE_TYPE=$(ros2 topic type /turtle1/pose)
```

Значение переменной:

```text
turtlesim/msg/Pose
```

Команды:

```bash
# Терминал B
export ROS_DOMAIN_ID=17
ros2 run turtlesim turtle_teleop_key

# Терминал C
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?"
```

### Наблюдение сбоя

В домене `17` обнаружена только нода:

```text
/teleop_turtle
```

Нода `/turtlesim` не обнаружена. За 5 секунд не было получено ни одного сообщения `/turtle1/pose`. Файл `evidence/pr01/pose-broken.txt` имеет размер 0 байт. Код возврата команды `timeout`:

```text
exit=124
```

Нажатия стрелок в teleop не приводили к движению черепахи.

## Восстановление связи

### Условия и команды

Нода `/teleop_turtle` была остановлена, затем повторно запущена в исходном DDS-домене `16`. Наблюдающий CLI также вернулся в домен `16`.

```bash
# Терминал B
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key

# Терминал C
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2
timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?"
```

### Наблюдение после исправления

В домене `16` обнаружены ноды:

```text
/teleop_turtle
/turtlesim
```

Сообщение позы было получено. Код возврата:

```text
exit=0
```

Содержимое `evidence/pr01/pose-fixed.txt`:

```yaml
x: 4.399378776550293
y: 7.543224811553955
theta: 1.440000057220459
linear_velocity: 0.0
angular_velocity: 0.0
***
```

После возврата teleop в домен `16` стрелки снова управляли черепахой.

## Сравнение состояний

| Состояние | Домен `/turtlesim` | Домен `/teleop_turtle` | Ноды, видимые из терминала C | `/turtle1/pose` | Код возврата |
|---|---:|---:|---|---|---:|
| До сбоя | 16 | 16 | `/turtlesim`, `/teleop_turtle` | Получена | Не применимо |
| Сбой | 16 | 17 | `/teleop_turtle` | Не получена за 5 секунд | 124 |
| После исправления | 16 | 16 | `/turtlesim`, `/teleop_turtle` | Получена | 0 |

## Объяснение результата

ROS 2 использует DDS для обнаружения участников и обмена сообщениями. Переменная `ROS_DOMAIN_ID` задаёт DDS-домен — логическую область, в пределах которой ноды могут обнаружить друг друга. Участники с одинаковым идентификатором домена формируют один доступный друг другу ROS-граф. Участники разных доменов не обнаруживают друг друга и не обмениваются данными.

При доменах 16 и 17 teleop публиковал `/turtle1/cmd_vel` в домене 17, а `/turtlesim` был подписан на этот топик в домене 16. Поэтому симулятор не получил команду движения. Аналогично CLI-подписчик в домене 17 не получил `/turtle1/pose`, опубликованный симулятором в домене 16.

Команда `export ROS_DOMAIN_ID=16` меняет переменную окружения текущего Bash и влияет только на процессы, запущенные после неё. Уже работающая нода `/teleop_turtle` была создана в домене 17, поэтому для переноса в домен 16 её нужно было остановить и запустить заново. `/turtlesim` уже был запущен в домене 16, поэтому его не нужно было переустанавливать или перезапускать.
