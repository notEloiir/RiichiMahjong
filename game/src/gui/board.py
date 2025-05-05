from __future__ import annotations
import pygame

import game.src.gui.discard_pile as discard_pile
import game.src.gui.hand as hand
import game.src.gui.menu as menu
import game.src.gui.resource_manager as resource_manager
import game.src.gui.scores as scores
import game.src.gui.settings as settings
import game.src.gui.status_bar as status_bar
import game.src.gui.tile_sprite as tile_sprite
import game.src.gui.ui_items as ui_items
from game.src.core.mahjong_enums import MoveType

class Board:
    def __init__(self, game):
        self.game = game
        self.display_surface = self.game.display_surface
        self.buffer_surface = pygame.Surface(self.display_surface.get_size())
        self.width, self.height = self.game.display_surface.get_size()
        self.game_state = None
        self.possible_moves = []
        self.chosen_move = None
        self.input_ready = False
        self.curr_player_id = None

        center_offset = 0.1 * self.height / 2
        pile_spacing = 0.01 * self.height

        self.prevalent_wind_label = ui_items.Label(
            position=(
                0.5 * self.width - center_offset,
                0.5 * self.height - center_offset,
            ),
            size=(
                2 * center_offset,
                center_offset,
            ),
            text="",
            align="center",
        )
        self.tiles_count_label = ui_items.Label(
            position=(
                0.5 * self.width - center_offset,
                0.5 * self.height,
            ),
            size=(
                2 * center_offset,
                center_offset,
            ),
            text="",
            align="center",
        )

        self.dora_indicators_label = ui_items.Label(
            position=(0.27 * self.height, 0.25 * self.height),
            size=(0.3 * self.width, 0.05 * self.height),
            text="Dora indicators",
            align="left",
        )

        self.dora_indicators = discard_pile.DiscardPile(
            position=(0.27 * self.height, 0.3 * self.height),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=0,
        )

        self.discard_pile_0 = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset + pile_spacing,
                0.5 * self.height + center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=0,
        )
        self.discard_pile_1 = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset + pile_spacing,
                0.5 * self.height + center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=1,
        )
        self.discard_pile_2 = discard_pile.DiscardPile(
            position=(
                0.5 * self.width + center_offset - pile_spacing,
                0.5 * self.height - center_offset - pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=2,
        )
        self.discard_pile_3 = discard_pile.DiscardPile(
            position=(
                0.5 * self.width - center_offset - pile_spacing,
                0.5 * self.height - center_offset + pile_spacing,
            ),
            size=(0.6 * self.width, 0.15 * self.height),
            rotation=3,
        )

        self.waiting_prompt = ui_items.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.6 * self.width, 0.05 * self.height),
            text="...",
            align="left",
        )

        self.discarding_prompt = ui_items.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            text="Choose tile to discard",
            align="left",
        )
        self.discarding_button = ui_items.Button(
            position=(
                0.5 * self.width + 0.5 * 0.9 * self.height - 0.1 * self.width,
                0.80 * self.height,
            ),
            size=(0.1 * self.width, 0.05 * self.height),
            text="Confirm",
            on_click=lambda: self.discard_tile(),
        )

        self.decision_prompt = ui_items.Label(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.80 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            text="Take action?",
            align="left",
        )
        self.decision_buttons = []

        self.bot_1_label = ui_items.Label(
            position=(self.width - 0.2 * self.height, 0.95 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            rotation=1,
            text="Bot 1",
        )
        self.bot_2_label = ui_items.Label(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.2 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            rotation=2,
            text="Bot 2",
        )
        self.bot_3_label = ui_items.Label(
            position=(0.2 * self.height, 0.05 * self.height),
            size=(0.5 * self.width, 0.05 * self.height),
            rotation=3,
            text="Bot 3",
        )

        self.player_hand = hand.PlayerHand(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.85 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
        )
        self.bot_hand_1 = hand.Hand(
            position=(self.width - 0.15 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=1,
        )
        self.bot_hand_2 = hand.Hand(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.15 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=2,
        )
        self.bot_hand_3 = hand.Hand(
            position=(0.15 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.1 * self.height),
            rotation=3,
        )

        self.status_bar_0 = status_bar.StatusBar(
            position=(0.5 * self.width - 0.5 * 0.9 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=0,
        )
        self.status_bar_1 = status_bar.StatusBar(
            position=(self.width - 0.05 * self.height, 0.95 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=1,
        )
        self.status_bar_2 = status_bar.StatusBar(
            position=(0.5 * self.width + 0.5 * 0.9 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=2,
        )
        self.status_bar_3 = status_bar.StatusBar(
            position=(0.05 * self.height, 0.05 * self.height),
            size=(0.9 * self.height, 0.05 * self.height),
            rotation=3,
        )

        self.exit_pop_up = ui_items.YesOrNoPopUp(
            position=(0.2 * self.width, 0.3 * self.height),
            size=(0.6 * self.width, 0.4 * self.height),
            on_yes=lambda: self.game.switch_game_screen(menu.Menu(self.game)),
            on_no=lambda: self.exit_pop_up.toggle(),
            yes_text="YES",
            no_text="NO",
            pop_up_text="Exit to menu?",
        )

        self.score_display = scores.Scores(self.game, (self.width, self.height))

    def restrict_tiles(self, can_select_tiles: list[bool]):
        self.player_hand.restrict_tiles(can_select_tiles)

    def lift_restriction_tiles(self):
        self.player_hand.lift_restriction_tiles()

    def update_state(
        self,
        prevalent_wind,
        seat_wind,
        turn_no,
        dealer_id,
        closed_hands,
        melds,
        discard_piles,
        dora_indicators,
        scores,
        show_stick,
        show_furiten,
    ):
        winds = "East South West North"
        self.prevalent_wind_label.text = winds.split()[prevalent_wind]
        self.tiles_count_label.text = f"Wall: {70 - turn_no}"

        specials = [
            ("D" if dealer_id == i else "")
            + ("R" if show_stick[i] else "")
            + ("F" if show_furiten[i] else "")
            for i in range(4)
        ]
        self.status_bar_0.update_status(
            winds.split()[seat_wind[0]], str(scores[0]), specials[0]
        )
        self.status_bar_1.update_status(
            winds.split()[seat_wind[1]], str(scores[1]), specials[1]
        )
        self.status_bar_2.update_status(
            winds.split()[seat_wind[2]], str(scores[2]), specials[2]
        )
        self.status_bar_3.update_status(
            winds.split()[seat_wind[3]], str(scores[3]), specials[3]
        )

        self.player_hand.update_tiles(closed_hands[0], melds[0])
        self.bot_hand_1.update_tiles(closed_hands[1], melds[1])
        self.bot_hand_2.update_tiles(closed_hands[2], melds[2])
        self.bot_hand_3.update_tiles(closed_hands[3], melds[3])

        self.dora_indicators.update_tiles(dora_indicators)

        self.discard_pile_0.update_tiles(discard_piles[0])
        self.discard_pile_1.update_tiles(discard_piles[1])
        self.discard_pile_2.update_tiles(discard_piles[2])
        self.discard_pile_3.update_tiles(discard_piles[3])

    def update_curr_player_id(self, curr_player_id):
        self.curr_player_id = curr_player_id

    def play_sound(self, sound_name):
        resource_manager.get_sound(sound_name).play()

    def switch_game_state(self, game_state, **kwargs):
        self.game_state = game_state
        self.input_ready = False

        if self.game_state == "WAITING":
            self.possible_moves = []
            self.chosen_move = None
            self.player_hand.selected_tile = None
        elif self.game_state == "DECIDING":
            self.decision_prompt.text = "Take action?"
            if kwargs.get("target_tile") and kwargs.get("target_tile") is not None:
                self.decision_prompt.text += f" ({tile_sprite.TileSprite.get_tile_name(kwargs.get('target_tile').true_id())})"
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
                    ui_items.Button(
                        position=button_position,
                        size=button_size,
                        text=MoveType(move).name,
                        on_click=lambda x=move: self.make_decision(x),
                    )
                )
                button_position = (
                    button_position[0] + button_size[0] + spacing,
                    button_position[1],
                )
        elif self.game_state == "DECIDING_CHI":
            self.decision_prompt.text = "Which chi to meld?"
            target_tile = kwargs.get("target_tile")
            if target_tile:
                self.decision_prompt.text += f" ({tile_sprite.TileSprite.get_tile_name(target_tile.true_id())})"
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
            for i, move in enumerate(self.possible_moves):
                tile_number = (target_tile.to_int()) % 9 + 1
                button_text = " - ".join(sorted([str(tile_number), str(tile_number + move[0]), str(tile_number + move[1])]))
                self.decision_buttons.append(
                    ui_items.Button(
                        position=button_position,
                        size=button_size,
                        text=button_text,
                        on_click=lambda chosen_chi_id=i: self.make_decision(chosen_chi_id),
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

    def show_scores(self, scores, scores_gained, message):
        self.score_display.show(scores, scores_gained, message)

    def handle_event(self, event: pygame.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.score_display.active:
                    self.score_display.toggle_visible()
                else:
                    self.exit_pop_up.toggle()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.score_display.active and self.score_display.visible:
                self.score_display.handle_click(event.pos)
            elif self.exit_pop_up.active:
                self.exit_pop_up.handle_click(event.pos)
            elif self.game_state == "DISCARDING":
                self.player_hand.handle_click(event.pos)
                self.discarding_button.handle_click(event.pos)
            elif self.game_state == "DECIDING" or self.game_state == "DECIDING_CHI":
                for button in self.decision_buttons:
                    button.handle_click(event.pos)

    def draw(self) -> None:
        self.buffer_surface.fill("#79BD8F")

        if self.curr_player_id == 0:
            pygame.draw.rect(
                self.buffer_surface,
                "#68AC7E",
                (
                    0.25 * self.height,
                    0.75 * self.height,
                    self.width - 0.5 * self.height,
                    0.25 * self.height,
                ),
            )
        if self.curr_player_id == 1:
            pygame.draw.rect(
                self.buffer_surface,
                "#68AC7E",
                (
                    self.width - 0.25 * self.height,
                    0,
                    0.25 * self.height,
                    self.height,
                ),
            )
        if self.curr_player_id == 2:
            pygame.draw.rect(
                self.buffer_surface,
                "#68AC7E",
                (
                    0.25 * self.height,
                    0,
                    self.width - 0.5 * self.height,
                    0.25 * self.height,
                ),
            )
        if self.curr_player_id == 3:
            pygame.draw.rect(
                self.buffer_surface,
                "#68AC7E",
                (
                    0,
                    0,
                    0.25 * self.height,
                    self.height,
                ),
            )

        pygame.draw.line(
            self.buffer_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0.75 * self.height),
            (self.width - 0.25 * self.height, 0.75 * self.height),
            width=5,
        )
        pygame.draw.line(
            self.buffer_surface,
            settings.PRIMARY_COLOR,
            (self.width - 0.25 * self.height, 0),
            (self.width - 0.25 * self.height, self.height),
            width=5,
        )
        pygame.draw.line(
            self.buffer_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0.25 * self.height),
            (self.width - 0.25 * self.height, 0.25 * self.height),
            width=5,
        )
        pygame.draw.line(
            self.buffer_surface,
            settings.PRIMARY_COLOR,
            (0.25 * self.height, 0),
            (0.25 * self.height, self.height),
            width=5,
        )

        self.prevalent_wind_label.draw(self.buffer_surface)
        self.tiles_count_label.draw(self.buffer_surface)

        self.dora_indicators_label.draw(self.buffer_surface)
        self.dora_indicators.draw(self.buffer_surface)

        self.discard_pile_0.draw(self.buffer_surface)
        self.discard_pile_1.draw(self.buffer_surface)
        self.discard_pile_2.draw(self.buffer_surface)
        self.discard_pile_3.draw(self.buffer_surface)

        self.player_hand.draw(self.buffer_surface)
        self.bot_hand_1.draw(self.buffer_surface)
        self.bot_hand_2.draw(self.buffer_surface)
        self.bot_hand_3.draw(self.buffer_surface)

        self.bot_1_label.draw(self.buffer_surface)
        self.bot_2_label.draw(self.buffer_surface)
        self.bot_3_label.draw(self.buffer_surface)

        self.status_bar_0.draw(self.buffer_surface)
        self.status_bar_1.draw(self.buffer_surface)
        self.status_bar_2.draw(self.buffer_surface)
        self.status_bar_3.draw(self.buffer_surface)

        if self.game_state == "WAITING":
            self.waiting_prompt.draw(self.buffer_surface)
        elif self.game_state == "DISCARDING":
            self.discarding_prompt.draw(self.buffer_surface)
            self.discarding_button.draw(self.buffer_surface)
        elif self.game_state == "DECIDING" or self.game_state == "DECIDING_CHI":
            self.decision_prompt.draw(self.buffer_surface)
            for button in self.decision_buttons:
                button.draw(self.buffer_surface)

        self.exit_pop_up.draw(self.buffer_surface)
        self.score_display.draw(self.buffer_surface)

        self.display_surface.blit(self.buffer_surface, (0, 0))
