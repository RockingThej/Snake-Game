"""User interface package for Snake Game screens and controllers."""

from ui.screen_manager import Screen, ScreenManager

__all__ = [
    "Screen",
    "ScreenManager",
    "MainMenuScreen",
    "ModeSelectionScreen",
    "DifficultySelectionScreen",
    "GameOverScreen",
]


def __getattr__(name):
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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")