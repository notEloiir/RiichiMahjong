from game.src.core.round import Round
from ml.src.data_structures import DataPoint
from game.src.core.player import Player
from game.src.core.mahjong_enums import EventType, RiichiStatus, FuritenStatus, MoveType
from game.src.core.tile import Tile
from game.src.core.shanten import correct_shanten


class ReplayRound(Round):
    def __init__(self, competitors: list[Player], scores, non_repeat_round_no, match_type,
                 device, replay_rounds, collect_data=True, gui=None):
        self.replay_rounds = replay_rounds
        self.collect_data = collect_data
        self.collected_data: list[DataPoint] = []

        super().__init__(competitors, scores, non_repeat_round_no, match_type, device, gui)