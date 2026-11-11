# Project Deviations & Architectural Decisions Report
## Project: A Snake Game
### Comprehensive Analysis of Specification Refinements across SRS, SAD, and STP

**Sprint:** Sprint 2 Baseline (S2-18)  
**Date:** 11-11-2026  
**Authors:** Team 6 (Thejaswi S, Vishnu Maddirala, V S Shashidharan, Vishwas Hosamath)  
**Status:** Approved & Formally Documented  

---

## Executive Summary

During Sprint 1 and Sprint 2, the implementation of **A Snake Game** progressed from initial conceptual specifications (SRS v0.1, SAD v1.0, and STP v1.0) to a fully realized, verified software product. In this evolution, several design choices and requirements were adapted, refined, or augmented to address technical realities, optimize engine performance, harden security, and enable full test automation in headless Continuous Integration (CI) environments.

This document serves as the formal **Engineering Deviations Ledger**, providing transparent, structured documentation of every divergence from the original specifications, including technical rationales, impact analyses, and automated verification evidence.

---

## Table of Deviations

| Deviation ID | Category | Affected Document & Req | Title / Summary |
|---|---|---|---|
| **DEV-F-01** | Functional | SRS: SNAKE-F-003 | Separation of Profile Statistics from Game Settings |
| **DEV-F-02** | Functional | SRS: SNAKE-F-007 | Administration Overrides for Difficulty Speed Intervals |
| **DEV-F-03** | Functional | SRS: Section 4.1 | Formalized Progression Formula for Survival Mode |
| **DEV-F-04** | Functional | SRS: SNAKE-F-015 | Deterministic Five-Item Power-Up Mechanics & Timers |
| **DEV-NF-01** | Non-Functional | SRS: SNAKE-NF-001 / STP: TC-NF-PERF-001 | Input Latency vs. Turn-Based Tick Interval Disambiguation |
| **DEV-NF-02** | Non-Functional | SRS: SNAKE-NF-002 / STP: TC-NF-PERF-002 | Microsecond Engine Benchmarking vs. Display Frame Rate |
| **DEV-ARCH-01** | Architecture | SAD: Section 3.6 / ADR-001 | Hybrid Architecture: Native Pygame Desktop + Flask REST API |
| **DEV-ARCH-02** | Architecture | SAD: Section 3.5 | Decoupled Pure-Python Engine from Pygame Subsystem |
| **DEV-ARCH-03** | Architecture | SAD: Section 3.6 | Modular SQLite Extension System (`ext_*.py`) vs. Monolithic Migrations |
| **DEV-ARCH-04** | Architecture | SAD: Section 3.2 | $O(1)$ Snake Body Collision Bookkeeping |
| **DEV-SEC-01** | Security | SRS: SNAKE-SR-004 / SAD: Section 3.9 | Database-Level Immutability Triggers for Score Protection |
| **DEV-SEC-02** | Security | SRS: SNAKE-SR-005 / SAD: Section 3.9 | Tiered Session Expiration (Desktop vs. REST API) |
| **DEV-SEC-03** | Security | SRS: SNAKE-SR-002 / SAD: Section 3.4 | Re-Verification of Admin Authorization on Every Invocable Method |
| **DEV-TEST-01** | Testing | STP: Section 5 / Appendix A | Headless UI Automated Testing via Pygame Dummy Video Driver |
| **DEV-TEST-02** | Testing | STP: Section 13 / Appendix B | Continuous Automated RTM Consistency Enforcement (`test_rtm.py`) |

---

## 1. Functional Requirements Deviations (SRS)

### DEV-F-01: Separation of Profile Statistics from Game Settings
* **Affected Specification:** SRS v0.1 Section 4, Requirement `SNAKE-F-003` (Player Profile)
* **Original Baseline:** The initial draft stated: *"The system shall allow authenticated players to view and update permitted profile information."* It did not delineate between statistical gameplay data and system configuration preferences.
* **Implemented Reality:** To preserve data integrity and prevent players from altering statistical metrics, the functionality was cleanly separated into two distinct screens:
  1. **Profile Screen (`ProfileScreen`):** A read-only analytical view populated by `scoring/stats.py`, displaying total games played, high score, average score, and favorite game mode.
  2. **Settings Screen (`SettingsScreen`):** An interactive configuration screen allowing users to set preferred default difficulty, controls, and visual color preferences.
* **Rationale:** Permitting users to write to arbitrary profile attributes without strict schema boundaries created security risks (e.g., players manually overwriting their own game count or rank). Decoupling read-only performance statistics from mutable configuration cleanly eliminates this risk.
* **Verification:** `tests/test_statistics.py` and `tests/test_menu_screens.py::TestMenuScreens.test_profile_and_settings_are_accessible_from_main_menu`.

