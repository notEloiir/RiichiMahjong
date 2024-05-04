import pygame, menu, board
from settings import *
from sys import exit
import torch, threading
from game_logic import simulate_match
from models import load_model
from player import Player


class Gui:
    def __init__(self) -> None:
        pygame.init()
        self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)
        # self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Riichi Mahjong")
        self.running = False
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.game_screen = menu.Menu(self)
        self.game = None

    def switch_game_screen(self, game_screen) -> None:
        self.game_screen = game_screen

        if isinstance(self.game_screen, board.Board):
            self.start_game()

    def start_game(self):
        init_seed = None

        competitors = []
        competitors.append(Player(is_human=True))
        for _ in range(3):
            filename = "b0_new"
            competitors.append(Player(is_human=False, model=load_model(filename, torch.device("cpu"))))

        self.game = threading.Thread(target=simulate_match, args=(competitors, init_seed, torch.device("cpu"), self.game_screen), daemon=True)
        self.game.start()

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
            self.dt = self.clock.tick() / 1000

        pygame.quit()
        exit()


if __name__ == "__main__":
    game = Gui()
    game.run()
