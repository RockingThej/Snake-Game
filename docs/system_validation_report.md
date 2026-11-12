# Final System Validation Testing Report

## Project: A Snake Game (Team 6)
**Software Engineering Course Project — Final Viva Submission**  
**Execution Environment:** Python 3.13.18, pytest 9.2.0, Windows 11  
**Execution Date:** 12-11-2026  
**Status:** **100% PASSED (292/292 Tests)**  

---

## 1. Executive Summary

System Validation Testing validates the integrated Snake Game system end-to-end, confirming that all subcomponents (Pygame UI, Game Engine, SQLite Repositories, Session Policy Management, Administration Service, REST Backend, and Security Triggers) function harmoniously according to the IEEE Software Requirements Specification (SRS v2.0).

| Metric | Result |
|---|---|
| **Total System Validation Tests** | **292** |
| **Passed** | **292 (100.0%)** |
| **Failed** | **0 (0.0%)** |
| **Errors** | **0 (0.0%)** |
| **RTM Traceability Verification** | **31 / 31 Requirements Verified (100%)** |

---

## 2. System Validation Test Suites Breakdown

| Test Suite / File | Category | Test Count | Status | Scope & Validation Objective |
|---|---|:---:|:---:|---|
| [`test_all_modes_live.py`](file:///C:/Snake-Game/tests/test_all_modes_live.py) | Live End-to-End | 5 | PASSED | Executes real game loops for all 5 modes (Classic, Obstacle, Power-Up, Survival, Two-Player) with active Pygame surfaces and event dispatching. |
| [`test_launcher_flow.py`](file:///C:/Snake-Game/tests/test_launcher_flow.py) | Workflow Validation | 7 | PASSED | Full player user journey: Registration -> Login -> Main Menu -> Mode Selection -> Difficulty -> Gameplay -> Score Storage -> Leaderboard. |
| [`test_launcher_security.py`](file:///C:/Snake-Game/tests/test_launcher_security.py) | Security Flow | 7 | PASSED | Validates that disabled users cannot authenticate via UI, oversized inputs (>10,000 chars) are refused without UI crashes, and logout invalidates session tokens. |
| [`test_security_suite.py`](file:///C:/Snake-Game/tests/test_security_suite.py) | Security Architecture | 116 | PASSED | Exhaustive validation of security requirements SNAKE-SR-001 through SNAKE-SR-005 (Bcrypt, Role-Based Access, SQL injection immunity, Score immutability triggers, Session expiry). |
| [`test_flask_sessions.py`](file:///C:/Snake-Game/tests/test_flask_sessions.py) | REST Backend | 13 | PASSED | HTTP REST endpoints session protection, session timeout, `/api/auth/logout-all`, and token hijacking resistance. |
| [`test_engine_integration.py`](file:///C:/Snake-Game/tests/test_engine_integration.py) | Invariant Integration | 8 | PASSED | Executes 50 automated simulated bot games across all 5 modes, checking game-state invariants: coordinate containment, non-negative scores, and game-over finality. |
| [`test_admin_cli.py`](file:///C:/Snake-Game/tests/test_admin_cli.py) | CLI Subsystem | 6 | PASSED | Tests command-line administration (`python -m admin make-admin`, `list-users`, `remove-admin`), argument parsing, and immutable audit logs. |
| [`test_menu_screens.py`](file:///C:/Snake-Game/tests/test_menu_screens.py) | UI Navigation | 12 | PASSED | Screen stack transitions between Main Menu, Mode Selection, Difficulty, Player Profile, Settings, and Admin management screens. |
| [`test_auth_screens.py`](file:///C:/Snake-Game/tests/test_auth_screens.py) | UI Interaction | 6 | PASSED | Login and Register screens: keyboard input handling, field toggling, password masking, and error banner display. |
| [`test_game_screen.py`](file:///C:/Snake-Game/tests/test_game_screen.py) | Gameplay UI | 16 | PASSED | Game board surface rendering, HUD scoring text, pause screen overlay, and dual-input routing (WASD to P1, Arrows to P2). |
| [`test_performance.py`](file:///C:/Snake-Game/tests/test_performance.py) | Non-Functional Performance | 7 | PASSED | Confirms engine tick duration < 1.1 ms (under 30 FPS budget of 33.3 ms) and user input response latency < 100 ms (SNAKE-NF-001, SNAKE-NF-002). |
| [`test_rtm.py`](file:///C:/Snake-Game/tests/test_rtm.py) | Traceability Verification | 67 | PASSED | Automated parser that inspects `docs/RTM.md` against the test codebase to guarantee zero unverified requirements or broken test references. |

---

## 3. Detailed Security & Validation Results

### 3.1 Authentication & Password Storage (SNAKE-SR-001)
- **Hash Algorithm:** Bcrypt with automatic salt generation.
- **Verification Result:** Zero instances of plaintext passwords found across SQLite database files, transient variables, or log streams. Tested against rainbow table attacks and repeated identical password hashing (which generate differing salt hashes).

### 3.2 Role-Based Access Control & Admin Protection (SNAKE-SR-002)
- **Authorization Barrier:** 23 separate `AdminService` public methods were evaluated under non-privileged player sessions. Every single call was intercepted and rejected with `PermissionDeniedError`.
- **Session Revocation:** Verified that if an administrator's privileges are removed or their account is disabled mid-session, all further calls immediately fail.

### 3.3 Score & Leaderboard Immutability (SNAKE-SR-004)
- **Database Trigger:** Verified that SQLite database triggers intercept and abort direct `UPDATE` or `DELETE` SQL queries against the `scores` and `leaderboard` tables.
- **Data Integrity Audit:** Verified automated repair tools (`AdminService.rebuild_leaderboard()`) accurately reconstruct leaderboard rankings from historical score records.

### 3.4 Session Expiration & Invalidation (SNAKE-SR-005)
- **Desktop Client:** Idle timeout enforced at 2 hours; absolute lifetime capped at 12 hours.
- **Web REST API:** Idle timeout enforced at 30 minutes; absolute lifetime capped at 8 hours.
- **Logout Invalidation:** Verified that upon logout, tokens are terminated server-side, preventing replay attacks or cookie theft.
