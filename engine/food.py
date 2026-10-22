"""Food Manager (SNAKE-F-011): spawn food on a free cell."""
import random


def spawn_food(width, height, occupied, rng=random):
    """Return a random free (x, y) cell, or None if the board is full."""
    free = [(x, y) for x in range(width) for y in range(height)
            if (x, y) not in occupied]
    if not free:
        return None
    return rng.choice(free)
