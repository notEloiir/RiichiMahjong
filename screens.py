from __future__ import annotations
from typing import TYPE_CHECKING
import pygame, ui.ui_items as ui_items, ui.ui_layouts as ui_layouts
from settings import *

if TYPE_CHECKING:
    from gui import Gui


class GameScreen:
    def __init__(self, gui: Gui):
        self.gui = gui
    
    def handle_event(self, event: pygame.Event) -> None:
        raise NotImplementedError("Method process_events is not implemented!")
    
    def update(self) -> None:
        raise NotImplementedError("Method update is not implemented!")
    

class Menu(GameScreen):
    def __init__(self, gui: Gui) -> None:
        super().__init__(gui)
        self.buttons = [
            ui_items.Button(
                (0, 0),
                (0, 0),
                "#F2EBBF",
                lambda: self.gui.switch_game_screen(Board(self.gui)),
                "Play",
                text_color="#5C4B51",
            ),
            ui_items.Button(
                (0, 0),
                (0, 0),
                "#F2EBBF",
                lambda: print("options"),
                "Options",
                text_color="#5C4B51",
            ),
            ui_items.Button(
                (0, 0),
                (0, 0),
                "#F2EBBF",
                lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
                "Exit",
                text_color="#5C4B51",
            ),
        ]
        self.ui_vertical_box = ui_layouts.UIVerticalBox(
            (0, 0), gui.display_surface.get_size(), self.buttons, (0.3, 0.1), 0.05
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        if event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                btn.handle_click(event.pos)

    def update(self) -> None:
        self.gui.display_surface.fill("#8CBEB2")
        self.ui_vertical_box.draw(self.gui.display_surface)


class Board(GameScreen):
    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.gui.switch_game_screen(Menu(self.gui))

    def update(self) -> None:
        self.gui.display_surface.fill('#79BD8F')