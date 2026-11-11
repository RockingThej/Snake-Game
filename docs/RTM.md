# Requirements Traceability Matrix: status after Sprint 2 work (S2-17)

Source: SRS section 8 and STP Appendix A (requirement and test-case IDs are
unchanged). Status codes are the SRS ones:

* **N**: not yet implemented
* **P**: partially implemented
* **A**: accepted / verified (implemented **and** covered by passing automated tests)

Status is *proposed* from the evidence in the "Automated evidence" column. The
team should confirm it before copying it into the SRS PDF. `tests/test_rtm.py`
checks that this file stays consistent with the code base: every evidence
reference must exist, every `A` needs evidence, and the summary must match.

Evidence format: `path` (the file exists) or `path::Name` (a test class or
function inside that file).

## Functional requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-F-001 | Player Registration | `auth/__init__.py`, `auth/secure_auth.py`, `app/auth.py` | TC-AUTH-001 | `tests/test_auth_service.py`, `tests/test_auth_screens.py`, `tests/test_auth.py`, `tests/test_launcher_security.py` | A | Duplicate and invalid input rejected |
| SNAKE-F-002 | Player Authentication | `auth/__init__.py`, `auth/secure_auth.py`, `app/auth.py` | TC-AUTH-002 | `tests/test_auth_service.py`, `tests/test_launcher_flow.py`, `tests/test_security_suite.py::TestInputValidation` | A | Disabled accounts and oversized passwords are refused, not crashed on |
| SNAKE-F-003 | Player Profile | `scoring/stats.py` (data only) | TC-PROFILE-001 | `tests/test_statistics.py` | P | Statistics for a profile screen are ready; the profile/settings screens (S2-11) and profile update are not built |
| SNAKE-F-004 | Logout | `auth/session_manager.py`, `auth/guarded_session.py`, `app/sessions.py` | TC-AUTH-003 | `tests/test_session_manager.py`, `tests/test_flask_sessions.py`, `tests/test_launcher_security.py`, `tests/test_security_suite.py::TestSessionTermination` | A | Logout ends the server-side session on desktop and in the Flask API |
| SNAKE-F-005 | Start Game | `main.py`, `modes/manager.py` | TC-GAME-001 | `tests/test_launcher_flow.py`, `tests/test_menu_screens.py` | P | Only Classic can be started so far |
| SNAKE-F-006 | Game Mode Selection | `modes/manager.py` | TC-MODE-001 | `tests/test_modes.py` | P | All five modes can be selected; four are still "not implemented" |
| SNAKE-F-007 | Difficulty Selection | `modes/difficulty.py`, `admin/config.py` | TC-DIFF-001 | `tests/test_difficulty.py`, `tests/test_menu_screens.py` | A | Speeds are also admin-configurable |
| SNAKE-F-008 | Pause and Resume | `engine/game_state.py` | TC-GAME-002 | `tests/test_pause_resume.py` | A | |
| SNAKE-F-009 | Snake Movement | `engine/snake.py`, `ui/input_handler.py` | TC-MOVE-001 | `tests/test_engine.py`, `tests/test_input_handler.py` | A | |
| SNAKE-F-010 | Food Consumption | `engine/food.py`, `engine/game_state.py` | TC-FOOD-001 | `tests/test_engine.py` | A | |
| SNAKE-F-011 | Food Generation | `engine/food.py` | TC-FOOD-002 | `tests/test_engine.py` | A | |
| SNAKE-F-012 | Collision Detection | `engine/collision.py` | TC-COLLISION-001 | `tests/test_engine.py` | P | Wall, self and obstacle checks tested; opponent-snake collision (S2-06) pending |
| SNAKE-F-013 | Score Calculation | `engine/game_state.py`, `scoring/integrity.py`, `app/scores.py` | TC-SCORE-001 | `tests/test_engine.py`, `tests/test_scores.py`, `tests/test_score_integrity.py` | P | Classic scoring and web Score Manager done; per-mode rules pending |
| SNAKE-F-014 | Obstacle Mode | none yet | TC-OBSTACLE-001 | | N | S2-01 |
| SNAKE-F-015 | Power-Up Mode | none yet | TC-POWERUP-001 | | N | S2-09 |
| SNAKE-F-016 | Two-Player Battle | none yet | TC-MULTI-001 | | N | S2-05 to S2-07 |
| SNAKE-F-017 | Survival Mode | none yet | TC-SURVIVAL-001 | | N | S2-02 |
| SNAKE-F-018 | Classic Mode | `modes/manager.py`, `engine/game_state.py` | TC-CLASSIC-001 | `tests/test_modes.py`, `tests/test_engine.py`, `tests/test_launcher_flow.py` | A | |
| SNAKE-F-019 | Save Game Score | `db/score_repository.py`, `scoring/integrity.py` | TC-SCORE-002 | `tests/test_database.py`, `tests/test_session.py`, `tests/test_score_integrity.py` | A | Results are validated before they are stored |
| SNAKE-F-020 | Leaderboard | `db/leaderboard_repository.py`, `app/leaderboard.py` | TC-LEADER-001 | `tests/test_database.py`, `tests/test_leaderboard.py`, `tests/test_launcher_flow.py` | A | |

