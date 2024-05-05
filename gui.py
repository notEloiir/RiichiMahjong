import pygame, menu
from settings import *
from sys import exit


class Gui:
    def __init__(self) -> None:
        pygame.init()
        # self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Riichi Mahjong")
        self.running = False
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.game_screen = menu.Menu(self)

    def switch_game_screen(self, game_screen) -> None:
        self.game_screen = game_screen

    def run(self) -> None:
        self.running = True

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.game_screen.handle_event(event)

            self.game_screen.draw()
            pygame.display.flip()
            self.dt = self.clock.tick(60) / 1000

        pygame.quit()
        exit()


if __name__ == "__main__":
    game = Gui()
    game.run()
