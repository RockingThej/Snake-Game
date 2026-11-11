# Requirements Traceability Matrix: status after Sprint 2 completion (S2-18)

Source: SRS section 8 and STP Appendix A (requirement and test-case IDs are
unchanged). Status codes are the SRS ones:

* **N**: not yet implemented
* **P**: partially implemented
* **A**: accepted / verified (implemented **and** covered by passing automated tests)

Status is backed by automated test evidence in the "Automated evidence" column.
`tests/test_rtm.py` checks that this file stays consistent with the code base:
every evidence reference must exist, every `A` needs evidence, and the summary must match.

Evidence format: `path` (the file exists) or `path::Name` (a test class or
function inside that file).

## Functional requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-F-001 | Player Registration | `auth/__init__.py`, `auth/secure_auth.py`, `app/auth.py` | TC-AUTH-001 | `tests/test_auth_service.py`, `tests/test_auth_screens.py`, `tests/test_auth.py`, `tests/test_launcher_security.py` | A | Duplicate and invalid input rejected |
| SNAKE-F-002 | Player Authentication | `auth/__init__.py`, `auth/secure_auth.py`, `app/auth.py` | TC-AUTH-002 | `tests/test_auth_service.py`, `tests/test_launcher_flow.py`, `tests/test_security_suite.py::TestInputValidation` | A | Disabled accounts and oversized passwords are refused, not crashed on |
| SNAKE-F-003 | Player Profile | `scoring/stats.py`, `ui/menu_screens.py` | TC-PROFILE-001 | `tests/test_statistics.py`, `tests/test_menu_screens.py` | A | Profile and settings screens display stats and preferences |
| SNAKE-F-004 | Logout | `auth/session_manager.py`, `auth/guarded_session.py`, `app/sessions.py` | TC-AUTH-003 | `tests/test_session_manager.py`, `tests/test_flask_sessions.py`, `tests/test_launcher_security.py`, `tests/test_security_suite.py::TestSessionTermination` | A | Logout ends the server-side session on desktop and in the Flask API |
| SNAKE-F-005 | Start Game | `main.py`, `modes/manager.py`, `ui/menu_screens.py` | TC-GAME-001 | `tests/test_launcher_flow.py`, `tests/test_menu_screens.py`, `tests/test_modes.py` | A | All 5 modes launch with selected difficulty |
| SNAKE-F-006 | Game Mode Selection | `modes/manager.py`, `ui/menu_screens.py` | TC-MODE-001 | `tests/test_modes.py`, `tests/test_menu_screens.py` | A | All five modes are registered, selectable, and implemented |
| SNAKE-F-007 | Difficulty Selection | `modes/difficulty.py`, `admin/config.py` | TC-DIFF-001 | `tests/test_difficulty.py`, `tests/test_menu_screens.py` | A | Speeds are also admin-configurable |
| SNAKE-F-008 | Pause and Resume | `engine/game_state.py` | TC-GAME-002 | `tests/test_pause_resume.py` | A | Pause freezes movement, resume preserves full state |
| SNAKE-F-009 | Snake Movement | `engine/snake.py`, `ui/input_handler.py` | TC-MOVE-001 | `tests/test_engine.py`, `tests/test_input_handler.py` | A | Snake moves continuously according to input |
| SNAKE-F-010 | Food Consumption | `engine/food.py`, `engine/game_state.py` | TC-FOOD-001 | `tests/test_engine.py` | A | Length and score increase upon consumption |
| SNAKE-F-011 | Food Generation | `engine/food.py` | TC-FOOD-002 | `tests/test_engine.py` | A | Food spawns at unoccupied cells using random probes |
| SNAKE-F-012 | Collision Detection | `engine/collision.py`, `engine/two_player_state.py`, `engine/obstacles.py` | TC-COLLISION-001 | `tests/test_engine.py`, `tests/test_two_player.py`, `tests/test_obstacle_mode.py` | A | Wall, O(1) self, obstacle, and opponent collisions verified |
| SNAKE-F-013 | Score Calculation | `engine/game_state.py`, `scoring/integrity.py`, `app/scores.py`, `engine/two_player_state.py` | TC-SCORE-001 | `tests/test_engine.py`, `tests/test_scores.py`, `tests/test_score_integrity.py`, `tests/test_two_player.py` | A | Classic, obstacle, survival, powerup multipliers and battle scoring verified |
| SNAKE-F-014 | Obstacle Mode | `modes/obstacle.py`, `engine/obstacles.py` | TC-OBSTACLE-001 | `tests/test_obstacle_mode.py`, `tests/test_modes.py` | A | S2-01: ~4% obstacles, flood fill reachability check, collision detection |
| SNAKE-F-015 | Power-Up Mode | `modes/power_up.py` | TC-POWERUP-001 | `tests/test_powerups.py`, `tests/test_modes.py` | A | S2-09: Speed Boost, Slow Down, Shield, Score Multiplier, Snake Shrink |
| SNAKE-F-016 | Two-Player Battle | `modes/two_player.py`, `engine/two_player_state.py` | TC-MULTI-001 | `tests/test_two_player.py`, `tests/test_menu_screens.py` | A | S2-05 to S2-08: Dual input, collision winner logic, battle results screen |
| SNAKE-F-017 | Survival Mode | `modes/survival.py`, `modes/rules.py` | TC-SURVIVAL-001 | `tests/test_survival_mode.py`, `tests/test_modes.py` | A | S2-02: Progressive speed and dynamic obstacle additions every 3 foods |
| SNAKE-F-018 | Classic Mode | `modes/manager.py`, `engine/game_state.py` | TC-CLASSIC-001 | `tests/test_modes.py`, `tests/test_engine.py`, `tests/test_launcher_flow.py` | A | Traditional single-player snake gameplay |
| SNAKE-F-019 | Save Game Score | `db/score_repository.py`, `scoring/integrity.py` | TC-SCORE-002 | `tests/test_database.py`, `tests/test_session.py`, `tests/test_score_integrity.py` | A | Results validated before storage, immutable record |
| SNAKE-F-020 | Leaderboard | `db/leaderboard_repository.py`, `app/leaderboard.py` | TC-LEADER-001 | `tests/test_database.py`, `tests/test_leaderboard.py`, `tests/test_launcher_flow.py` | A | Ranked personal best scores per player |

