from __future__ import annotations
from typing import TYPE_CHECKING
import pygame, ui
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
            ui.Button(
                on_click=lambda: self.gui.switch_game_screen(Board(self.gui)),
                text="Play",
            ),
            ui.Button(
                on_click=lambda: print("options"),
                text="Options",
            ),
            ui.Button(
                on_click=lambda: pygame.event.post(pygame.event.Event(pygame.QUIT)),
                text="Exit",
            ),
        ]
        self.buttons_container = ui.UIVerticalBox(
            size=gui.display_surface.get_size(), 
            items=self.buttons, 
            padding=(0.3, 0.1), 
            spacing=0.05
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
        self.buttons_container.draw(self.gui.dt, self.gui.display_surface)


class Board(GameScreen):
    def __init__(self, gui: Gui):
        super().__init__(gui)
        self.exit_pop_up = ui.TextPopUp(
            position=(
                int(0.2 * self.gui.display_surface.get_width()),
                int(0.3 * self.gui.display_surface.get_height()),
            ),
            size=(
                int(0.6 * self.gui.display_surface.get_width()),
                int(0.4 * self.gui.display_surface.get_height()),
            ),
            buttons=[
                ui.Button(
                    on_click=lambda: self.gui.switch_game_screen(Menu(self.gui)),
                    text="YES",
                    bg_color="#8CBEB2",
                ),
                ui.Button(
                    on_click=lambda: self.exit_pop_up.toggle(),
                    text="NO",
                    bg_color="#F3B562",
                ),
            ],
            text="Exit to menu?",
        )
        self.info_stripe = ui.UIHorizontalBox(
            position=(
                0,
                int(0.95 * self.gui.display_surface.get_height()),
            ),
            size=(
                self.gui.display_surface.get_width(),
                int(0.05 * self.gui.display_surface.get_height()),
            ),
            items=[
                ui.Label(text="TABLE WIND: EAST"),
                ui.Label(text="PLAYER WIND: SOUTH"),
                ui.Label(text="POINTS: 1000"),
            ]
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
        self.info_stripe.draw(self.gui.dt, self.gui.display_surface)
        self.exit_pop_up.draw(self.gui.dt, self.gui.display_surface)
        