---

### DEV-F-02: Administration Overrides for Difficulty Speed Intervals
* **Affected Specification:** SRS v0.1 Requirement `SNAKE-F-007` (Difficulty Selection)
* **Original Baseline:** Difficulty was defined solely as player-selectable levels (Easy, Medium, Hard) with hardcoded movement intervals.
* **Implemented Reality:** While the default intervals remain 160 ms (Easy), 110 ms (Medium), and 75 ms (Hard), an administrative configuration mechanism (`admin/config.py`) was introduced. Authorized administrators can adjust tick speeds dynamically via CLI (`python -m admin set-config difficulty.hard.speed_ms 60`) or GUI, which propagates to `DifficultyManager(speeds_ms=...)`.
* **Rationale:** Game balance tuning requires iterative adjustment. Exposing configurable speeds via the Administration Module empowers game organizers to tailor pacing without modifying source code.
* **Verification:** `tests/test_difficulty.py` and `tests/test_admin_service.py`.

---

### DEV-F-03: Formalized Progression Formula for Survival Mode
* **Affected Specification:** SRS v0.1 Section 4.1 (Survival Mode)
* **Original Baseline:** Stated qualitatively that *"difficulty progressively increases through changes such as increased speed, additional obstacles, or reduced safe movement area."*
* **Implemented Reality:** Formalized into a rigorous, deterministic step function in `modes/rules.py` (`SurvivalRules`):
  * Every $3\text{ foods}$ consumed:
    $$\text{Level} \leftarrow \text{Level} + 1$$
    $$\text{Tick Interval} \leftarrow \max(40\text{ ms}, \text{Tick Interval} - 8\text{ ms})$$
    $$\text{New Obstacles} \leftarrow 2 \quad (\text{bounded by } 10\% \text{ of grid area})$$
* **Rationale:** A quantitative specification guarantees reproducible gameplay and predictable unit test assertions.
* **Verification:** `tests/test_survival_mode.py`.

---

### DEV-F-04: Deterministic Five-Item Power-Up Mechanics & Timers
* **Affected Specification:** SRS v0.1 Section 4.1 (Power-Up Mode)
* **Original Baseline:** Listed prospective power-ups as examples without defining durations, stack behavior, or collision overrides.
* **Implemented Reality:** Implemented a concrete suite of five power-up entities in `modes/power_up.py`:
  1. **Speed Boost:** Decreases tick interval by 30% for 8 seconds.
  2. **Slow Down:** Increases tick interval by 40% for 8 seconds.
  3. **Shield:** Single-use passive ward absorbing one fatal collision with a wall or obstacle.
  4. **Score Multiplier:** $2\times$ point modifier for 10 seconds.
  5. **Snake Shrink:** Instant reduction of snake body length by 3 segments (floor of 2 segments).
* **Rationale:** Explicit duration bounds and defined stack behavior ensure fair competition and deterministic testability.
* **Verification:** `tests/test_powerups.py`.

---

## 2. Non-Functional Requirements Deviations (SRS & STP)

### DEV-NF-01: Input Latency vs. Turn-Based Tick Interval Disambiguation
* **Affected Specification:** SRS Requirement `SNAKE-NF-001` / STP `TC-NF-PERF-001`
* **Original Baseline:** *"Valid movement input processed within 100 ms under normal operating conditions."*
* **Implemented Reality:** In a discrete grid arcade game, input processing occurs in two stages:
  1. *Input Acceptance & Buffer Latching:* Keystrokes are captured and applied to the snake's buffered velocity vector in $<1\text{ ms}$ ($<1\mu\text{s}$ in benchmarks).
  2. *Physical Segment Displacement:* The snake advances only when the game clock emits a tick. On Easy mode, the tick interval is 160 ms.
* **Rationale:** If "input processed" was interpreted as "snake takes a physical step on screen", an intentional 160 ms Easy tick interval would mathematically violate a 100 ms threshold by design. The requirement is disambiguated: **Input registration and direction queuing is guaranteed within $\le 100\text{ ms}$ (actual $<1\text{ ms}$)**, while physical movement operates on the selected difficulty clock.
* **Verification:** `tests/test_performance.py` and `tests/test_input_handler.py`.

---