## Non-functional requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-NF-001 | Movement input within 100 ms | `engine/snake.py`, `ui/input_handler.py`, `benchmarks/engine_benchmark.py` | TC-NF-PERF-001 | `tests/test_performance.py`, `tests/test_input_handler.py` | A | Direction change registered in microseconds; tick moves snake |
| SNAKE-NF-002 | At least 30 FPS | `engine/game_state.py`, `ui/game_screen.py`, `benchmarks/engine_benchmark.py` | TC-NF-PERF-002 | `tests/test_performance.py` | A | Engine tick takes ~1-3 us (well under 33.3 ms frame budget) |
| SNAKE-NF-003 | Stored scores preserved | `db/`, `scoring/integrity.py` | TC-NF-REL-001 | `tests/test_security_suite.py::TestScorePersistence`, `tests/test_database.py` | A | Repeated retrieval matches the stored score |
| SNAKE-NF-004 | Start Classic within 3 menu interactions | `ui/menu_screens.py`, `main.py` | TC-NF-USE-001 | `tests/test_launcher_flow.py`, `tests/test_menu_screens.py` | A | 1. Play -> 2. Select Classic -> 3. Select Difficulty |
| SNAKE-NF-005 | Modular components | whole code base (`engine/`, `modes/`, `auth/`, `admin/`, `db/`) | TC-NF-MAIN-001 | `docs/ADR-001-tech-stack.md`, `tests/test_database.py` | A | Clean package boundaries verified by independent test suites |
| SNAKE-NF-006 | Consistent behaviour across environments | CI (`.github/workflows/tests.yml`), `db/`, `engine/` | TC-NF-COMP-001 | `tests/test_database.py`, `tests/test_security_suite.py` | A | Automated CI and headless driver compatibility pass |

## Security requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-SR-001 | One-way password hashing | `auth/__init__.py`, `app/auth.py`, `admin/service.py` | TC-SEC-001 | `tests/test_security_suite.py::TestPasswordStorage`, `tests/test_auth_service.py`, `tests/test_auth.py` | A | bcrypt; checked in the database file and in the logs |
| SNAKE-SR-002 | Admin functions restricted | `admin/service.py`, `db/admin_repository.py` | TC-SEC-002 | `tests/test_security_suite.py::TestAdminAuthorization`, `tests/test_admin_service.py` | A | Every public admin function is tested for refusal; checked on every call |
| SNAKE-SR-003 | Input validated | `app/validators.py`, `auth/secure_auth.py`, `scoring/integrity.py`, `admin/config.py` | TC-SEC-003 | `tests/test_security_suite.py::TestInputValidation`, `tests/test_validators.py`, `tests/test_launcher_security.py` | A | Bounds checking, JSON validation, score sanity checks |
| SNAKE-SR-004 | Players cannot modify scores/leaderboard | `scoring/integrity.py`, `db/ext_integrity.py` | TC-SEC-004 | `tests/test_security_suite.py::TestScoreIntegrity`, `tests/test_score_integrity.py` | A | Database trigger forbids direct update; admin repair tools available |
| SNAKE-SR-005 | Sessions terminate; blocked after logout | `auth/session_policy.py`, `auth/session_manager.py`, `app/sessions.py` | TC-SEC-005 | `tests/test_security_suite.py::TestSessionTermination`, `tests/test_session_manager.py`, `tests/test_flask_sessions.py` | A | Idle and absolute time limits; copied cookies stop working |

## Summary

Total 31 requirements: A = 31, P = 0, N = 0
