import pygame
import gui.tile_sprite as tile_sprite


class DiscardPile:
    def __init__(self, position, size, rotation):
        self.position = position
        self.size = size
        self.rotation = rotation
        self.tiles = pygame.sprite.Group()

    def update_tiles(self, tiles):
        if tiles == self.tiles:
            return

        self.tiles.empty()

        spacing = 3
        tile_size = (
            int(0.75 * ((self.size[1] - 3 * spacing) // 4)),
            (self.size[1] - 3 * spacing) // 4,
        )

        if self.rotation == 0:
            base_x = self.position[0] + tile_size[0] // 2
            base_y = self.position[1] + tile_size[1] // 2
            delta_x = tile_size[0] + spacing
            delta_y = tile_size[1] + spacing
        elif self.rotation == 1:
            base_x = self.position[0] + tile_size[1] // 2
            base_y = self.position[1] - tile_size[0] // 2
            delta_x = tile_size[1] + spacing
            delta_y = -(tile_size[0] + spacing)
        elif self.rotation == 2:
            base_x = self.position[0] - tile_size[0] // 2
            base_y = self.position[1] - tile_size[1] // 2
            delta_x = -(tile_size[0] + spacing)
            delta_y = -(tile_size[1] + spacing)
        elif self.rotation == 3:
            base_x = self.position[0] - tile_size[1] // 2
            base_y = self.position[1] + tile_size[0] // 2
            delta_x = -(tile_size[1] + spacing)
            delta_y = tile_size[0] + spacing
        
        def get_tile_position(row, col):
            nonlocal base_x, base_y, delta_x, delta_y

            if self.rotation == 0:
                return (base_x + col * delta_x, base_y + row * delta_y)
            elif self.rotation == 1:
                return (base_x + row * delta_x, base_y + col * delta_y)
            elif self.rotation == 2:
                return (base_x + col * delta_x, base_y + row * delta_y)
            elif self.rotation == 3:
                return (base_x + row * delta_x, base_y + col * delta_y)

        row = 0
        col = 0

        for tile in tiles:
            if col == 6:
                row += 1
                col = 0

            self.tiles.add(
                tile_sprite.TileSprite(get_tile_position(row, col), tile_size, tile, self.rotation)
            )

            col += 1

    def draw(self, display_surface):
        self.tiles.update()
        self.tiles.draw(display_surface)