### DEV-NF-02: Microsecond Engine Benchmarking vs. Display Frame Rate
* **Affected Specification:** SRS Requirement `SNAKE-NF-002` / STP `TC-NF-PERF-002`
* **Original Baseline:** *"Maintain at least 30 FPS during normal single-player gameplay."*
* **Implemented Reality:** Headless automated CI servers (e.g. GitHub Actions Linux runners) lack physical GPUs and display servers, preventing hardware frame-rate measurement. The requirement was verified through deterministic computational budgets:
  * Engine ticks take $1.4\mu\text{s}$ to $1.8\mu\text{s}$ under typical conditions, and $\sim 3\mu\text{s}$ during food consumption.
  * A 30 FPS target allows a $33.33\text{ ms}$ budget per frame ($33,333\mu\text{s}$). The engine consumes less than $0.01\%$ of the frame budget, guaranteeing $>99.9\%$ of CPU time remains available for Pygame blitting and display flips.
* **Rationale:** Separating simulation performance from hardware GPU rendering allows automated verification of performance budgets on any machine or headless CI runner.
* **Verification:** `benchmarks/engine_benchmark.py`, `docs/performance.md`, and `tests/test_performance.py`.

---

## 3. Architectural & Design Deviations (SAD)

### DEV-ARCH-01: Hybrid Architecture: Native Pygame Desktop + Flask REST API
* **Affected Specification:** SAD v1.0 Section 3.6 & ADR-001
* **Original Baseline:** Initial architectural documents contemplated choosing between either a desktop client or a web application.
* **Implemented Reality:** Engineered a unified hybrid solution:
  * Native desktop Pygame application (`main.py`) provides responsive, zero-latency local arcade play with custom sound and keyboard controls.
  * Lightweight Flask REST API (`run.py` & `app/`) exposes endpoints for authentication, score recording, and leaderboard queries.
  * Both frontends share identical database repositories (`db/`) and security validation logic (`auth/`).
* **Rationale:** Delivers optimal user responsiveness on the desktop while maintaining an API suitable for automated integration tests, web leaderboards, and administrative tools.
* **Verification:** `tests/test_flask_sessions.py`, `tests/test_launcher_flow.py`.

---

### DEV-ARCH-02: Decoupled Pure-Python Engine from Pygame Subsystem
* **Affected Specification:** SAD v1.0 Section 3.4 (Game Engine)
* **Original Baseline:** Early prototypes tightly coupled game coordinate updates and input handling directly with Pygame event loops and surfaces.
* **Implemented Reality:** The `engine/` package was stripped of all Pygame references, becoming a 100% pure Python simulation model. Pygame is isolated exclusively within `ui/` screens.
* **Rationale:** Allows complete simulation, property testing, and regression benchmarking without initializing graphics contexts or mock windowing systems.
* **Verification:** `tests/test_engine.py`, `tests/test_engine_integration.py`.

---

### DEV-ARCH-03: Modular SQLite Extension System (`ext_*.py`) vs. Monolithic Migrations
* **Affected Specification:** SAD v1.0 Section 3.6 (Data Store)
* **Original Baseline:** Standard centralized schema script (`db/schema.py`).
* **Implemented Reality:** Implemented a dynamic extension discovery pattern (`db/extensions.py`). Subsystems define independent SQL snippets in `db/ext_<feature>.py`:
  * `db/ext_admin.py` $\rightarrow$ admin tables and audit logs
  * `db/ext_sessions.py` $\rightarrow$ server-side session tracking
  * `db/ext_integrity.py` $\rightarrow$ database triggers
* **Rationale:** Allows parallel development across feature teams without merge conflicts on a single monolithic `schema.sql` file or introducing heavy migration frameworks like Alembic.
* **Verification:** `tests/test_database.py`.

---

### DEV-ARCH-04: $O(1)$ Snake Body Collision Bookkeeping
* **Affected Specification:** SAD v1.0 Section 3.4 (Collision Detection Module)
* **Original Baseline:** Linear scanning of the entire snake body list:
  $$\text{Complexity: } O(N) \text{ where } N \text{ is the number of body segments}$$
* **Implemented Reality:** The `Snake` entity maintains an internal coordinate frequency map (`Counter`). Adding the new head and popping the tail updates the map in $O(1)$ time. Self-collision checks perform a single dictionary lookup:
  $$\text{Complexity: } O(1)$$
* **Rationale:** On a crowded $30 \times 20$ board (up to 590 body segments), linear collision checks scaled up to $12.7\mu\text{s}$. The $O(1)$ structure reduced this to a flat $0.4\mu\text{s}$ regardless of snake length.
* **Verification:** `tests/test_snake_bookkeeping.py` and `benchmarks/engine_benchmark.py`.

---

