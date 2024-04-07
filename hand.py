import pygame
import tile


class PlayerHand():
    def __init__(self, position, size):
        self.position = position
        self.size = size
        self.tiles = pygame.sprite.Group()

    def update_tiles(self, tile_ids):
        self.tiles.empty()
        tile_spacing = 3
        tile_size = (
            int(0.75 * self.size[1]), 
            self.size[1]
        )
        tile_position = (
            (self.size[0] - 14 * (tile_size[0] + tile_spacing) - tile_spacing) // 2, 
            self.position[1]
        )
        for tile_id in tile_ids:
            self.tiles.add(tile.Tile(tile_position, tile_size, tile_id))
            tile_position = (tile_position[0] + tile_size[0] + tile_spacing, tile_position[1])

    def draw(self, display_surface):
        self.tiles.draw(display_surface)