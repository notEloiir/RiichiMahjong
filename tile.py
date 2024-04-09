import pygame


# TODO: zrobić resource managera, który wczytuje wszystkie obrazki na początku
class Tile(pygame.sprite.Sprite):
    def __init__(self, position, size, tile_id, rotation=0) -> None:
        pygame.sprite.Sprite.__init__(self)
        self.position = position
        self.size = size
        self.tile_id = tile_id
        self.image = pygame.transform.rotate(self.prepare_tile_image(), rotation * 90)
        self.rect = self.image.get_rect(center=self.position)

    def prepare_tile_image(self):
        symbol_image = """
            Man1 Man2 Man3 Man4 Man5 Man6 Man7 Man8 Man9
            Pin1 Pin2 Pin3 Pin4 Pin5 Pin6 Pin7 Pin8 Pin9
            Sou1 Sou2 Sou3 Sou4 Sou5 Sou6 Sou7 Sou8 Sou9
            EastWind SouthWind WestWind NorthWind
            WhiteDragon GreenDragon RedDragon
        """.split()[self.tile_id // 4]

        image = pygame.image.load("resources/img/tiles/Back.png").convert_alpha()
        image.blit(pygame.image.load("resources/img/tiles/Front.png").convert_alpha(), (0, 0))
        image.blit(pygame.image.load(f"resources/img/tiles/{symbol_image}.png").convert_alpha(), (0, 0))
        return pygame.transform.smoothscale(image, self.size).convert_alpha()

    def draw(self, display_surface):
        display_surface.blit(self.image, self.position)
        