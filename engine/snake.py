"""Snake Controller (SNAKE-F-009): movement, direction changes and growth."""
from collections import Counter, deque
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
    """A snake on a grid. The head is body[0]; cells are (x, y) tuples.

    ``body`` is exposed for drawing, but change it only through the methods
    below: the snake also keeps a count of how many segments sit on each cell,
    which makes the self-collision check O(1) instead of O(length).
    """

    def __init__(self, start, direction=Direction.RIGHT, length=3):
        x, y = start
        dx, dy = direction.value
        self.direction = direction          # direction used by the last move
        self._pending = direction           # direction requested for the next move
        self.body = deque((x - dx * i, y - dy * i) for i in range(length))
        self._counts = Counter(self.body)
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
        self._counts[new_head] += 1
        if self._to_grow > 0:
            self._to_grow -= 1
            self._last_tail = None
        else:
            tail = self.body.pop()
            self._counts[tail] -= 1
            if self._counts[tail] == 0:
                del self._counts[tail]
            self._last_tail = tail
        return new_head

    def undo_move(self):
        """Revert the most recent move step (e.g. absorbed by shield)."""
        if len(self.body) <= 1:
            return
        head = self.body.popleft()
        self._counts[head] -= 1
        if self._counts[head] == 0:
            del self._counts[head]
        last_tail = getattr(self, "_last_tail", None)
        if last_tail is not None:
            self.body.append(last_tail)
            self._counts[last_tail] += 1
            self._last_tail = None
        else:
            self._to_grow += 1

    def head_overlaps_body(self):
        """True if the head shares a cell with any other body segment."""
        return self._counts[self.head] > 1

    def cells(self):
        return set(self._counts)

    def __len__(self):
        return len(self.body)
