from __future__ import annotations
from typing import TYPE_CHECKING
import pygame, ui, menu, discard_pile, player_hand, random

if TYPE_CHECKING:
    from gui import Gui


class Board():
    def __init__(self, gui: Gui):
        self.gui = gui
        self.prepare_ui_elements()
        self.game_state = "WAITING"

    def prepare_ui_elements(self):
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
                    on_click=lambda: self.gui.switch_game_screen(menu.Menu(self.gui)),
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

        self.discard_pile_1 = discard_pile.DiscardPile(
            position=(
                int(0.4 * self.gui.display_surface.get_width()), 
                int(0.55 * self.gui.display_surface.get_height())
            ),
            size=(
                int(0.6 * self.gui.display_surface.get_width()), 
                int(0.2 * self.gui.display_surface.get_height())
            ),
        )
        self.discard_pile_1.update_tiles(random.sample(range(135), 16))

        self.waiting_prompt = ui.Label(
            position=(
                int(0.2 * self.gui.display_surface.get_width()), 
                int(0.80 * self.gui.display_surface.get_height())
            ),
            size=(
                int(0.6 * self.gui.display_surface.get_width()), 
                int(0.05 * self.gui.display_surface.get_height())
            ),
            text="Opponent's turn...",
            align="left",
        )

        self.discarding_prompt = ui.Label(
            position=(
                int(0.2 * self.gui.display_surface.get_width()), 
                int(0.80 * self.gui.display_surface.get_height()),
            ),
            size=(
                int(0.5 * self.gui.display_surface.get_width()), 
                int(0.05 * self.gui.display_surface.get_height()),
            ),
            text="Choose tile to discard",
            align="left",
        )
        self.discarding_button = ui.Button(
             position=(
                int(0.7 * self.gui.display_surface.get_width()), 
                int(0.8 * self.gui.display_surface.get_height())
            ),
            size=(
                int(0.1* self.gui.display_surface.get_width()), 
                int(0.05 * self.gui.display_surface.get_height())
            ),
            text="Confirm",
        )

        self.hand = player_hand.PlayerHand(
            position=(
                int(0.2 * self.gui.display_surface.get_width()), 
                int(0.87 * self.gui.display_surface.get_height())
            ),
            size=(
                int(0.8 * self.gui.display_surface.get_width()), 
                int(0.1 * self.gui.display_surface.get_height())
            ),
        )
        self.hand.update_tiles(sorted(random.sample(range(135), 14)))

        self.table_wind_label = ui.Label(
            position=(
                int(0.2 * self.gui.display_surface.get_width()),
                0
            ),
            size=(
                int(0.2 * self.gui.display_surface.get_width()),
                int(0.05 * self.gui.display_surface.get_height()),
            ),
            text="TABLE WIND: EAST",
            align="left"
        )
        self.player_wind_label = ui.Label(
            position=(
                int(0.4 * self.gui.display_surface.get_width()),
                0
            ),
            size=(
                int(0.2 * self.gui.display_surface.get_width()),
                int(0.05 * self.gui.display_surface.get_height()),
            ),
            text="PLAYER WIND: SOUTH",
            align="center"
        )
        self.player_points_label = ui.Label(
            position=(
                int(0.6 * self.gui.display_surface.get_width()),
                0
            ),
            size=(
                int(0.2 * self.gui.display_surface.get_width()),
                int(0.05 * self.gui.display_surface.get_height()),
            ),
            text="POINTS: 1000",
            align="right",
        )

    def switch_game_state(self, game_state):
        self.game_state = game_state

        if self.game_state == "WAITING":
            self.hand.selected_tile = None


    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_pop_up.toggle()
            elif event.key == pygame.K_w:
                self.switch_game_state("WAITING")
            elif event.key == pygame.K_d:
                self.switch_game_state("DISCARDING")
            else:
                self.gui.switch_game_screen(menu.Menu(self.gui))
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.exit_pop_up.active:
                self.exit_pop_up.handle_click(event.pos)
                return
            if self.game_state == "DISCARDING":
                self.hand.handle_click(event.pos)

    def draw(self) -> None:
        self.gui.display_surface.fill("#79BD8F")

        self.table_wind_label.draw(self.gui.display_surface)
        self.player_wind_label.draw(self.gui.display_surface)
        self.player_points_label.draw(self.gui.display_surface)

        self.discard_pile_1.draw(self.gui.display_surface)

        if self.game_state == "WAITING":
            self.waiting_prompt.draw(self.gui.display_surface)
        elif self.game_state == "DISCARDING":
            self.discarding_prompt.draw(self.gui.display_surface)
            self.discarding_button.draw(self.gui.display_surface)

        self.hand.draw(self.gui.display_surface)
        
        self.exit_pop_up.draw(self.gui.display_surface)