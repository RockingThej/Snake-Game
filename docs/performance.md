# Engine performance (Sprint 2, S2-03)

Budgets from the SRS: at least **30 FPS** (SNAKE-NF-002), so a frame has
33.3 ms, and player input handled within **100 ms** (SNAKE-NF-001).

Measured with `python benchmarks/engine_benchmark.py` (Python 3.12, one run on
a Linux sandbox; re-run it on your own machine, absolute numbers will differ).
All times are the mean per call.

| Operation | Before | After |
|---|---|---|
| Collision check, snake of 100 segments | 2.5 us | 0.4 us |
| Collision check, snake of 590 segments (full 30x20 board) | 12.7 us | 0.4 us |
| Collision check, snake of 5000 segments | ~100 us | 0.4 us |
| Spawn food, 30x20 board, mostly empty | 40 us | 0.8 us |
| Spawn food, 100x100 board, mostly empty | ~1000 us | 0.8 us |
| Spawn food, board with one free cell | 40 us / 600 us | unchanged (needs the full scan) |
| Tick without food, classic | 1.4 us | 1.8 us |
| Tick that eats food, classic | 45 us | 3 us |
| Survival level-up tick (adds obstacles) | n/a | ~1 ms |
| Create an Obstacle Mode game (places obstacles) | n/a | ~9 ms |

## What changed

* **Self-collision is O(1).** `Snake` now keeps a count of segments per cell,
  so `collision.hits_self` no longer copies and scans the whole body every
  tick. The price is a little bookkeeping on every move, which is why a tick
  with a 3-segment snake got about 0.4 us slower.
* **Food spawn tries random cells first.** It only falls back to scanning the
  whole board when 24 random probes all hit occupied cells, so spawning costs
  the same on any board size while the board is not nearly full.

## Findings

* The engine was never close to the budget: the slowest operation on the
  normal board is the Survival level-up at about 1 ms, which is 3% of a
  33 ms frame, and an ordinary tick is a few microseconds. The 30 FPS
  target depends on **rendering**, not on the engine.
* Rendering could not be measured in the sandbox because Pygame is not
  installed there. The benchmark times `GameScreen.draw` automatically when
  Pygame is available, so run it once on a real machine and add the FPS
  figure to the test report (TC-NF-PERF-002).
* Input handling: `set_direction()` applies a key press immediately, but the
  snake only moves on the next tick, up to 160 ms later on Easy. If the test
  plan measures "key press to visible turn", Easy mode can exceed 100 ms by
  design; if it measures "key press to input accepted", it is far below. The
  team should decide which one SNAKE-NF-001 means.

## Regression tests

`tests/test_performance.py` fails if collision checks or food spawning start
scaling with snake length or board size again, and if a tick, an eating tick,
a Survival level-up or creating an Obstacle game stops fitting in the frame
budget. Thresholds have 20x or more headroom so they are safe on slow CI.
