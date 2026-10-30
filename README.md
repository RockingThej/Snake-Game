# A Snake Game

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
Survival. The development runner lets you select them with keys `1` through
`5`. Classic is implemented; selecting another registered mode reports that
it is not implemented yet and returns to the mode list.

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

## Team 6

- Thejaswi S
- Vishnu Maddirala
- V S Shashidharan
- Vishwas Hosamath

## Documentation

- Software Requirements Specification (SRS)
- Software Architecture and Design Specification (SAD)
- Software Test Plan (STP)
