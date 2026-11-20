import math
import time

import rclpy
from rclpy.parameter import Parameter
from ackermann_msgs.msg import AckermannDriveStamped
from nav_msgs.msg import Odometry


rclpy.init()
node = rclpy.create_node(
    'motion_live_check',
    parameter_overrides=[Parameter('use_sim_time', value=True)],
)
publisher = node.create_publisher(
    AckermannDriveStamped, '/drive/safe', 10
)
state = {'odom': None}
subscription = node.create_subscription(
    Odometry,
    '/vehicle/odom',
    lambda msg: state.update(odom=msg),
    10,
)


def spin():
    rclpy.spin_once(node, timeout_sec=0.02)


def send(speed):
    msg = AckermannDriveStamped()
    msg.header.stamp = node.get_clock().now().to_msg()
    msg.drive.speed = float(speed)
    msg.drive.steering_angle = 0.2 if speed > 0 else 0.0
    publisher.publish(msg)


def position():
    p = state['odom'].pose.pose.position
    return p.x, p.y


def wait_ready():
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        spin()
        if (
            state['odom'] is not None
            and node.get_clock().now().nanoseconds > 0
            and publisher.get_subscription_count() >= 1
        ):
            return
    raise AssertionError('Clock, odometry or drive subscriber unavailable')


def run_phase(speed, duration):
    start_ns = node.get_clock().now().nanoseconds
    wall_deadline = time.monotonic() + 20.0
    peak_speed = 0.0

    while (
        node.get_clock().now().nanoseconds - start_ns
        < int(duration * 1_000_000_000)
    ):
        if time.monotonic() > wall_deadline:
            raise AssertionError('Simulation time stopped or too slow')

        send(speed)
        end = time.monotonic() + 0.05
        while time.monotonic() < end:
            spin()

        if state['odom'] is not None:
            peak_speed = max(
                peak_speed,
                abs(state['odom'].twist.twist.linear.x),
            )

    return peak_speed


try:
    wait_ready()

    # Establish a stopped baseline before measuring displacement.
    run_phase(0.0, 0.5)
    start = position()

    peak_speed = run_phase(0.2, 2.0)
    run_phase(0.0, 1.0)

    finish = position()
    distance = math.hypot(
        finish[0] - start[0],
        finish[1] - start[1],
    )
    stopped_speed = abs(
        state['odom'].twist.twist.linear.x
    )
    stamp = state['odom'].header.stamp
    odom_age_ns = (
        node.get_clock().now().nanoseconds
        - stamp.sec * 1_000_000_000
        - stamp.nanosec
    )

    print(f'displacement_m={distance:.6f}', flush=True)
    print(f'peak_odom_speed_mps={peak_speed:.6f}', flush=True)
    print(f'final_odom_speed_mps={stopped_speed:.6f}', flush=True)
    print(f'final_odom_age_s={odom_age_ns / 1e9:.6f}', flush=True)

    assert 0 <= odom_age_ns < 500_000_000, 'Odometry is not fresh'
    assert 0.05 < distance < 1.0, 'Unexpected displacement'
    assert peak_speed > 0.05, 'No clear motion in odometry'
    assert stopped_speed < 0.03, 'Robot did not stop'

    print('PASS: motion and stop observed in odometry', flush=True)

finally:
    for _ in range(5):
        send(0.0)
        deadline = time.monotonic() + 0.05
        while time.monotonic() < deadline:
            spin()
    node.destroy_node()
    rclpy.shutdown()
