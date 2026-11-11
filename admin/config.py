"""Game parameters an administrator may change (SRS 7.2, "Configure
Selected Game Parameters").

Only the parameters listed in ``PARAMETERS`` can be set, and each has a
valid range, so an administrator cannot store nonsense. Game code reads the
effective values with ``load_config`` and falls back to the defaults.
"""
from dataclasses import dataclass

from db import admin_repository as repo


@dataclass(frozen=True)
class Parameter:
    key: str
    default: int
    minimum: int
    maximum: int
    description: str


PARAMETERS = {
    p.key: p for p in (
        Parameter("difficulty.easy.speed_ms", 160, 30, 1000,
                  "Milliseconds between snake moves on Easy"),
        Parameter("difficulty.medium.speed_ms", 110, 30, 1000,
                  "Milliseconds between snake moves on Medium"),
        Parameter("difficulty.hard.speed_ms", 75, 30, 1000,
                  "Milliseconds between snake moves on Hard"),
        Parameter("powerup.duration_s", 10, 1, 60,
                  "How long a power-up effect lasts, in seconds"),
        Parameter("leaderboard.display_size", 10, 1, 100,
                  "How many players the leaderboard screen shows"),
        Parameter("score.max_per_game", 1_000_000, 100, 10_000_000,
                  "Largest score accepted for one finished game"),
    )
}


class ConfigError(ValueError):
    """Unknown parameter or value outside its allowed range."""


def validate_value(key, value):
    """Return ``value`` as an int, or raise ConfigError."""
    parameter = PARAMETERS.get(key)
    if parameter is None:
        raise ConfigError("unknown parameter: %r" % (key,))
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        value = int(value.strip())
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError("%s must be a whole number" % key)
    if not parameter.minimum <= value <= parameter.maximum:
        raise ConfigError("%s must be between %d and %d" % (
            key, parameter.minimum, parameter.maximum))
    return value


def load_config(db_path=None):
    """Return every parameter's effective value (stored or default)."""
    values = {key: p.default for key, p in PARAMETERS.items()}
    for row in repo.get_config_rows(db_path=db_path):
        if row["key"] in PARAMETERS:
            try:
                values[row["key"]] = validate_value(row["key"], row["value"])
            except ConfigError:
                pass          # a damaged stored value falls back to default
    return values


def get_difficulty_speeds(db_path=None):
    """Speeds in the form ``DifficultyManager(speeds_ms=...)`` expects."""
    config = load_config(db_path)
    return {
        name: config["difficulty.%s.speed_ms" % name]
        for name in ("easy", "medium", "hard")
    }
