import pygame, resource_manager


class TileSprite(pygame.sprite.Sprite):
    def __init__(self, position, size, tile, rotation=0, hidden=False) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.size = size
        self.rotation = rotation
        self.hidden = hidden
        self.tile = tile
        self.tile_id = tile.true_id()
        self.tile_name = self.get_tile_name(self.tile_id)
        self.image = self.__get_tile_img()
        self.rect = self.image.get_rect(center=self.position)

    @staticmethod
    def get_tile_name(tile_id):
        tile_names = """
            Man1 Man2 Man3 Man4 Man5 Man6 Man7 Man8 Man9
            Pin1 Pin2 Pin3 Pin4 Pin5 Pin6 Pin7 Pin8 Pin9
            Sou1 Sou2 Sou3 Sou4 Sou5 Sou6 Sou7 Sou8 Sou9
            EastWind SouthWind WestWind NorthWind
            WhiteDragon GreenDragon RedDragon
        """
        return tile_names.split()[tile_id // 4]
    
    def __get_tile_img(self):
        if self.hidden:
            img = resource_manager.get_tile_image("Back")
        else:
            img = resource_manager.get_tile_image(self.tile_name)
        scaled_img = pygame.transform.smoothscale(img, self.size).convert_alpha()
        rotated_img = pygame.transform.rotate(scaled_img, 90 * self.rotation)
        return rotated_img

    def draw(self, display_surface):
        display_surface.blit(self.image, self.position)
        