import math

import pytest
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Twist

from drive_adapter import convert_drive


NOW_NS = 10_000_000_000


def command(speed=0.8, steering=0.2, age_ns=0):
    msg = AckermannDriveStamped()
    stamp_ns = NOW_NS - age_ns
    msg.header.stamp.sec, msg.header.stamp.nanosec = divmod(
        stamp_ns, 1_000_000_000
    )
    msg.drive.speed = float(speed)
    msg.drive.steering_angle = float(steering)
    return msg


@pytest.mark.parametrize('speed,steering', [
    (0.8, 0.2),
    (1.2, 0.45),
    (1.2, -0.45),
    (0.0, 0.3),
])
def test_conversion(speed, steering):
    result, reason = convert_drive(command(speed, steering), NOW_NS)
    assert reason == 'ok'
    assert result.linear.x == pytest.approx(speed)
    assert result.angular.z == pytest.approx(
        speed * math.tan(steering) / 0.8
    )
    assert result.linear.y == result.linear.z == 0.0
    assert result.angular.x == result.angular.y == 0.0


@pytest.mark.parametrize('speed,steering,v,delta', [
    (-1.0, 0.2, 0.0, 0.2),
    (9.0, 0.2, 1.2, 0.2),
    (0.8, 2.0, 0.8, 0.45),
    (0.8, -2.0, 0.8, -0.45),
])
def test_clamping(speed, steering, v, delta):
    result, reason = convert_drive(command(speed, steering), NOW_NS)
    assert reason == 'ok'
    assert result.linear.x == pytest.approx(v)
    assert result.angular.z == pytest.approx(
        v * math.tan(delta) / 0.8
    )


@pytest.mark.parametrize('field', [
    'speed', 'steering_angle', 'steering_angle_velocity',
    'acceleration', 'jerk',
])
@pytest.mark.parametrize('value', [
    float('nan'), float('inf'), float('-inf'),
])
def test_non_finite_stops(field, value):
    msg = command()
    setattr(msg.drive, field, value)
    result, reason = convert_drive(msg, NOW_NS)
    assert reason == 'non_finite'
    assert result == Twist()


@pytest.mark.parametrize('age_ns,expected', [
    (0, 'ok'),
    (250_000_000, 'ok'),
    (250_000_001, 'stale_command'),
    (-1, 'future_stamp'),
])
def test_timestamp_boundary(age_ns, expected):
    result, reason = convert_drive(
        command(age_ns=age_ns), NOW_NS
    )
    assert reason == expected
    if expected != 'ok':
        assert result == Twist()
