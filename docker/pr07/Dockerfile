ARG BASE_IMAGE=course-pr07-base:local
FROM ${BASE_IMAGE}

USER root

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ros-lyrical-ackermann-msgs \
       ros-lyrical-std-msgs \
       ros-lyrical-builtin-interfaces \
       ros-lyrical-rosidl-runtime-c \
       ros-lyrical-rosidl-typesupport-fastrtps-c \
       ros-lyrical-ros-gz \
       ros-lyrical-xacro \
       ros-lyrical-robot-state-publisher \
       ros-lyrical-tf2-tools \
       ros-lyrical-rosbag2-storage-mcap \
       python3-colcon-common-extensions \
       python3-pytest \
       python3-yaml \
       liburdfdom-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
CMD ["bash"]
