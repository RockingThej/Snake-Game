"""Snake Game launcher: login -> menu -> mode -> difficulty -> game -> results.

Run from the repo root:  python main.py
(run.py starts the Flask backend; this starts the desktop game.)
"""
from db import initialize_database
from ui.auth_screens import LoginScreen, RegisterScreen
from ui.leaderboard_screen import LeaderboardScreen
from ui.menu_screens import GameOverScreen, MainMenuScreen
from ui.screen_manager import ScreenManager
from ui.session import Session

WINDOW_SIZE = (900, 640)   # matches a 30x20 board plus the HUD


def build_app(db_path=None):
    """Create the manager and wire every screen together.

    Returns (manager, first_screen_factory); pass both to manager.run().
    """
    initialize_database(db_path)
    manager = ScreenManager()
    session = Session(db_path=db_path)
    manager.session = session

    def make_login():
        return LoginScreen(session.auth, on_success=after_auth,
                           on_switch=lambda: manager.replace(make_register()))

    def make_register():
        return RegisterScreen(
            session.auth, on_success=after_auth,
            on_switch=lambda: manager.replace(make_login()),
            on_cancel=lambda: manager.replace(make_login()))

    def make_menu():
        return MainMenuScreen(username=session.username,
                              on_leaderboard=show_leaderboard,
                              on_logout=logout)

    def after_auth(username):
        session.login(username)
        manager.replace(make_menu())

    def logout():
        session.logout()
        manager.replace(make_login())

    def show_leaderboard():
        manager.push(LeaderboardScreen(session.leaderboard()))

    def show_game_over(state, saved):
        manager.replace(GameOverScreen(state, saved=saved,
                                       on_leaderboard=show_leaderboard))

    session.on_game_over = show_game_over
    return manager, make_login


def main():
    manager, first_screen = build_app()
    manager.run(first_screen, size=WINDOW_SIZE)


if __name__ == "__main__":
    main()
