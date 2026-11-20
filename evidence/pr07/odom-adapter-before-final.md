# Адаптер одометрии ПР07

## Маршрут данных

Gazebo:
`/model/course_ackermann/odometry`

ROS bridge:
`/vehicle/odom_gz`, тип `nav_msgs/msg/Odometry`

Единственный адаптер:
`/odom_adapter`

Нормализованный выход:
`/vehicle/odom`, тип `nav_msgs/msg/Odometry`

## Нормализация

Разрешены только исходные frames:

- `header.frame_id = course_ackermann/odom`
- `child_frame_id = course_ackermann/base_link`

Адаптер снимает ровно префикс `course_ackermann/` и получает:

- `header.frame_id = odom`
- `child_frame_id = base_link`

Сообщения с другими frames отклоняются. NaN и бесконечности
в pose, twist и обеих covariance также отклоняются.

Исходное сообщение глубоко копируется. Сохраняются stamp, pose,
twist и обе covariance; изменяются только два frame ID.

## Владение TF

Адаптер публикует динамическое преобразование `odom -> base_link`
с тем же stamp и той же позой, что и нормализованная одометрия.

Топик Gazebo `/model/course_ackermann/tf` не мостится в ROS.
В проверенном запуске единственным издателем `/vehicle/odom`
и `/tf` был `odom_adapter`.

Статические преобразования `base_link -> camera_link`,
`base_link -> lidar_link`, `base_link -> imu_link` публикуются
отдельными static_transform_publisher в `/tf_static`.

## QoS и время

Одометрия: reliable, keep last, depth 10.
Адаптер запускается с `use_sim_time=true`.
Временная метка входа сохраняется, а не заменяется временем обработки.

## Проверки

- 262 модульных теста нормализации пройдены.
- Проверены сохранение полей, неизменность входного сообщения,
  неверные frames и нечисловые значения.
- В основной записи все 566 сообщений одометрии имеют TF
  с совпадающими stamp и позой.
- Одно дополнительное сообщение TF не имеет пары в одометрии.

Evidence:

- `odom-adapter-unit-tests.txt`
- `odom-adapter-check.txt`
- `adapters-unit-tests.txt`
- `sensor-tf-check.txt`
- `bag-motion-content-check.txt`

Основная запись: `bags/pr07/motion_20261120_044812`.

## Replay

Запись уже содержит нормализованную одометрию и TF.
При её воспроизведении адаптер одометрии повторно не запускается.
Проверка replay пока не выполнена.
