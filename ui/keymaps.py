"""Default keyboard layouts for the Pygame user interface.

Projects can replace these mappings when constructing ``InputHandler``;
the game engine does not contain or depend on keyboard bindings.
"""
import pygame

from engine.snake import Direction


SINGLE_PLAYER_KEYS = {
    "player1": {
        pygame.K_UP: Direction.UP,
        pygame.K_w: Direction.UP,
        pygame.K_DOWN: Direction.DOWN,
        pygame.K_s: Direction.DOWN,
        pygame.K_LEFT: Direction.LEFT,
        pygame.K_a: Direction.LEFT,
        pygame.K_RIGHT: Direction.RIGHT,
        pygame.K_d: Direction.RIGHT,
    },
}

TWO_PLAYER_KEYS = {
    "player1": {
        pygame.K_w: Direction.UP,
        pygame.K_s: Direction.DOWN,
        pygame.K_a: Direction.LEFT,
        pygame.K_d: Direction.RIGHT,
    },
    "player2": {
        pygame.K_UP: Direction.UP,
        pygame.K_DOWN: Direction.DOWN,
        pygame.K_LEFT: Direction.LEFT,
        pygame.K_RIGHT: Direction.RIGHT,
    },
}
