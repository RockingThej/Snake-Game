"""Collision Detection Module (SNAKE-F-012): walls, self and obstacles."""
from enum import Enum


class Collision(Enum):
    WALL = "wall"
    SELF = "self"
    OBSTACLE = "obstacle"
    SNAKE = "snake"


def hits_wall(head, width, height):
    x, y = head
    return x < 0 or y < 0 or x >= width or y >= height


def hits_self(snake):
    """True if the head overlaps any other body segment."""
    body = list(snake.body)
    return body[0] in body[1:]


def hits_obstacle(head, obstacles):
    return head in obstacles


def hits_snake(head, other_snakes):
    """Return whether ``head`` overlaps another snake's body."""
    return any(head in other.body for other in other_snakes)


def check(snake, width, height, obstacles=(), other_snakes=()):
    """Return the Collision type for the snake's current head, or None."""
    if hits_wall(snake.head, width, height):
        return Collision.WALL
    if hits_self(snake):
        return Collision.SELF
    if hits_obstacle(snake.head, obstacles):
        return Collision.OBSTACLE
    if hits_snake(snake.head, other_snakes):
        return Collision.SNAKE
    return None
