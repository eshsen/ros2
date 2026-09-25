# ПР02 — типы сообщений и топиков

## Основные топики

| Топик | Тип | Назначение |
|---|---|---|
| `/turtle1/cmd_vel` | `geometry_msgs/msg/Twist` | Команда линейной и угловой скорости для ноды `/turtlesim` |
| `/turtle1/pose` | `turtlesim/msg/Pose` | Положение, ориентация и текущие скорости черепахи |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Ошибочный топик из опыта; publisher существует, но `/turtlesim` на него не подписан |

## Тип `geometry_msgs/msg/Twist`

Команда:

```bash
ros2 interface show geometry_msgs/msg/Twist
```

Фактический вывод:

```text
# This expresses velocity in free space broken into its linear and angular parts.

Vector3  linear
float64 x
float64 y
float64 z
Vector3  angular
float64 x
float64 y
float64 z
```

Сообщение `Twist` состоит из двух векторов типа `Vector3`:

- `linear.x`, `linear.y`, `linear.z` — компоненты линейной скорости;
- `angular.x`, `angular.y`, `angular.z` — компоненты угловой скорости.

В опыте использовались:

```yaml
linear:
  x: 1.0
angular:
  z: 0.5
```

`linear.x = 1.0` задаёт движение черепахи вперёд. `angular.z = 0.5` задаёт поворот вокруг оси Z. Остальные поля, не указанные в YAML-команде, имеют значение 0.

## Тип `turtlesim/msg/Pose`

Команда:

```bash
ros2 topic type /turtle1/pose
```

Результат:

```text
turtlesim/msg/Pose
```

Поля сообщения pose:

- `x`, `y` — положение черепахи на плоскости симулятора;
- `theta` — ориентация в радианах;
- `linear_velocity` — текущая линейная скорость;
- `angular_velocity` — текущая угловая скорость.

## Вывод

Совместимый тип `geometry_msgs/msg/Twist` сам по себе не обеспечивает доставку сообщения. Publisher и subscriber должны иметь одинаковое полное имя топика. `/cmd_vel` и `/turtle1/cmd_vel` — разные топики: у `/cmd_vel` был publisher и не было subscriber, а после публикации в `/turtle1/cmd_vel` были обнаружены publisher CLI и subscriber `/turtlesim`.
