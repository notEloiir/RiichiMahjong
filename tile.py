class Tile:
    TILES = """
        1m 2m 3m 4m 5m 6m 7m 8m 9m
        1p 2p 3p 4p 5p 6p 7p 8p 9p
        1s 2s 3s 4s 5s 6s 7s 8s 9s
        ew sw ww nw
        wd gd rd
    """

    def __init__(self, tile_id):
        self.id = tile_id

    def true_id(self):
        return self.id

    def to_int(self):
        return self.id // 4

    def is_red5(self):
        return self.to_int() < 27 and self.to_int() % 9 == 4 and self.id % 4 == 0

    def __str__(self):
        return Tile.TILES.split()[self.id // 4]

    def __eq__(self, other):
        if type(other) != Tile:
            return False
        return self.id == other.id
