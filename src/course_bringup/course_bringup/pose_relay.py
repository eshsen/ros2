"""Relay relative pose input to sensor_pose with best-effort QoS."""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from turtlesim.msg import Pose


class PoseRelay(Node):
    def __init__(self) -> None:
        super().__init__('pose_relay')
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        # Input is connected to turtlesim through a launch remapping.
        self._pub = self.create_publisher(Pose, 'sensor_pose', sensor_qos)
        self.create_subscription(Pose, 'pose', self._on_pose, sensor_qos)

    def _on_pose(self, msg: Pose) -> None:
        self._pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = PoseRelay()
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
