import pygame, tile, settings


class PlayerHand():
    def __init__(self, position, size):
        self.position = position
        self.size = size
        self.tiles = pygame.sprite.Group()
        self.selected_tile = None

    def update_tiles(self, tile_ids):
        self.tiles.empty()
        row_end = self.position[0]
        tile_spacing = 3
        tile_size = (
            int(0.75 * self.size[1]), 
            self.size[1],
        )
        for tile_id in tile_ids:
            tile_position = (
                row_end + tile_size[0] // 2, 
                self.position[1] + self.size[1] // 2,
            )
            row_end += tile_size[0] + tile_spacing
            
            self.tiles.add(tile.Tile(tile_position, tile_size, tile_id, 0))

    def handle_click(self, mouse_pos):
        for tile in self.tiles:
            if tile.rect.collidepoint(mouse_pos):
                self.selected_tile = tile

    def draw(self, display_surface):
        self.tiles.update()
        self.tiles.draw(display_surface)
        for tile in self.tiles:
            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.circle(
                    display_surface, 
                    settings.PRIMARY_COLOR, 
                    (tile.rect.center[0], tile.rect.center[1] + tile.size[1] // 2 + 10),
                    5,
                    2,
                )
            if self.selected_tile and tile.tile_id == self.selected_tile.tile_id:
                pygame.draw.circle(
                    display_surface, 
                    settings.PRIMARY_COLOR, 
                    (tile.rect.center[0], tile.rect.center[1] + tile.size[1] // 2 + 10),
                    5,
                    5,
                )

                
                