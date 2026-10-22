import unittest

from ui.screen_manager import Screen, ScreenManager


class TestScreenManager(unittest.TestCase):
    def test_push_pop_replace(self):
        m = ScreenManager()
        a, b, c = Screen(), Screen(), Screen()
        m.push(a)
        m.push(b)
        self.assertIs(m.current, b)
        self.assertIs(b.manager, m)
        m.pop()
        self.assertIs(m.current, a)
        m.replace(c)
        self.assertIs(m.current, c)
        self.assertEqual(len(m.stack), 1)

    def test_popping_last_screen_stops_app(self):
        m = ScreenManager()
        m.push(Screen())
        m.pop()
        self.assertFalse(m.running)


if __name__ == "__main__":
    unittest.main()
