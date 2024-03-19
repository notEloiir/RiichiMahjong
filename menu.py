import pygame, game_screen, board, events
from sys import exit


class Menu(game_screen.GameScreen):
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            ev = pygame.event.Event(events.SWITCH_GAME_SCREEN, game_screen=board.Board())
            pygame.event.post(ev)

    def update(self):
        self.display_surface.fill('#331133')