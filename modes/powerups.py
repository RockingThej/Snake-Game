"""Power-ups for the Power-Up mode."""

POWERUP_CONFIG = {
    "speed_boost": {
        "duration_ms": 10_000,
        "multiplier": 0.7,
        "label": "Speed Boost",
    },
    "slow_down": {
        "duration_ms": 10_000,
        "multiplier": 1.5,
        "label": "Slow Down",
    },
    "shield": {
        "duration_ms": 12_000,
        "label": "Shield",
    },
    "score_multiplier": {
        "duration_ms": 12_000,
        "multiplier": 2,
        "label": "Score Multiplier",
    },
    "snake_shrink": {
        "duration_ms": 15_000,
        "amount": 2,
        "label": "Snake Shrink",
    },
}

POWERUP_TYPES = tuple(POWERUP_CONFIG)


class PowerUpManager:
    """Track active power-ups and their remaining duration."""

    def __init__(self, state):
        self.state = state
        self.active = {}

    def apply(self, powerup_name):
        if powerup_name not in POWERUP_CONFIG:
            raise ValueError(f"unknown power-up: {powerup_name!r}")

        self.active[powerup_name] = POWERUP_CONFIG[powerup_name]["duration_ms"]
        self.state.active_powerups = self.active
        if powerup_name == "speed_boost":
            self.state.tick_interval_ms = max(
                20,
                int(self.state.base_tick_interval_ms * POWERUP_CONFIG[powerup_name]["multiplier"]),
            )
        elif powerup_name == "slow_down":
            self.state.tick_interval_ms = max(
                20,
                int(self.state.base_tick_interval_ms * POWERUP_CONFIG[powerup_name]["multiplier"]),
            )
        elif powerup_name == "score_multiplier":
            self.state.score_multiplier = POWERUP_CONFIG[powerup_name]["multiplier"]
        elif powerup_name == "snake_shrink":
            self.state._apply_shrink()

    def expire(self, powerup_name):
        if powerup_name not in self.active:
            return
        del self.active[powerup_name]
        self.state.active_powerups = self.active
        if powerup_name in ("speed_boost", "slow_down") and self.state.mode != "survival":
            self.state.tick_interval_ms = self.state.base_tick_interval_ms
        if powerup_name == "score_multiplier":
            self.state.score_multiplier = 1

    def update(self, elapsed_ms):
        for powerup_name in list(self.active):
            remaining = self.active[powerup_name] - elapsed_ms
            if remaining <= 0:
                self.expire(powerup_name)
            else:
                self.active[powerup_name] = remaining
                self.state.active_powerups = self.active

        if (
            "speed_boost" not in self.active
            and "slow_down" not in self.active
            and self.state.mode != "survival"
        ):
            self.state.tick_interval_ms = self.state.base_tick_interval_ms

    @property
    def names(self):
        return tuple(self.active)
