# PR06 — Системы координат и владельцы преобразований

## Соглашения

Единицы: метры, килограммы, секунды; углы — радианы.
Оси: X вперёд, Y влево, Z вверх.
Корень дерева и Fixed Frame RViz: base_link.
map и odom в этой работе не публикуются.

Размеры взяты из .course-kit/v1/models/course_ackermann/model.sdf.
URDF является учебным упрощённым описанием: колёса подключены напрямую
к base_link; рулевые кулаки и плагины Gazebo не перенесены.

## Исправные связи

Все перечисленные преобразования публикует robot_state_publisher.
Ожидаемые значения заданы относительно родительского звена.

| Parent | Child | XYZ, м | RPY, рад | Joint | Топик |
|---|---|---|---|---|---|
| base_link | camera_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | lidar_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | imu_link | 0.28, 0, 0.38 | 0, 0, 0 | fixed | /tf_static |
| base_link | front_left_wheel | 0.40, 0.31, 0 | 0, 0, 0 при q=0 | continuous | /tf |
| base_link | front_right_wheel | 0.40, -0.31, 0 | 0, 0, 0 при q=0 | continuous | /tf |
| base_link | rear_left_wheel | -0.40, 0.31, 0 | 0, 0, 0 при q=0 | continuous | /tf |
| base_link | rear_right_wheel | -0.40, -0.31, 0 | 0, 0, 0 при q=0 | continuous | /tf |

Ось вращения колёс: 0 1 0.
Для отображения колёс пользователь публиковал нулевые позиции четырёх
сочленений в /joint_states с частотой 10 Гц.
Публикация /joint_states не является вторым владельцем TF.

В RViz выбраны Fixed Frame=base_link, Description Topic=/robot_description,
Durability=Transient Local. После публикации состояний колёс
RobotModel перешёл в зелёный статус.

## Воспроизведённый дефект

В ветке pr06-defect-lidar-parent родитель только lidar_link изменён
с base_link на camera_link; прежний offset 0.28 0 0.38 сохранён.

Получена цепочка base_link -> camera_link -> lidar_link.
tf2_echo показал положение лидара относительно корпуса 0.56 0 0.76.
Тест test_lidar_parent_is_base_link завершился ошибкой.
check_urdf при этом принял модель: дерево оставалось структурно допустимым.

После возврата в pr06 восстановлена связь base_link -> lidar_link.
Повторный tf2_echo показал 0.28 0 0.38.

## QoS

Единственный издатель /tf_static: robot_state_publisher.
Профиль: RELIABLE и TRANSIENT_LOCAL.
Поздняя transient_local-подписка получила три статических преобразования,
exit=0; volatile-подписка не получила сообщения, exit=124.

Старые процессы останавливались перед запуском другой версии модели.
В измерениях дефекта и восстановления подтверждён один издатель /tf_static.

## Evidence

- tf-qos.txt — профили и поздние подписки.
- tf-lidar-fixed.txt — исходное исправное положение.
- tf-lidar-defect.txt — неверное положение.
- tf-lidar-restored.txt — восстановленное положение.
- test-parent-defect.txt — падение проверки parent.
- test-parent-restored.txt — повтор проверки после восстановления.
- model-check-defect.txt — принятие дефектного дерева check_urdf.
- model-check.txt — проверка исправного описания.
- view-frames-*.txt и frames_*.pdf — сохранённые деревья.
- defect-commit.txt — SHA коммита с дефектом.
