class Tile:
    TILES = """
        1m 2m 3m 4m 5m 6m 7m 8m 9m
        1p 2p 3p 4p 5p 6p 7p 8p 9p
        1s 2s 3s 4s 5s 6s 7s 8s 9s
        ew sw ww nw
        wd gd rd
    """

    def __init__(self, tile_id136):
        self.id136 = tile_id136

    def id136(self):
        return self.id136

    def id34(self):
        return self.id136 // 4

    def is_red5(self):
        return self.id34() < 27 and self.id34() % 9 == 4 and self.id136 % 4 == 0

    def __str__(self):
        return Tile.TILES.split()[self.id136 // 4]

    def __eq__(self, other):
        if type(other) != Tile:
            return False
        return self.id136 == other.id136

    def __hash__(self):
        return hash(self.id136)
