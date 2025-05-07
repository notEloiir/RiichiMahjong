import pygame
import sys
import torch
import threading
import mahjong.constants as mc

from game.src.gui.board import Board
from game.src.gui.menu import Menu
from game.src.core.match import run_match
from game.src.core.player import  Player
from ml.src.models.mahjong_nn import MahjongNN


class GameGui:
    def __init__(self) -> None:
        pygame.init()
        self.display_surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        # self.display_surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Riichi Mahjong")
        self.running = False
        self.playing = False
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.game_screen = Menu(self)

        self.run()

    def switch_game_screen(self, game_screen) -> None:
        self.game_screen = game_screen

        if isinstance(self.game_screen, Board):
            self.playing = True
            self.start_game()
        elif isinstance(self.game_screen, Menu):
            self.playing = False

    def start_game(self):
        init_seed = None

        competitors = [Player(is_human=True)]
        for _ in range(3):
            filename = "2017raw24"
            competitors.append(
                Player(is_human=False, model=MahjongNN.from_file(filename, torch.device("cpu")))
            )

        game = threading.Thread(
            target=run_match,
            args=(competitors, init_seed, mc.EAST, self),
            daemon=True,
        )
        game.start()

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
        sys.exit()
