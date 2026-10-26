"""Stack-based screen manager for the Snake Game UI.

The screen manager owns a stack of screens and drives the main event loop.
The Pygame dependency is imported lazily inside ``run()`` so this module can be
imported in headless CI where Pygame is not installed.
"""


class Screen:
    """Base class for any UI screen in the game."""

    manager = None

    def on_enter(self):
        """Called when the screen becomes active."""
        return None

    def handle_event(self, event):
        """Handle one input event."""
        return None

    def update(self, dt):
        """Advance transient or animated state for this frame."""
        return None

    def draw(self, surface):
        """Render the current screen to the provided display surface."""
        return None


class ScreenManager:
    """Manage a stack of screens and run the main app loop."""

    def __init__(self):
        self._stack = []
        self.running = False

    @property
    def current(self):
        """Return the active screen, or ``None`` when the stack is empty."""
        if not self._stack:
            return None
        return self._stack[-1]

    def push(self, screen):
        """Push a new screen onto the stack and activate it."""
        self._stack.append(screen)
        screen.manager = self
        self.running = True
        screen.on_enter()
        return screen

    def pop(self):
        """Pop the current screen and return the previous screen."""
        if not self._stack:
            self.running = False
            return None

        self._stack.pop()
        if not self._stack:
            self.running = False
            return None

        current = self.current
        current.manager = self
        self.running = True
        return current

    def replace(self, screen):
        """Replace the current screen with a new one while keeping the stack.

        If the stack is empty, the new screen becomes the only item; otherwise the
        top of the stack is replaced in place.
        """
        if self._stack:
            self._stack[-1] = screen
        else:
            self._stack = [screen]
        screen.manager = self
        self.running = True
        screen.on_enter()
        return screen

    def run(self, initial_screen=None, size=(1280, 720), clock_tick=60):
        """Run the manager loop until the screen stack is empty.

        ``initial_screen`` is optional and may be a screen instance or a factory
        callable that returns a screen. Any screen-specific event handling is
        delegated directly to the screen objects.

        The default window size matches the SRS minimum supported desktop display.
        """
        import pygame

        if initial_screen is not None:
            if callable(initial_screen):
                initial_screen = initial_screen()
            self.replace(initial_screen)

        pygame.init()
        surface = pygame.display.set_mode(size)
        clock = pygame.time.Clock()

        try:
            while self.running:
                dt = clock.tick(clock_tick) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._stack.clear()
                        self.running = False
                        break
                    current = self.current
                    if current is not None:
                        current.handle_event(event)

                current = self.current
                if current is not None:
                    current.update(dt)
                    current.draw(surface)

                pygame.display.flip()
        finally:
            pygame.quit()

        return self
