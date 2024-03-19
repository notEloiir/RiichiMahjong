import pygame, board, game_screen
from sys import exit


class Menu(game_screen.GameScreen):
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                self.context.switch_game_screen(board.Board(self.context))

    def update(self):
        self.context.display_surface.fill('#331133')
        self.process_events()