"""Choose a velocity command from the latest pose."""

from geometry_msgs.msg import Twist


def command_from_pose(pose, linear_speed=0.5, turn_rate=0.3):
    """Return zero without a pose, otherwise use the supplied speeds."""
    command = Twist()

    if pose is not None:
        command.linear.x = float(linear_speed)
        command.angular.z = float(turn_rate)

    return command
