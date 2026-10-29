# Декларация использования ИИ

- Использован ИИ: да
- Модель и версия: Perplexity AI
- Среда или интерфейс агента: веб-интерфейс Perplexity
- Затронутые компоненты: диагностика DDS/WSL, `evidence/pr01/graph.md`, `environment.json`, `report.json`, `AI_USAGE.md`, README
- Характер помощи: разбор, оформление evidence по выводу терминала C
- Как результат был проверен независимо: `ros2 node list --no-daemon`, `timeout … topic echo`, коды 124/0, `pose-broken.txt` / `pose-fixed.txt`, `ros2 topic hz`

---

## ПР02 — Терминал, пакет и запуск turtlesim

- Использован ИИ: да
- Модель и версия: Perplexity AI
- Среда или интерфейс агента: веб-интерфейс Perplexity
- Затронутые компоненты: `turtle_bringup`, `evidence/pr02/*`, README, CI workflow, AI_USAGE.md
- Характер помощи: сборка пакета/launch, оформление commands.md/types.md/report, настройка CI
- Как результат был проверен независимо: локально выполнены `colcon build --symlink-install --packages-select turtle_bringup`, `python3 -m py_compile`, `ros2 pkg prefix turtle_bringup`, `ros2 launch turtle_bringup sim.launch.py`, `ros2 node list --no-daemon --spin-time 2`, `ros2 topic pub`, `ros2 topic info --verbose`, `ros2 topic echo --once` до и после исправления имени топика.

---

## PR03 — Первая нода: поза и команда

- Использован ИИ: да.
- Модель / сервис: Perplexity; точная версия базовой модели интерфейсом не указана.
- Инструмент: веб-интерфейс Perplexity.
- Компоненты: пакет `patrol`, тесты, `evidence/pr03/*`, README, CI.
- Характер помощи: каркас ноды, чистая функция выбора команды, тесты,
  исправление порядка импортов и области проверки flake8, инструкции
  воспроизведения дефекта, оформление demo и подготовка CI.
- Проверка: самостоятельно выполнила colcon build и pytest
  (5 passed, 1 skipped), проверил topic info без remap и с remap,
  получил Pose при движении, измерил частоту команды
  (последняя оценка 10.000 Гц) и проверил нулевые скорости после остановки.
- Команды выполнялись пользователем локально; Perplexity анализировал
  присланные результаты. Результат CI проверяется отдельно после push.

---

## PR04 — Параметризуем движение

- Использован ИИ: да.
- Модель / сервис: Perplexity; точная версия базовой модели интерфейсом не указана.
- Инструмент: веб-интерфейс Perplexity.
- Компоненты: пакет `patrol`, чистая проверка параметров, тесты,
  `evidence/pr04/*`, README и CI.
- Характер помощи: параметры движения, проверка допустимости значений,
  обновление таймера, тесты, подготовка отдельной ветки дефекта,
  разбор traceback и оформление результатов.
- Проверка: пользователь самостоятельно выполнил сборку и pytest
  (25 passed, 1 skipped), изменение 10 -> 5 Гц, отклонение нуля
  и отрицательной частоты, измерения потока и изменение скоростей.
  В отдельной ветке воспроизведён ZeroDivisionError, после возврата
  проверки повторён тот же запрос и подтверждён поток 5.000 Гц.
  Вызван /clear и найден /turtle1/rotate_absolute.
- Команды выполнялись пользователем локально; Perplexity анализировал
  присланные результаты. Результат CI проверяется отдельно после push.

---

## PR05 - Launch, QoS и повтор записи

- Использован ИИ: да
- Модель и версия: Perplexity AI
- Среда или интерфейс агента: веб-интерфейс Perplexity
- Компоненты: course_bringup (launch, pose_relay, pose_subscriber), evidence/pr05/*, CI kit v1-w06
- Характер помощи: namespace/remap/IfCondition record, QoS best_effort vs reliable, MCAP bag + replay overrides
- Проверка: launch /robot_a; qos-before incompatible; qos-after + bag info один топик; replay best_effort ок

---

## PR06 - Модель робота, tf2 и QoS преобразований

- Использован ИИ: да
- Модель и версия: Perplexity AI
- Среда или интерфейс агента: веб-интерфейс Perplexity
- Компоненты: `course_description` (Xacro/URDF, display.launch, тесты),
  `evidence/pr06/*`, README и CI под course kit v1-w08
- Характер помощи: адаптация параметризованной модели по размерам SDF,
  настройка отображения RViz, опыт QoS /tf_static, тест parent лидара,
  отдельная ветка дефекта camera_link, диагностика и оформление результатов.
- Проверка: пользователь самостоятельно выполнил сборку, check_urdf
  и colcon test (5 passed). Поздняя transient_local-подписка получила
  преобразования с exit=0, volatile-подписка завершилась с exit=124.
  Модель открыта в RViz; после публикации состояний колёс статус зелёный.
  В дефектной ветке тест parent упал, но check_urdf принял дерево;
  tf2_echo показал 0.56/0/0.76. После возврата в pr06 тот же тест прошёл,
  tf2_echo показал 0.28/0/0.38. Деревья сохранены через view_frames.
