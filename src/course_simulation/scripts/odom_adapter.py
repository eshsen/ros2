#!/usr/bin/env python3
from copy import deepcopy
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster


def normalize_odometry(msg):
    if (
        msg.header.frame_id != 'course_ackermann/odom'
        or msg.child_frame_id != 'course_ackermann/base_link'
    ):
        raise ValueError('unexpected_frames')

    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    linear = msg.twist.twist.linear
    angular = msg.twist.twist.angular

    values = [
        p.x, p.y, p.z,
        q.x, q.y, q.z, q.w,
        linear.x, linear.y, linear.z,
        angular.x, angular.y, angular.z,
        *msg.pose.covariance,
        *msg.twist.covariance,
    ]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('non_finite')

    result = deepcopy(msg)
    prefix = 'course_ackermann/'
    result.header.frame_id = msg.header.frame_id.removeprefix(prefix)
    result.child_frame_id = msg.child_frame_id.removeprefix(prefix)
    return result


class OdomAdapter(Node):
    def __init__(self):
        super().__init__('odom_adapter')
        self.declare_parameter('input_topic', '/vehicle/odom_gz')
        self.declare_parameter('output_topic', '/vehicle/odom')

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.publisher = self.create_publisher(
            Odometry,
            self.get_parameter('output_topic').value,
            qos,
        )
        self.broadcaster = TransformBroadcaster(self)
        self.subscription = self.create_subscription(
            Odometry,
            self.get_parameter('input_topic').value,
            self.on_odometry,
            qos,
        )
        self.rejected_count = 0
        self.get_logger().info('Odometry adapter started')

    def on_odometry(self, msg):
        try:
            normalized = normalize_odometry(msg)
        except ValueError as error:
            self.rejected_count += 1
            if self.rejected_count == 1 or self.rejected_count % 100 == 0:
                self.get_logger().warning(
                    f'Rejected odometry: {error}; count={self.rejected_count}'
                )
            return

        transform = TransformStamped()
        transform.header = deepcopy(normalized.header)
        transform.child_frame_id = normalized.child_frame_id

        position = normalized.pose.pose.position
        transform.transform.translation.x = position.x
        transform.transform.translation.y = position.y
        transform.transform.translation.z = position.z
        transform.transform.rotation = deepcopy(
            normalized.pose.pose.orientation
        )

        self.publisher.publish(normalized)
        self.broadcaster.sendTransform(transform)


def main():
    rclpy.init()
    node = None
    try:
        node = OdomAdapter()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
