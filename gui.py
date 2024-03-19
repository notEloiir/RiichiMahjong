import pygame, menu, events
from settings import *
from sys import exit


class Gui:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Riichi Mahjong')
        self.running = False
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.game_screen = menu.Menu()

    def switch_game_screen(self, game_screen):
        self.game_screen = game_screen

    def run(self):
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == events.SWITCH_GAME_SCREEN:
                    self.switch_game_screen(event.game_screen)
                else:
                    self.game_screen.handle_event(event)

            self.game_screen.update()
            pygame.display.flip()
            self.dt = self.clock.tick(60) / 1000

        pygame.quit()
        exit()

if __name__ == '__main__':
    game = Gui()
    game.run()