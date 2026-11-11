"""Engine performance measurements (S2-03).

Run from the repo root:   python benchmarks/engine_benchmark.py

Measures how long the engine takes per game step and compares it with the
budgets from the SRS: at least 30 FPS (SNAKE-NF-002), so one frame must take
under 33.3 ms, and input handled within 100 ms (SNAKE-NF-001).

If Pygame is installed it also times drawing a frame, which is where most of
the real frame time goes. Only the public engine API is used, so the script
also runs against older versions of the engine for before/after comparisons.
"""
import os
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import collision                       # noqa: E402
from engine.food import spawn_food                 # noqa: E402
from engine.game_state import GameState            # noqa: E402
from engine.snake import Direction, Snake          # noqa: E402

FRAME_BUDGET_MS = 1000 / 30      # SNAKE-NF-002: at least 30 FPS
INPUT_BUDGET_MS = 100            # SNAKE-NF-001: respond within 100 ms


def stats_us(samples):
    """(mean, p99, max) of a list of seconds, in microseconds."""
    us = sorted(s * 1e6 for s in samples)
    return (statistics.mean(us), us[max(0, int(len(us) * 0.99) - 1)], us[-1])


def timed(fn, repeat):
    samples = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return samples


def row(name, samples):
    mean, p99, worst = stats_us(samples)
    print(f"  {name:<46} mean {mean:9.1f} us   p99 {p99:9.1f} us"
          f"   max {worst:9.1f} us")
    return mean


def bench_self_collision():
    print("Collision check (one call per tick), by snake length")
    for length in (3, 100, 590, 5000):
        snake = Snake((length + 10, 0), Direction.RIGHT, length=length)
        row(f"collision.check, length {length}",
            timed(lambda: collision.check(snake, length * 2, 5), 3000))


def bench_food():
    print("Food spawn")
    rng = random.Random(1)
    for width, height in ((30, 20), (100, 100)):
        sparse = {(x, y) for x in range(5) for y in range(5)}
        nearly_full = {(x, y) for x in range(width) for y in range(height)}
        nearly_full.discard((width - 1, height - 1))
        row(f"spawn_food {width}x{height}, mostly empty",
            timed(lambda: spawn_food(width, height, sparse, rng), 300))
        row(f"spawn_food {width}x{height}, one free cell",
            timed(lambda: spawn_food(width, height, nearly_full, rng), 100))


def warm_up():
    """Run some games first so interpreter start-up cost is not measured."""
    for seed in range(100):
        game = GameState(rng=random.Random(seed))
        game.start()
        for _ in range(10):
            game.tick()


def bench_level_up():
    """Survival's most expensive tick: eating the food that levels up."""
    print("Survival level-up tick (adds obstacles)")
    samples = []
    for seed in range(150):
        game = GameState(mode="survival", rng=random.Random(seed))
        game.start()
        game.foods_eaten = 2                   # the next food makes level 2
        hx, hy = game.snake.head
        dx, dy = game.snake.direction.value
        game.food = (hx + dx, hy + dy)
        start = time.perf_counter()
        game.tick()
        samples.append(time.perf_counter() - start)
    return row("survival: tick that levels up", samples)


def bench_ticks():
    print("Game ticks on the default 30x20 board")
    worst_mean = 0
    for mode in ("classic", "obstacle", "survival"):
        plain, eating = [], []
        for seed in range(150):
            game = GameState(mode=mode, rng=random.Random(seed))
            game.start()
            for _ in range(5):                        # a few ordinary ticks
                start = time.perf_counter()
                game.tick()
                plain.append(time.perf_counter() - start)
            hx, hy = game.snake.head
            dx, dy = game.snake.direction.value
            game.food = (hx + dx, hy + dy)            # next tick eats
            start = time.perf_counter()
            game.tick()
            eating.append(time.perf_counter() - start)
        worst_mean = max(worst_mean, row(f"{mode}: tick", plain),
                         row(f"{mode}: tick that eats food", eating))
    return worst_mean


def bench_game_setup():
    print("Game creation (includes obstacle placement)")
    for mode in ("classic", "obstacle", "survival"):
        row(f"GameState(mode={mode!r})",
            timed(lambda: GameState(mode=mode, rng=random.Random(1)), 100))


def bench_drawing():
    print("Rendering one frame with Pygame (offscreen)")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    try:
        import pygame
        from ui.game_screen import GameScreen, window_size
    except ImportError:
        print("  skipped: Pygame is not installed")
        return None
    pygame.init()
    game = GameState(mode="obstacle", rng=random.Random(1))
    game.snake.grow(100)
    for _ in range(100):
        game.snake.move()
    screen = GameScreen(game)
    screen.on_enter()
    surface = pygame.Surface(window_size(game))
    mean = row("GameScreen.draw (long snake + obstacles)",
               timed(lambda: screen.draw(surface), 300))
    pygame.quit()
    return mean


def main():
    print(f"Python {sys.version.split()[0]}\n")
    warm_up()
    bench_self_collision()
    bench_food()
    tick_us = bench_ticks()
    tick_us = max(tick_us, bench_level_up())
    bench_game_setup()
    draw_us = bench_drawing()
    print("\nBudget check")
    print(f"  Frame budget at 30 FPS: {FRAME_BUDGET_MS:.1f} ms")
    print(f"  Slowest mean engine tick (level-up): {tick_us / 1000:.4f} ms "
          f"({tick_us / 1000 / FRAME_BUDGET_MS:.2%} of a frame)")
    if draw_us is not None:
        total_ms = (tick_us + draw_us) / 1000
        print(f"  Draw + tick: {total_ms:.3f} ms "
              f"-> up to {1000 / total_ms:.0f} FPS before the 60 FPS cap")
    print(f"  Input is applied in set_direction() immediately; it shows on "
          f"screen at the next tick (<= 160 ms on Easy), "
          f"input budget is {INPUT_BUDGET_MS} ms.")


if __name__ == "__main__":
    main()
