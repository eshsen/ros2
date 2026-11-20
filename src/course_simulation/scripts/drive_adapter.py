#!/usr/bin/env python3
import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist


MAX_AGE_NS = 250_000_000


def convert_drive(msg, now_ns):
    drive = msg.drive
    values = (
        drive.speed,
        drive.steering_angle,
        drive.steering_angle_velocity,
        drive.acceleration,
        drive.jerk,
    )
    if not all(math.isfinite(value) for value in values):
        return Twist(), 'non_finite'

    stamp_ns = (
        msg.header.stamp.sec * 1_000_000_000
        + msg.header.stamp.nanosec
    )
    age_ns = now_ns - stamp_ns

    if age_ns < 0:
        return Twist(), 'future_stamp'
    if age_ns > MAX_AGE_NS:
        return Twist(), 'stale_command'

    speed = min(max(drive.speed, 0.0), 1.2)
    steering = min(max(drive.steering_angle, -0.45), 0.45)

    result = Twist()
    result.linear.x = speed
    result.angular.z = speed * math.tan(steering) / 0.8
    return result, 'ok'


class DriveAdapter(Node):
    def __init__(self):
        super().__init__('drive_adapter')
        self.declare_parameter('input_topic', '/drive/safe')
        self.declare_parameter('output_topic', '/vehicle/gz_cmd_vel')

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
        )
        self.publisher = self.create_publisher(
            Twist,
            self.get_parameter('output_topic').value,
            qos,
        )
        self.subscription = self.create_subscription(
            AckermannDriveStamped,
            self.get_parameter('input_topic').value,
            self.on_command,
            qos,
        )
        self.last_valid_stamp_ns = None
        self.last_reason = None
        self.timer = self.create_timer(0.02, self.check_timeout)
        self.get_logger().info('Drive adapter started')

    def report(self, reason):
        if reason != self.last_reason:
            if reason == 'ok':
                self.get_logger().info('drive_status=ok')
            else:
                self.get_logger().warning(f'drive_status={reason}')
            self.last_reason = reason

    def on_command(self, msg):
        result, reason = convert_drive(
            msg, self.get_clock().now().nanoseconds
        )

        self.last_valid_stamp_ns = None
        if reason == 'ok':
            self.last_valid_stamp_ns = (
                msg.header.stamp.sec * 1_000_000_000
                + msg.header.stamp.nanosec
            )

        self.publisher.publish(result)
        self.report(reason)

    def check_timeout(self):
        if self.last_valid_stamp_ns is None:
            return

        age_ns = (
            self.get_clock().now().nanoseconds
            - self.last_valid_stamp_ns
        )
        if age_ns < 0 or age_ns > MAX_AGE_NS:
            self.last_valid_stamp_ns = None
            self.publisher.publish(Twist())
            self.report(
                'clock_jump' if age_ns < 0 else 'command_timeout'
            )


def main():
    rclpy.init()
    node = None
    try:
        node = DriveAdapter()
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
