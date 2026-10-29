"""Publish turtle commands using validated runtime parameters."""

from geometry_msgs.msg import Twist
from patrol.control import command_from_pose
from patrol.settings import Settings, updated_settings, validate_settings
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose


class Patrol(Node):
    """Store pose and publish commands with configurable settings."""

    def __init__(self):
        """Declare parameters and create ROS entities."""
        super().__init__('patrol')

        self.declare_parameter('linear_speed', 0.5)
        self.declare_parameter('turn_rate', 0.3)
        self.declare_parameter('publish_hz', 10.0)

        self._settings = validate_settings(Settings(
            linear_speed=self.get_parameter('linear_speed').value,
            turn_rate=self.get_parameter('turn_rate').value,
            publish_hz=self.get_parameter('publish_hz').value,
        ))

        self._last_pose = None
        self._pose_sub = self.create_subscription(
            Pose, 'pose', self._on_pose, 10,
        )
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(
            1.0 / self._settings.publish_hz, self._on_timer,
        )

        self.add_on_set_parameters_callback(self._validate_parameters)
        self.add_post_set_parameters_callback(self._apply_parameters)

    def _candidate_settings(self, parameters):
        """Build a validated candidate from the requested changes."""
        names = {'linear_speed', 'turn_rate', 'publish_hz'}
        changes = {
            parameter.name: parameter.value
            for parameter in parameters
            if parameter.name in names
        }
        return updated_settings(self._settings, changes)

    def _validate_parameters(self, parameters):
        """Validate without changing active state or the timer."""
        try:
            self._candidate_settings(parameters)
        except ValueError as error:
            return SetParametersResult(
                successful=False, reason=str(error),
            )
        return SetParametersResult(successful=True)

    def _apply_parameters(self, parameters):
        """Apply settings after the parameter update succeeds."""
        candidate = self._candidate_settings(parameters)

        if candidate.publish_hz != self._settings.publish_hz:
            period = 1.0 / candidate.publish_hz
            self._timer.cancel()
            self.destroy_timer(self._timer)
            self._timer = self.create_timer(period, self._on_timer)
            self.get_logger().info(
                f'Publication rate changed to {candidate.publish_hz} Hz'
            )

        self._settings = candidate

    def _on_pose(self, message):
        """Store the latest pose."""
        self._last_pose = message

    def _on_timer(self):
        """Publish a command using active settings."""
        self._cmd_pub.publish(command_from_pose(
            self._last_pose,
            self._settings.linear_speed,
            self._settings.turn_rate,
        ))


def main(args=None):
    """Initialize ROS, spin the node and clean up."""
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
