import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    EmitEvent,
    ExecuteProcess,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('course_simulation'))

    resource_paths = [str(share / 'models')]
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH')
    if existing:
        resource_paths.append(existing)

    gazebo = ExecuteProcess(
        cmd=[
            'gz', 'sim',
            '-s', '-r', '--headless-rendering', '-v', '3',
            str(share / 'worlds' / 'mcity-minimal.sdf'),
        ],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='pr07_bridge',
        parameters=[{
            'config_file': str(share / 'config' / 'bridge.yaml'),
            'use_sim_time': True,
        }],
        output='screen',
    )

    odometry = Node(
        package='course_simulation',
        executable='odom_adapter.py',
        name='odom_adapter',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    drive = Node(
        package='course_simulation',
        executable='drive_adapter.py',
        name='drive_adapter',
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    sensor_frames = [
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name=f'{frame}_static_tf',
            arguments=[
                '--x', '0.28',
                '--y', '0',
                '--z', '0.38',
                '--roll', '0',
                '--pitch', '0',
                '--yaw', '0',
                '--frame-id', 'base_link',
                '--child-frame-id', frame,
            ],
            parameters=[{'use_sim_time': True}],
            output='screen',
        )
        for frame in ('camera_link', 'lidar_link', 'imu_link')
    ]

    actions = [
        SetEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.pathsep.join(resource_paths),
        ),
    ]

    for process in (gazebo, bridge, odometry, drive):
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=process,
                    on_exit=[
                        EmitEvent(event=Shutdown(
                            reason='A required PR07 process exited'
                        )),
                    ],
                )
            )
        )

    return LaunchDescription(actions + [gazebo, bridge, odometry, drive] + sensor_frames)
