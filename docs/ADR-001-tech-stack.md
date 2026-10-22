# ADR-001: Technology Stack

Status: Accepted (Sprint 1)
Date: 19-10-2026
Deciders: Team 6

## Context
The SRS and SAD leave the implementation technology and tools as TBD. The SRS
requires a Windows desktop game, keyboard input, a 1280x720 display, a local
database, and modular components that can be tested independently.

## Decision
| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.12 | Fast to develop, easy for the whole team |
| Game and UI | Pygame | Real-time loop, keyboard input, 2D drawing |
| Database | SQLite (stdlib `sqlite3`) | Local, file-based, no server (SAD 3.6) |
| Password hashing | bcrypt | Secure one-way hashing (SNAKE-SR-001) |
| Testing | unittest / pytest | Runs in CI on every PR |
| Linting | flake8 | Consistent style in CI |
| CI | GitHub Actions (windows-latest) | Matches the supported OS |

## Consequences
- Core game logic (`engine/`) has no Pygame imports, so it is unit testable and
  the UI only renders the state (supports SNAKE-NF-005 modularity).
- Two-Player Battle runs on one keyboard (WASD and arrow keys), so no
  networking is required for core gameplay (SRS 3.4).
- Replaces the "Tools: TBD" entries in SAD 5.3 and STP section 6.
