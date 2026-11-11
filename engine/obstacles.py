"""Obstacle placement for Obstacle and Survival modes (SNAKE-F-014, F-017).

Pure logic with no Pygame imports. Obstacles are placed so that the game
stays fair: they never land on the snake or right in front of it, and they
never split the free cells of the board into separate pockets (which could
trap the snake or cut it off from the food).
"""
from collections import deque

from engine.snake import Direction

# Cells straight ahead of the head that must stay clear so the player always
# has time to react after a game starts or after new obstacles appear, and a
# shorter run each side in case a turn is already queued.
SAFE_CELLS_AHEAD = 6
SAFE_CELLS_SIDE = 3


def protected_cells(snake, width, height, ahead=SAFE_CELLS_AHEAD):
    """Cells where obstacles must not be placed for this snake.

    That is the whole snake, the eight cells around its head, ``ahead``
    cells in the direction it is travelling and ``SAFE_CELLS_SIDE`` cells in
    each direction it could turn to (all clipped to the board).
    """
    cells = snake.cells()
    hx, hy = snake.head
    for direction in Direction:
        if direction == snake.direction.opposite:
            continue
        run = ahead if direction == snake.direction else SAFE_CELLS_SIDE
        dx, dy = direction.value
        for step in range(1, run + 1):
            cells.add((hx + dx * step, hy + dy * step))
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            cells.add((hx + ox, hy + oy))
    return {(x, y) for x, y in cells if 0 <= x < width and 0 <= y < height}


def is_connected(width, height, blocked):
    """True if all cells not in ``blocked`` form one 4-connected region."""
    free_total = width * height - len(blocked)
    if free_total <= 0:
        return True
    start = next((x, y) for x in range(width) for y in range(height)
                 if (x, y) not in blocked)
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nx, ny = nxt
            if (0 <= nx < width and 0 <= ny < height
                    and nxt not in blocked and nxt not in seen):
                seen.add(nxt)
                queue.append(nxt)
    return len(seen) == free_total


def generate_obstacles(width, height, count, keep_free, rng, existing=()):
    """Return up to ``count`` new obstacle cells as a set.

    ``keep_free`` lists cells that must stay empty (snake, food, ...) and
    ``existing`` the obstacles already on the board. A candidate is skipped if
    adding it would disconnect the free cells, so fewer than ``count`` cells
    are returned when the board has no room left.
    """
    if count <= 0:
        return set()
    obstacles = set(existing)
    placed = set()
    candidates = [(x, y) for x in range(width) for y in range(height)
                  if (x, y) not in obstacles and (x, y) not in keep_free]
    rng.shuffle(candidates)
    for cell in candidates:
        if len(placed) >= count:
            break
        obstacles.add(cell)
        if is_connected(width, height, obstacles):
            placed.add(cell)
        else:
            obstacles.discard(cell)
    return placed
