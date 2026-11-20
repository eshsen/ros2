import os
from pathlib import Path

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context):
    share = Path(get_package_share_directory('course_simulation'))
    description_share = Path(
        get_package_share_directory('course_description')
    )

    world = LaunchConfiguration('world').perform(context)
    bridge_config = LaunchConfiguration('bridge_config').perform(context)
    namespace = LaunchConfiguration('namespace').perform(context)
    headless_value = LaunchConfiguration('headless').perform(context).lower()

    if headless_value not in ('true', 'false'):
        raise ValueError('headless must be true or false')

    robot_description = xacro.process_file(
        str(description_share / 'urdf' / 'vehicle.urdf.xacro')
    ).toxml()

    resource_paths = [str(share / 'models')]
    existing = os.environ.get('GZ_SIM_RESOURCE_PATH')
    if existing:
        resource_paths.append(existing)

    gazebo_args = ['gz', 'sim', '-r', '-v', '3']
    if headless_value == 'true':
        gazebo_args += ['-s', '--headless-rendering']
    gazebo_args.append(world)

    gazebo = ExecuteProcess(
        cmd=gazebo_args,
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='bridge',
        namespace=namespace,
        parameters=[{
            'config_file': bridge_config,
            'use_sim_time': True,
        }],
        output='screen',
    )

    tf_remappings = [
        ('tf', '/tf'),
        ('tf_static', '/tf_static'),
    ]

    odometry = Node(
        package='course_simulation',
        executable='odom_adapter.py',
        name='odom_adapter',
        namespace=namespace,
        parameters=[{'use_sim_time': True}],
        remappings=tf_remappings,
        output='screen',
    )

    drive = Node(
        package='course_simulation',
        executable='drive_adapter.py',
        name='drive_adapter',
        namespace=namespace,
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=namespace,
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
        remappings=tf_remappings + [('joint_states', '/joint_states')],
        output='screen',
    )

    processes = [gazebo, bridge, odometry, drive, state_publisher]
    actions = [
        SetEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.pathsep.join(resource_paths),
        ),
    ]

    for process in processes:
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=process,
                    on_exit=[
                        EmitEvent(event=Shutdown(
                            reason='A required simulation process exited'
                        )),
                    ],
                )
            )
        )

    return actions + processes


def generate_launch_description():
    share = Path(get_package_share_directory('course_simulation'))
    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=str(share / 'worlds' / 'mcity-minimal.sdf'),
        ),
        DeclareLaunchArgument(
            'bridge_config',
            default_value=str(share / 'config' / 'bridge.yaml'),
        ),
        DeclareLaunchArgument('headless', default_value='true'),
        DeclareLaunchArgument('namespace', default_value='pr07'),
        OpaqueFunction(function=launch_setup),
    ])
