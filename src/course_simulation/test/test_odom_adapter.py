from copy import deepcopy

import pytest
from nav_msgs.msg import Odometry

from odom_adapter import normalize_odometry


def make_message():
    msg = Odometry()
    msg.header.stamp.sec = 12
    msg.header.stamp.nanosec = 345678901
    msg.header.frame_id = 'course_ackermann/odom'
    msg.child_frame_id = 'course_ackermann/base_link'

    msg.pose.pose.position.x = 1.25
    msg.pose.pose.position.y = -0.75
    msg.pose.pose.position.z = 0.1
    msg.pose.pose.orientation.z = 0.6
    msg.pose.pose.orientation.w = 0.8

    msg.twist.twist.linear.x = 0.7
    msg.twist.twist.angular.z = -0.2
    msg.pose.covariance = [float(i) / 100 for i in range(36)]
    msg.twist.covariance = [float(i + 36) / 100 for i in range(36)]
    return msg


def test_preserves_message_except_frames():
    source = make_message()
    original = deepcopy(source)
    expected = deepcopy(source)
    expected.header.frame_id = 'odom'
    expected.child_frame_id = 'base_link'

    result = normalize_odometry(source)

    assert result == expected
    assert source == original
    assert result is not source

    result.pose.pose.position.x = 99.0
    assert source == original


@pytest.mark.parametrize('field,value', [
    ('header.frame_id', 'other/odom'),
    ('header.frame_id', 'odom'),
    ('header.frame_id', 'course_ackermann/course_ackermann/odom'),
    ('child_frame_id', 'other/base_link'),
    ('child_frame_id', 'base_link'),
    ('child_frame_id', 'course_ackermann/course_ackermann/base_link'),
])
def test_rejects_unexpected_frames(field, value):
    msg = make_message()
    parent_path, attribute = field.rsplit('.', 1) if '.' in field else ('', field)
    parent = getattr(msg, parent_path) if parent_path else msg
    setattr(parent, attribute, value)

    with pytest.raises(ValueError, match='^unexpected_frames$'):
        normalize_odometry(msg)


SCALAR_PATHS = [
    f'{group}.{component}'
    for group, components in [
        ('pose.pose.position', 'xyz'),
        ('pose.pose.orientation', 'xyzw'),
        ('twist.twist.linear', 'xyz'),
        ('twist.twist.angular', 'xyz'),
    ]
    for component in components
]

NUMERIC_FIELDS = (
    [(path, None) for path in SCALAR_PATHS]
    + [('pose.covariance', i) for i in range(36)]
    + [('twist.covariance', i) for i in range(36)]
)


@pytest.mark.parametrize('bad_value', [
    float('nan'), float('inf'), float('-inf'),
])
@pytest.mark.parametrize('path,index', NUMERIC_FIELDS)
def test_rejects_non_finite(path, index, bad_value):
    msg = make_message()
    parts = path.split('.')
    parent = msg
    for part in parts[:-1]:
        parent = getattr(parent, part)

    if index is None:
        setattr(parent, parts[-1], bad_value)
    else:
        getattr(parent, parts[-1])[index] = bad_value

    with pytest.raises(ValueError, match='^non_finite$'):
        normalize_odometry(msg)
