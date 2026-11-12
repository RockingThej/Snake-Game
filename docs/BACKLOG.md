# GitHub Product & Sprint Backlog

## Project: A Snake Game (Team 6)
**Software Engineering Course Project**  
**Repository:** [RockingThej/Snake-Game](https://github.com/RockingThej/Snake-Game)  
**Methodology:** Agile Scrum (2 Sprints, 2-week iterations)  
**Estimation Technique:** Fibonacci Story Points (1, 2, 3, 5, 8)  
**Sprint Status:** All Sprints Completed (100% Acceptance Rate, 31/31 Requirements Verified)

---

## 1. Scrum Team Roles & Responsibilities

| Role | Name | SRN | Primary Functional Ownership |
|---|---|---|---|
| **Product Owner & Engine Lead** | Thejaswi S | PES2UG24CS562 | Core Game Engine, Collision Algorithms, Game State Machine, Obstacle & Survival Engine Logic, Performance Benchmarks |
| **Scrum Master & Multiplayer Architect** | Vishnu Maddirala | PES2UG24CS593 | Two-Player Battle Mode, Dual-Input Dispatch, Multiplayer State Synchronization, Match Lifecycle & Winner Logic |
| **UI/UX & Gameplay Feature Lead** | V S Shashidharan | PES2UG24CS568 | Pygame UI Architecture, Screen Stack Manager, Power-Up Effects, Profile & Settings Screens, Admin GUI Visuals |
| **QA, Security & Persistence Lead** | Vishwas Hosamath | PES2UG24CS596 | SQLite Schema & Extensions, REST API Backend, Session Policies, Score Integrity Triggers, Admin Service, Security Suite & RTM |

---

## 2. Story Point Estimation Reference Scale

Story points quantify relative effort, technical complexity, risk, and dependencies:

* **1 Point (Trivial):** Minor documentation updates, constant tweaks, or cosmetic formatting.
* **2 Points (Simple):** Straightforward functions with minimal branching, simple UI text adjustments, basic validators.
* **3 Points (Moderate):** Self-contained algorithmic modules, simple screen layouts, standard CRUD repository queries.
* **5 Points (Complex):** Interactive UI screens with state machines, multi-condition collision detectors, session token lifecycle, database triggers.
* **8 Points (High Complexity):** Full game mode implementation with lifecycle rules, dual-player real-time arbitration, end-to-end admin subsystem with audit logging.

---

## 3. Sprint Summary & Velocity Metrics

| Sprint | Period | Planned SP | Completed SP | Velocity | Completion Rate |
|---|---|:---:|:---:|:---:|:---:|
| **Sprint 1** | Oct 16 – Oct 30, 2026 | 50 SP | 50 SP | 50 pts | 100% |
| **Sprint 2** | Oct 31 – Nov 11, 2026 | 60 SP | 60 SP | 60 pts | 100% |
| **Total** | Oct 16 – Nov 11, 2026 | **110 SP** | **110 SP** | **55 pts / sprint** | **100%** |

---

## 4. Sprint 1 Backlog: Foundation, Engine Core & Classic MVP

**Goal:** Deliver a playable, standalone Classic Snake game with user authentication, SQLite persistence, and high-performance Pygame rendering.

| Issue ID | User Story Title | User Story Description (`As a... I want... So that...`) | Epic | Story Points | Assignee | Status | Linked PR / Commit | Verified Requirement |
|---|---|---|---|:---:|---|:---:|---|---|
| **SG-02** | Tech Stack ADR & Initial Repo Setup | As a developer, I want an Architectural Decision Record and clean repo scaffolding, so that development conforms to standard conventions. | Infrastructure | **2** | Team 6 | Closed | PR #43 / `1d43104` | SNAKE-NF-005 |
| **S1-01** | Snake Movement & Direction Control | As a player, I want responsive direction controls (Arrow keys/WASD), so that the snake moves predictably across grid coordinates. | Engine Core | **3** | Thejaswi S | Closed | PR #44 / `09ca7dd` | SNAKE-F-009, SNAKE-NF-001 |
| **S1-02** | Food Generation & Consumption | As a player, I want food to spawn randomly on unoccupied tiles and grow the snake upon consumption, so that my score increases. | Engine Core | **3** | Thejaswi S | Closed | PR #45 / `7d599b9` | SNAKE-F-010, SNAKE-F-011 |
| **S1-03** | Collision Detection (Walls & Self) | As a player, I want the game to terminate when colliding with walls or the snake's own body, so that gameplay rules are enforced. | Engine Core | **5** | Thejaswi S | Closed | PR #46 / `ce5c602` | SNAKE-F-012 |
| **S1-04** | Classic Mode Game State & Dev Runner | As a player, I want a complete Classic Mode state machine, so that game start, run, game-over, and reset transitions function smoothly. | Game Modes | **5** | Thejaswi S | Closed | PR #47 / `25014e9` | SNAKE-F-018 |
| **S1-05** | Configurable Player Input Handler | As a player, I want customizable keybindings for movement and actions, so that I can configure my preferred control scheme. | Input & Controls | **3** | Vishnu M | Closed | PR #50 / `f458676` | SNAKE-F-009 |
| **S1-06** | SQLite Schema & Repositories | As a system, I want an SQLite database with tables for users, scores, and leaderboards, so that state is persisted locally across sessions. | Persistence | **5** | Vishwas H | Closed | PR #51 / `666ea1e` | SNAKE-F-019, SNAKE-NF-003 |
| **S1-07** | Difficulty Manager & Speed Levels | As a player, I want to choose between Easy (160ms), Medium (110ms), and Hard (75ms), so that gameplay speed adapts to my skill. | Game Modes | **2** | Thejaswi S | Closed | PR #52 / `649265a` | SNAKE-F-007 |
| **S1-08** | Game Mode Manager & Registry | As a system, I want a mode registry pattern, so that new game modes can be plugged in modularly without rewriting core engine code. | Architecture | **2** | V S Shashidharan | Closed | PR #53 / `c4b0c82` | SNAKE-F-006 |
| **S1-09** | Pause & Resume Controls | As a player, I want to press `P` to pause and resume gameplay, so that I can temporarily halt my session without losing game state. | Engine Core | **2** | Thejaswi S | Closed | PR #54 / `ec91470` | SNAKE-F-008 |
| **S1-10** | UI Framework & Screen Manager | As a player, I want smooth transitions across login, menu, and gameplay screens, so that the game has a cohesive graphical shell. | User Interface | **5** | V S Shashidharan | Closed | PR #55 / `7fdcb42` | SNAKE-F-005, SNAKE-NF-004 |
| **S1-11** | Login & Registration Screens | As a user, I want graphical forms to register an account and log in, so that my personal high scores can be recorded. | User Interface | **3** | V S Shashidharan | Closed | PR #58 / `2a8cd9f` | SNAKE-F-001, SNAKE-F-002 |
| **S1-12** | Main Menu, Mode & Difficulty Menus | As a player, I want intuitive menus with keyboard shortcuts, so that I can start a game within 3 menu actions. | User Interface | **3** | V S Shashidharan | Closed | PR #57 / `7ea623c` | SNAKE-NF-004 |
| **S1-13** | Game Board Rendering & HUD | As a player, I want visual grid rendering, colorful snake bodies, and an informative heads-up display showing score and level. | User Interface | **5** | V S Shashidharan | Closed | PR #56 / `0c159ba` | SNAKE-NF-002 |
| **S1-16** | Secure Authentication Service | As a user, I want my password hashed with bcrypt and verified during login, so that plaintext passwords are never stored. | Security | **3** | Vishwas H | Closed | PR #60 / `5d9f018` | SNAKE-SR-001 |
| **S1-17** | Launcher Integration & Flow | As a user, I want a unified executable launcher linking login, menus, gameplay, score recording, and leaderboards. | Integration | **5** | Team 6 | Closed | PR #61 / `fc46f7d` | SNAKE-F-005, SNAKE-F-020 |
| **S1-18** | Sprint 1 Outcome Video | As stakeholders, we want a recorded 1-minute video demonstrating Sprint 1 working software. | Deliverable | **1** | Team 6 | Closed | Commit `6a8c17a` | `docs/Demo_Sprint_1.mp4` |

*Sprint 1 Velocity Total: 52 Story Points Delivered.*

---

## 5. Sprint 2 Backlog: Advanced Modes, Security, Admin Subsystem & Polish

**Goal:** Implement all four remaining game modes, provide a multi-level administration subsystem, enforce score immutability triggers, implement security hardening, and achieve 100% automated test verification.

| Issue ID | User Story Title | User Story Description (`As a... I want... So that...`) | Epic | Story Points | Assignee | Status | Linked PR / Commit | Verified Requirement |
|---|---|---|---|:---:|---|:---:|---|---|
| **S2-01** | Obstacle Mode Engine & Placement | As a player, I want static obstacles placed on ~4% of the board with flood-fill path validation, so that gameplay offers navigation challenges without unreachable pockets. | Game Modes | **5** | Thejaswi S | Closed | PR #66 / `908b7d9` | SNAKE-F-014, SNAKE-F-012 |
| **S2-02** | Survival Mode Progressive Scaling | As a player, I want difficulty and obstacles to increase dynamically every 3 food items eaten, so that survival becomes progressively challenging. | Game Modes | **5** | Thejaswi S | Closed | PR #66 / `908b7d9` | SNAKE-F-017 |
| **S2-03** | Engine Performance Optimization & $O(1)$ Collisions | As a developer, I want constant-time self-collision checking and sub-millisecond ticks, so that the game exceeds 30 FPS under load. | Performance | **3** | Thejaswi S | Closed | PR #66 / `908b7d9` | SNAKE-NF-001, SNAKE-NF-002 |
| **S2-05** | Two-Player Battle Engine & Dual Input | As two players, we want to play simultaneously on one screen using WASD (P1) and Arrow keys (P2), so that we can compete in real-time. | Multiplayer | **8** | Vishnu M | Closed | PR #67 / `078dc08` | SNAKE-F-016 |
| **S2-06** | Battle Collision Arbitrator & Winner Logic | As players, we want head-to-head collisions resolved accurately (awarding wins on body hits, draws on simultaneous head clashes), so that matches conclude fairly. | Multiplayer | **5** | Vishnu M | Closed | PR #67 / `c7380bb` | SNAKE-F-016, SNAKE-F-012 |
| **S2-07** | Battle Scoring & Results Screen | As multiplayer competitors, we want a dedicated post-match summary screen showing winner, final lengths, and head-to-head stats. | Multiplayer | **3** | Vishnu M | Closed | PR #62 / `fb58253` | SNAKE-F-016 |
| **S2-08** | Multiplayer Automated Test Suite | As QA, I want exhaustive tests for edge cases like simultaneous food capture, opposite-direction inputs, and corner traps. | Quality Assurance | **3** | Vishnu M | Closed | PR #65 / `9a7b01b` | SNAKE-F-016 |
| **S2-09** | Power-Up Mode with 5 Power-Up Types | As a player, I want temporary power-ups (Speed, Slow, Shield, 2x Multiplier, Shrink), so that gameplay has dynamic strategic variety. | Game Modes | **8** | V S Shashidharan | Closed | PR #73 / `6b0db5d` | SNAKE-F-015 |
| **S2-10** | Game Mode Visuals, Obstacles & Power-Up Icons | As a player, I want distinct visual themes and icons for obstacles, power-ups, and survival levels on the Pygame board. | User Interface | **3** | V S Shashidharan | Closed | PR #73 / `c5cc689` | SNAKE-F-014, SNAKE-F-015, SNAKE-F-017 |
| **S2-11** | Player Profile & Settings Screen | As a player, I want to inspect personal game history, win rates, high scores per mode, and adjust local key maps and sound options. | User Interface | **3** | V S Shashidharan | Closed | PR #73 / `407bc14` | SNAKE-F-003 |
| **S2-12** | Administrator Graphical Screens | As an administrator, I want dedicated screens to manage users, toggle account status, inspect audit logs, and configure global speed settings. | Administration | **5** | V S Shashidharan | Closed | PR #73 / `365889d` | SNAKE-SR-002 |
| **S2-13** | Guarded Sessions & Session Termination | As a security engineer, I want idle timeout (2h desktop / 30m web), absolute expiration, and explicit logout invalidation. | Security | **5** | Vishwas H | Closed | PR #69 / `d13849a` | SNAKE-F-004, SNAKE-SR-005 |
| **S2-14** | Administration Service & CLI Subsystem | As a system administrator, I want an isolated service layer and CLI (`python -m admin`) for user management, role grants, and config overrides. | Administration | **5** | Vishwas H | Closed | PR #70 / `cec6877` | SNAKE-SR-002 |
| **S2-15** | Player Statistics & Global Aggregation | As a user and admin, I want SQL aggregations calculating win/loss ratios, per-mode performance, and 7-day play trends. | Analytics | **3** | Vishwas H | Closed | PR #68 / `a826341` | SNAKE-F-003 |
| **S2-16** | Database Score & Leaderboard Integrity Triggers | As a system, I want SQLite triggers forbidding direct score updates, and integrity verification utilities to repair corrupted boards. | Security & DB | **5** | Vishwas H | Closed | PR #71 / `fd00b4b` | SNAKE-SR-004, SNAKE-F-019 |
| **S2-17** | Comprehensive Security Test Suite | As QA, I want automated verification covering bcrypt hash storage, SQL injection resistance, session reuse denial, and RTM checks. | Quality Assurance | **5** | Vishwas H | Closed | PR #72 / `0c66add` | SNAKE-SR-001 through SNAKE-SR-005 |
| **S2-18** | IEEE Documentation Update & Deviations Log | As stakeholders, we want updated IEEE SRS, SAD, and STP artifacts with formal deviation documentation and RTM alignment. | Documentation | **3** | Team 6 | Closed | Commit `a504e49` | docs/SRS.md, SAD.md, STP.md |
| **S2-19** | Bug-Fix Buffer & Edge-Case Hardening | As developers, we want a dedicated stabilization buffer to eliminate regressions, resolve multiplayer boundary crashes, and refine power-up expiry. | Hardening | **3** | Team 6 | Closed | Commit `2c00b47` | All modules |
| **S2-20** | Sprint 2 Outcome Video Demonstration | As stakeholders, we want a 2-minute video demonstrating all advanced game modes, admin tools, profile screens, and security behaviors. | Deliverable | **1** | Team 6 | Closed | `docs/Demo_Sprint_2.mp4` | `docs/Demo_Sprint_2.mp4` |

*Sprint 2 Velocity Total: 61 Story Points Delivered.*

---

## 6. Definition of Done (DoD)

A user story is considered complete and accepted only when:
1. **Implementation:** Fully coded complying with PEP 8 and the modular architecture.
2. **Automated Testing:** Backed by automated unit and integration tests with 100% pass rate.
3. **Traceability:** Linked to a designated SRS Functional (`SNAKE-F-*`), Non-Functional (`SNAKE-NF-*`), or Security (`SNAKE-SR-*`) requirement.
4. **Security & Input Validation:** Inputs sanitized, boundary conditions handled, authorization rules enforced.
5. **Code Review:** Submitted, peer-reviewed, and merged via pull request.
6. **Documentation & RTM:** Updated in the Requirements Traceability Matrix (`docs/RTM.md`).
