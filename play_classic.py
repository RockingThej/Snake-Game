"""Temporary development runner for Classic Mode (S1-04).

Run from the repo root:  python play_classic.py
Arrow keys or WASD to move, R to restart after game over, Esc to quit.
The real screens (menus, HUD, login) are built by the UI module in ui/.
"""
import sys

import pygame

from engine.game_state import GameState, Status
from engine.snake import Direction

WIDTH, HEIGHT, CELL, HUD = 30, 20, 30, 40
TICK_MS = 110    # placeholder speed; Difficulty Manager (S1-07) will supply this

KEYS = {
    pygame.K_UP: Direction.UP, pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN, pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT, pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT, pygame.K_d: Direction.RIGHT,
}


def draw(screen, font, state):
    screen.fill((20, 20, 24))
    for x, y in state.snake.body:
        pygame.draw.rect(screen, (60, 200, 90),
                         (x * CELL + 1, y * CELL + HUD + 1, CELL - 2, CELL - 2))
    hx, hy = state.snake.head
    pygame.draw.rect(screen, (140, 255, 160),
                     (hx * CELL + 1, hy * CELL + HUD + 1, CELL - 2, CELL - 2))
    if state.food:
        fx, fy = state.food
        pygame.draw.rect(screen, (230, 70, 70),
                         (fx * CELL + 4, fy * CELL + HUD + 4, CELL - 8, CELL - 8))
    text = (f"Score: {state.score}   Mode: {state.mode}   "
            f"Difficulty: {state.difficulty}")
    screen.blit(font.render(text, True, (230, 230, 230)), (10, 10))
    if state.status == Status.READY:
        msg = "Press any key to start"
    elif state.status == Status.GAME_OVER:
        msg = f"Game over ({state.collision.value if state.collision else 'win'})" \
              " - press R to restart"
    else:
        msg = ""
    if msg:
        label = font.render(msg, True, (255, 220, 120))
        screen.blit(label, (WIDTH * CELL // 2 - label.get_width() // 2,
                            HEIGHT * CELL // 2 + HUD))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * CELL, HEIGHT * CELL + HUD))
    pygame.display.set_caption("Snake - Classic Mode (dev runner)")
    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()
    state = GameState(WIDTH, HEIGHT)
    elapsed = 0

    while True:
        elapsed += clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if state.status == Status.GAME_OVER and event.key == pygame.K_r:
                    state = GameState(WIDTH, HEIGHT)
                    elapsed = 0
                elif state.status == Status.READY:
                    state.start()
                if event.key in KEYS:
                    state.set_direction(KEYS[event.key])
        while elapsed >= TICK_MS:
            elapsed -= TICK_MS
            state.tick()
        draw(screen, font, state)
        pygame.display.flip()


if __name__ == "__main__":
    main()
