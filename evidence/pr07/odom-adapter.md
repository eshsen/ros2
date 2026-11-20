# Адаптер одометрии ПР07

## Основной запуск

`docker/pr07/run.sh` запускает
`ros2 launch course_simulation simulation.launch.py`.

Проверенный запуск:
`headless:=true namespace:=pr07 bridge_config:=/work/src/course_simulation/config/bridge.yaml`.

## Маршрут данных

Gazebo `/model/course_ackermann/odometry`
-> ros_gz_bridge
-> ROS `/vehicle/odom_gz`
-> `/pr07/odom_adapter`
-> `/vehicle/odom`.

Тип входной и выходной одометрии: `nav_msgs/msg/Odometry`.

## Нормализация

Разрешены исходные frames:
- `header.frame_id = course_ackermann/odom`;
- `child_frame_id = course_ackermann/base_link`.

Адаптер снимает ровно префикс `course_ackermann/`:
- `header.frame_id = odom`;
- `child_frame_id = base_link`.

Другие frames и нечисловые значения отклоняются.
Исходное сообщение глубоко копируется. Сохраняются stamp, pose,
twist и обе covariance; изменяются только два frame ID.

## Владение TF

Адаптер публикует `/vehicle/odom` и динамическое преобразование
`odom -> base_link` с одинаковыми stamp и позой.

Gazebo-топик `/model/course_ackermann/tf` не мостится в ROS.

В основном `simulation.launch.py` статические преобразования
`base_link -> camera_link`, `base_link -> lidar_link`,
`base_link -> imu_link` публикует `/pr07/robot_state_publisher`,
используя описание из пакета `course_description`.

Старый `pr07.launch.py` содержит альтернативную схему с отдельными
static_transform_publisher. В итоговом проверенном запуске он не используется.

## QoS и время

Одометрия: reliable, keep last, depth 10.
Адаптер запускается с `use_sim_time=true`.
Временная метка входа сохраняется.

## Итоговая запись

Каталог: `fixtures/pr07-sensors`.
Формат: MCAP.
Длительность: 43.958 секунды симуляционного времени.

Проверка `check_bag.py`:
- перемещение: 0.402267 м;
- максимальная скорость: 0.2 м/с;
- конечная скорость: 0 м/с;
- совпавших пар odometry/TF: 2197;
- доля совпавших сообщений odometry: 1.0;
- odometry без TF: 0;
- дополнительных TF без пары: 1;
- все статические преобразования сенсоров записаны.

## Тесты и evidence

- `colcon-tests.txt`: модульные тесты адаптеров пройдены;
- `odom-adapter-unit-tests.txt`: тесты нормализации;
- `odom-adapter-check.txt`: проверка адаптера;
- `sensor-tf-check.txt`: проверка TF сенсоров;
- `bag-info.txt`: сведения об итоговом bag;
- `fixture-content-check.txt`: проверка содержимого итогового bag;
- `fixture-record-retry.txt`: успешное завершение recorder.

## Replay

Запись содержит нормализованную одометрию и TF.
При воспроизведении адаптер одометрии повторно не запускается.
Проверка replay пока не выполнена.
