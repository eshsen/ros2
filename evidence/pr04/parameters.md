# ПР04 — Параметризуем движение

## Среда

Ubuntu 24.04, ROS 2 Jazzy, ROS_DOMAIN_ID=16.
Тип позы: turtlesim/msg/Pose.
Использован patrol из ПР03; подписка, издатель и таймер сохранены.

## Параметры и ограничения

| Параметр | По умолчанию | Допустимые значения |
| --- | --- | --- |
| linear_speed | 0.5 | конечное число от 0 до 1 |
| turn_rate | 0.3 | конечное число от -1 до 1 |
| publish_hz | 10.0 | конечное число от 1 до 30 |

Проверка вынесена в чистые функции validate_settings и updated_settings.
Кандидат настроек создаётся отдельно; исходный объект Settings неизменяемый.

Callback _validate_parameters проверяет запрос без изменения рабочего
состояния или таймера. После успешной установки параметров
_apply_parameters применяет новые настройки.

При изменении частоты период равен 1/publish_hz:
старый таймер отменяется и уничтожается, затем создаётся новый.
Изменение только скоростей не пересоздаёт таймер.
До первой позы публикуется нулевая команда.

## Сборка и тесты

```bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
python3 -m pytest src/patrol/test -v
```

Сборка завершилась с кодом 0.
Итог тестов: 25 passed, 1 skipped.
Проверены 10 -> 5 Гц, ноль, отрицательная частота, NaN,
бесконечность, границы диапазонов, сохранение прежних настроек
при отказе, выбор команды и отсутствие позы.
Пропущен шаблонный copyright-тест; flake8 и pep257 прошли.

## Запуск опыта

Терминал A:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
export ROS_DOMAIN_ID=16
ros2 launch turtle_bringup sim.launch.py
```

Терминал B с тем же окружением:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

## Итоги измерений

- При publish_hz=10.0 последняя оценка частоты — 9.999 Гц.
- После установки publish_hz=5.0 последняя оценка — 5.000 Гц.
- Ноль и отрицательная частота отклонены; параметр остался 5.0.
- После отклонения нуля поток сохранился около 5 Гц.
- После изменения скоростей команда содержит 0.8 и -0.4;
  Pose подтверждает движение с соответствующими скоростями.

Измерения ограничивались 12 секундами.
Код 124 в этих измерениях относится к timeout.
У ros2 param set отклонение сопровождалось текстом Setting parameter failed,
хотя код CLI был 0; дополнительно проверены значение параметра и поток.

## Намеренный дефект и восстановление

Ветка: pr04-defect-zero-hz.
Коммит дефекта: db1deb1d7bea995d4790b443d44247f0ee9c4be1.

В settings.py временно удалена проверка publish_hz из списка диапазонов.
После передачи publish_hz=0.0 вычисление периода 1.0/0.0 в
_apply_parameters вызвало ZeroDivisionError: float division by zero.
Patrol завершился с кодом 1; запрос CLI завершился по timeout с кодом 124.
После отказа в графе остался только turtlesim.

Затем выполнен возврат в исправную ветку pr04 и повторная сборка.
После установки 5.0 тот же запрос нуля отклонён:
значение осталось 5.0, patrol остался в графе,
последняя оценка частоты — 5.000 Гц.
Дефектная ветка не слита в исправную.

## Запрос сервиса и цель действия

Запрос сервиса /clear выполняет отдельную операцию и возвращает ответ,
не предоставляя протокол обратной связи о ходе выполнения.
Цель действия /turtle1/rotate_absolute задаёт выполнение поворота,
для которого интерфейс action предусматривает feedback, результат
и запрос отмены.

Вызван готовый /clear типа std_srvs/srv/Empty.
Через ros2 action list -t найден
/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute].
Сама цель поворота в этом опыте не отправлялась.

## Реальные команды и выводы

### Исходные параметры

Файл: `initial-parameters.txt`.

```text

$ ros2 node list --no-daemon --spin-time 2
/patrol
/turtlesim
exit=0

$ ros2 param get /patrol linear_speed
Double value is: 0.5
exit=0

$ ros2 param get /patrol turn_rate
Double value is: 0.3
exit=0

$ ros2 param get /patrol publish_hz
Double value is: 10.0
exit=0
```

### Исходная частота около 10 Гц

Файл: `hz-10.txt`.

```text

$ timeout --signal=INT --kill-after=3s 12s ros2 topic hz /turtle1/cmd_vel
average rate: 9.995
	min: 0.099s max: 0.101s std dev: 0.00043s window: 11
average rate: 9.996
	min: 0.099s max: 0.101s std dev: 0.00048s window: 21
average rate: 9.997
	min: 0.099s max: 0.101s std dev: 0.00050s window: 32
average rate: 9.999
	min: 0.099s max: 0.101s std dev: 0.00046s window: 43
average rate: 10.001
	min: 0.099s max: 0.101s std dev: 0.00047s window: 54
average rate: 9.999
	min: 0.099s max: 0.101s std dev: 0.00050s window: 64
average rate: 10.000
	min: 0.099s max: 0.101s std dev: 0.00047s window: 75
average rate: 10.000
	min: 0.099s max: 0.101s std dev: 0.00046s window: 85
average rate: 9.999
	min: 0.099s max: 0.101s std dev: 0.00045s window: 95
average rate: 9.999
	min: 0.099s max: 0.101s std dev: 0.00047s window: 105
exit=124
```

### Изменение частоты на 5 Гц

Файл: `change-to-5.txt`.

```text

$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
exit=0

$ ros2 param get /patrol publish_hz
Double value is: 5.0
exit=0
```

### Поток после допустимого изменения

Файл: `hz-5.txt`.

```text

