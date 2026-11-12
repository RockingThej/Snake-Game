# A Snake Game

Software Engineering mini-project, Section J, Team 6, PES University. Version 2.0 (v1.0 froze development at the end of Sprint 1 on 30 Oct 2026; Sprint 2 completed all 5 game modes, admin subsystem, security hardening, and final verification on 11 Nov 2026).

| SRN | Name | Role | GitHub |
|---|---|---|---|
| PES2UG24CS562 | Thejaswi S | Dev Lead / Engine Lead, repo owner | [@RockingThej](https://github.com/RockingThej) |
| PES2UG24CS593 | Vishnu Maddirala | Developer / Multiplayer & Database | [@vishnu-1107-cloud](https://github.com/vishnu-1107-cloud) |
| PES2UG24CS568 | V S Shashidharan | Developer / UI & Game Modes | [@shashidharanvs](https://github.com/shashidharanvs) |
| PES2UG24CS596 | Vishwas Hosamath | QA Lead / Security & Testing | [@Vishwas-H-sys](https://github.com/Vishwas-H-sys) |

A modular Snake Game developed as a Software Engineering project, designed to provide multiple gameplay experiences while maintaining separate and maintainable game components.

The game allows players to create accounts, select different game modes and difficulty levels, play, earn scores, and compete on leaderboards.

## Game Modes

- **Classic Mode** – Traditional Snake gameplay with food collection and increasing score.
- **Obstacle Mode** – Navigate the board while avoiding obstacles.
- **Power-Up Mode** – Collect temporary power-ups that affect gameplay.
- **Survival Mode** – Survive as long as possible while the difficulty progressively increases.
- **Two-Player Battle** – Two players control separate snakes on the same board.

## Features

- Player registration and authentication
- Multiple game modes and difficulty levels
- Snake movement and collision detection
- Score calculation and score storage
- Power-ups and progressive difficulty
- Two-player gameplay
- Player profiles
- Leaderboards
- Pause and resume functionality
- Secure account and data handling

## Project Structure

The project follows a modular architecture with separate components for the game engine, game modes, collision detection, scoring, user management, leaderboard, database, and administration.

## Database

The SQLite database and its `users`, `scores`, and `leaderboard` tables are
created automatically when the game starts. The default database file is kept
in the operating system's local application data directory. Set
`SNAKE_GAME_DB_PATH` to use a different file.

Database access is contained in `db/`. Use its repository functions, such as
`create_user`, `save_score`, `get_scores_for_user`, and `get_leaderboard`, rather
than issuing SQL from other modules. `create_user` requires a precomputed
`password_hash`; callers must never pass a plaintext password. The leaderboard
stores each player's personal best, while `scores` retains every completed
game and its mode and difficulty.

## Difficulty

Choose Easy, Medium, or Hard before starting a game with keys `1`, `2`, or `3`.
The default movement intervals are 160 ms, 110 ms, and 75 ms respectively;
lower intervals make the snake move faster. Medium preserves the former runner
speed. The SRS names difficulty selection but does not define numeric speeds.

## Game modes

The mode registry lists Classic, Obstacle, Power-Up, Two-Player Battle, and
Survival. The mode screen lets you select them with keys `1` through `5`.
Classic, Obstacle, and Survival are implemented; selecting Power-Up or
Two-Player Battle reports that it is not implemented yet and returns to the
mode list.

- **Obstacle Mode** places obstacles on about 4% of the board when the game
  starts. They never cover the snake or the cells right in front of it, and
  they never wall off part of the board, so every cell stays reachable.
  Hitting one ends the game.
- **Survival Mode** starts with an empty board and gets harder as you eat:
  every 3 foods the level goes up, the snake moves 8 ms faster (never below
  40 ms), and 2 more obstacles appear (up to 10% of the board). The current
  level is shown in the HUD.

Mode rules live in `modes/rules.py`; obstacle placement is in
`engine/obstacles.py`.

## Performance

`python benchmarks/engine_benchmark.py` measures the engine against the SRS
budgets (30 FPS, 100 ms input response). The engine uses well under 1% of a
frame; see `docs/performance.md` for the numbers.

## Pause and resume

Press `P` during gameplay to pause. The pause menu freezes movement and shows
the resume option; press `Enter`, `Space`, or `P` to continue the same session.

## Running the game

```
pip install -r requirements.txt
python main.py
```

`main.py` opens the login screen (F2 switches to Create account), then the
main menu, mode and difficulty screens, the game, a results screen that saves
your score, and the leaderboard. `run.py` is separate: it starts the Flask
backend only.

## Documentation & Viva Deliverables

- [Software Requirements Specification (SRS v2.0 - IEEE Format)](docs/SRS.md)
- [Software Architecture and Design Specification (SAD v2.0 - IEEE Format)](docs/SAD.md)
- [Software Test Plan (STP v2.0 - IEEE Format)](docs/STP.md)
- [GitHub Product & Sprint Backlog (with Story Points)](docs/BACKLOG.md)
- [Unit Testing Report (328/328 Passed)](docs/unit_test_report.md)
- [System Validation Testing Report (292/292 Passed)](docs/system_validation_report.md)
- [Code Coverage Report (83% Codebase Coverage)](docs/code_coverage_report.md)
- [Branch Coverage Report (86% Branch Coverage)](docs/branch_coverage_report.md)
- [Sprint 1 Outcome Video (1 min)](docs/Demo_Sprint_1.mp4)
- [Sprint 2 Outcome Video (2 min)](docs/Demo_Sprint_2.mp4)
- [Requirements Traceability Matrix (RTM - 31/31 Verified)](docs/RTM.md)
- [Project Deviations & Architectural Decisions Report](docs/deviations.md)
- [Performance & Benchmarks Report](docs/performance.md)
- [Sprint 2 Modules Guide](docs/SPRINT2-modules.md)
- [ADR-001: Technology Stack](docs/ADR-001-tech-stack.md)
- Original Drafts (Sprint 0 Baseline): [SRS PDF](SnakeGame_Team6_SRS.pdf), [SAD PDF](SnakeGame_Team6_SAD.pdf), [STP PDF](SnakeGame_Team6_STP.pdf)
