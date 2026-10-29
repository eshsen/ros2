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

---

# ПР02 — Терминал, пакет и запуск turtlesim

## Назначение пакета

`src/turtle_bringup` — пакет типа `ament_python`. Он не содержит собственной ROS-ноды. Его задача — установить launch-файл `sim.launch.py`, который запускает готовую ноду `turtlesim_node` из установленного пакета `turtlesim`.

## Сборка

Из корня workspace:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2
colcon build --symlink-install --packages-select turtle_bringup
```

## Запуск симулятора

В терминале A:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py
```

После запуска появляется нода `/turtlesim` и открывается окно turtlesim.

## Отправка команды движения

В другом терминале:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2
source install/setup.bash
export ROS_DOMAIN_ID=16

ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

## Ошибка имени топика

Неправильный топик:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

Publisher существует, но `/turtlesim` не получает сообщения, так как подписан на `/turtle1/cmd_vel`, а не на `/cmd_vel`.

Исправление — изменить только имя топика:

```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}'
```

---

# ПР03 — Первая нода: поза и команда

## Назначение

Пакет `patrol` содержит ноду `/patrol`.
Подписка сохраняет последнюю позу из `/turtle1/pose`,
таймер с периодом 0.1 с публикует `Twist` в относительный `cmd_vel`.

Без позы команда нулевая. После получения позы:
`linear.x=0.5`, `angular.z=0.3`.

## Сборка и тесты

```bash
cd ~/ros2
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
python3 -m pytest src/patrol/test -v
```

## Запуск

В терминале A:

```bash
cd ~/ros2
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py
```

В терминале B с таким же окружением:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

## Дефект и исправление

Без remap patrol публикует в `/cmd_vel`, а turtlesim подписан
на `/turtle1/cmd_vel`. После remap имена совпадают и черепаха движется.

Измеренная частота: около 10 Гц; последняя оценка — 10.000 Гц.
После остановки patrol и ожидания скорости в Pose стали нулевыми.

## Результаты

- `evidence/pr03/demo.md` — устройство ноды и опыт.
- `evidence/pr03/build.txt` — сборка.
- `evidence/pr03/tests.txt` — тесты.
- `evidence/pr03/cmd-hz.txt` — измерение частоты.
- `evidence/pr03/report.json` — отчёт, создаваемый после коммита реализации.

---

# ПР04 — Параметризуем движение

Нода `patrol` дополнена параметрами:

| Параметр | По умолчанию | Диапазон |
| --- | --- | --- |
| linear_speed | 0.5 | 0–1 |
| turn_rate | 0.3 | −1–1 |
| publish_hz | 10.0 | 1–30 |

Принимаются только конечные числовые значения.
Недопустимый запрос не изменяет активные настройки и таймер.
При смене частоты старый таймер отменяется и уничтожается.

## Проверка

```bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
python3 -m pytest src/patrol/test -v
```

После запуска turtlesim и patrol с remap:

```bash
ros2 param set /patrol publish_hz 5.0
ros2 param set /patrol publish_hz 0.0
ros2 param get /patrol publish_hz
```

Допустимая установка меняет поток примерно с 10 до 5 Гц.
Ноль отклоняется; прежние 5.0 и поток сохраняются.

## Намеренный дефект

В отдельной ветке `pr04-defect-zero-hz` сохранена версия без проверки
частоты. Ноль вызывает `ZeroDivisionError`.
Ветка не слита в исправную `pr04`.

## Результаты

- `evidence/pr04/parameters.md` — описание и реальные команды с выводами.
- `evidence/pr04/tests.txt` — 25 passed, 1 skipped.
- `evidence/pr04/patrol-defect.log` — traceback намеренного дефекта.
- `evidence/pr04/zero-restored-request.txt` — отказ установки нуля после исправления.
- `evidence/pr04/hz-after-restoration.txt` — сохранённый поток около 5 Гц.
- `evidence/pr04/report.json` — отчёт сдачи.

---

## PR05 — Launch, QoS и повтор записи

### Состав системы

Пакет `course_bringup` запускает один глобальный turtlesim,
а также patrol, pose_relay и pose_subscriber в заданном namespace.

Имена топиков внутри нод относительные. Launch подключает входы
patrol и pose_relay к `/turtle1/pose`, а выход patrol — к
`/turtle1/cmd_vel`. pose_relay публикует `sensor_pose` с best_effort.
Надёжность отдельного подписчика настраивается аргументом launch.

### Сборка и тесты

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install \
  --packages-select turtle_bringup patrol course_bringup
source install/setup.bash

colcon test \
  --packages-select turtle_bringup patrol course_bringup \
  --return-code-on-test-failure
colcon test-result --verbose
```

Получено: 29 tests, 0 errors, 0 failures, 2 skipped.
У course_bringup пока нет собственных автоматических тестов;
его работа проверена функциональными опытами ниже.

### Воспроизведение дефекта

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
```

В другом терминале:

```bash
timeout 3s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability reliable --once
```

Топик существует, но best_effort-издатель не удовлетворяет
запрос reliable-подписчика. Получены предупреждение о несовместимой
политике RELIABILITY и exit=124.

### Исправление и запись

После остановки предыдущего launch:

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort \
  record:=true bag_dir:=evidence/pr05/bag
```

Каталог bag не должен существовать перед новой записью.

```bash
timeout 5s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability best_effort --once
```

Получено сообщение Pose и exit=0.
Recorder запускается через IfCondition(record).
При record:=false процесс recorder не запускается.

После завершения записи через Ctrl+C:

```bash
ros2 bag info evidence/pr05/bag
```

Записан один топик `/robot_a/sensor_pose`, тип `turtlesim/msg/Pose`,
формат MCAP, 2103 сообщения за 33.851547590 секунды.

### Повтор записи

Живой launch должен быть остановлен.

```bash
ros2 bag play evidence/pr05/bag --loop \
  --qos-profile-overrides-path config/qos-overrides.yaml
