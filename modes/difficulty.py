"""Difficulty levels mapped to the game loop's movement interval."""
from types import MappingProxyType


class DifficultyManager:
    """Resolve a named difficulty to milliseconds between snake moves.

    Smaller intervals make the snake move faster. Medium retains the
    development runner's previous 110 ms default; the SRS does not prescribe
    numeric speeds, so easy and hard are sensible defaults around it.
    """

    DEFAULT_SPEEDS_MS = MappingProxyType({
        "easy": 160,
        "medium": 110,
        "hard": 75,
    })

    def __init__(self, speeds_ms=None):
        configured_speeds = dict(self.DEFAULT_SPEEDS_MS)
        if speeds_ms is not None:
            for difficulty, interval in speeds_ms.items():
                name = self.normalize(difficulty)
                if name not in configured_speeds:
                    raise ValueError(f"unsupported difficulty: {difficulty!r}")
                if (isinstance(interval, bool) or
                        not isinstance(interval, int) or interval <= 0):
                    raise ValueError(
                        "speed intervals must be positive integers"
                    )
                configured_speeds[name] = interval
        self._speeds_ms = MappingProxyType(configured_speeds)

    @staticmethod
    def normalize(difficulty):
        """Normalize a supported difficulty name or raise ``ValueError``."""
        if not isinstance(difficulty, str):
            raise ValueError("difficulty must be Easy, Medium, or Hard")
        name = difficulty.strip().lower()
        if name not in DifficultyManager.DEFAULT_SPEEDS_MS:
            raise ValueError("difficulty must be Easy, Medium, or Hard")
        return name

    def get_speed_ms(self, difficulty):
        """Return the per-move interval for a named difficulty."""
        return self._speeds_ms[self.normalize(difficulty)]

    @property
    def speed_levels_ms(self):
        """Read-only mapping of difficulty names to movement intervals."""
        return self._speeds_ms
