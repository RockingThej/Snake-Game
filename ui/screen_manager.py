"""S1-10: screen manager and UI framework."""
import pygame


class Screen:
    """Base class for every screen. Override only what you need."""

    manager = None

    def on_enter(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


class ScreenManager:
    """Keeps a stack of screens. Only the top screen gets events, updates and drawing."""

    def __init__(self):
        self.stack = []
        self.running = True

    @property
    def current(self):
        return self.stack[-1] if self.stack else None

    def push(self, screen):
        screen.manager = self
        self.stack.append(screen)
        screen.on_enter()

    def pop(self):
        if self.stack:
            self.stack.pop()
        if not self.stack:
            self.running = False

    def replace(self, screen):
        if self.stack:
            self.stack.pop()
        self.push(screen)

    def run(self, first_screen, size=(800, 600), title="Snake Game", fps=60):
        pygame.init()
        surface = pygame.display.set_mode(size)
        pygame.display.set_caption(title)
        clock = pygame.time.Clock()
        self.push(first_screen)
        while self.running:
            dt = clock.tick(fps) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.current:
                    self.current.handle_event(event)
            if self.current:
                self.current.update(dt)
            if self.current:
                surface.fill((18, 24, 32))
                self.current.draw(surface)
                pygame.display.flip()
        pygame.quit()
