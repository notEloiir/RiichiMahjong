from mahjong import shanten
from mahjong.meld import Meld


def correct_shanten(tiles34: list[int], melds: list[Meld]):
    for meld in melds:
        if meld.type == Meld.KAN:
            tiles34[meld.tiles[0] // 4] -= 1
    return shanten.Shanten().calculate_shanten(tiles34)
