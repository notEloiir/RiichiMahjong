import random
import numpy as np
from time import sleep
from sys import exit
from mahjong import agari
from mahjong.meld import Meld
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
import mahjong.constants as mc

from ml.src.data_structures import DataPoint
from game.src.core.player import Player
from game.src.core.mahjong_enums import EventType, RiichiStatus, FuritenStatus, MoveType
from game.src.core.tile import Tile
from game.src.core.shanten import correct_shanten


def wind_from_int(wind_id):
    match wind_id:
        case 0:
            return mc.EAST
        case 1:
            return mc.SOUTH
        case 2:
            return mc.WEST
        case 3:
            return mc.NORTH
    raise ValueError("invalid wind id")


def count_tiles(tiles: list[Tile]):
    counts = [0] * 34
    for tile in tiles:
        counts[tile.id34()] += 1
    return counts


class Event:
    def __init__(self, what: EventType, who=None, from_who=None):
        self.what: EventType = what
        self.who = who
        self.from_who = from_who


# Main game logic
class Round:
    def __init__(self, competitors: list[Player], scores, non_repeat_round_no, match_type, device, gui=None):
        self.hand_calculator = HandCalculator()
        self.competitors = competitors
        self.scores = scores
        self.device = device
        self.gui = gui
        self.board = None

        # INIT
        self.dealer_id = (match_type + non_repeat_round_no) % 4
        self.prevalent_wind = (match_type + (non_repeat_round_no // 4)) % 4
        self.seat_wind = [(non_repeat_round_no + i) % 4 for i in range(4)]
        self.turn_no = 0
        self.round_no = non_repeat_round_no
        self.curr_player_id = self.dealer_id
        self.closed_hands: list[list[Tile]] = [[] for _ in range(4)]
        self.closed_hand_counts = [[0] * 34 for _ in range(4)]
        self.open_hands: list[list[Tile]] = [[] for _ in range(4)]
        self.open_hand_counts = [[0] * 34 for _ in range(4)]
        self.melds: list[list[Meld]] = [[] for _ in range(4)]
        self.discard_piles: list[list[Tile]] = [[] for _ in range(4)]
        self.discard_orders = [[0] * 34 for _ in range(4)]
        self.hidden_tile_counts = [[4] * 34 for _ in range(4)]
        self.hand_in_riichi = [0] * 4
        self.hand_is_closed = [1] * 4
        self.visible_dora = [0] * 34
        self.red5_closed_hand = [[0] * 3 for _ in range(4)]
        self.red5_open_hand = [[0] * 3 for _ in range(4)]
        self.red5_discarded = [0] * 3
        self.red5_hidden = [[1] * 3 for _ in range(4)]

        # extra tracking
        self.first_move = [True] * 4
        self.four_quads_draw_flag = False
        self.riichi_status: list[RiichiStatus] = [RiichiStatus.DEFAULT for _ in range(4)]
        self.furiten_status: list[FuritenStatus] = [FuritenStatus.DEFAULT for _ in range(4)]
        self.double_riichi = [False] * 4
        self.ippatsu = [False] * 4
        self.after_a_kan = False
        self.stolen_kan = False
        self.waiting_tiles = [[False] * 34 for _ in range(4)]
        self.can_riichi_discard = [[False] * 34 for _ in range(4)]
        self.nagashi_mangan = [False] * 4

        self.wall: list[Tile] = []
        self.dora_indicators: list[Tile] = []
        self.uradora_indicators: list[Tile] = []
        self.dead_wall: list[Tile] = []
        self.dora_revealed_no = 0

        self.check_input()
        self.prep_round()

        self.event = None
        self.dealer_won = False
        self.finished = False
        self.tile = Tile(-1)
        self.open_kan = False
        self.kan_tile = Tile(-1)
        self.discard_after_kan = False

    def check_input(self):
        if any(c.is_human for c in self.competitors) and self.gui is None:
            raise ValueError("need gui with human competitors")

    def prep_round(self):
        # PREP ROUND
        game_tiles = [Tile(t) for t in range(34 * 4)]
        random.shuffle(game_tiles)

        # give out tiles to players
        for p in range(4):
            for i in range(13):
                tile = game_tiles[p * 13 + i]
                self.closed_hands[p].append(tile)
                self.closed_hand_counts[p][tile.id34()] += 1
                if tile.is_red5():
                    self.red5_hidden[p][tile.id34() // 9] = 0
                    self.red5_closed_hand[p][tile.id34() // 9] = 1

        # build walls
        self.wall = game_tiles[52:122]  # from 13*4, 70 tiles
        self.dora_indicators = game_tiles[122:127]  # 5 tiles
        self.uradora_indicators = game_tiles[127:132]  # 5 tiles
        self.dead_wall = game_tiles[132:]  # 4 tiles

        # reveal the first dora indicator
        self.reveal_dora()

        if not self.gui:
            return
        self.board = self.gui.game_screen
        self.update_board()

    def update_board(self, play_sound_name=""):
        # update board
        if not self.board:
            return
        if not self.gui.playing:
            exit()
        if play_sound_name:
            self.board.play_sound(play_sound_name)

        self.board.update_state(
            self.prevalent_wind, self.seat_wind, self.turn_no, self.dealer_id, self.closed_hands,
            self.melds, self.discard_piles, self.dora_indicators[:self.dora_revealed_no], self.scores,
            [rs == RiichiStatus.RIICHI for rs in self.riichi_status],
            [fs != FuritenStatus.DEFAULT for fs in self.furiten_status],
        )

    def changed_curr_player_id(self):
        if not self.board:
            return
        if not self.gui.playing:
            exit()
        self.board.update_curr_player_id(self.curr_player_id)

    def delay(self, t=0.5):
        if self.board and not self.competitors[self.curr_player_id].is_human:
            sleep(t)

    def open_melds_tile_id34s(self):
        return [t // 4 for m in self.melds[self.curr_player_id] for t in m.tiles]

    def is_closed_kan_possible(self):
        return self.closed_hand_counts[self.curr_player_id][self.tile.id34()] == 4

    def is_added_kan_possible(self):
        return any(meld.type == Meld.PON and meld.tiles[0] // 4 == self.tile.id34()
                   for meld in self.melds[self.curr_player_id])

    def is_riichi_possible(self):
        tiles_to_ready_hand = correct_shanten(
            [self.closed_hand_counts[self.curr_player_id][i] +
             self.open_hand_counts[self.curr_player_id][i]
             for i in range(34)],
            self.melds[self.curr_player_id]
        )
        return tiles_to_ready_hand == 0 and \
               self.hand_is_closed[self.curr_player_id] and \
               not self.hand_in_riichi[self.curr_player_id] and \
               self.scores[self.curr_player_id] > 10

    def get_hand_result(self, config=None):
        if config is None:
            config = HandConfig(
                is_tsumo=True,
                is_riichi=self.hand_in_riichi[self.curr_player_id],
                player_wind=wind_from_int(self.seat_wind[self.curr_player_id]),
                round_wind=wind_from_int(self.prevalent_wind)
            )
        tiles136 = [
            t.id136()
            for t in self.closed_hands[self.curr_player_id] + self.open_hands[self.curr_player_id]
        ]
        win_tile136 = self.closed_hands[self.curr_player_id][-1].id136()
        hand_result = self.hand_calculator.estimate_hand_value(
            tiles=tiles136, win_tile=win_tile136, melds=self.melds[self.curr_player_id], config=config
        )
        return hand_result

    def is_tsumo_possible(self):
        if agari.Agari().is_agari(
            [self.closed_hand_counts[self.curr_player_id][i] +
             self.open_hand_counts[self.curr_player_id][i]
             for i in range(34)],
            self.open_melds_tile_id34s()
        ):
            return self.get_hand_result().error is None
        return False

    def is_ron_possible(self):
        if self.furiten_status[self.curr_player_id] == FuritenStatus.DEFAULT and agari.Agari().is_agari(
            [self.closed_hand_counts[self.curr_player_id][i] +
             self.open_hand_counts[self.curr_player_id][i] +
             int(self.tile.id34() == i)
             for i in range(34)],
            self.open_melds_tile_id34s()
        ):
            return self.get_hand_result().error is None
        return False

    def reveal_dora(self):
        # reveal dora
        if self.dora_revealed_no >= 5:
            self.event = Event(EventType.ROUND_DRAW)
            return

        dora_indicator = self.dora_indicators[self.dora_revealed_no]
        self.visible_dora[dora_indicator.id34()] += 1
        self.dora_revealed_no += 1
        for p in range(4):
            self.hidden_tile_counts[p][dora_indicator.id34()] -= 1
            if dora_indicator.is_red5():
                self.red5_hidden[p][dora_indicator.id34() // 9] = 0

    def play_kan(self, is_closed_kan, is_added_kan, from_who):
        # move tiles to "open" hand
        # though the hand stays closed, since it's closed kan
        self.open_hand_counts[self.curr_player_id][self.tile.id34()] = 4
        self.closed_hand_counts[self.curr_player_id][self.tile.id34()] = 0
        i = 0
        while i < len(self.closed_hands[self.curr_player_id]):
            if self.tile.id34() == self.closed_hands[self.curr_player_id][i].id34():
                self.open_hands[self.curr_player_id].append(self.closed_hands[self.curr_player_id].pop(i))
            else:
                i += 1
        self.open_kan = not is_closed_kan
        self.kan_tile = self.tile
        self.after_a_kan = True
        self.discard_after_kan = True

        if is_added_kan:
            for meld in self.melds[self.curr_player_id]:
                if meld.type == Meld.PON and meld.tiles[0] // 4 == self.tile.id34():
                    meld.type = Meld.KAN
                    meld.tiles = [i for i in range(self.tile.id34() * 4, (self.tile.id34() + 1) * 4)]
                    break
        else:
            self.melds[self.curr_player_id].append(
                Meld(
                    meld_type=Meld.KAN,
                    tiles=[i for i in range(self.tile.id34() * 4, (self.tile.id34() + 1) * 4)],
                    opened=(not is_closed_kan),
                    who=self.curr_player_id, from_who=from_who
                )
            )

        if is_closed_kan:
            self.reveal_dora()

        self.update_board(play_sound_name="tile_meld")

        # TODO: reveal previously hidden tiles (0 if added, 3 if open, 4 if closed) to other players

        # check kan theft, then get another tile from dead wall
        self.event = Event(EventType.AFTER_KAN, self.curr_player_id, from_who)

    def play_pon(self, from_who):
        # Move tiles from closed hand to open hand
        i = 0
        ctr = 0
        meld_tiles = []
        while i < len(self.closed_hands[self.curr_player_id]) and ctr < 2:
            if self.closed_hands[self.curr_player_id][i].id34() == self.tile.id34():
                meld_tiles.append(self.closed_hands[self.curr_player_id].pop(i))
                ctr += 1
            else:
                i += 1
        self.closed_hand_counts[self.curr_player_id][self.tile.id34()] -= 2  # you take the third one from someone
        self.open_hand_counts[self.curr_player_id][self.tile.id34()] += 3
        if self.tile.is_red5():
            self.red5_discarded[self.tile.id34() // 9] = 0
            self.red5_open_hand[self.curr_player_id][self.tile.id34() // 9] = 1
        meld_tiles.append(self.tile)
        self.open_hands[self.curr_player_id].extend(meld_tiles)

        self.melds[self.curr_player_id].append(
            Meld(
                meld_type=Meld.PON,
                tiles=[t.id136() for t in meld_tiles],
                opened=True,
                called_tile=self.tile.id136(),
                who=self.curr_player_id, from_who=from_who
            )
        )

        self.update_board(play_sound_name="tile_meld")

        # TODO: reveal previously hidden tiles (2) to other players

    def play_chi(self, possible_chi, call_tiles, from_who):
        # query what chi exactly
        best_chi = possible_chi[0]
        if self.competitors[self.curr_player_id].is_human and len(possible_chi) > 1:
            if self.board:
                self.board.switch_game_state("DECIDING_CHI", possible_moves=possible_chi, target_tile=self.tile)
                while not self.board.input_ready:
                    if not self.gui.playing:
                        exit()
                    pass
                best_chi = possible_chi[self.board.chosen_move]
                self.board.switch_game_state("WAITING")
        elif not self.competitors[self.curr_player_id].is_human and len(possible_chi) > 1:
            best_chi_value = 0.
            for i, chi in enumerate(possible_chi):
                for tile_id_mod in chi:
                    chi_value = call_tiles[self.tile.id34() + tile_id_mod]
                    if best_chi_value < chi_value:
                        best_chi = possible_chi[i]
                        best_chi_value = chi_value

            if not best_chi_value:
                best_chi = random.choice(possible_chi)

        # move tiles to open hand
        meld_tiles = []
        for tile_id_mod in best_chi:
            found = False
            for tile_id in range((self.tile.id34() + tile_id_mod) * 4 + 3,
                                 (self.tile.id34() + tile_id_mod) * 4 - 1, -1):
                for i in range(len(self.closed_hands[self.curr_player_id])):
                    if self.closed_hands[self.curr_player_id][i].id136() == tile_id:
                        meld_tiles.append(self.closed_hands[self.curr_player_id].pop(i))
                        self.open_hand_counts[self.curr_player_id][self.tile.id34() + tile_id_mod] += 1
                        self.closed_hand_counts[self.curr_player_id][self.tile.id34() + tile_id_mod] -= 1

                        found = True
                        break
                if found:
                    break

        meld_tiles.append(self.tile)
        self.open_hands[self.curr_player_id].extend(meld_tiles)
        self.open_hand_counts[self.curr_player_id][self.tile.id34()] += 1
        self.melds[self.curr_player_id].append(
            Meld(
                meld_type=Meld.CHI,
                tiles=[t.id136() for t in meld_tiles],
                opened=True,
                called_tile=self.tile.id136(),
                who=self.curr_player_id, from_who=from_who)
        )

        if self.tile.is_red5():
            self.red5_discarded[self.tile.id34() // 9] = 0
            self.red5_open_hand[self.curr_player_id][self.tile.id34() // 9] = 1

        self.update_board(play_sound_name="tile_meld")

        # TODO: reveal previously hidden tiles (2) to other players

    def play_riichi(self):
        self.hand_in_riichi[self.curr_player_id] = self.turn_no
        self.riichi_status[self.curr_player_id] = RiichiStatus.RIICHI_DISCARD
        self.riichi_status[self.curr_player_id] = RiichiStatus.RIICHI_DISCARD
        self.double_riichi[self.curr_player_id] = self.first_move[self.curr_player_id]

    def set_riichi_discards(self):
        for tile in self.closed_hands[self.curr_player_id]:
            # is shanten still 0 if you discard the tile
            self.can_riichi_discard[self.curr_player_id][tile.id34()] = 0 == correct_shanten(
                [self.closed_hand_counts[self.curr_player_id][i] +
                 self.open_hand_counts[self.curr_player_id][i] -
                 int(i == tile.id34())
                 for i in range(34)],
                self.melds[self.curr_player_id]
            )

    def play_tsumo(self):
        self.event = Event(EventType.WINNER, self.curr_player_id, [self.curr_player_id])

    def decide(self, possible_calls: list[MoveType], target_tile=None):
        if self.competitors[self.curr_player_id].is_human:
            take_action = self.query_human(possible_calls, target_tile)
            return None, None, take_action
        else:
            return self.query_model(possible_calls)

    def query_human(self, possible_calls: list[MoveType], target_tile=None):
        self.board.switch_game_state("DECIDING", possible_moves=possible_calls, target_tile=target_tile)
        while not self.board.input_ready:
            if not self.gui.playing:
                exit()
            pass
        self.board.switch_game_state("WAITING")
        return self.board.chosen_move

    def query_model(self, possible_calls: list[MoveType]):
        tile_to_call = None
        tile_origin = None
        if MoveType.KAN in possible_calls:
            tile_to_call = self.tile.id34()
            tile_origin = self.curr_player_id

        datapoint = DataPoint()
        datapoint.load_input(
            self.curr_player_id, self.round_no, self.turn_no, self.dealer_id, self.prevalent_wind,
            self.seat_wind[self.curr_player_id], self.closed_hand_counts[self.curr_player_id],
            self.open_hand_counts, self.discard_orders, self.hidden_tile_counts[self.curr_player_id],
            self.visible_dora, self.hand_is_closed, self.hand_in_riichi, self.scores,
            self.red5_closed_hand[self.curr_player_id], self.red5_open_hand, self.red5_discarded,
            self.red5_hidden[self.curr_player_id], tile_to_call, tile_origin
        )

        # query the model
        discard_tiles, call_tiles, action = \
            self.competitors[self.curr_player_id].model.get_prediction(datapoint.features)
        discard_tiles = discard_tiles.numpy(force=True)
        call_tiles = call_tiles.numpy(force=True)
        action = action.numpy(force=True)

        # Zero out everything that isn't possible
        for call in MoveType:
            if call not in possible_calls:
                action[call.value] = 0.

        if MoveType.DISCARD in possible_calls:
            for tile_id in range(34):
                if not self.closed_hand_counts[self.curr_player_id][tile_id]:
                    discard_tiles[tile_id] = 0.
            if self.riichi_status[self.curr_player_id] == RiichiStatus.RIICHI_DISCARD:
                for tile_id in range(34):
                    if not self.can_riichi_discard[self.curr_player_id][tile_id]:
                        discard_tiles[tile_id] = 0.

        if MoveType.DISCARD in possible_calls and np.any(discard_tiles):
            # turn the results to probabilities
            discard_tiles /= np.sum(discard_tiles)

        if np.any(action):
            # turn the results to probabilities
            action /= np.sum(action)

        # decide what to do
        discard_tile_id34 = np.argmax(discard_tiles, 0)

        discard_tile = None
        call_tile = None
        take_action = MoveType(np.argmax(action, 0))

        if MoveType.DISCARD:
            if self.closed_hand_counts[self.curr_player_id][discard_tile_id34]:
                # find the actual tile
                for tid136 in range(discard_tile_id34 * 4 + 3, discard_tile_id34 * 4 - 1, -1):
                    discard_tile = Tile(tid136)
                    if discard_tile in self.closed_hands[self.curr_player_id]:
                        break
            else:
                # model is confused and has no idea what to do
                discard_tile = random.choice(self.closed_hands[self.curr_player_id])

        # decide what to do
        return discard_tile, call_tile, take_action

    def run(self):
        self.event = Event(EventType.DRAW_TILE, self.dealer_id)
        while not self.finished:
            match self.event.what:
                case EventType.DRAW_TILE:
                    self.handle_draw_tile()
                case EventType.DISCARD_TILE:
                    self.handle_discard_tile()
                case EventType.TILE_DISCARDED:
                    self.handle_tile_discarded()
                case EventType.ROUND_DRAW:
                    self.handle_round_draw()
                case EventType.WALL_EXHAUSTED:
                    self.handle_wall_exhausted()
                case EventType.WINNER:
                    self.handle_winner()
                case EventType.AFTER_KAN:
                    self.handle_after_kan()
        return self.scores, self.dealer_won, None

    def handle_draw_tile(self):
        # draw the tile and related game logic
        self.curr_player_id = self.event.who
        if self.board:
            self.delay()
            self.changed_curr_player_id()

        if self.event.what == EventType.DRAW_TILE:
            if self.turn_no == 70:
                self.event = Event(EventType.WALL_EXHAUSTED)
                return
            self.turn_no += 1
            self.tile = self.wall[self.turn_no - 1]
        else:
            self.tile = self.dead_wall[self.dora_revealed_no - 1]
            if self.dora_revealed_no == 5 and sum(self.open_hand_counts[self.curr_player_id]) != 16:  # 4 kans by >1 player
                self.four_quads_draw_flag = True

        self.closed_hand_counts[self.curr_player_id][self.tile.id34()] += 1
        self.closed_hands[self.curr_player_id].append(self.tile)
        self.hidden_tile_counts[self.curr_player_id][self.tile.id34()] -= 1
        if self.tile.is_red5():
            self.red5_closed_hand[self.curr_player_id][self.tile.id34() // 9] = 1
            self.red5_hidden[self.curr_player_id][self.tile.id34() // 9] = 0

        self.update_board(play_sound_name="tile_draw")

        # check for nine orphans draw
        if self.competitors[self.curr_player_id].is_human and self.first_move[self.curr_player_id] and sum(
                [self.closed_hand_counts[self.curr_player_id][i] for i in
                 mc.TERMINAL_INDICES + list(range(26, 34))]) >= 9:

            possible_calls = [MoveType.PASS, MoveType.ABORT]
            _, _, action = self.decide(possible_calls)

            if action == MoveType.ABORT:
                self.event = Event(EventType.ROUND_DRAW, -1)
                return

        # checking whether KAN, RIICHI, TSUMO possible
        is_closed_kan_possible = self.is_closed_kan_possible()
        is_added_kan_possible = self.is_added_kan_possible()
        is_riichi_possible = self.is_riichi_possible()
        is_tsumo_possible = self.is_tsumo_possible()

        possible_calls = [MoveType.PASS]
        if is_closed_kan_possible or is_added_kan_possible:
            possible_calls.append(MoveType.KAN)
        if is_riichi_possible:
            possible_calls.append(MoveType.RIICHI)
        if is_tsumo_possible:
            possible_calls.append(MoveType.TSUMO)

        # if nothing but PASS is possible
        if len(possible_calls) == 1:
            self.event = Event(EventType.DISCARD_TILE, self.curr_player_id)
            return

        if is_riichi_possible:
            self.set_riichi_discards()
            self.board.restrict_tiles(self.can_riichi_discard[self.curr_player_id])

        _, _, decision = self.decide(possible_calls)

        # game logic based on decision made
        match decision:
            case MoveType.KAN:
                self.play_kan(is_closed_kan_possible, is_added_kan_possible, self.curr_player_id)

            case MoveType.RIICHI:
                self.board.lift_restriction_tiles()
                self.play_riichi()

            case MoveType.TSUMO:
                self.play_tsumo()

        # update trackers
        self.after_a_kan = False

        # move onto next event, only if playing a call didn't set event type already
        if self.event == EventType.DRAW_TILE:
            self.event = Event(EventType.DISCARD_TILE, self.curr_player_id)

    def handle_discard_tile(self):
        if self.riichi_status[self.curr_player_id].value > 1:  # after initial riichi discard
            self.delay()
            discard_tile = self.closed_hands[self.curr_player_id][-1]
        elif self.competitors[self.curr_player_id].is_human:
            # ask player what to discard
            self.board.switch_game_state("DISCARDING")
            while not self.board.input_ready:
                if not self.gui.playing:
                    exit()
                pass
            discard_tile = self.board.player_hand.selected_tile.tile
            self.board.switch_game_state("WAITING")

            if self.riichi_status[self.curr_player_id] == RiichiStatus.RIICHI_DISCARD:
                self.board.lift_restriction_tiles()
        else:
            self.delay()
            # query the model what to discard
            discard_tile, _, _ = self.decide([MoveType.DISCARD])

        # Actually discard decided tile
        self.closed_hand_counts[self.curr_player_id][discard_tile.id34()] -= 1
        self.closed_hands[self.curr_player_id].remove(discard_tile)
        self.discard_piles[self.curr_player_id].append(discard_tile)
        self.discard_orders[self.curr_player_id][discard_tile.id34()] = self.turn_no

        if discard_tile.is_red5():
            self.red5_closed_hand[self.curr_player_id][discard_tile.id34() // 9] = 0
            self.red5_discarded[discard_tile.id34() // 9] = 1

        self.waiting_tiles[self.curr_player_id] = [False] * 34
        # For furiten tracking: if ready hand, calculate what tiles needed to win
        if self.furiten_status[self.curr_player_id] == FuritenStatus.DEFAULT and 0 == correct_shanten(
                [self.closed_hand_counts[self.curr_player_id][i] +
                 self.open_hand_counts[self.curr_player_id][i]
                 for i in range(34)],
                self.melds[self.curr_player_id]
        ):
            for i in range(34):
                if self.closed_hand_counts[self.curr_player_id][i]:
                    self.waiting_tiles[self.curr_player_id][i] = True
                    if i % 9 > 0 and i < 27 and self.closed_hand_counts[self.curr_player_id][i + 1]:
                        self.waiting_tiles[self.curr_player_id][i - 1] = True
                    if i % 9 < 8 and i < 27 and self.closed_hand_counts[self.curr_player_id][i - 1]:
                        self.waiting_tiles[self.curr_player_id][i + 1] = True

            for i in range(34):
                self.waiting_tiles[self.curr_player_id][i] = \
                    self.waiting_tiles[self.curr_player_id][i] and agari.Agari().is_agari(
                        [self.closed_hand_counts[self.curr_player_id][j] +
                         self.open_hand_counts[self.curr_player_id][j] +
                         int(bool(i)) for j in range(34)],
                        self.open_melds_tile_id34s()
                    )

        if self.discard_after_kan and self.open_kan:
            self.reveal_dora()

        # update board
        if self.board:
            self.update_board(play_sound_name="tile_discard")

        # update hand status trackers
        self.discard_after_kan = False
        self.first_move[self.curr_player_id] = False
        self.ippatsu[self.curr_player_id] = False
        furiten_before = self.furiten_status[self.curr_player_id]
        if self.riichi_status[self.curr_player_id] == RiichiStatus.RIICHI_DISCARD:
            self.riichi_status[self.curr_player_id] = RiichiStatus.RIICHI_NO_STICK
            self.ippatsu[self.curr_player_id] = True
        if self.furiten_status[self.curr_player_id] == FuritenStatus.TEMP_FURITEN:
            self.furiten_status[self.curr_player_id] = FuritenStatus.DEFAULT

        # furiten because of discard?
        if self.furiten_status[self.curr_player_id] != FuritenStatus.PERM_FURITEN and any(
            self.waiting_tiles[self.curr_player_id][i] and self.discard_orders[self.curr_player_id][i]
            for i in range(34)
        ):
            self.furiten_status[self.curr_player_id] = FuritenStatus.TEMP_FURITEN

        if self.board and furiten_before != self.furiten_status[self.curr_player_id]:
            self.update_board()

        self.event = Event(EventType.TILE_DISCARDED, self.curr_player_id)

    def handle_tile_discarded(self):
        from_who = self.event.who
        decision = MoveType.PASS
        self.tile = self.discard_piles[from_who][-1]

        # check for four winds draw
        if self.turn_no == 4 and any(all(self.discard_orders[p][wind] for p in range(4)) for wind in range(27, 31)):
            self.event = Event(EventType.ROUND_DRAW, -1)
            return

        is_chi_possible = [False] * 4
        is_pon_possible = [False] * 4
        is_kan_possible = [False] * 4
        is_ron_possible = [False] * 4
        possible_chi = [[] for _ in range(4)]
        for p in range(4):
            if p == from_who:
                continue
            self.curr_player_id = p

            # reveal the tile
            self.hidden_tile_counts[p][self.tile.id34()] -= 1
            if self.tile.is_red5():
                self.red5_hidden[p][self.tile.id34() // 9] = 0

            # get possible chi
            if p == ((from_who + 1) % 4) and self.tile.id34() < 27 and not self.hand_in_riichi[p]:
                order_in_set = self.tile.id34() % 9
                if (
                    0 < order_in_set < 8 and
                    self.closed_hand_counts[p][self.tile.id34() - 1] and
                    self.closed_hand_counts[p][self.tile.id34() + 1]
                ):
                    possible_chi[p].append((-1, 1))
                if (
                    order_in_set > 1 and
                    self.closed_hand_counts[p][self.tile.id34() - 2] and
                    self.closed_hand_counts[p][self.tile.id34() - 1]
                ):
                    possible_chi[p].append((-2, -1))
                if (
                    order_in_set < 7 and
                    self.closed_hand_counts[p][self.tile.id34() + 1] and
                    self.closed_hand_counts[p][self.tile.id34() + 2]
                ):
                    possible_chi[p].append((1, 2))

            is_chi_possible[p] = bool(possible_chi[p])
            is_pon_possible[p] = self.closed_hand_counts[p][self.tile.id34()] >= 2 and not self.hand_in_riichi[p]
            is_kan_possible[p] = self.closed_hand_counts[p][self.tile.id34()] == 3 and not self.hand_in_riichi[p]
            is_ron_possible[p] = self.is_ron_possible()

        wants = [MoveType.PASS for _ in range(4)]
        call_tiles = [[] for _ in range(4)]
        for p in range(4):
            if p == from_who or \
                    not (is_chi_possible[p] or is_pon_possible[p] or is_kan_possible[p] or is_ron_possible[p]):
                continue
            self.curr_player_id = p

            possible_calls = [MoveType.PASS]
            if is_chi_possible[p]:
                possible_calls.append(MoveType.CHI)
            if is_pon_possible[p]:
                possible_calls.append(MoveType.PON)
            if is_kan_possible[p]:
                possible_calls.append(MoveType.KAN)
            if is_ron_possible[p]:
                possible_calls.append(MoveType.RON)

            _, ct, ac = self.decide(possible_calls)
            call_tiles[p] = ct
            wants[p] = ac

        # Handle priority
        # Set self.current_player_id to the one with prio
        if MoveType.RON in wants:
            for p in range(4):
                if wants[p] == MoveType.RON:
                    self.closed_hands[p].append(self.tile)
                    self.closed_hand_counts[p][self.tile.id34()] += 1
            self.event = Event(EventType.WINNER, self.curr_player_id, [p for p in range(4) if wants[p] == MoveType.RON])
            return
        elif MoveType.KAN in wants or MoveType.PON in wants:
            # find who
            self.curr_player_id = 0
            while wants[self.curr_player_id] != MoveType.KAN and wants[self.curr_player_id] != MoveType.PON:
                self.curr_player_id += 1
            decision = wants[self.curr_player_id]
            self.changed_curr_player_id()
        elif MoveType.CHI in wants:
            decision = MoveType.CHI
            # find who
            self.curr_player_id = 0
            while wants[self.curr_player_id] != MoveType.CHI:
                self.curr_player_id += 1
            self.changed_curr_player_id()

        # the last discard is not a winning tile, check for 4 kan draw or 4 riichi draw
        if self.four_quads_draw_flag or all(self.hand_in_riichi):
            self.event = Event(EventType.ROUND_DRAW, -1)
            return

        new_meld_ids = []
        match decision:
            case MoveType.KAN:
                self.play_kan(False, False, from_who)

            case MoveType.PON:
                self.play_pon(from_who)

            case MoveType.CHI:
                self.play_chi(possible_chi[self.curr_player_id], call_tiles, from_who)

            case MoveType.PASS:
                if self.riichi_status[from_who] == RiichiStatus.RIICHI_NO_STICK:
                    self.riichi_status[from_who] = RiichiStatus.RIICHI
                    self.scores[from_who] -= 10

        # update hand status trackers
        for p in range(4):
            if is_ron_possible[p] and wants[p] != MoveType.RON:
                self.furiten_status[p] = FuritenStatus.PERM_FURITEN if self.hand_in_riichi[p] \
                    else FuritenStatus.TEMP_FURITEN

        if decision != MoveType.PASS:
            self.delay()
            self.hand_is_closed[self.curr_player_id] = 0
            self.discard_piles[from_who].pop()
            self.nagashi_mangan[from_who] = False
            if decision == MoveType.KAN:
                self.event = Event(EventType.AFTER_KAN, self.curr_player_id, from_who)
            else:
                self.event = Event(EventType.DISCARD_TILE, self.curr_player_id)
        else:
            self.event = Event(EventType.DRAW_TILE, (self.curr_player_id + 1) % 4)

    def handle_round_draw(self):
        # no score change, same dealer next round
        if self.board:
            self.board.show_scores(self.scores, [0] * 4, "Draw")
            while not self.board.score_display.ready_to_continue:
                if not self.gui.playing:
                    exit()

        self.dealer_won = True
        self.finished = True

    def handle_after_kan(self):
        self.tile = self.kan_tile
        self.curr_player_id = self.event.who
        # from_who = self.event.from_who

        is_ron_possible = [[False] * 4]
        for p in range(4):
            if p == self.event.who:
                continue
            self.curr_player_id = p
            hand_result = self.get_hand_result()
            is_ron_possible[p] = hand_result.error is None and \
                                 (self.open_kan or any([y.name == "Kokushi Musou" for y in hand_result.yaku]))
            # robbing a kan works only on added kan, or closed kan + thirteen orphans

        self.event = Event(EventType.DRAW_TILE, self.curr_player_id)
        if not any(is_ron_possible):
            return

        wants = [MoveType.PASS for _ in range(4)]
        for p in range(4):
            if p == self.event.who:
                continue
            self.curr_player_id = p

            possible_calls = [MoveType.PASS, MoveType.RON]
            _, _, wants[p] = self.decide(possible_calls, target_tile=self.tile)

        # update hand status trackers
        for p in range(4):
            if is_ron_possible[p] and wants[p] != MoveType.RON:
                self.furiten_status[p] = FuritenStatus.PERM_FURITEN if self.hand_in_riichi[p] \
                    else FuritenStatus.TEMP_FURITEN

        if MoveType.RON in wants:
            for p in range(4):
                if wants[p] == MoveType.RON:
                    self.closed_hands[p].append(self.tile)
                    self.closed_hand_counts[p][self.tile.id34()] += 1

            self.event = Event(
                EventType.WINNER,
                who=[p for p in range(4) if wants[p] == MoveType.RON],
                from_who=self.curr_player_id
            )

    def handle_wall_exhausted(self):
        # check nagashi mangan yaku conditions
        for p in range(4):
            self.nagashi_mangan[p] &= \
                all(not self.discard_orders[i] or i in mc.TERMINAL_INDICES + list(range(26, 34)) for i in range(34))

            if self.nagashi_mangan[p]:
                self.event = Event(EventType.WINNER, [p, [p]])
                return

        has_tenpai = [0] * 4  # ready hand
        for p in range(4):
            has_tenpai[p] = int(correct_shanten([self.closed_hand_counts[p][i] +
                                                 self.open_hand_counts[p][i] for i in range(34)], self.melds[p]) <= 0)
        match sum(has_tenpai):
            case 3:
                for p in range(4):
                    self.scores[p] += 10 if has_tenpai[p] else -30
            case 2:
                for p in range(4):
                    self.scores[p] += 15 if has_tenpai[p] else -15
            case 1:
                for p in range(4):
                    self.scores[p] += 30 if has_tenpai[p] else -10

        if self.board:
            self.board.show_scores(self.scores, [0] * 4, "Wall exhausted")
            while not self.board.score_display.ready_to_continue:
                if not self.gui.playing:
                    exit()

        self.dealer_won = has_tenpai[self.dealer_id]
        self.finished = True

    def handle_winner(self):
        winners = self.event.who
        dealt_in = self.event.from_who

        points_gained = [0] * 4
        yaku_text = ""

        for p in winners:
            self.curr_player_id = p

            # possible
            is_tsumo = (dealt_in in winners)
            is_riichi = bool(self.hand_in_riichi[p])
            is_ippatsu = self.ippatsu[p]
            is_rinshan = self.after_a_kan
            is_chankan = self.stolen_kan
            is_haitei = is_tsumo and self.turn_no == 70
            is_houtei = not is_tsumo and self.turn_no == 70
            is_daburu_riichi = self.double_riichi[p]

            # pretty much impossible
            is_nagashi_mangan = self.nagashi_mangan[p]  # 🗿 https://riichi.wiki/Nagashi_mangan
            is_tenhou = is_tsumo and self.turn_no == 1  # win on first draw (dealer)
            # ron on starting hand (no draws) as a first call of the round
            is_renhou = not is_tsumo and self.first_move[p] and all(not m for m in self.melds)
            # win on first draw, before any call (not dealer)
            is_chiihou = is_tsumo and self.turn_no > 1 and self.first_move[p]
            is_open_riichi = False  # this rule variation doesn't use open riichi yaku
            is_paarenchan = False  # this rule variation doesn't use parenchan yaku

            # other info
            player_wind = wind_from_int(self.seat_wind[p])
            round_wind = wind_from_int(self.prevalent_wind)
            # riichi sticks (no of bets placed)
            kyoutaku_number = sum(rs == RiichiStatus.RIICHI for rs in self.riichi_status)
            tsumi_number = 0  # penalty sticks
            options = OptionalRules(has_aka_dora=True)

            config = HandConfig(is_tsumo, is_riichi, is_ippatsu, is_rinshan, is_chankan, is_haitei,
                                is_houtei, is_daburu_riichi, is_nagashi_mangan, is_tenhou, is_renhou,
                                is_chiihou, is_open_riichi, player_wind, round_wind, kyoutaku_number,
                                tsumi_number, is_paarenchan, options)

            hand_result = self.get_hand_result(config=config)

            # show result
            # TODO: also show fu and han
            yaku_text += (
                ["Player", "Bot1", "Bot2", "Bot3"][p]
                + ("<-" + ["Player", "Bot1", "Bot2", "Bot3"][dealt_in] if p != dealt_in else "")
                + f":{str(hand_result.yaku)}\n"
            )
            print(hand_result.han, hand_result.fu)
            print(hand_result.cost['main'])
            print(hand_result.yaku)
            for fu_item in hand_result.fu_details:
                print(fu_item)
            print('')

            points_gained[p] = hand_result.cost['main'] // 100

        total_plus = sum(points_gained)

        if dealt_in not in winners:  # win by ron
            points_gained[dealt_in] = -total_plus
        else:  # win by tsumo
            for p in range(4):
                if p in winners:
                    continue
                if self.dealer_id in winners:
                    points_gained[p] = -total_plus // 3
                elif self.dealer_id == p:
                    points_gained[p] = -total_plus // 2
                else:
                    points_gained[p] = -total_plus // 4

        for p in range(4):
            self.scores[p] += points_gained[p]

        if self.board:
            self.board.show_scores(
                self.scores,
                points_gained,
                yaku_text.rstrip("\n"),
            )
            while not self.board.score_display.ready_to_continue:
                if not self.gui.playing:
                    exit()

        self.dealer_won = self.dealer_id in winners
        self.finished = True
