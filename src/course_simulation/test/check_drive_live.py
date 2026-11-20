import math
import time

import rclpy
from rclpy.parameter import Parameter
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist


rclpy.init()
node = rclpy.create_node(
    'drive_live_check',
    parameter_overrides=[
        Parameter('use_sim_time', value=True),
    ],
)
publisher = node.create_publisher(
    AckermannDriveStamped, '/drive/safe', 10
)
received = []
subscription = node.create_subscription(
    Twist,
    '/vehicle/gz_cmd_vel',
    lambda msg: received.append(msg),
    10,
)


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.02)
        if predicate():
            return
    raise AssertionError('Timed out waiting for expected result')


def pump(duration):
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.02)


def send(speed=0.2, steering=0.1, age_ns=0):
    msg = AckermannDriveStamped()
    stamp_ns = node.get_clock().now().nanoseconds - age_ns
    msg.header.stamp.sec, msg.header.stamp.nanosec = divmod(
        stamp_ns, 1_000_000_000
    )
    msg.drive.speed = float(speed)
    msg.drive.steering_angle = float(steering)
    publisher.publish(msg)


def is_zero(msg):
    return all(value == 0.0 for value in (
        msg.linear.x, msg.linear.y, msg.linear.z,
        msg.angular.x, msg.angular.y, msg.angular.z,
    ))


def check_fresh():
    received.clear()
    send()
    expected_yaw_rate = 0.2 * math.tan(0.1) / 0.8
    wait_for(lambda: any(
        math.isclose(msg.linear.x, 0.2, abs_tol=1e-6)
        and math.isclose(
            msg.angular.z, expected_yaw_rate, abs_tol=1e-6
        )
        for msg in received
    ))


try:
    wait_for(lambda: (
        node.get_clock().now().nanoseconds > 1_000_000_000
        and publisher.get_subscription_count() >= 1
        and node.count_publishers('/vehicle/gz_cmd_vel') == 1
    ), timeout=15.0)
    pump(0.5)

    check_fresh()
    print('PASS: fresh command converted', flush=True)

    wait_for(lambda: any(is_zero(msg) for msg in received))
    received.clear()
    pump(0.5)
    assert all(is_zero(msg) for msg in received)
    print('PASS: timeout produced zero; no old command replay', flush=True)

    for label, kwargs in [
        ('stale command', {'age_ns': 1_000_000_000}),
        ('non-finite command', {'speed': float('nan')}),
    ]:
        check_fresh()
        received.clear()
        send(**kwargs)
        wait_for(lambda: any(is_zero(msg) for msg in received))
        received.clear()
        pump(0.5)
        assert all(is_zero(msg) for msg in received)
        print(f'PASS: {label} stopped output; no replay', flush=True)

    print('PASS: live drive checks completed', flush=True)

finally:
    for _ in range(3):
        send(speed=0.0, steering=0.0)
        pump(0.1)
    node.destroy_node()
    rclpy.shutdown()
