from __future__ import annotations
from typing import TYPE_CHECKING
import pygame, settings, ui, menu, discard_pile, hand, status_bar, tile_sprite
from mahjong_enums import MoveType


if TYPE_CHECKING:
    from gui import Gui


class Board:
    def __init__(self, gui: Gui):
        self.gui = gui
        self.display_surface = self.gui.display_surface
        self.width, self.height = self.gui.display_surface.get_size()
        self.game_state = "WAITING"
        self.possible_moves = []
        self.chosen_move = None
        self.input_ready = False

        center_offset = 0.1 * self.height / 2
        pile_spacing = 0.01 * self.height

        self.prevalent_wind_label = ui.Label(
            position=(
                0.5 * self.width - center_offset,
                0.5 * self.height - center_offset,
            ),
            size=(
                2 * center_offset,
                2 * center_offset,
            ),
            text="",
            align="center",
        )

        self.discard_pile_south = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset + pile_spacing,
                0.5 * self.height + center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=0,
        )
        self.discard_pile_east = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset + pile_spacing,
                0.5 * self.height + center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=1,
        )
        self.discard_pile_north = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset - pile_spacing,
                0.5 * self.height - center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=2,
        )
        self.discard_pile_west = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset - pile_spacing,
                0.5 * self.height - center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=3,
        )

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
            on_click=lambda: self.discard_tile(),
        )

        self.decision_promt = ui.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            text="Take action?",
            align="left",
        )
        self.decision_buttons = []

        self.player_hand = hand.PlayerHand(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.85 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
        )
        self.hand_east = hand.Hand(
            position=(self.width - 0.15 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=1,
        )
        self.hand_north = hand.Hand(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.15 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=2,
        )
        self.hand_west = hand.Hand(
            position=(0.15 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=3,
        )

        self.status_bar_south = status_bar.StatusBar(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=0,
        )
        self.status_bar_east = status_bar.StatusBar(
            position=(self.width - 0.05 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=1,
        )
        self.status_bar_north = status_bar.StatusBar(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=2,
        )
        self.status_bar_west = status_bar.StatusBar(
            position=(0.05 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=3,
        )

        self.exit_pop_up = ui.YesOrNoPopUp(
            position=(0.2 * self.width, 0.3 * self.height),
            size=(0.6 * self.width, 0.4 * self.height),
            on_yes=lambda: self.gui.switch_game_screen(menu.Menu(self.gui)),
            on_no=lambda: self.exit_pop_up.toggle(),
            yes_text="YES",
            no_text="NO",
            pop_up_text="Exit to menu?",
        )

    def update_state(
        self,
        prevalent_wind,
        seat_wind,
        turn_no,
        dealer_id,
        closed_hands,
        open_hands,
        discard_piles,
        dora_indicators,
        scores,
        show_stick,
        show_furiten,
    ):
        winds = "East South West North"
        self.prevalent_wind_label.text = winds.split()[prevalent_wind][0]

        specials = [
            ("D" if dealer_id == i else "")
            + ("R" if show_stick[i] else "")
            + ("F" if show_furiten[i] else "")
            for i in range(4)
        ]
        self.status_bar_south.update_status(
            winds.split()[seat_wind[0]], str(scores[0]), specials[0]
        )
        self.status_bar_east.update_status(
            winds.split()[seat_wind[1]], str(scores[1]), specials[1]
        )
        self.status_bar_north.update_status(
            winds.split()[seat_wind[2]], str(scores[2]), specials[2]
        )
        self.status_bar_west.update_status(
            winds.split()[seat_wind[3]], str(scores[3]), specials[3]
        )

        self.player_hand.update_tiles(closed_hands[0], open_hands[0])
        self.hand_east.update_tiles(closed_hands[1], open_hands[1])
        self.hand_north.update_tiles(closed_hands[2], open_hands[2])
        self.hand_west.update_tiles(closed_hands[3], open_hands[3])

        self.discard_pile_south.update_tiles(discard_piles[0])
        self.discard_pile_east.update_tiles(discard_piles[1])
        self.discard_pile_north.update_tiles(discard_piles[2])
        self.discard_pile_west.update_tiles(discard_piles[3])

    def switch_game_state(self, game_state, **kwargs):
        self.game_state = game_state
        self.input_ready = False

        if self.game_state == "WAITING":
            self.possible_moves = []
            self.chosen_move = None
            self.player_hand.selected_tile = None
        elif self.game_state == "DECIDING":
            self.decision_promt.text = "Take action?"
            if kwargs.get("target_tile"):
                self.decision_promt.text += f" ({tile_sprite.TileSprite.get_tile_name(kwargs.get('target_tile').true_id())})"
            self.possible_moves = kwargs.get("possible_moves")
            self.chosen_move = None
            self.player_hand.selected_tile = None

            self.decision_buttons = []
            spacing = 3
            button_size = (
                (0.2 * self.width - (len(self.possible_moves) - 1) * spacing)
                / len(self.possible_moves),
                0.05 * self.height,
            )
            button_position = (
                0.5 * self.width + 0.5 * 0.9 * self.height - 0.2 * self.width,
                0.80 * self.height,
            )
            for move in self.possible_moves:
                self.decision_buttons.append(
                    ui.Button(
                        position=button_position,
                        size=button_size,
                        text=MoveType(move).name,
                        on_click=lambda move=move: self.make_decision(move),
                    )
                )
                button_position = (
                    button_position[0] + button_size[0] + spacing,
                    button_position[1],
                )

    def make_decision(self, move):
        self.chosen_move = move
        self.input_ready = True

    def discard_tile(self):
        if self.player_hand.selected_tile:
            self.input_ready = True

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_pop_up.toggle()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.exit_pop_up.active:
                self.exit_pop_up.handle_click(event.pos)
                return
            if self.game_state == "DISCARDING":
                self.player_hand.handle_click(event.pos)
                self.discarding_button.handle_click(event.pos)
            if self.game_state == "DECIDING":
                for button in self.decision_buttons:
                    button.handle_click(event.pos)

    def draw(self) -> None:
        self.display_surface.fill("#79BD8F")
        pygame.draw.line(
            self.display_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0.75 * self.height),
            (self.width - 0.25 * self.height, 0.75 * self.height),
            width=5,
        )
        pygame.draw.line(
            self.display_surface,
            settings.PRIMARY_COLOR,
            (self.width - 0.25 * self.height, 0),
            (self.width - 0.25 * self.height, self.height),
            width=5,
        )
        pygame.draw.line(
            self.display_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0.25 * self.height),
            (self.width - 0.25 * self.height, 0.25 * self.height),
            width=5,
        )
        pygame.draw.line(
            self.display_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0),
            (0.25 * self.height, self.height),
            width=5,
        )

        self.prevalent_wind_label.draw(self.display_surface)

        self.discard_pile_south.draw(self.display_surface)
        self.discard_pile_east.draw(self.display_surface)
        self.discard_pile_north.draw(self.display_surface)
        self.discard_pile_west.draw(self.display_surface)

        self.player_hand.draw(self.display_surface)
        self.hand_east.draw(self.display_surface)
        self.hand_north.draw(self.display_surface)
        self.hand_west.draw(self.display_surface)

        self.status_bar_south.draw(self.display_surface)
        self.status_bar_east.draw(self.display_surface)
        self.status_bar_north.draw(self.display_surface)
        self.status_bar_west.draw(self.display_surface)

        if self.game_state == "WAITING":
            self.waiting_prompt.draw(self.display_surface)
        elif self.game_state == "DISCARDING":
            self.discarding_prompt.draw(self.display_surface)
            self.discarding_button.draw(self.display_surface)
        elif self.game_state == "DECIDING":
            self.decision_promt.draw(self.display_surface)
            for button in self.decision_buttons:
                button.draw(self.display_surface)

        self.exit_pop_up.draw(self.display_surface)
