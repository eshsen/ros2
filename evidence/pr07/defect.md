# Дефект Gazebo-топика IMU

## Воспроизведение

В копии `config/bridge-broken-imu.yaml` для ROS-топика
`/vehicle/imu` изменён только `gz_topic_name`:

- правильно: `/vehicle/imu`;
- сломанная копия: `/vehicle/imu_typo`.

Launch запущен с аргументом bridge_config, указывающим на сломанную копию.
Дополнительный экземпляр моста не запускался.

## Наблюдения до исправления

- ROS `/vehicle/imu` имеет одного издателя — `/pr07/bridge`.
- Ограниченное чтение ROS IMU завершилось с кодом 124, без сообщения.
- Gazebo `/vehicle/imu` имеет издателя и выдаёт gz.msgs.IMU.
- Gazebo `/vehicle/imu_typo` не имеет издателя, но имеет подписчика моста.
- Направление GZ_TO_ROS и пара типов оставались правильными.

Причина: мост подписан на несуществующий источник Gazebo.
Наличие ROS-издателя не доказывает поступление данных.

## Исправление

Сломанный launch остановлен. Тот же launch запущен с основным
`config/bridge.yaml`, где gz_topic_name равен `/vehicle/imu`.
Сломанная копия сохранена для повторения опыта.

## Результат после исправления

- Параметр `/pr07/bridge config_file` указывает на основной bridge.yaml.
- На Gazebo `/vehicle/imu` есть издатель и подписчик.
- ROS IMU получена с frame_id=imu_link.
- Код ограниченного ROS echo: 0.

## Evidence

- `defect-before.txt`
- `defect-after.txt`
- `defect-launch.txt`
- `defect-fixed-launch.txt`
