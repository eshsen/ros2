"""Подписчик sensor_pose с настраиваемой reliability (для демонстрации QoS)."""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from turtlesim.msg import Pose


class PoseSubscriber(Node):
    def __init__(self) -> None:
        super().__init__('pose_subscriber')
        self.declare_parameter('reliability', 'best_effort')
        reliability_name = str(self.get_parameter('reliability').value).lower()
        if reliability_name == 'reliable':
            reliability = ReliabilityPolicy.RELIABLE
        elif reliability_name == 'best_effort':
            reliability = ReliabilityPolicy.BEST_EFFORT
        else:
            raise ValueError(
                'reliability must be reliable or best_effort'
            )
        qos = QoSProfile(
            reliability=reliability,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        self.create_subscription(Pose, 'sensor_pose', self._on_pose, qos)
        self.get_logger().info(f'subscribing to sensor_pose with {reliability_name}')

    def _on_pose(self, msg: Pose) -> None:
        self.get_logger().info(f'pose x={msg.x:.2f} y={msg.y:.2f}', throttle_duration_sec=1.0)


def main() -> None:
    rclpy.init()
    node = PoseSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
