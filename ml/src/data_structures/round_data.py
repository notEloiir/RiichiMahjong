from game.src.core.tile import Tile


class MoveData:
    def __init__(self):
        self.move_type = None
        self.tile: Tile | None = None  # used for DRAW, DISCARD, CHI, PON, KAN
        self.base: list[Tile] = []  # only used for CHI, PON, KAN
        self.dora_revealed_ind: Tile | None = None  # only used for KAN
        self.player_id = None


class RoundData:
    def __init__(self, dealer, initial_dora):
        self.moves: list[MoveData] = []
        self.dealer = dealer
        self.dealt_in: int | None = None  # id of player who dealt in, not None only for RON
        self.initial_dora: Tile = initial_dora
        self.uradora = []
        self.score_before = [0] * 4
        self.score_change = [0] * 4
        self.init_hands: list[list[Tile]] = [[] for _ in range(4)]
