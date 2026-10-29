"""Tests for the stack-based UI screen manager."""
import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame  # noqa: E402
except ImportError:  # pragma: no cover - depends on optional runtime deps
    pygame = None

from ui.screen_manager import Screen, ScreenManager  # noqa: E402


class DummyScreen(Screen):
    def __init__(self, name):
        self.name = name
        self.entered = 0

    def on_enter(self):
        self.entered += 1


@unittest.skipIf(pygame is None, "pygame not installed")
class TestScreenManager(unittest.TestCase):
    def test_default_window_size_matches_srs_minimum(self):
        manager = ScreenManager()
        self.assertEqual(manager.run.__defaults__[1], (1280, 720))

    def test_push_and_current(self):
        manager = ScreenManager()
        first = DummyScreen("first")
        second = DummyScreen("second")

        manager.push(first)
        manager.push(second)

        self.assertEqual(manager.current, second)
        self.assertEqual(first.entered, 1)
        self.assertEqual(second.entered, 1)
        self.assertTrue(manager.running)

    def test_replace_replaces_top_of_stack(self):
        manager = ScreenManager()
        first = DummyScreen("first")
        second = DummyScreen("second")
        manager.push(first)
        manager.replace(second)

        self.assertEqual(manager.current, second)
        self.assertEqual(manager._stack, [second])
        self.assertEqual(second.entered, 1)

    def test_pop_stops_running_when_stack_is_empty(self):
        manager = ScreenManager()
        screen = DummyScreen("solo")
        manager.push(screen)

        manager.pop()

        self.assertIsNone(manager.current)
        self.assertFalse(manager.running)


if __name__ == "__main__":
    unittest.main()
