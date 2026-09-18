# ПР01 — Окружение и граф ROS 2

Практическая работа №1 по дисциплине «Робототехника».

## Цель

Запустить готовую систему `turtlesim` в ROS 2 Jazzy, исследовать граф ROS 2, измерить частоту публикации `/turtle1/pose`, разорвать связь между нодами разными значениями `ROS_DOMAIN_ID` и подтвердить восстановление связи.

## Среда

- ОС: Ubuntu 24.04
- ROS 2: Jazzy
- Пакет: `turtlesim`
- Домены опыта: 16 и 17

## Подготовка

В каждом терминале необходимо выполнить:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
```

## Исправный граф

Терминал A — запуск симулятора:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtlesim_node
```

Терминал B — управление черепахой:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key
```

Для управления нужно установить фокус в терминале B и нажимать клавиши-стрелки.

Терминал C — наблюдение графа:

```bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=16

ros2 node list --no-daemon --spin-time 2
ros2 topic list -t
ros2 node info /turtlesim
ros2 topic type /turtle1/pose

POSE_TYPE=$(ros2 topic type /turtle1/pose)
echo "$POSE_TYPE"

ros2 topic echo /turtle1/pose --once
ros2 topic hz /turtle1/pose
```

Измерение частоты должно продолжаться не менее 10 секунд, после чего его нужно остановить через `Ctrl+C`.

## Разрыв связи

Симулятор продолжает работать в домене 16. В терминале B нужно остановить `turtle_teleop_key` через `Ctrl+C` и запустить его в домене 17:

```bash
export ROS_DOMAIN_ID=17
ros2 run turtlesim turtle_teleop_key
```

В терминале C необходимо перейти в домен 17:

```bash
export ROS_DOMAIN_ID=17
ros2 node list --no-daemon --spin-time 2

timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-broken.txt 2>&1
printf 'exit=%s\n' "$?"
```

Ожидается код `124`: поза не поступает в течение пяти секунд.

## Восстановление связи

В терминале B остановить teleop и снова запустить его в домене 16:

```bash
export ROS_DOMAIN_ID=16
ros2 run turtlesim turtle_teleop_key
```

В терминале C:

```bash
export ROS_DOMAIN_ID=16
ros2 node list --no-daemon --spin-time 2

timeout 5s ros2 topic echo /turtle1/pose "$POSE_TYPE" --once \
  > evidence/pr01/pose-fixed.txt 2>&1
printf 'exit=%s\n' "$?"
```

Ожидается код `0`, а `evidence/pr01/pose-fixed.txt` должен содержать сообщение `Pose`.

## Проверка

```bash
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

## Файлы результата

- `evidence/pr01/doctor.txt` — отчёт `ros2 doctor --report`
- `evidence/pr01/environment.json` — описание среды
- `evidence/pr01/graph.md` — состав графа и наблюдения эксперимента
- `evidence/pr01/pose-broken.txt` — наблюдение отсутствия данных в домене 17
- `evidence/pr01/pose-fixed.txt` — получение данных после возврата в домен 16
- `evidence/pr01/report.json` — машиночитаемый отчёт

## Вывод

`ROS_DOMAIN_ID` разделяет ROS 2-участников на DDS-домены. Ноды, запущенные в одном домене, обнаруживают друг друга и могут обмениваться сообщениями. Ноды в разных доменах изолированы. Значение `ROS_DOMAIN_ID` применяется при запуске процесса, поэтому для смены домена `turtle_teleop_key` нужно остановить и запустить заново.
