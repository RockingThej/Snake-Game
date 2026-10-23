"""Translate keyboard keys into player-specific game directions.

This module has no Pygame dependency. The caller supplies key maps using its
own key constants, which keeps input configuration outside the game engine.
"""


class InputHandler:
    """Resolve a key press to ``(player_id, direction)`` using key maps.

    ``key_maps`` maps player identifiers to mappings of key values to
    ``engine.snake.Direction`` values. For example::

        InputHandler({"player1": {pygame.K_w: Direction.UP}})
    """

    def __init__(self, key_maps):
        if not key_maps:
            raise ValueError("At least one player's key map is required")
        self._key_maps = {
            player_id: dict(mapping)
            for player_id, mapping in key_maps.items()
        }

    def resolve(self, key):
        """Return the mapped player and direction, or ``None`` if unmapped."""
        for player_id, mapping in self._key_maps.items():
            direction = mapping.get(key)
            if direction is not None:
                return player_id, direction
        return None

    @property
    def players(self):
        """Player identifiers with configured key maps, in map order."""
        return tuple(self._key_maps)
