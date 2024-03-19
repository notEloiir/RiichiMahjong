import pygame, game_screen, menu, events
from sys import exit


class Board(game_screen.GameScreen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            ev = pygame.event.Event(events.SWITCH_GAME_SCREEN, game_screen=menu.Menu())
            pygame.event.post(ev)

    def update(self):
        self.display_surface.fill('#113311')