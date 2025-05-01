from enum import Enum


class EventType(Enum):
    DRAW_TILE = 0
    DISCARD_TILE = 1
    TILE_DISCARDED = 2
    ROUND_DRAW = 3
    WALL_EXHAUSTED = 4
    WINNER = 5
    AFTER_KAN = 6


class RiichiStatus(Enum):
    DEFAULT = 0
    RIICHI_DISCARD = 1
    RIICHI_NO_STICK = 2
    RIICHI = 3


class FuritenStatus(Enum):
    DEFAULT = 0
    TEMP_FURITEN = 1  # logically the same as discard furiten
    PERM_FURITEN = 2


class MoveType(Enum):
    PASS = 0
    DISCARD = 1
    CHI = 2
    PON = 3
    RIICHI = 4
    RON = 5
    TSUMO = 6
    KAN = 7
    DRAW = 8
    ABORT = 9

    def __str__(self):
        return self.name
