"""Choose a velocity command from the latest pose."""

from geometry_msgs.msg import Twist


def command_from_pose(pose):
    """Return zero without a pose, otherwise return a patrol command."""
    command = Twist()

    if pose is not None:
        command.linear.x = 0.5
        command.angular.z = 0.3

    return command
