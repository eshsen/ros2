# Декларация использования ИИ

- Использован ИИ: да
- Модель и версия: Perplexity AI
- Среда или интерфейс агента: веб-интерфейс Perplexity
- Затронутые компоненты: `turtle_bringup`, `evidence/pr02/*`, README, CI workflow, AI_USAGE.md
- Характер помощи: сборка пакета/launch, оформление commands.md/types.md/report, настройка CI
- Как результат был проверен независимо: локально выполнены `colcon build --symlink-install --packages-select turtle_bringup`, `python3 -m py_compile`, `ros2 pkg prefix turtle_bringup`, `ros2 launch turtle_bringup sim.launch.py`, `ros2 node list --no-daemon --spin-time 2`, `ros2 topic pub`, `ros2 topic info --verbose`, `ros2 topic echo --once` до и после исправления имени топика.
