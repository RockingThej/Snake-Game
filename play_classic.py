"""Temporary development runner for Classic Mode (S1-04).

Run from the repo root:  python play_classic.py
Arrow keys or WASD to move, R to restart after game over, Esc to quit.
The real screens (menus, HUD, login) are built by the UI module in ui/.
"""
import sys

import pygame

from db import initialize_database
from engine.game_state import Status
from modes import GameModeManager, ModeNotImplementedError
from ui.input_handler import InputHandler
from ui.keymaps import SINGLE_PLAYER_KEYS

WIDTH, HEIGHT, CELL, HUD = 30, 20, 30, 40


def draw_mode_menu(screen, font, mode_manager, message=None):
    """Display all registered modes and any unavailable-mode message."""
    screen.fill((20, 20, 24))
    heading = font.render("Select a game mode", True, (230, 230, 230))
    screen.blit(heading, (24, 24))

    for index, mode in enumerate(mode_manager.list_modes()):
        availability = "Available" if mode.implemented else "Not implemented"
        line = f"{mode.selection_key}. {mode.name} - {availability}"
        color = (130, 240, 155) if mode.implemented else (180, 180, 190)
        screen.blit(font.render(line, True, color), (40, 80 + index * 42))

    if message:
        warning = font.render(message, True, (255, 150, 120))
        screen.blit(warning, (24, HEIGHT * CELL - 20))


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
        msg = "1: Easy  2: Medium  3: Hard  |  Enter: Start"
    elif state.status == Status.PAUSED:
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title = font.render("PAUSED", True, (255, 220, 120))
        option = font.render("Resume - press Enter or P", True,
                             (230, 230, 230))
        center_x = WIDTH * CELL // 2
        center_y = HEIGHT * CELL // 2 + HUD
        screen.blit(title, (center_x - title.get_width() // 2, center_y - 32))
        screen.blit(option, (center_x - option.get_width() // 2, center_y + 4))
        msg = ""
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
    initialize_database()
    pygame.init()
    screen = pygame.display.set_mode((WIDTH * CELL, HEIGHT * CELL + HUD))
    pygame.display.set_caption("Snake - Mode Selection (dev runner)")
    font = pygame.font.SysFont(None, 28)
    clock = pygame.time.Clock()
    mode_manager = GameModeManager()
    state = None
    mode_message = None
    input_handler = InputHandler(SINGLE_PLAYER_KEYS)
    elapsed = 0

    while True:
        frame_elapsed = clock.tick(60)
        if state is not None and state.status == Status.RUNNING:
            elapsed += frame_elapsed
        else:
            elapsed = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if state is None:
                    selected_mode = next(
                        (mode for mode in mode_manager.list_modes()
                         if event.key == getattr(
                             pygame, f"K_{mode.selection_key}"
                         )),
                        None,
                    )
                    if selected_mode is not None:
                        try:
                            state = mode_manager.create_game(
                                selected_mode.id,
                                width=WIDTH,
                                height=HEIGHT,
                            )
                            mode_message = None
                            elapsed = 0
                        except ModeNotImplementedError as exc:
                            mode_message = str(exc)
                    continue
                if state.status == Status.PAUSED:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                     pygame.K_p):
                        state.resume()
                    continue
                if (state.status == Status.RUNNING and
                        event.key == pygame.K_p):
                    state.pause()
                    elapsed = 0
                    continue
                if (state.status == Status.GAME_OVER and
                        event.key == pygame.K_r):
                    state = mode_manager.create_game(
                        state.mode,
                        width=WIDTH,
                        height=HEIGHT,
                        difficulty=state.difficulty,
                    )
                    elapsed = 0
                elif state.status == Status.READY:
                    difficulty_keys = {
                        pygame.K_1: "easy",
                        pygame.K_2: "medium",
                        pygame.K_3: "hard",
                    }
                    if event.key in difficulty_keys:
                        state.set_difficulty(difficulty_keys[event.key])
                        continue
                    state.start()
                resolved = input_handler.resolve(event.key)
                if resolved is not None:
                    player_id, direction = resolved
                    if player_id == "player1":
                        state.set_direction(direction)
        if state is not None:
            while elapsed >= state.tick_interval_ms:
                elapsed -= state.tick_interval_ms
                state.tick()
            draw(screen, font, state)
        else:
            draw_mode_menu(screen, font, mode_manager, mode_message)
        pygame.display.flip()


if __name__ == "__main__":
    main()
