import math
import sys
from collections import Counter

import rosbag2_py
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
from tf2_msgs.msg import TFMessage
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist


reader = rosbag2_py.SequentialReader()
reader.open(
    rosbag2_py.StorageOptions(uri=sys.argv[1], storage_id='mcap'),
    rosbag2_py.ConverterOptions('', ''),
)

counts = Counter()
odometry = {}
transforms = {}
positions = []
speeds = []
static_edges = set()
drive_speeds = []
twist_speeds = []


def stamp_key(stamp):
    return stamp.sec, stamp.nanosec


while reader.has_next():
    record = reader.read_next_ext()
    topic, data = record[0], record[1]
    counts[topic] += 1

    if topic == '/vehicle/odom':
        msg = deserialize_message(data, Odometry)
        assert msg.header.frame_id == 'odom'
        assert msg.child_frame_id == 'base_link'

        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        values = (p.x, p.y, p.z, q.x, q.y, q.z, q.w)
        assert all(math.isfinite(v) for v in values)

        odometry[stamp_key(msg.header.stamp)] = values
        positions.append((p.x, p.y))
        speeds.append(msg.twist.twist.linear.x)

    elif topic == '/tf':
        msg = deserialize_message(data, TFMessage)
        for transform in msg.transforms:
            assert transform.header.frame_id == 'odom'
            assert transform.child_frame_id == 'base_link'
            p = transform.transform.translation
            q = transform.transform.rotation
            transforms[stamp_key(transform.header.stamp)] = (
                p.x, p.y, p.z, q.x, q.y, q.z, q.w
            )

    elif topic == '/tf_static':
        msg = deserialize_message(data, TFMessage)
        for transform in msg.transforms:
            static_edges.add((
                transform.header.frame_id,
                transform.child_frame_id,
            ))

    elif topic == '/drive/safe':
        msg = deserialize_message(data, AckermannDriveStamped)
        assert math.isfinite(msg.drive.speed)
        drive_speeds.append(msg.drive.speed)

    elif topic == '/vehicle/gz_cmd_vel':
        msg = deserialize_message(data, Twist)
        assert math.isfinite(msg.linear.x)
        twist_speeds.append(msg.linear.x)


required = {
    '/clock', '/drive/safe', '/tf', '/tf_static',
    '/vehicle/camera/image_raw', '/vehicle/gz_cmd_vel',
    '/vehicle/imu', '/vehicle/odom', '/vehicle/scan',
}
assert all(counts[topic] > 0 for topic in required)
assert counts['/vehicle/odom_gz'] == 0
assert len(positions) >= 2

matched = odometry.keys() & transforms.keys()
assert matched
for stamp in matched:
    assert odometry[stamp] == transforms[stamp], stamp

match_fraction = len(matched) / len(odometry)
assert match_fraction >= 0.99, 'Too many odometry messages without TF'

assert static_edges == {
    ('base_link', 'camera_link'),
    ('base_link', 'lidar_link'),
    ('base_link', 'imu_link'),
}

start, finish = positions[0], positions[-1]
distance = math.hypot(
    finish[0] - start[0], finish[1] - start[1]
)
peak_speed = max(abs(value) for value in speeds)
assert all(math.isfinite(value) for value in speeds)
assert 0.05 < distance < 1.0, 'Unexpected recorded displacement'
assert peak_speed > 0.05, 'No recorded motion in odometry'
assert abs(speeds[-1]) < 0.03, 'Final odometry is not stopped'
assert any(value > 0.05 for value in drive_speeds)
assert any(value > 0.05 for value in twist_speeds)
assert abs(drive_speeds[-1]) < 1e-6
assert abs(twist_speeds[-1]) < 1e-6

print(f'bag={sys.argv[1]}')
for topic in sorted(required):
    print(f'{topic}: {counts[topic]} messages')
print(f'displacement_m={distance:.6f}')
print(f'peak_odom_speed_mps={peak_speed:.6f}')
print(f'final_odom_speed_mps={speeds[-1]:.6f}')
print(f'matched_odom_tf_pairs={len(matched)}')
print(f'odom_tf_match_fraction={match_fraction:.6f}')
print(f'odom_without_tf={len(odometry.keys() - transforms.keys())}')
print(f'tf_without_odom={len(transforms.keys() - odometry.keys())}')
print('PASS: recorded motion and final stop verified')
print('PASS: matched odometry/TF stamps and poses agree')
print('PASS: all sensor static transforms recorded')
