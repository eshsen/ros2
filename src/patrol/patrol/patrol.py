"""Subscribe to turtle pose and publish commands every 0.1 seconds."""

from geometry_msgs.msg import Twist
from patrol.control import command_from_pose
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    """Store the latest pose and publish a periodic velocity command."""

    def __init__(self):
        """Create the subscription, publisher and timer."""
        super().__init__('patrol')

        self._last_pose = None
        self._pose_sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._on_pose,
            10,
        )
        self._cmd_pub = self.create_publisher(
            Twist,
            'cmd_vel',
            10,
        )
        self._timer = self.create_timer(0.1, self._on_timer)

    def _on_pose(self, message):
        """Store the latest pose without publishing a command."""
        self._last_pose = message

    def _on_timer(self):
        """Publish the command selected from the latest pose."""
        self._cmd_pub.publish(command_from_pose(self._last_pose))


def main(args=None):
    """Initialize ROS, spin the node and release resources on shutdown."""
    rclpy.init(args=args)
    node = Patrol()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
