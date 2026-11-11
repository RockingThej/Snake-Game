"""User interface package for Snake Game screens and controllers."""

from ui.screen_manager import Screen, ScreenManager

__all__ = [
    "Screen",
    "ScreenManager",
    "TextField",
    "LoginScreen",
    "RegisterScreen",
    "MainMenuScreen",
    "ModeSelectionScreen",
    "DifficultySelectionScreen",
    "GameOverScreen",
    "BattleResultsScreen",
]


def __getattr__(name):
    if name == "TextField":
        from ui.auth_screens import TextField
        return TextField
    if name == "LoginScreen":
        from ui.auth_screens import LoginScreen
        return LoginScreen
    if name == "RegisterScreen":
        from ui.auth_screens import RegisterScreen
        return RegisterScreen
    if name == "MainMenuScreen":
        from ui.menu_screens import MainMenuScreen
        return MainMenuScreen
    if name == "ModeSelectionScreen":
        from ui.menu_screens import ModeSelectionScreen
        return ModeSelectionScreen
    if name == "DifficultySelectionScreen":
        from ui.menu_screens import DifficultySelectionScreen
        return DifficultySelectionScreen
    if name == "GameOverScreen":
        from ui.menu_screens import GameOverScreen
        return GameOverScreen
    if name == "BattleResultsScreen":
        from ui.menu_screens import BattleResultsScreen
        return BattleResultsScreen
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
