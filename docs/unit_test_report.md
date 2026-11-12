# Final Unit Test Execution Report

## Project: A Snake Game (Team 6)
**Software Engineering Course Project — Final Viva Submission**  
**Execution Environment:** Python 3.13.18, pytest 9.2.0, Windows 11  
**Execution Date:** 12-11-2026  
**Status:** **100% PASSED (328/328 Tests)**  
**Duration:** 95.18 seconds  

---

## 1. Executive Summary

The Snake Game unit test suite provides comprehensive, automated verification of all core logic components in isolation, including game engine state transitions, collision detection algorithms, obstacle reachability mathematics, scoring algorithms, session policy token lifecycles, and database repositories.

| Metric | Result |
|---|---|
| **Total Unit Tests Executed** | **328** |
| **Passed** | **328 (100.0%)** |
| **Failed** | **0 (0.0%)** |
| **Errors** | **0 (0.0%)** |
| **Skipped** | **0** |
| **Subtests Passed** | **44** |

---

## 2. Test Execution Breakdown by Module

| Module / Test File | Target Package | Number of Tests | Status | Execution Scope & Verification Objective |
|---|---|:---:|:---:|---|
| [`test_auth.py`](file:///C:/Snake-Game/tests/test_auth.py) | `auth`, `app.auth` | 9 | PASSED | Registration input validation, bcrypt password hashing, duplicate detection. |
| [`test_auth_service.py`](file:///C:/Snake-Game/tests/test_auth_service.py) | `auth.auth_service` | 2 | PASSED | Account credential verification, password verification against hash. |
| [`test_database.py`](file:///C:/Snake-Game/tests/test_database.py) | `db` | 8 | PASSED | First-run schema creation, idempotency, foreign key integrity, repository transactions. |
| [`test_difficulty.py`](file:///C:/Snake-Game/tests/test_difficulty.py) | `modes.difficulty` | 10 | PASSED | Easy, Medium, Hard tick intervals (160ms, 110ms, 75ms) and custom admin overrides. |
| [`test_engine.py`](file:///C:/Snake-Game/tests/test_engine.py) | `engine` | 15 | PASSED | $O(1)$ body collision detection, wall collisions, direction locking, food consumption. |
| [`test_input_handler.py`](file:///C:/Snake-Game/tests/test_input_handler.py) | `ui.input_handler` | 4 | PASSED | Dual player keymap parsing, WASD and Arrow key resolution, invalid key filtering. |
| [`test_leaderboard.py`](file:///C:/Snake-Game/tests/test_leaderboard.py) | `db.leaderboard_repository` | 4 | PASSED | Personal best score aggregation, ranking order, leaderboard row limits. |
| [`test_modes.py`](file:///C:/Snake-Game/tests/test_modes.py) | `modes.manager` | 6 | PASSED | Mode registry, 5 mode implementations, state factory instantiation. |
| [`test_obstacle_mode.py`](file:///C:/Snake-Game/tests/test_obstacle_mode.py) | `modes.obstacle`, `engine.obstacles` | 25 | PASSED | ~4% obstacle placement, flood-fill BFS board reachability, obstacle collisions. |
| [`test_pause_resume.py`](file:///C:/Snake-Game/tests/test_pause_resume.py) | `engine.game_state` | 4 | PASSED | Pause freeze semantics, state conservation, unpause continuation. |
| [`test_powerups.py`](file:///C:/Snake-Game/tests/test_powerups.py) | `modes.powerups` | 9 | PASSED | Speed Boost, Slow Down, Shield, 2x Multiplier, Snake Shrink lifecycles. |
| [`test_score_integrity.py`](file:///C:/Snake-Game/tests/test_score_integrity.py) | `scoring.integrity` | 42 | PASSED | Sanity checks on score, mode ID validation, tamper detection, leaderboard rebuild. |
| [`test_score_manager.py`](file:///C:/Snake-Game/tests/test_score_manager.py) | `scoring.score_manager` | 3 | PASSED | Score formatting, persistence hooks, player association. |
| [`test_scores.py`](file:///C:/Snake-Game/tests/test_scores.py) | `db.score_repository`, `app.scores` | 7 | PASSED | Score insertion, per-user score querying, negative score refusal. |
| [`test_screen_manager.py`](file:///C:/Snake-Game/tests/test_screen_manager.py) | `ui.screen_manager` | 4 | PASSED | Stack operations (push, pop, replace), default screen resolution. |
| [`test_session.py`](file:///C:/Snake-Game/tests/test_session.py) | `ui.session` | 5 | PASSED | Session state tracking, active user binding, logout clearing. |
| [`test_session_manager.py`](file:///C:/Snake-Game/tests/test_session_manager.py) | `auth.session_manager` | 24 | PASSED | Cryptographic token generation, SHA-256 storage, idle/absolute expiry. |
| [`test_snake_bookkeeping.py`](file:///C:/Snake-Game/tests/test_snake_bookkeeping.py) | `engine.snake` | 4 | PASSED | Hash set body coordinate maintenance for constant time lookup ($O(1)$). |
| [`test_statistics.py`](file:///C:/Snake-Game/tests/test_statistics.py) | `scoring.stats`, `db.stats_repository` | 20 | PASSED | User win/loss ratios, per-mode averages, 7-day play history aggregation. |
| [`test_survival_mode.py`](file:///C:/Snake-Game/tests/test_survival_mode.py) | `modes.survival`, `modes.rules` | 15 | PASSED | Progressive speed acceleration every 3 foods, dynamic obstacle placement. |
| [`test_two_player.py`](file:///C:/Snake-Game/tests/test_two_player.py) | `engine.two_player_game_state` | 9 | PASSED | Simultaneous independent motion, head-to-body kills, head-to-head draw logic. |
| [`test_validators.py`](file:///C:/Snake-Game/tests/test_validators.py) | `app.validators` | 32 | PASSED | Username regex, password strength, integer bounds, XSS sanitation. |
| [`test_admin_service.py`](file:///C:/Snake-Game/tests/test_admin_service.py) | `admin.service`, `db.admin_repository` | 67 | PASSED | Non-admin denial on every endpoint, user disablement, password reset, audit logs. |

---

## 3. Notable Verified Logic Gates

1. **$O(1)$ Self-Collision Detection:**
   - Rather than scanning an $O(N)$ body array every frame, `engine/snake.py` maintains an internal `set` of occupied grid coordinates. Verified with snake lengths up to 5,000 segments.
2. **Flood-Fill Reachability Guarantee:**
   - `engine/obstacles.py` verifies using Breadth-First Search (BFS) that no generated obstacle walls off any free grid area. 100% of reachable cells stay connected.
3. **Multi-Condition Two-Player Head Clash Resolution:**
   - Verified that when Player 1 and Player 2 step into each other's head on the same tick, the match evaluates as a `DRAW`. When Player 1 hits Player 2's body, Player 2 is awarded the `WIN`.
4. **Bcrypt Authentication & Zero Plaintext Storage:**
   - Verified by direct SQL table inspection that raw passwords never appear in memory dumps, SQLite rows, or debug logs.
