from __future__ import annotations
from typing import TYPE_CHECKING
import pygame, ui, menu, discard_pile, hand, random

if TYPE_CHECKING:
    from gui import Gui


class Board:
    def __init__(self, gui: Gui):
        self.gui = gui
        self.display_surface = self.gui.display_surface
        self.width, self.height = self.gui.display_surface.get_size()
        self.game_state = "WAITING"

        self.table_wind_label = ui.Label(
            position=(0.2 * self.width, 0),
            size=(0.2 * self.width, 0.05 * self.height),
            text="TABLE WIND: EAST",
            align="left",
        )
        self.player_wind_label = ui.Label(
            position=(0.4 * self.width, 0),
            size=(0.2 * self.width, 0.05 * self.height),
            text="PLAYER WIND: SOUTH",
            align="center",
        )
        self.player_points_label = ui.Label(
            position=(0.6 * self.width, 0),
            size=(0.2 * self.width, 0.05 * self.height),
            text="POINTS: 1000",
            align="right",
        )

        center_offset = 0.1 * self.height / 2
        pile_spacing = 0.01 * self.height
        self.discard_pile_south = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset + pile_spacing,
                0.5 * self.height + center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.2 * self.height),
            rotation=0,
        )
        self.discard_pile_south.update_tiles(random.sample(range(135), 16))
        self.discard_pile_east = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset + pile_spacing,
                0.5 * self.height + center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.2 * self.height),
            rotation=1,
        )
        self.discard_pile_east.update_tiles(random.sample(range(135), 16))
        self.discard_pile_north = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset - pile_spacing,
                0.5 * self.height - center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.2 * self.height),
            rotation=2,
        )
        self.discard_pile_north.update_tiles(random.sample(range(135), 16))
        self.discard_pile_west = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset - pile_spacing,
                0.5 * self.height - center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.2 * self.height),
            rotation=3,
        )
        self.discard_pile_west.update_tiles(random.sample(range(135), 16))

        self.waiting_prompt = ui.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.6 * self.width, 0.05 * self.height),
            text="Opponent's turn...",
            align="left",
        )

        self.discarding_prompt = ui.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            text="Choose tile to discard",
            align="left",
        )
        self.discarding_button = ui.Button(
            position=(
                0.5 * self.width + 0.5 * 0.9 * self.height - 0.1 * self.width,
                0.80 * self.height,
            ),
            size=(0.1 * self.width, 0.05 * self.height),
            text="Confirm",
        )

        self.player_hand = hand.PlayerHand(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.85 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
        )
        self.player_hand.update_tiles(sorted(random.sample(range(135), 14)))

        self.hand_east = hand.Hand(
            position=(self.width - 0.15 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=1,
        )
        self.hand_east.update_tiles(sorted(random.sample(range(135), 14)))

        self.hand_north = hand.Hand(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.15 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=2,
        )
        self.hand_north.update_tiles(sorted(random.sample(range(135), 14)))

        self.hand_west = hand.Hand(
            position=(0.15 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=3,
        )
        self.hand_west.update_tiles(sorted(random.sample(range(135), 14)))

        self.exit_pop_up = ui.YesOrNoPopUp(
            position=(0.2 * self.width, 0.3 * self.height),
            size=(0.6 * self.width, 0.4 * self.height),
            on_yes=lambda: self.gui.switch_game_screen(menu.Menu(self.gui)),
            on_no=lambda: self.exit_pop_up.toggle(),
            yes_text="YES",
            no_text="NO",
            pop_up_text="Exit to menu?",
        )

    def switch_game_state(self, game_state):
        self.game_state = game_state

        if self.game_state == "WAITING":
            self.player_hand.selected_tile = None

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_pop_up.toggle()
            elif event.key == pygame.K_w:
                self.switch_game_state("WAITING")
            elif event.key == pygame.K_d:
                self.switch_game_state("DISCARDING")
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.exit_pop_up.active:
                self.exit_pop_up.handle_click(event.pos)
                return
            if self.game_state == "DISCARDING":
                self.player_hand.handle_click(event.pos)

    def draw(self) -> None:
        self.display_surface.fill("#79BD8F")

        self.table_wind_label.draw(self.display_surface)
        self.player_wind_label.draw(self.display_surface)
        self.player_points_label.draw(self.display_surface)

        self.discard_pile_south.draw(self.display_surface)
        self.discard_pile_east.draw(self.display_surface)
        self.discard_pile_north.draw(self.display_surface)
        self.discard_pile_west.draw(self.display_surface)

        if self.game_state == "WAITING":
            self.waiting_prompt.draw(self.display_surface)
        elif self.game_state == "DISCARDING":
            self.discarding_prompt.draw(self.display_surface)
            self.discarding_button.draw(self.display_surface)

        self.player_hand.draw(self.display_surface)
        self.hand_east.draw(self.display_surface)
        self.hand_north.draw(self.display_surface)
        self.hand_west.draw(self.display_surface)

        self.exit_pop_up.draw(self.display_surface)