## Non-functional requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-NF-001 | Movement input within 100 ms | engine / UI | TC-NF-PERF-001 | | N | Performance measurement is S2-03 |
| SNAKE-NF-002 | At least 30 FPS | UI | TC-NF-PERF-002 | | N | Performance measurement is S2-03 |
| SNAKE-NF-003 | Stored scores preserved | `db/`, `scoring/integrity.py` | TC-NF-REL-001 | `tests/test_security_suite.py::TestScorePersistence`, `tests/test_database.py` | A | Repeated retrieval matches the stored score |
| SNAKE-NF-004 | Start Classic within 3 menu interactions | `ui/menu_screens.py` | TC-NF-USE-001 | `tests/test_launcher_flow.py` | P | The flow is tested, but no test counts the interactions yet |
| SNAKE-NF-005 | Modular components | whole code base | TC-NF-MAIN-001 | `docs/ADR-001-tech-stack.md` | P | Separate packages exist; the formal architecture review is still to do |
| SNAKE-NF-006 | Consistent behaviour across environments | CI | TC-NF-COMP-001 | `.github/workflows/tests.yml` | P | Tests run on windows-latest; a manual compatibility pass is pending |

## Security requirements

| Req ID | Requirement | Module / code | Test case | Automated evidence | Status | Notes |
|---|---|---|---|---|---|---|
| SNAKE-SR-001 | One-way password hashing | `auth/__init__.py`, `app/auth.py`, `admin/service.py` | TC-SEC-001 | `tests/test_security_suite.py::TestPasswordStorage`, `tests/test_auth_service.py`, `tests/test_auth.py` | A | bcrypt; checked in the database file and in the logs |
| SNAKE-SR-002 | Admin functions restricted | `admin/service.py`, `db/admin_repository.py` | TC-SEC-002 | `tests/test_security_suite.py::TestAdminAuthorization`, `tests/test_admin_service.py` | A | Every public admin function is tested for refusal. The admin screens (S2-12) must use `AdminService.from_session` |
| SNAKE-SR-003 | Input validated | `app/validators.py`, `auth/secure_auth.py`, `scoring/integrity.py`, `admin/config.py` | TC-SEC-003 | `tests/test_security_suite.py::TestInputValidation`, `tests/test_validators.py`, `tests/test_launcher_security.py` | A | Found and fixed: non-object JSON gave HTTP 500; 73+ character password crashed the login screen |
| SNAKE-SR-004 | Players cannot modify scores/leaderboard | `scoring/integrity.py`, `db/ext_integrity.py` | TC-SEC-004 | `tests/test_security_suite.py::TestScoreIntegrity`, `tests/test_score_integrity.py` | A | A desktop game cannot stop someone editing the SQLite file with other tools; edits are detected and repairable by an admin |
| SNAKE-SR-005 | Sessions terminate; blocked after logout | `auth/session_policy.py`, `auth/session_manager.py`, `app/sessions.py` | TC-SEC-005 | `tests/test_security_suite.py::TestSessionTermination`, `tests/test_session_manager.py`, `tests/test_flask_sessions.py` | A | Idle and absolute time limits; copied cookies stop working |

## Summary

Total 31 requirements: A = 17, P = 8, N = 6
