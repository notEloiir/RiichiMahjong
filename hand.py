import pygame, tile_sprite, settings


class Hand:
    def __init__(self, position, size, rotation, hidden=True):
        self.position = position
        self.size = size
        self.rotation = rotation
        self.closed_tiles = pygame.sprite.Group()
        self.open_tiles = pygame.sprite.Group()
        self.hidden = hidden

    def update_tiles(self, closed_tiles, open_tiles):
        closed_tiles_sorted = sorted(closed_tiles, key=lambda tile: tile.true_id())

        spacing = 3
        tile_width = (self.size[0] - 18 * spacing) / 19
        tile_height = 4 / 3 * tile_width
        tile_size = (
            tile_width, tile_height
        )

        if self.rotation == 0:
            base_x = self.position[0] + tile_size[0] / 2
            base_y = self.position[1] + self.size[1] / 2
            delta_x = tile_size[0] + spacing
            delta_y = 0
        elif self.rotation == 1:
            base_x = self.position[0] + self.size[1] / 2
            base_y = self.position[1] - tile_size[0] / 2
            delta_x = 0
            delta_y = -(tile_size[0] + spacing)
        elif self.rotation == 2:
            base_x = self.position[0] - tile_size[0] / 2
            base_y = self.position[1] - self.size[1] / 2
            delta_x = -(tile_size[0] + spacing)
            delta_y = 0
        elif self.rotation == 3:
            base_x = self.position[0] - self.size[1] / 2
            base_y = self.position[1] + tile_size[0] / 2
            delta_x = 0
            delta_y = tile_size[0] + spacing

        def get_tile_position(i):
            nonlocal base_x, base_y, delta_x, delta_y

            if self.rotation == 0:
                return (base_x + i * delta_x, base_y + i * delta_y)
            elif self.rotation == 1:
                return (base_x + i * delta_x, base_y + i * delta_y)
            elif self.rotation == 2:
                return (base_x + i * delta_x, base_y + i * delta_y)
            elif self.rotation == 3:
                return (base_x + i * delta_x, base_y + i * delta_y)

        if closed_tiles_sorted != self.closed_tiles:
            self.closed_tiles.empty()
            i = 0
            for tile in closed_tiles_sorted:
                self.closed_tiles.add(
                    tile_sprite.TileSprite(get_tile_position(i), tile_size, tile, self.rotation, hidden=self.hidden)
                )
                i += 1

        if open_tiles != self.open_tiles:
            self.open_tiles.empty()
            i = 19 - len(open_tiles)

            for tile in open_tiles:
                self.open_tiles.add(
                    tile_sprite.TileSprite(get_tile_position(i), tile_size, tile, self.rotation)
                )
                i += 1

    def draw(self, display_surface):
        self.closed_tiles.draw(display_surface)
        self.open_tiles.draw(display_surface)

class PlayerHand(Hand):
    def __init__(self, position, size, rotation=0):
        super().__init__(position, size, rotation, False)
        self.selected_tile = None

    def handle_click(self, mouse_pos):
        for tile in self.closed_tiles:
            if tile.rect.collidepoint(mouse_pos):
                self.selected_tile = tile

    def draw(self, display_surface):
        super().draw(display_surface)

        for tile in self.closed_tiles:
            if tile.rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.circle(
                    display_surface,
                    settings.PRIMARY_COLOR,
                    (tile.rect.center[0], tile.rect.center[1] + tile.size[1] // 2 + 10),
                    5,
                    2,
                )
            if self.selected_tile and tile.tile == self.selected_tile.tile:
                pygame.draw.circle(
                    display_surface,
                    settings.PRIMARY_COLOR,
                    (tile.rect.center[0], tile.rect.center[1] + tile.size[1] // 2 + 10),
                    5,
                    5,
                )
