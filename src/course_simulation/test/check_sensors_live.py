import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image, Imu, LaserScan


rclpy.init()
node = rclpy.create_node('sensor_live_check')

specs = [
    ('/vehicle/camera/image_raw', Image, 'camera_link', 15.0),
    ('/vehicle/scan', LaserScan, 'lidar_link', 10.0),
    ('/vehicle/imu', Imu, 'imu_link', 100.0),
]
samples = {
    topic: {'stamps': [], 'frames': set(), 'last': None}
    for topic, _, _, _ in specs
}


def callback(topic, msg):
    entry = samples[topic]
    stamp = msg.header.stamp
    entry['stamps'].append(
        stamp.sec * 1_000_000_000 + stamp.nanosec
    )
    entry['frames'].add(msg.header.frame_id)
    entry['last'] = msg


subscriptions = [
    node.create_subscription(
        msg_type,
        topic,
        lambda msg, topic=topic: callback(topic, msg),
        qos_profile_sensor_data,
    )
    for topic, msg_type, _, _ in specs
]

try:
    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)

    failures = []

    for topic, _, expected_frame, expected_hz in specs:
        entry = samples[topic]
        stamps = entry['stamps']
        print(f'\n===== {topic} =====', flush=True)
        print(f'messages_received={len(stamps)}', flush=True)
        print(f'frames={sorted(entry["frames"])}', flush=True)

        if len(stamps) < 2:
            failures.append(f'{topic}: too few messages')
            continue

        monotonic = all(
            second > first
            for first, second in zip(stamps, stamps[1:])
        )
        span = (stamps[-1] - stamps[0]) / 1e9
        hz = (len(stamps) - 1) / span if span > 0 else 0.0

        print(f'stamp_span_s={span:.6f}', flush=True)
        print(f'received_hz_sim={hz:.3f}', flush=True)
        print(f'expected_hz={expected_hz:.1f}', flush=True)
        print(f'stamps_strictly_increasing={monotonic}', flush=True)

        if not monotonic:
            failures.append(f'{topic}: non-increasing stamps')
        if entry['frames'] != {expected_frame}:
            failures.append(f'{topic}: unexpected frame')
        if not 0.8 * expected_hz <= hz <= 1.2 * expected_hz:
            failures.append(f'{topic}: received rate outside test tolerance')

        msg = entry['last']
        if isinstance(msg, Image):
            print(
                f'image={msg.width}x{msg.height}; '
                f'encoding={msg.encoding}; bytes={len(msg.data)}',
                flush=True,
            )
            if (
                msg.width != 640
                or msg.height != 360
                or len(msg.data) != msg.step * msg.height
            ):
                failures.append(f'{topic}: unexpected image dimensions/data')

        if isinstance(msg, LaserScan):
            print(
                f'rays={len(msg.ranges)}; '
                f'range_min={msg.range_min}; range_max={msg.range_max}',
                flush=True,
            )
            if len(msg.ranges) != 360:
                failures.append(f'{topic}: unexpected ray count')

    assert not failures, '; '.join(failures)
    print('\nPASS: sensor frames and received rates verified', flush=True)

finally:
    node.destroy_node()
    rclpy.shutdown()
