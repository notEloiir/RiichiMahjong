import pygame, menu
from settings import *


class Gui:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Riichi Mahjong')
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.game_screen = menu.Menu(self)

    def switch_game_screen(self, new_game_screen):
        self.game_screen = new_game_screen

    def run(self):
        while True:
            self.game_screen.update()
            pygame.display.flip()
            self.dt = self.clock.tick(60) / 1000


if __name__ == '__main__':
    game = Gui()
    game.run()