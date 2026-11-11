"""Food Manager (SNAKE-F-011): spawn food on a free cell."""
import random

# Random probes before falling back to a full scan of the board. On a mostly
# empty board a probe almost always hits, so spawning costs O(1) instead of
# O(width * height); a crowded board falls through to the exact scan.
_PROBES = 24


def spawn_food(width, height, occupied, rng=random):
    """Return a random free (x, y) cell, or None if the board is full."""
    if width * height > len(occupied):
        for _ in range(_PROBES):
            cell = (rng.randrange(width), rng.randrange(height))
            if cell not in occupied:
                return cell
    free = [(x, y) for x in range(width) for y in range(height)
            if (x, y) not in occupied]
    if not free:
        return None
    return rng.choice(free)
