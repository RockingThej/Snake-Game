# GitHub Product & Sprint Backlog

## Project: A Snake Game (Team 6)
**Software Engineering Course Project**  
**Repository:** [RockingThej/Snake-Game](https://github.com/RockingThej/Snake-Game)  
**Methodology:** Agile Scrum (2 Sprints, 2-week iterations)  
**Estimation Technique:** Fibonacci Story Points (1, 2, 3, 5, 8)  
**Board Status:** 42 / 42 Issues Completed (100% Done, All Closed)

---

## 1. Scrum Team Members & Roles

| Team Member | GitHub Username | SRN | Primary Functional Responsibilities |
|---|---|---|---|
| **Thejaswi S** | `@RockingThej` | PES2UG24CS562 | Game Engine Core, Collision Detection, Obstacle & Survival Modes, Performance Benchmarks |
| **Vishnu Maddirala** | `@vishnu-1107-cloud` | PES2UG24CS593 | Two-Player Battle Mode, Dual Input Dispatch, Multiplayer Collisions & Battle Scoring |
| **V S Shashidharan** | `@shashidharanvs` | PES2UG24CS568 | UI Framework, Screen Flow & HUD, Power-Up Mode & Visuals, Profile, Settings & Admin Screens |
| **Vishwas Hosamath** | `@Vishwas-H-sys` | PES2UG24CS596 | Authentication & Bcrypt Hashing, Session Management, Admin Subsystem, Score Integrity & Security Suite |

---

## 2. Story Point Estimation Reference Scale

Story points quantify relative effort, technical complexity, risk, and dependencies:

* **1 Point (Trivial):** Documentation freezes, tag creation, minor configuration updates.
* **2 Points (Simple):** Simple parameter managers, basic validation utilities, single-purpose helper functions.
* **3 Points (Moderate):** Self-contained algorithmic modules, screen implementations, statistics aggregators.
* **5 Points (Complex):** Interactive UI state machines, multi-condition collision detectors, session token lifecycle, database triggers.
* **8 Points (High Complexity):** Complete game mode lifecycle implementation (Power-Up mode with 5 distinct power-ups, Two-Player battle arbitration).

---

## 3. Sprint Summary & Velocity Metrics

| Sprint | Issues | Planned SP | Completed SP | Velocity | Completion Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Sprint 0 / Scaffolding** | #1 - #2 | 4 SP | 4 SP | 4 pts | 100% |
| **Sprint 1** | #3 - #22 | 57 SP | 57 SP | 57 pts | 100% |
| **Sprint 2** | #23 - #42 | 68 SP | 68 SP | 68 pts | 100% |
| **Total** | **42 Issues** | **129 SP** | **129 SP** | **~60 pts / sprint** | **100%** |

---

## 4. Sprint 0: Architecture & Infrastructure Setup

| Issue # | Title | Assignee | Story Points | Status | Linked PR | Scope & Description |
|---|---|---|:---:|:---:|---|---|
| **#1** | `[SG-02] Tech stack decision and ADR` | `@RockingThej` | **2** | Done | PR #43 | Architecture Decision Record (ADR-001) for Python/Pygame/SQLite stack. |
| **#2** | `[SG-03] CI workflow, PR template, branch protection` | `@Vishwas-H-sys` | **2** | Done | - | GitHub Actions CI workflow, PR templates, and branch rules. |

---

## 5. Sprint 1 Backlog: Foundation, Engine Core & Classic MVP

| Issue # | Title | Assignee | Story Points | Status | Linked PR | Scope & Description |
|---|---|---|:---:|:---:|---|---|
| **#3** | `[S1-01] Snake Controller: continuous movement and direction changes` | `@RockingThej` | **3** | Done | PR #44 | Snake vector heading, coordinate updates, opposite-direction lock. |
| **#4** | `[S1-02] Food generation and consumption` | `@RockingThej` | **3** | Done | PR #45 | Stochastic food generation on unoccupied cells, body growth on consumption. |
| **#5** | `[S1-03] Wall and self collision detection` | `@RockingThej` | **5** | Done | PR #46 | Grid bounds checking and constant-time $O(1)$ body coordinate collision. |
| **#6** | `[S1-04] Game Manager and Classic Mode loop` | `@RockingThej` | **5** | Done | PR #47 | Classic mode state machine (Ready, Running, GameOver), tick timer. |
| **#7** | `[S1-05] Input handler with configurable key maps` | `@vishnu-1107-cloud` | **3** | Done | - | Key event translation, dual player layout resolution (WASD/Arrows). |
| **#8** | `[S1-06] Database Layer: SQLite schema and repositories` | `@vishnu-1107-cloud` | **5** | Done | - | SQLite schema creation (`users`, `scores`, `leaderboard`), repository CRUD. |
| **#9** | `[S1-07] Difficulty Manager (speed levels)` | `@vishnu-1107-cloud` | **2** | Done | - | Easy (160ms), Medium (110ms), and Hard (75ms) interval mappings. |
| **#10** | `[S1-08] Game Mode Manager: registry for the five modes` | `@vishnu-1107-cloud` | **2** | Done | - | Registry pattern for Classic, Obstacle, Power-Up, Two-Player, Survival. |
| **#11** | `[S1-09] Pause and resume` | `@vishnu-1107-cloud` | **2** | Done | - | Pause toggling (`P` key), state conservation, seamless resume. |
| **#12** | `[S1-10] Screen manager and UI framework` | `@shashidharanvs` | **5** | Done | PR #55 | Stack-based screen transitions (push, pop, replace) in Pygame. |
| **#13** | `[S1-11] Login and Register screens` | `@shashidharanvs` | **3** | Done | PR #58 | Interactive text inputs, cursor management, password masking. |
| **#14** | `[S1-12] Main menu, mode, difficulty and game-over screens` | `@shashidharanvs` | **3** | Done | PR #57 | Navigable menu screens, keyboard shortcuts, game-over summary. |
| **#15** | `[S1-13] Game board rendering and HUD` | `@shashidharanvs` | **5** | Done | PR #56 | Grid rendering, snake segment drawing, score & difficulty HUD. |
| **#16** | `[S1-14] Registration with bcrypt password hashing` | `@Vishwas-H-sys` | **3** | Done | - | Bcrypt password hashing with automatic salt generation on registration. |
| **#17** | `[S1-15] Authentication and session handling` | `@Vishwas-H-sys` | **3** | Done | - | Credential verification, session token generation, login state tracking. |
| **#18** | `[S1-16] Input validation utilities` | `@Vishwas-H-sys` | **2** | Done | - | Username regex validation, password length bounds, sanitization. |
| **#19** | `[S1-17] Score Manager: calculation and save` | `@Vishwas-H-sys` | **3** | Done | - | Score calculation and historical persistence into SQLite. |
| **#20** | `[S1-18] Basic Leaderboard` | `@Vishwas-H-sys` | **3** | Done | - | High score aggregation, ranking queries, top-N leaderboard display. |
| **#21** | `[S1-19] Unit tests for Sprint 1 modules` | `@Vishwas-H-sys` | **3** | Done | - | Automated unit test suite covering engine, db, and auth modules. |
| **#22** | `[S1-20] Record and upload 1-minute Sprint 1 demo video` | `@RockingThej` | **1** | Done | - | Recorded and placed 1-minute video in `docs/Demo_Sprint_1.mp4`. |

---

## 6. Sprint 2 Backlog: Advanced Modes, Security, Admin Subsystem & Polish

| Issue # | Title | Assignee | Story Points | Status | Linked PR | Scope & Description |
|---|---|---|:---:|:---:|---|---|
| **#23** | `[S2-01] Obstacle Mode: obstacle placement and collision` | `@RockingThej` | **5** | Done | PR #66 | ~4% obstacle generation with BFS flood-fill reachability guarantee. |
| **#24** | `[S2-02] Survival Mode: progressive difficulty` | `@RockingThej` | **5** | Done | PR #66 | Dynamic acceleration and progressive obstacle spawning every 3 foods. |
| **#25** | `[S2-03] Performance tuning and measurement` | `@RockingThej` | **3** | Done | PR #66 | Sub-millisecond tick benchmarks (<1.1 ms), 30+ FPS compliance. |
| **#26** | `[S2-04] Engine unit and integration tests` | `@RockingThej` | **3** | Done | PR #66 | Automated bot integration tests running full simulated games across modes. |
| **#27** | `[S2-05] Two-Player Battle: two snakes and dual input` | `@vishnu-1107-cloud` | **8** | Done | - | Real-time dual snake simulation: P1 (WASD) vs P2 (Arrow keys). |
| **#28** | `[S2-06] Snake-to-snake collision and winner logic` | `@vishnu-1107-cloud` | **5** | Done | - | Collision arbitration: body hits award kills, simultaneous head hits draw. |
| **#29** | `[S2-07] Battle scoring and results screen` | `@vishnu-1107-cloud` | **3** | Done | - | Post-match battle summary screen showing winner and final lengths. |
| **#30** | `[S2-08] Multiplayer tests` | `@vishnu-1107-cloud` | **3** | Done | - | Edge cases: simultaneous food consumption, corner entrapment, draws. |
| **#31** | `[S2-09] Power-Up Mode with five power-ups` | `@shashidharanvs` | **8** | Done | PR #73 | Speed Boost, Slow Down, Shield, 2x Multiplier, and Snake Shrink. |
| **#32** | `[S2-10] Visuals for obstacle, power-up and survival modes` | `@shashidharanvs` | **3** | Done | PR #73 | Custom colors, icons, power-up timers, and survival level displays. |
| **#33** | `[S2-11] Player profile and settings screens` | `@shashidharanvs` | **3** | Done | PR #73 | Personal stats view, high scores per mode, audio and keymap settings. |
| **#34** | `[S2-12] Administrator interface screens` | `@shashidharanvs` | **5** | Done | PR #73 | Graphical admin screens for user management, audit logs, and config. |
| **#35** | `[S2-13] Logout and session termination` | `@Vishwas-H-sys` | **5** | Done | - | Idle timeout (2h desktop / 30m API), absolute timeout, logout-all. |
| **#36** | `[S2-14] Administration module` | `@Vishwas-H-sys` | **5** | Done | - | AdminService API, CLI subsystem (`python -m admin`), audit logging. |
| **#37** | `[S2-15] Statistics module` | `@Vishwas-H-sys` | **3** | Done | - | Player and global statistical calculations, win rates, 7-day trend. |
| **#38** | `[S2-16] Score and leaderboard integrity` | `@Vishwas-H-sys` | **5** | Done | - | SQLite triggers preventing direct UPDATEs, repair/rebuild tools. |
| **#39** | `[S2-17] Security test suite and RTM status update` | `@Vishwas-H-sys` | **5** | Done | - | Automated security test suite (`test_security_suite.py`) and RTM sync. |
| **#40** | `[S2-18] Update SRS, SAD and STP; document deviations` | `@RockingThej` | **3** | Done | - | Post-Sprint 2 updates to SRS, SAD, STP and `deviations.md`. |
| **#41** | `[S2-19] Bug-fix buffer` | `@RockingThej` | **3** | Done | - | Stabilization buffer for edge cases, power-up expiry, and multi-collisions. |
| **#42** | `[S2-20] Record 2-minute demo video, freeze and tag v1.0` | `@RockingThej` | **1** | Done | - | Recorded and placed 2-minute video in `docs/Demo_Sprint_2.mp4`. |

---

## 7. Definition of Done (DoD) Checklist

For any user story to be marked as **Done / Closed**, it must fulfill:
1. **Implementation:** Fully coded according to modular architecture guidelines.
2. **Automated Testing:** Backed by unit and integration tests (620 tests, 100% pass rate).
3. **Traceability:** Linked to a designated SRS Functional, Non-Functional, or Security requirement.
4. **Security & Input Validation:** Inputs sanitized, boundary conditions handled, authorization rules enforced.
5. **Code Review:** Peer-reviewed and merged via GitHub Pull Request.
6. **Documentation & RTM:** Updated in the Requirements Traceability Matrix (`docs/RTM.md`).
