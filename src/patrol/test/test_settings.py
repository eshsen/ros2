"""Test parameter validation and command selection."""

from patrol.control import command_from_pose
from patrol.settings import Settings, updated_settings, validate_settings
import pytest
from turtlesim.msg import Pose


def test_frequency_changes_from_ten_to_five():
    """Accept a valid frequency without modifying the original."""
    current = Settings()
    candidate = updated_settings(current, {'publish_hz': 5.0})

    assert current.publish_hz == 10.0
    assert candidate.publish_hz == 5.0


@pytest.mark.parametrize(
    'value', [0.0, -1.0, float('nan'), float('inf'), 31.0],
)
def test_invalid_frequency_preserves_previous_settings(value):
    """Reject invalid frequency and retain the previous settings."""
    current = Settings(publish_hz=5.0)

    with pytest.raises(ValueError):
        updated_settings(current, {'publish_hz': value})

    assert current == Settings(publish_hz=5.0)


@pytest.mark.parametrize('value', [1.0, 30.0])
def test_frequency_boundaries(value):
    """Accept both frequency boundaries."""
    candidate = updated_settings(Settings(), {'publish_hz': value})
    assert candidate.publish_hz == value


@pytest.mark.parametrize(
    'name,value',
    [
        ('linear_speed', -0.1),
        ('linear_speed', 1.1),
        ('linear_speed', float('nan')),
        ('turn_rate', -1.1),
        ('turn_rate', 1.1),
        ('turn_rate', float('inf')),
        ('publish_hz', True),
    ],
)
def test_invalid_settings(name, value):
    """Reject values outside the allowed domains."""
    with pytest.raises(ValueError):
        updated_settings(Settings(), {name: value})


@pytest.mark.parametrize(
    'speed,turn', [(0.0, -1.0), (1.0, 1.0)],
)
def test_motion_boundaries(speed, turn):
    """Accept boundary values of speed and turn rate."""
    settings = Settings(linear_speed=speed, turn_rate=turn)
    assert validate_settings(settings) == settings


def test_invalid_batch_does_not_modify_current_settings():
    """Reject the complete candidate if one value is invalid."""
    current = Settings()

    with pytest.raises(ValueError):
        updated_settings(
            current, {'linear_speed': 0.8, 'publish_hz': 0.0},
        )

    assert current == Settings()


def test_command_uses_configured_speeds():
    """Use supplied speed and turn rate when pose exists."""
    command = command_from_pose(Pose(), 0.8, -0.4)
    assert command.linear.x == 0.8
    assert command.angular.z == -0.4


def test_no_pose_still_returns_zero():
    """Keep the command zero before the first pose."""
    command = command_from_pose(None, 0.8, -0.4)
    assert command.linear.x == 0.0
    assert command.angular.z == 0.0