```

В другом терминале:

```bash
timeout 5s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability reliable --once

timeout 5s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability best_effort --once
```

При единственном издателе rosbag2_player получены:
reliable — несовместимость и exit=124;
best_effort — сообщение Pose и exit=0.
Обе проверки проведены на одной и той же записи.
После проверки replay останавливается через Ctrl+C.

### Evidence

- `evidence/pr05/qos-before.txt` — несовместимость на живом потоке и replay.
- `evidence/pr05/qos-after.txt` — доставка на живом потоке и replay, bag info.
- `evidence/pr05/bag-metadata.yaml` — копия метаданных MCAP.
- `evidence/pr05/tests.txt` и `test-results.txt` — результаты тестов.
- `evidence/pr05/report.json` — отчёт с SHA коммита реализации.

Сама запись `evidence/pr05/bag/` хранится локально и исключена из Git.
Для повторения replay на другом компьютере необходимо перенести этот
каталог или создать новую запись по приведённым командам.

### Course kit

- Версия: `v1-w08`.
- SHA-256 архива:
  `aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb`.

---

## PR06 — Модель робота, tf2 и QoS преобразований

### Описание

Пакет `course_description` содержит модель `urdf/vehicle.urdf.xacro`,
launch-файл `display.launch.py` и пять структурных тестов.

Источник размеров — `.course-kit/v1/models/course_ackermann/model.sdf`.
Корпус: 1.05 × 0.52 × 0.22 м; колёсная база: 0.80 м;
колея: 0.62 м; радиус колеса: 0.12 м.

URDF — учебное упрощённое описание: четыре колеса подключены напрямую
к base_link, без рулевых кулаков и плагинов Gazebo.
Модель параметризована Xacro-переменными, visual и collision заданы отдельно.
Единицы СИ, оси X вперёд, Y влево, Z вверх.

### Подготовка и проверка

```bash
sudo apt install ros-jazzy-xacro
source /opt/ros/jazzy/setup.bash

colcon build --symlink-install --packages-select course_description
source install/setup.bash

xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf

colcon test --packages-select course_description \
  --return-code-on-test-failure --event-handlers console_direct+
```

Результат: check_urdf exit=0, 5 passed.
Тесты проверяют развёртывание Xacro, наличие сенсоров, parent лидара,
связность и отсутствие циклов, положения сенсоров.

### Запуск

```bash
ros2 launch course_description display.launch.py use_sim_time:=false
```

В другом терминале:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
rviz2
```

Настройки RViz:
Fixed Frame=base_link;
RobotModel Description Source=Topic;
Description Topic=/robot_description;
Durability=Transient Local;
Reliability=Reliable.
Добавлен Display TF.

Для отображения колёс в отдельном терминале:

```bash
ros2 topic pub -r 10 /joint_states sensor_msgs/msg/JointState \
  "{header: auto, name: [front_left_wheel_joint, front_right_wheel_joint, rear_left_wheel_joint, rear_right_wheel_joint], position: [0.0, 0.0, 0.0, 0.0]}"
```

После публикации состояний четырёх колёс RobotModel имеет зелёный статус.
Для обязательного опыта с фиксированными сенсорами joint_states не нужен.

### QoS преобразований

На работающем robot_state_publisher:

```bash
ros2 topic info /tf_static --verbose

timeout 4s ros2 topic echo /tf_static --once \
  --qos-durability transient_local --qos-reliability reliable

timeout 4s ros2 topic echo /tf_static --once \
  --qos-durability volatile --qos-reliability reliable
```

Подтверждён профиль RELIABLE + TRANSIENT_LOCAL.
Поздняя transient_local-подписка получила три преобразования, exit=0.
Поздняя volatile-подписка не получила сообщение, exit=124.
Во время опыта publisher не перезапускался.

### Дефект и исправление

Ветка: pr06-defect-lidar-parent.
Коммит дефекта: 0e64ab8233288df0e79ebef54d18503f9757f331.

У lidar_link parent изменён с base_link на camera_link,
а прежний offset 0.28 0 0.38 сохранён.

Результат:
- тест test_lidar_parent_is_base_link упал;
- check_urdf принял структурно допустимое дерево;
- tf2_echo base_link lidar_link показал 0.56 0 0.76;
- view_frames показал цепочку base_link -> camera_link -> lidar_link.

После остановки дефектного publisher и возврата в pr06:
- тот же тест прошёл;
- все пять тестов прошли;
- check_urdf завершился с exit=0;
- tf2_echo показал 0.28 0 0.38;
- дерево восстановлено: base_link -> lidar_link.

Дефектная ветка не сливается в pr06.

### Evidence

Каталог `evidence/pr06/` содержит:
- frames.md — связи, ожидаемые преобразования и владельцы;
- model-check.txt — проверка исправной модели;
- tf-qos.txt — профили /tf_static и результаты позднего чтения;
- test-parent-defect.txt и test-parent-restored.txt — тот же тест до/после;
- tf-lidar-defect.txt и tf-lidar-restored.txt — измерения до/после;
- view-frames-*.txt и frames_*.pdf — деревья;
- tests.txt — финальные тесты;
- defect-commit.txt — SHA дефекта;
- report.json — итоговый отчёт.

### Course kit

Версия: v1-w08.
SHA-256:
aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb.
