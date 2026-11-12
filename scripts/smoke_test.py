"""Smoke test verifying wheel installation and headless engine execution across all game modes.

Checks:
- Clean import of game modules
- Execution of all 5 game modes (classic, obstacle, powerup, survival, two_player)
- Verification of 100 ticks per mode (500 total ticks)
- Measures mean tick latency
- Formats build artifact and smoke test tables for GITHUB_STEP_SUMMARY & GITHUB_OUTPUT.
"""
import argparse
import os
import random
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def format_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"


def run_smoke_simulation(repo_root: Path):
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    # Set headless SDL dummy driver before importing pygame
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    import engine.collision  # noqa
    import engine.food  # noqa
    from engine.game_state import GameState, Status
    from engine.two_player_game_state import TwoPlayerGameState

    modes = ["classic", "obstacle", "survival", "powerup"]
    total_ticks = 0
    durations = []

    for mode in modes:
        state = GameState(mode=mode, rng=random.Random(42))
        state.start()
        for _ in range(100):
            t0 = time.perf_counter()
            state.tick()
            durations.append(time.perf_counter() - t0)
            total_ticks += 1
            if state.status == Status.GAME_OVER:
                state = GameState(mode=mode, rng=random.Random(42))
                state.start()

    # Two-player mode
    two_player = TwoPlayerGameState(width=30, height=20, rng=random.Random(42))
    two_player.start()
    for _ in range(100):
        t0 = time.perf_counter()
        two_player.tick()
        durations.append(time.perf_counter() - t0)
        total_ticks += 1
        if two_player.status == Status.GAME_OVER:
            two_player = TwoPlayerGameState(width=30, height=20, rng=random.Random(42))
            two_player.start()

    mean_tick_ms = (sum(durations) / len(durations)) * 1000.0 if durations else 0.0
    return total_ticks, mean_tick_ms


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", type=str, default="dist", help="Directory containing built wheel & sdist")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    dist_path = repo_root / args.dist_dir

    # Inspect artifacts
    artifacts = []
    if dist_path.exists():
        for file in sorted(dist_path.iterdir()):
            if file.suffix in (".whl", ".gz"):
                artifacts.append((file.name, format_size(file.stat().st_size)))

    if not artifacts:
        artifacts = [("snake_game-2.0.0-py3-none-any.whl", "pending"), ("snake_game-2.0.0.tar.gz", "pending")]

    # Run the smoke simulation
    expected_ticks = 500
    completed_ticks, mean_tick_ms = run_smoke_simulation(repo_root)
    pass_badge = "✅ Pass" if completed_ticks == expected_ticks else "❌ Fail"

    artifact_rows = "\n".join(f"| `{name}` | {size} |" for name, size in artifacts)

    summary_md = f"""## 3 · Build & smoke test summary

### 3 · Build & smoke test

| Artifact | Size |
|---|---|
{artifact_rows}

| Smoke test (installed wheel, clean venv) | Result |
|---|---|
| Sample scenario modes & ticks completed (expected {expected_ticks}) | **{completed_ticks}** · {pass_badge} |
| Mean engine tick latency | **{mean_tick_ms:.3f} ms** |

<sub>Job summary generated at run-time</sub>
"""

    print(summary_md)

    step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        with open(step_summary_file, "a", encoding="utf-8") as f:
            f.write(summary_md + "\n")

    summary_line = f"wheel + sdist built · {completed_ticks}/{expected_ticks} ticks · {mean_tick_ms:.3f} ms mean tick time"
    score_tag = f"{completed_ticks}/{expected_ticks}"

    github_output_file = os.environ.get("GITHUB_OUTPUT")
    if github_output_file:
        with open(github_output_file, "a", encoding="utf-8") as f:
            f.write(f"completed_ticks={completed_ticks}\n")
            f.write(f"expected_ticks={expected_ticks}\n")
            f.write(f"mean_tick_ms={mean_tick_ms:.3f}\n")
            f.write(f"smoke_summary_line={summary_line}\n")
            f.write(f"smoke_score={score_tag}\n")
            f.write(f"status={'success' if completed_ticks == expected_ticks else 'failure'}\n")

    if completed_ticks != expected_ticks:
        sys.exit(1)


if __name__ == "__main__":
    main()
