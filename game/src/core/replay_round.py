from game.src.core.round import Round
from ml.src.data_structures import DataPoint, RoundData, MoveData
from game.src.core.player import Player
from game.src.core.mahjong_enums import EventType, MoveType


class ReplayRound(Round):
    def __init__(self, competitors: list[Player], scores, non_repeat_round_no, match_type,
                 replay_rounds: RoundData, collect_data=True, gui=None):
        self.replay_rounds = replay_rounds
        self.collect_data = collect_data
        self.collected_data: list[DataPoint] = []

        self.move = MoveData()
        self.move_id = -1  # incremented before decision
        self.deciding_what: EventType = EventType.DRAW_TILE
        move_guard = MoveData()  # safety measure to not go out of range
        move_guard.move_type = MoveType.PASS
        self.replay_rounds.moves.append(move_guard)

        competitors = [Player(is_human=False) for _ in range(4)]
        super().__init__(competitors, scores, non_repeat_round_no, match_type, gui)

        self.dealer_id = replay_rounds.dealer

    def prep_round(self):
        self.dora_indicators = [self.replay_rounds.initial_dora]
        for move in self.replay_rounds.moves:
            if move.dora_revealed_ind is not None:
                self.dora_indicators.append(move.dora_revealed_ind)
        self.uradora_indicators = self.replay_rounds.uradora

        self.reveal_dora()
        for p in range(4):
            self.curr_player_id = p
            for tile in self.replay_rounds.init_hands[p]:
                self.track_draw_tile(tile)
        self.turn_no = 0

    def track_draw_tile(self, tile=None):
        if tile is None and self.turn_no < 70:
            self.increment_move()
            assert self.move.move_type == MoveType.DRAW
            tile = self.move.tile
        super().track_draw_tile(tile)

    def handle_draw_tile(self):
        self.deciding_what = EventType.DRAW_TILE
        super().handle_draw_tile()

    def after_riichi_discard(self):
        self.increment_move()
        assert self.closed_hands[self.curr_player_id][-1] == self.move.tile

    def play_chi(self, possible_chi, chi_prob, from_who, exact_tiles=None):
        if exact_tiles is None:
            exact_tiles = self.move.base
        super().play_chi(possible_chi, chi_prob, from_who, exact_tiles)

    def handle_discard_tile(self):
        self.deciding_what = EventType.DISCARD_TILE
        super().handle_discard_tile()

    def handle_tile_discarded(self):
        self.deciding_what = EventType.TILE_DISCARDED
        super().handle_tile_discarded()

    def handle_after_kan(self):
        self.deciding_what = EventType.AFTER_KAN
        super().handle_after_kan()

    def increment_move(self):
        self.move_id += 1
        self.move = self.replay_rounds.moves[self.move_id]

    def decide(self, possible_calls: list[MoveType], target_tile=None):
        discard_tile, which_chi, take_action = None, None, None
        next_move = self.replay_rounds.moves[self.move_id + 1]
        match self.deciding_what:
            case EventType.DRAW_TILE:
                if MoveType.DRAW in possible_calls:
                    # possible calls: PASS ABORT(kyuushu kyuhai)
                    # output: take_action
                    if next_move.move_type == MoveType.DRAW:
                        self.increment_move()
                        take_action = self.move.move_type
                    else:
                        take_action = MoveType.PASS
                else:
                    # possible calls: PASS KAN RICHI TSUMO
                    # output: take_action
                    if next_move.move_type in (MoveType.KAN, MoveType.RIICHI, MoveType.TSUMO) and \
                            next_move.move_type in possible_calls:
                        self.increment_move()
                        take_action = self.move.move_type
                    else:
                        take_action = MoveType.PASS
            case EventType.DISCARD_TILE:
                # output: discard_tile
                self.increment_move()
                assert self.move.move_type == MoveType.DISCARD
                discard_tile = self.move.tile
            case EventType.TILE_DISCARDED:
                # possible calls: PASS CHI PON KAN RON
                # output: call_tile, take_action
                if next_move.move_type in (MoveType.CHI, MoveType.PON, MoveType.KAN, MoveType.RON) and \
                        next_move.move_type in possible_calls:
                    self.increment_move()
                    if self.move.move_type == MoveType.CHI:
                        chi_delta = [t.id34() - self.move.tile.id34() for t in self.move.base]
                        which_chi = [0] * 3
                        if -2 in chi_delta:
                            which_chi[0] = 1
                        elif 2 in chi_delta:
                            which_chi[2] = 1
                        else:
                            which_chi[1] = 1
                    take_action = self.move.move_type
                else:
                    take_action = MoveType.PASS
            case EventType.AFTER_KAN:
                # possible calls: PASS RON(steal kan)
                # output: take_action
                if next_move.move_type == MoveType.RON:
                    self.increment_move()
                    take_action = self.move.move_type
                else:
                    take_action = MoveType.PASS

        if self.collect_data:
            datapoint = DataPoint()
            self.load_input(datapoint, possible_calls)
            datapoint.load_labels(discard_tile, which_chi, take_action)
            self.collected_data.append(datapoint)
        return discard_tile, which_chi, take_action

    def run(self):
        super().run()
        return self.scores, self.dealer_won, self.collected_data
