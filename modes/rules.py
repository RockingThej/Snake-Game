"""Per-mode gameplay rules (SNAKE-F-014 Obstacle, SNAKE-F-017 Survival).

``GameState`` stays generic and asks the rules object for the mode-specific
parts through two hooks:

    setup(state)            once, when the game is created
    on_food_eaten(state)    every time the snake eats, before new food spawns

Modes without special behaviour (Classic, and the not yet implemented
Power-Up and Two-Player Battle) use the do-nothing base class.
"""
from engine.obstacles import generate_obstacles, protected_cells


class ModeRules:
    """Classic rules: nothing extra happens."""

    id = "classic"

    def setup(self, state):
        return None

    def on_food_eaten(self, state):
        return None


class ObstacleRules(ModeRules):
    """A fixed set of obstacles is placed on the board when the game starts."""

    id = "obstacle"
    DENSITY = 0.04      # share of the board covered: 24 cells on 30 x 20

    def setup(self, state):
        count = int(state.width * state.height * self.DENSITY)
        state.obstacles = generate_obstacles(
            state.width, state.height, count,
            keep_free=protected_cells(state.snake, state.width, state.height),
            rng=state.rng,
        )


class SurvivalRules(ModeRules):
    """The game gets harder as the snake eats.

    Every ``FOODS_PER_LEVEL`` foods the level goes up by one, the snake moves
    ``SPEEDUP_MS`` faster (never below ``MIN_INTERVAL_MS``) and
    ``OBSTACLES_PER_LEVEL`` new obstacles appear, up to ``MAX_DENSITY`` of the
    board. New obstacles keep clear of the snake and its path.
    """

    id = "survival"
    FOODS_PER_LEVEL = 3
    SPEEDUP_MS = 8
    MIN_INTERVAL_MS = 40
    OBSTACLES_PER_LEVEL = 2
    MAX_DENSITY = 0.10

    def level_for(self, foods_eaten):
        return 1 + foods_eaten // self.FOODS_PER_LEVEL

    def interval_for(self, base_interval_ms, level):
        return max(self.MIN_INTERVAL_MS,
                   base_interval_ms - (level - 1) * self.SPEEDUP_MS)

    def on_food_eaten(self, state):
        new_level = self.level_for(state.foods_eaten)
        if new_level == state.level:
            return
        state.level = new_level
        state.tick_interval_ms = self.interval_for(
            state.base_tick_interval_ms, new_level)

        cap = int(state.width * state.height * self.MAX_DENSITY)
        room = cap - len(state.obstacles)
        wanted = min(self.OBSTACLES_PER_LEVEL, room)
        keep_free = protected_cells(state.snake, state.width, state.height)
        if state.food is not None:
            keep_free.add(state.food)
        state.obstacles |= generate_obstacles(
            state.width, state.height, wanted, keep_free, state.rng,
            existing=state.obstacles)


_RULES = {rules.id: rules
          for rules in (ModeRules, ObstacleRules, SurvivalRules)}


def get_rules(mode_id):
    """Return a fresh rules object for a mode id (Classic for unknown ids)."""
    return _RULES.get(mode_id, ModeRules)()
