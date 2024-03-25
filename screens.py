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

    def draw(self) -> None:
        raise NotImplementedError("Method draw is not implemented!")


class Menu(GameScreen):
    def __init__(self, gui: Gui) -> None:
        super().__init__(gui)
        self.buttons = [
            ui_items.Button(
                (0, 0),
                (0, 0),
                lambda: self.gui.switch_game_screen(Board(self.gui)),
                text="Play",
            ),
            ui_items.Button(
                (0, 0),
                (0, 0),
                lambda: print("options"),
                text="Options",
            ),
            ui_items.Button(
                (0, 0),
                (0, 0),
                lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
                text="Exit",
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

    def draw(self) -> None:
        self.gui.display_surface.fill("#8CBEB2")
        self.ui_vertical_box.draw(self.gui.dt, self.gui.display_surface)


class Board(GameScreen):
    def __init__(self, gui: Gui):
        super().__init__(gui)
        self.exit_pop_up = ui_items.TextPopUp(
            (0, 0),
            (0, 0),
            buttons=[
                ui_items.Button(
                    (0, 0),
                    (0, 0),
                    on_click=lambda: self.gui.switch_game_screen(Menu(self.gui)),
                    text="YES",
                ),
                ui_items.Button(
                    (0, 0),
                    (0, 0),
                    on_click=lambda: self.exit_pop_up.toggle(),
                    text="NO",
                ),
            ],
            text="Exit to menu?",
        )
        self.exit_pop_up_container = ui_layouts.UIVerticalBox(
            (0, 0),
            gui.display_surface.get_size(),
            [self.exit_pop_up],
            (0.2, 0.3),
        )

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_pop_up.toggle()
            else:
                self.gui.switch_game_screen(Menu(self.gui))
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.exit_pop_up.handle_click(event.pos)

    def draw(self) -> None:
        self.gui.display_surface.fill("#79BD8F")
        self.exit_pop_up_container.draw(self.gui.dt, self.gui.display_surface)
