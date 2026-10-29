"""Validate patrol settings without starting ROS."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Settings:
    """Store validated motion and publication settings."""

    linear_speed: float = 0.5
    turn_rate: float = 0.3
    publish_hz: float = 10.0


def validate_settings(settings):
    """Reject nonnumeric, nonfinite or out-of-range settings."""
    limits = (
        ('linear_speed', settings.linear_speed, 0.0, 1.0),
        ('turn_rate', settings.turn_rate, -1.0, 1.0),
        ('publish_hz', settings.publish_hz, 1.0, 30.0),
    )

    for name, value, minimum, maximum in limits:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{name} must be a number')
        if not math.isfinite(value):
            raise ValueError(f'{name} must be finite')
        if not minimum <= value <= maximum:
            raise ValueError(
                f'{name} must be within [{minimum}, {maximum}]'
            )

    return settings


def updated_settings(current, changes):
    """Return a validated candidate without modifying current settings."""
    values = {
        'linear_speed': current.linear_speed,
        'turn_rate': current.turn_rate,
        'publish_hz': current.publish_hz,
    }

    unknown = set(changes) - set(values)
    if unknown:
        raise ValueError(f'Unknown settings: {sorted(unknown)}')

    values.update(changes)
    return validate_settings(Settings(**values))
