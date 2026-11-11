# Sprint 2 modules: how to use them (S2-13 to S2-17)

For anyone building screens or modes on top of these. All paths are from the
repo root. Every function takes an optional `db_path` (tests use a temp DB).

## Sessions and logout (S2-13)

`main.build_app` now creates a `GuardedSession` (a drop-in subclass of
`ui.session.Session`), so existing screens keep working.

```python
session.login("alice")        # also starts a server-side session
session.logged_in             # False once logged out OR idle too long
session.require_login()       # returns user id, or raises NotAuthenticatedError
session.touch()               # call on activity to restart the idle timer
session.logout()              # ends the session on the server
session.logout_everywhere()
```

Policy lives in `auth/session_policy.py` (`SessionPolicy`). The desktop uses
2 h idle / 12 h absolute; the Flask API uses 30 min / 8 h
(`SESSION_IDLE_SECONDS`, `SESSION_ABSOLUTE_SECONDS`). The Flask API also has
`POST /api/auth/logout-all`.

## Statistics (S2-15)

```python
from scoring.stats import get_player_statistics, get_global_statistics
get_player_statistics(user_id)   # profile screen: games, best, average,
                                 # rank, by_mode, by_difficulty, recent_scores
get_global_statistics()          # admin screen: totals, games_by_mode, 7-day trend
```
Both return plain dicts (keys are listed at the top of `scoring/stats.py`).

## Administration (S2-14)

```python
from admin import AdminService, PermissionDeniedError
service = AdminService.from_session(session)   # NEVER build it from a bare user id in the UI
service.list_users(search="al", limit=50)
service.set_user_disabled(user_id, True, reason="cheating")
service.delete_score(score_id)
service.game_statistics()
service.set_config("difficulty.hard.speed_ms", 60)
service.audit_log()
```
The service re-checks "is this still an administrator with a live session?"
on **every call**, so an admin screen only has to catch
`PermissionDeniedError` and return to the menu.

The first administrator is created on the command line:

```
python -m admin make-admin <username>
python -m admin list-users
```

Game code can read admin-set values with `admin.config.load_config()`;
`admin.config.get_difficulty_speeds()` can be passed to
`DifficultyManager(speeds_ms=...)`.

## Score integrity (S2-16)

* Save scores through the session (`session.finish_game(state)`), which calls
  `scoring.integrity.submit_score`. It only accepts the five registered mode
  ids (`classic`, `obstacle`, `power_up`, `two_player_battle`, `survival`),
  the three difficulties and sane scores. **New modes must use those ids.**
* Saved scores cannot be edited (database trigger). Admins can delete a score
  (`AdminService.delete_score`) or repair the board
  (`AdminService.check_data_integrity()` / `.rebuild_leaderboard()`).

## Adding database tables

Do not edit `db/schema.py`. Create `db/ext_<feature>.py` with a `SQL` string
of `CREATE TABLE IF NOT EXISTS ...`; it is applied automatically
(`db/extensions.py`).

## Security tests and the RTM (S2-17)

`tests/test_security_suite.py` has one section per TC-SEC test case.
`docs/RTM.md` is the updated traceability matrix; `tests/test_rtm.py` fails
if it points at tests that do not exist, so update both together.
