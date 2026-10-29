"""Test command selection without starting a ROS node."""

from geometry_msgs.msg import Twist
from patrol.control import command_from_pose
from turtlesim.msg import Pose


def test_no_pose_returns_zero_command():
    """Return zero in every component before the first pose."""
    command = command_from_pose(None)

    assert isinstance(command, Twist)
    assert command.linear.x == 0.0
    assert command.linear.y == 0.0
    assert command.linear.z == 0.0
    assert command.angular.x == 0.0
    assert command.angular.y == 0.0
    assert command.angular.z == 0.0


def test_pose_returns_patrol_command():
    """Return the required forward speed and turn rate."""
    pose = Pose()
    pose.x = 1.0
    pose.y = 2.0
    pose.theta = 0.5

    command = command_from_pose(pose)

    assert command.linear.x == 0.5
    assert command.linear.y == 0.0
    assert command.linear.z == 0.0
    assert command.angular.x == 0.0
    assert command.angular.y == 0.0
    assert command.angular.z == 0.3


def test_pose_is_not_modified():
    """Leave the input pose unchanged."""
    pose = Pose()
    pose.x = 1.0
    pose.y = 2.0
    pose.theta = 0.5

    command_from_pose(pose)

    assert pose.x == 1.0
    assert pose.y == 2.0
    assert pose.theta == 0.5