## 4. Security & Data Protection Deviations (SRS, SAD, STP)

### DEV-SEC-01: Database-Level Immutability Triggers for Score Protection
* **Affected Specification:** SRS Requirement `SNAKE-SR-004` / SAD Section 3.9
* **Original Baseline:** Stated that normal player interfaces cannot modify scores.
* **Implemented Reality:** Because client-side desktop software cannot prevent determined local users from opening SQLite files with external tools, protection was embedded directly into the database engine via an SQLite `BEFORE UPDATE` trigger (`db/ext_integrity.py`):
  ```sql
  CREATE TRIGGER IF NOT EXISTS prevent_score_tampering
  BEFORE UPDATE ON scores
  BEGIN
      SELECT RAISE(FAIL, 'Direct updates to scores are prohibited for data integrity');
  END;
  ```
  Any attempt to issue an SQL `UPDATE` statement fails immediately with an integrity error.
* **Rationale:** Enforces score immutability at the lowest database layer rather than relying exclusively on application code.
* **Verification:** `tests/test_security_suite.py::TestScoreIntegrity`, `tests/test_score_integrity.py`.

---

### DEV-SEC-02: Tiered Session Expiration (Desktop vs. REST API)
* **Affected Specification:** SRS Requirement `SNAKE-SR-005` / SAD Section 3.9
* **Original Baseline:** Specified generic session termination after logout.
* **Implemented Reality:** Formulated dual-tier session policies in `auth/session_policy.py`:
  * **Desktop GUI Sessions:** 2-hour idle timeout, 12-hour absolute expiration.
  * **Flask REST API Sessions:** 30-minute idle timeout, 8-hour absolute expiration.
  * Added `POST /api/auth/logout-all` to invalidate all active sessions across devices upon password change or account compromise.
* **Rationale:** A desktop gamer paused mid-session expects a more relaxed idle window than a stateless HTTP web consumer. Tailoring timeouts to the operational context balances user convenience and security.
* **Verification:** `tests/test_security_suite.py::TestSessionTermination`, `tests/test_session_manager.py`, `tests/test_flask_sessions.py`.

---

### DEV-SEC-03: Re-Verification of Admin Authorization on Every Invocable Method
* **Affected Specification:** SRS Requirement `SNAKE-SR-002` / SAD Section 3.9
* **Original Baseline:** Administrator checks were specified at the UI menu level.
* **Implemented Reality:** The `AdminService` strictly enforces authorization re-checks on **every internal service call**. Constructing `AdminService.from_session(session)` requires a live, unexpired administrator token, and subsequent queries re-verify role status in the database.
* **Rationale:** Protects against privilege bypass if a non-admin session manages to construct or invoke administrative functions programmatically.
* **Verification:** `tests/test_security_suite.py::TestAdminAuthorization`, `tests/test_admin_service.py`.

---

## 5. Testing & Verification Methodology Deviations (STP)

### DEV-TEST-01: Headless UI Automated Testing via Pygame Dummy Video Driver
* **Affected Specification:** STP v1.0 Section 5 & Appendix A
* **Original Baseline:** Anticipated manual gameplay passes on supported Windows hardware.
* **Implemented Reality:** Introduced automated headless UI testing using Pygame's dummy video driver:
  ```python
  os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
  ```
  All UI screens, input events, menu transitions, and rendering routines are verified automatically without opening GUI windows.
* **Rationale:** Eliminates dependency on manual user testing and allows complete test coverage in headless CI environments.
* **Verification:** `tests/test_menu_screens.py`, `tests/test_auth_screens.py`, `tests/test_game_screen.py`.

---

### DEV-TEST-02: Continuous Automated RTM Consistency Enforcement (`test_rtm.py`)
* **Affected Specification:** STP v1.0 Section 13 (Traceability Management)
* **Original Baseline:** Traceability matrices were planned as static tabular documentation reviewed manually prior to project submission.
* **Implemented Reality:** Developed `tests/test_rtm.py` as an automated test. The test parses `docs/RTM.md`, verifies every requirement status (`A`, `P`, `N`), checks that referenced files and methods actually exist in the codebase, and fails the build if documentation drifts out of sync with code.
* **Rationale:** Prevents documentation rot and ensures that claims of test coverage are continuously verified by automated tests.
* **Verification:** `tests/test_rtm.py`.

---

## Summary of Impact

All documented deviations have either **strengthened software quality**, **improved test automation**, or **hardened system security**. No functional requirements from the course project charter have been discarded; all five game modes, user authentication, session security, leaderboards, and administrative controls are fully implemented, verified, and traced.
