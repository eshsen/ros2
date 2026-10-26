# ПР03 — Первая нода: поза и команда

## Среда

- Ubuntu 24.04, ROS 2 Jazzy.
- ROS_DOMAIN_ID=16.
- Тип позы: turtlesim/msg/Pose.
- Пакеты: turtle_bringup и patrol.

## Устройство ноды

Нода /patrol подписана на /turtle1/pose.
Callback подписки только сохраняет последнее сообщение в поле _last_pose.
Объект подписки сохранён в поле _pose_sub.

Таймер с периодом 0.1 с вызывает _on_timer.
Издатель публикует geometry_msgs/msg/Twist в относительный cmd_vel.

Выбор команды вынесен в функцию command_from_pose в patrol/control.py:
до получения первой позы все компоненты команды нулевые;
после получения позы linear.x=0.5, angular.z=0.3.
Остальные компоненты остаются нулевыми.

## init, spin, callback и Ctrl+C

- rclpy.init() инициализирует контекст ROS.
- Patrol() создаёт ноду, подписку, издатель и таймер.
- rclpy.spin(node) исполняет готовые callbacks подписки и таймера.
- _on_pose сохраняет полученную позу.
- _on_timer выбирает и публикует очередную команду.
- Ctrl+C прерывает работу; finally освобождает ноду и завершает
  контекст ROS, если он ещё активен.

Завершение процесса patrol не является мгновенной командой торможения.
После его остановки симулятор оставался запущенным.
После ожидания проверено фактическое обнуление скоростей в Pose.

## Сборка и тесты

```bash
colcon build --symlink-install --packages-select turtle_bringup patrol
source install/setup.bash
python3 -m pytest src/patrol/test -v
```

Сборка: два пакета успешно собраны, код 0.
Тесты: 5 passed, 1 skipped, код 0.
Пропущен шаблонный copyright-тест.
Тесты проверяют нулевую команду без позы, обычную команду с позой
и отсутствие изменения входного сообщения.
Также прошли flake8 и pep257.

Результаты: build.txt и tests.txt.

## Воспроизведение дефекта

При работающем turtlesim:

```bash
ros2 run patrol patrol
ros2 node info /patrol
ros2 topic info /cmd_vel --verbose
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /cmd_vel geometry_msgs/msg/Twist --once
ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
```

Наблюдение:

| Топик | Издателей | Подписчиков |
| --- | --- | --- |
| /cmd_vel | 1 — patrol | 0 |
| /turtle1/cmd_vel | 0 | 1 — turtlesim |

В /cmd_vel опубликованы linear.x=0.5 и angular.z=0.3.
При этом Pose содержит linear_velocity=0.0 и angular_velocity=0.0.

Причина: относительный cmd_vel у ноды в корневом namespace
разрешается в /cmd_vel, но turtlesim подписан на /turtle1/cmd_vel.
Совпадения типа сообщения недостаточно при разных именах топиков.

Доказательства: patrol-info-broken.txt, topic-info-broken-cmd.txt,
topic-info-broken-turtle.txt, command-broken.txt и pose-broken.txt.

## Исправление через remap

Предыдущий patrol остановлен, затем выполнено:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
ros2 topic info /turtle1/cmd_vel --verbose
ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
```

Исходник ноды не менялся.
На /turtle1/cmd_vel обнаружены один издатель patrol
и один подписчик turtlesim.

В Pose во время движения:
linear_velocity=0.5,
angular_velocity=0.30000001192092896.

Доказательства: topic-info-fixed.txt, patrol-info-fixed.txt,
command-fixed.txt и pose-fixed.txt.

## Измерение частоты

```bash
timeout --signal=INT --kill-after=3s 12s \
  ros2 topic hz /turtle1/cmd_vel
```

Измерение выполнялось с ограничением времени 12 секунд.
В сохранённом выводе average rate изменялась от 9.994 до 10.000 Гц.
Последняя оценка: 10.000 Гц, окно 108 сообщений.
Показанные минимальный и максимальный интервалы: 0.099 и 0.101 с.

Код 124 означает завершение по ограничению времени timeout.
Доказательство: cmd-hz.txt.

## Проверка остановки

Patrol остановлен через Ctrl+C в его терминале.
После ожидания выполнены:

```bash
ros2 node list --no-daemon --spin-time 2
ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
ros2 topic info /turtle1/cmd_vel --verbose
```

Осталась только нода /turtlesim.
У /turtle1/cmd_vel: Publisher count=0, Subscription count=1.
В Pose: linear_velocity=0.0, angular_velocity=0.0.

Первоначальная попытка проверки была выполнена, пока patrol ещё работал.
Она сохранена отдельно и не считается доказательством остановки.

Доказательства успешной проверки: pose-after-stop.txt и topic-info-after-stop.txt.