$ timeout --signal=INT --kill-after=3s 12s ros2 topic hz /turtle1/cmd_vel
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00047s window: 7
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00036s window: 12
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00030s window: 18
average rate: 4.999
	min: 0.199s max: 0.201s std dev: 0.00030s window: 23
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00033s window: 29
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00031s window: 34
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00029s window: 39
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00027s window: 45
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00030s window: 50
exit=124
```

### Отклонение нуля

Файл: `zero-rejected.txt`.

```text

$ ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz must be within [1.0, 30.0]
exit=0

$ ros2 param get /patrol publish_hz
Double value is: 5.0
exit=0
```

### Поток после отклонения нуля

Файл: `hz-after-zero.txt`.

```text

$ timeout --signal=INT --kill-after=3s 12s ros2 topic hz /turtle1/cmd_vel
average rate: 5.000
	min: 0.200s max: 0.200s std dev: 0.00004s window: 7
average rate: 4.998
	min: 0.200s max: 0.201s std dev: 0.00024s window: 12
average rate: 4.999
	min: 0.200s max: 0.201s std dev: 0.00022s window: 17
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00032s window: 23
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00041s window: 29
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00037s window: 34
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00041s window: 39
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00040s window: 44
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00038s window: 50
exit=124
```

### Отклонение отрицательной частоты

Файл: `negative-rejected.txt`.

```text

$ ros2 param set /patrol publish_hz -1.0
Setting parameter failed: publish_hz must be within [1.0, 30.0]
exit=0

$ ros2 param get /patrol publish_hz
Double value is: 5.0
exit=0
```

### Изменение скоростей и проверка Twist и Pose

Файл: `motion-parameters.txt`.

```text

$ ros2 param set /patrol linear_speed 0.8
Set parameter successful
exit=0

$ ros2 param set /patrol turn_rate -0.4
Set parameter successful
exit=0

$ timeout 10s ros2 topic echo /turtle1/cmd_vel geometry_msgs/msg/Twist --once
linear:
  x: 0.8
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: -0.4
---
exit=0

$ timeout 10s ros2 topic echo /turtle1/pose turtlesim/msg/Pose --once
x: 7.462220191955566
y: 4.811798572540283
theta: -0.8446823954582214
linear_velocity: 0.800000011920929
angular_velocity: -0.4000000059604645
---
exit=0

$ ros2 param set /patrol linear_speed 0.5
Set parameter successful
exit=0

$ ros2 param set /patrol turn_rate 0.3
Set parameter successful
exit=0
```

### Сервис и список действий

Файл: `services-actions.txt`.

```text

$ ros2 service type /clear
std_srvs/srv/Empty
exit=0

$ timeout 15s ros2 service call /clear std_srvs/srv/Empty
waiting for service to become available...
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()

exit=0

$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]
exit=0
```

### Запрос нуля в дефектной версии

Файл: `zero-defect-request.txt`.

```text
$ timeout 15s ros2 param set /patrol publish_hz 0.0
exit=124
```

### Отказ дефектной ноды

Файл: `patrol-defect.log`.

```text
Traceback (most recent call last):
  File "/home/anastasiia/ros2/install/patrol/lib/patrol/patrol", line 33, in <module>
    sys.exit(load_entry_point('patrol', 'console_scripts', 'patrol')())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/anastasiia/ros2/build/patrol/patrol/patrol.py", line 96, in main
    rclpy.spin(node)
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/__init__.py", line 247, in spin
    executor.spin_once()
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 926, in spin_once
    self._spin_once_impl(timeout_sec)
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 918, in _spin_once_impl
    raise handler.exception()
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/task.py", line 286, in _execute_coroutine_step
    result = coro.send(None)
             ^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 592, in handler
    await call_coroutine()
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 531, in _execute
    response = await await_or_execute(srv.callback, request, srv.srv_type.Response())
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/executors.py", line 115, in await_or_execute
    return callback(*args)
           ^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/parameter_service.py", line 117, in _set_parameters_callback
    result = node.set_parameters_atomically([param])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/node.py", line 839, in set_parameters_atomically
    return self._set_parameters_atomically(parameter_list)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/node.py", line 859, in _set_parameters_atomically
    return self._set_parameters_atomically_common(parameter_list)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/node.py", line 962, in _set_parameters_atomically_common
    self._call_post_set_parameters_callback(parameter_list)
  File "/opt/ros/jazzy/lib/python3.12/site-packages/rclpy/node.py", line 1055, in _call_post_set_parameters_callback
    callback(parameter_list)
  File "/home/anastasiia/ros2/build/patrol/patrol/patrol.py", line 67, in _apply_parameters
    period = 1.0 / candidate.publish_hz
             ~~~~^~~~~~~~~~~~~~~~~~~~~~
ZeroDivisionError: float division by zero
[ros2run]: Process exited with failure 1
Код завершения patrol: 1
```

### Граф после отказа

Файл: `nodes-after-defect.txt`.

```text
/turtlesim
```

### Установка 5 Гц в восстановленной версии

Файл: `restored-before-zero.txt`.

```text
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0
```

### Тот же запрос после восстановления проверки

Файл: `zero-restored-request.txt`.

```text
$ timeout 15s ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz must be within [1.0, 30.0]
exit=0
$ ros2 param get /patrol publish_hz
Double value is: 5.0
$ ros2 node list --no-daemon --spin-time 2
/patrol
/turtlesim
```

### Поток после восстановления проверки и отказа установки нуля

Файл: `hz-after-restoration.txt`.

```text
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00042s window: 7
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00032s window: 13
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00030s window: 19
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00033s window: 24
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00031s window: 30
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00032s window: 35
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00030s window: 40
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00029s window: 46
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00033s window: 52
```
