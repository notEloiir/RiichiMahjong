from enum import Enum


class EventType(Enum):
    DRAW_TILE = 0
    DRAW_TILE_AFTER_KAN = 1
    DISCARD_TILE = 2
    TILE_DISCARDED = 3
    ROUND_DRAW = 4
    WALL_EXHAUSTED = 5
    WINNER = 6


class HandStatus(Enum):
    DEFAULT = 0
    RIICHI_DISCARD = 1
    RIICHI_NO_STICK = 2
    RIICHI_NEW = 3
    RIICHI = 4
    TEMP_FURITEN = 5
    PERM_FURITEN = 6


class MoveType(Enum):
    DRAW = 0
    DISCARD = 1
    CHI = 2
    PON = 3
    RIICHI = 4
    RON = 5
    TSUMO = 6
    KAN = 7
    PASS = 8

    def __str__(self):
        return self.name
