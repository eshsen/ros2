#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

exec docker run --rm -it \
  --name pr07-sim \
  --user "$(id -u):$(id -g)" \
  --group-add "$(stat -c '%g' /dev/dri/card1)" \
  --group-add "$(stat -c '%g' /dev/dri/renderD128)" \
  --device /dev/dri/card1:/dev/dri/card1 \
  --device /dev/dri/renderD128:/dev/dri/renderD128 \
  --env HOME=/tmp \
  --env DISPLAY= \
  --mount "type=bind,src=$ROOT,dst=/work" \
  --workdir /work \
  --entrypoint /bin/bash \
  course-pr07:lyrical \
  -lc '
set -e
source /opt/ros/lyrical/setup.bash
source /work/install-pr07/setup.bash
exec ros2 launch course_simulation simulation.launch.py "$@"
' pr07-launch "$@"
