"""Collision Detection Module (SNAKE-F-012): walls, self and obstacles."""
from enum import Enum


class Collision(Enum):
    WALL = "wall"
    SELF = "self"
    OBSTACLE = "obstacle"


def hits_wall(head, width, height):
    x, y = head
    return x < 0 or y < 0 or x >= width or y >= height


def hits_self(snake):
    """True if the head overlaps any other body segment."""
    body = list(snake.body)
    return body[0] in body[1:]


def hits_obstacle(head, obstacles):
    return head in obstacles


def check(snake, width, height, obstacles=()):
    """Return the Collision type for the snake's current head, or None."""
    if hits_wall(snake.head, width, height):
        return Collision.WALL
    if hits_self(snake):
        return Collision.SELF
    if hits_obstacle(snake.head, obstacles):
        return Collision.OBSTACLE
    return None
