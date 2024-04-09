import pygame, tile


class DiscardPile:
    def __init__(self, position, size):
        self.position = position
        self.size = size
        self.tiles = pygame.sprite.Group()

    def update_tiles(self, tile_ids):
        self.tiles.empty()
        row_end = self.position[0]
        tile_spacing = 3
        tile_size = (
            int(0.75 * ((self.size[1] - 2 * tile_spacing) // 3)), 
            (self.size[1] - 2 * tile_spacing) // 3,
        )
        col = self.position[1] + tile_size[1] // 2
        for i, tile_id in enumerate(tile_ids):
            if i ==6 or i == 12:
                row_end = self.position[0]
                col += tile_size[1] + tile_spacing

            tile_position = (
                row_end + tile_size[0] // 2, 
                col,
            )
            row_end += tile_size[0] + tile_spacing
            
            self.tiles.add(tile.Tile(tile_position, tile_size, tile_id, 0))

    def draw(self, display_surface):
        self.tiles.update()
        self.tiles.draw(display_surface)