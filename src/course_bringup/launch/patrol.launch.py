"""Launch turtlesim, namespaced patrol, QoS probe and optional MCAP recording."""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    GroupAction,
    LogInfo,
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    """Build the launch description with configurable namespace and QoS."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    subscriber_reliability = LaunchConfiguration('subscriber_reliability')

    sensor_topic = PythonExpression([
        "'/' + '/'.join(filter(None, ['",
        namespace,
        "'.strip('/'), 'sensor_pose']))",
    ])

    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument(
            'record',
            default_value='false',
            choices=['true', 'false'],
        ),
        DeclareLaunchArgument(
            'bag_dir',
            default_value='evidence/pr05/bag',
        ),
        DeclareLaunchArgument(
            'subscriber_reliability',
            default_value='best_effort',
            choices=['reliable', 'best_effort'],
        ),
        LogInfo(msg=[
            'patrol.launch: namespace=', namespace,
            ' record=', record,
            ' subscriber_reliability=', subscriber_reliability,
            ' sensor_topic=', sensor_topic,
        ]),
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            namespace='/',
            name='turtlesim',
            output='screen',
        ),
        GroupAction([
            PushRosNamespace(namespace),
            Node(
                package='patrol',
                executable='patrol',
                name='patrol',
                output='screen',
                remappings=[
                    ('pose', '/turtle1/pose'),
                    ('cmd_vel', '/turtle1/cmd_vel'),
                ],
            ),
            Node(
                package='course_bringup',
                executable='pose_relay',
                name='pose_relay',
                output='screen',
                remappings=[('pose', '/turtle1/pose')],
            ),
            Node(
                package='course_bringup',
                executable='pose_subscriber',
                name='pose_subscriber',
                output='screen',
                parameters=[{'reliability': subscriber_reliability}],
            ),
        ]),
        ExecuteProcess(
            cmd=[
                'ros2', 'bag', 'record',
                '-s', 'mcap',
                '-o', bag_dir,
                '--topics', sensor_topic,
            ],
            output='screen',
            condition=IfCondition(record),
        ),
    ])
