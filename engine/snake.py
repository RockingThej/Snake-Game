"""Snake Controller (SNAKE-F-009): movement, direction changes and growth."""
from collections import deque
from enum import Enum


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self):
        dx, dy = self.value
        return Direction((-dx, -dy))


class Snake:
    """A snake on a grid. The head is body[0]; cells are (x, y) tuples."""

    def __init__(self, start, direction=Direction.RIGHT, length=3):
        x, y = start
        dx, dy = direction.value
        self.direction = direction          # direction used by the last move
        self._pending = direction           # direction requested for the next move
        self.body = deque((x - dx * i, y - dy * i) for i in range(length))
        self._to_grow = 0

    @property
    def head(self):
        return self.body[0]

    def set_direction(self, new_direction):
        """Request a turn. 180-degree reversals are ignored.

        The check is against the direction of the last *move*, so two quick
        key presses within one tick cannot make the snake reverse into itself.
        """
        if new_direction != self.direction.opposite:
            self._pending = new_direction

    def grow(self, amount=1):
        self._to_grow += amount

    def move(self):
        """Advance one cell and return the new head position."""
        self.direction = self._pending
        dx, dy = self.direction.value
        hx, hy = self.head
        new_head = (hx + dx, hy + dy)
        self.body.appendleft(new_head)
        if self._to_grow > 0:
            self._to_grow -= 1
        else:
            self.body.pop()
        return new_head

    def cells(self):
        return set(self.body)

    def __len__(self):
        return len(self.body)
